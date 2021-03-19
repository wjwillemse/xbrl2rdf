"""Main module."""

import sys
import click
from io import StringIO, BytesIO
import logging
import os
from os import listdir
from os.path import join, isfile, abspath
from datetime import datetime
import rdflib

from .PackageManager import Taxonomies
from .FileSource import openFileSource
from .InstanceProcessor import processInstance
from .DtsProcessor import dispatchDtsQueue
from .utilfunctions import addNamespace, printNamespaces, \
                        expandRelativePath, isHttpUrl, loadXML

TAXONOMY_PATH = join("data", "taxonomies")
taxonomies: list = [f for f in listdir(TAXONOMY_PATH) if isfile(join(TAXONOMY_PATH, f)) and f[-3:] == 'zip']
manager = Taxonomies(TAXONOMY_PATH)
for taxonomy in taxonomies:
    manager.addPackage(join(TAXONOMY_PATH, taxonomy))
manager.rebuildRemappings()
manager.save()
taxo_choices: str = "\n".join([str(idx)+": "+str(item['name']) for idx, item in enumerate(manager.config['packages'])])


@click.command()
@click.option('--url', default=join("data", "instances", "qrs_240_instance.xbrl"), prompt="input file")
@click.option('--taxo', default=2, prompt=taxo_choices)
@click.option('--output', default=join("data", "rdf"), prompt="output directory")
@click.option('--output_format', default=1, prompt="1: rdf-turtle\n2: rdf-star-turtle\n")


def main(url: str, taxo: int, output: str, output_format: int) -> int:

    log_file: str = join(output, "".join(os.path.basename(url).split(".")[0:-1])+".log")
    logging.basicConfig(filename=log_file, level=logging.DEBUG, filemode="w")

    fp_taxo_zipfile: FileSource = openFileSource(manager.config['packages'][taxo]['URL'])
    fp_taxo_zipfile.mappedPaths = manager.config['packages'][taxo]["remappings"]
    fp_taxo_zipfile.open()

    params: dict = dict()

    params['out']: StringIO = StringIO()
    params['facts']: StringIO = StringIO()
    params['prefix']: StringIO = StringIO()

    params['xbrl_zipfile']: FileSource = fp_taxo_zipfile
    params['uri2file']: dict = {abspath(join(params['xbrl_zipfile'].url, file)): file for file in params['xbrl_zipfile'].dir}

    params['package_name']: str = manager.config['packages'][taxo]['name']
    params['package_uri']: str = manager.config['packages'][taxo]['URL']
    params['output_format']: int = output_format

    params['namespaces']: dict = dict()
    params['dts_processed']: list = list()
    params['id2elementTbl']: dict = dict()
    params['dts_queue']: list = list()
    params['factCount']: int = 0
    params['conceptCount']: int = 0
    params['xlinkCount']: int = 0
    params['arcCount']: int = 0
    params['locCount']: int = 0
    params['resCount']: int = 0
    params['linkCount']: int = 0
    params['fileCount']: int = 0
    params['errorCount']: int = 0
    params['provenanceNumber']: int = 0
    params['arcroleNumber']: int = 0
    params['roleNumber']: int = 0
    params['resourceCount']: int = 0

    addNamespace("xbrli", "http://www.xbrl.org/2003/instance", params)
    addNamespace("link", "http://www.xbrl.org/2003/linkbase", params)
    addNamespace("xl", "http://www.xbrl.org/2003/XLink", params)
    addNamespace("arcrole", "http://www.xbrl.org/2003/arcrole/", params)
    addNamespace("arcroledim", "http://xbrl.org/int/dim/arcrole/", params)
    addNamespace("role", "http://www.xbrl.org/2003/role/", params)
    addNamespace("xsd", "http://www.w3.org/2001/XMLSchema", params)
    addNamespace("xlink", "http://www.w3.org/1999/xlink", params)
    addNamespace("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#", params)
    addNamespace("rdfs", "http://www.w3.org/2000/01/rdf-schema#", params)
    addNamespace("eurofiling", "http://www.eurofiling.info/xbrl/role", params)

    addNamespace("enum", "http://xbrl.org/2014/extensible-enumerations", params)
    addNamespace("gen", "http://xbrl.org/2008/generic", params)
    addNamespace("iso4217", "http://www.xbrl.org/2003/iso4217", params)
    addNamespace("label", "http://xbrl.org/2008/label", params)
    addNamespace("nonnum", "http://www.xbrl.org/dtr/type/non-numeric", params)
    addNamespace("num", "http://www.xbrl.org/dtr/type/numeric", params)
    addNamespace("table", "http://xbrl.org/2014/table", params)
    addNamespace("variable", "http://xbrl.org/2008/variable", params)
    addNamespace("xbrldi", "http://xbrl.org/2006/xbrldi", params)
    addNamespace("xbrldt", "http://xbrl.org/2005/xbrldt", params)
    addNamespace("xbrli", "http://www.xbrl.org/2003/instance", params)
    addNamespace("xs", "http://www.w3.org/2001/XMLSchema", params)

    addNamespace("cf", "http://xbrl.org/2008/filter/concept", params)
    addNamespace("tf", "http://xbrl.org/2008/filter/tuple", params)
    addNamespace("df", "http://xbrl.org/2008/filter/dimension", params)
    addNamespace("acf", "http://xbrl.org/2010/filter/aspect-cover", params)
    addNamespace("mf", "http://xbrl.org/2008/filter/match", params)
    addNamespace("gf", "http://xbrl.org/2008/filter/general", params)

    addNamespace("va", "http://xbrl.org/2008/assertion/value", params)
    addNamespace("ea", "http://xbrl.org/2008/assertion/existence", params)

    # schemas not to include
    params['namespaces_to_skip'] = ["http://www.xbrl.org/2003/instance",
                                    "http://xbrl.org/2005/xbrldt",
                                    "http://www.xbrl.org/2003/XLink",
                                    "http://xbrl.org/2008/variable",
                                    "http://www.xbrl.org/2003/linkbase"]

    # utilfunctions.printNamespaces(params)

    res = parse_xbrl(url, params)
    if res:
        logging.warning("WARNING: "+str(params['errorCount'])+" error(s) found when importing "+url)

    params['prefix'] = printNamespaces(params)

    file_content: StringIO = StringIO()
    file_content.write("# RDF triples (turtle syntax)\n\n")
    file_content.write("# INSTANCE URI  '"+url+"'\n")
    file_content.write("# TAXONOMY NAME '"+params['package_name']+"'\n")
    file_content.write("# TAXONOMY URI  '"+params['package_uri']+"'\n")
    file_content.write("\n")
    file_content.write(params['prefix'])
    file_content.write("\n\n")
    file_content.write(params['facts'].getvalue().replace('\u2264', ''))
    file_content.write("\n\n")
    file_content.write(params['out'].getvalue().replace('\u2264', ''))
    # print(list(params['namespaces'].keys()))

    # check is rdf triples can be read into graph
    # try:
    # g = rdflib.Graph()
    # g.parse(data = file_content.getvalue(), format='turtle')
    # file_content = BytesIO()
    # file_content.write(g.serialize(format='turtle'))
    # except:
    #     params['log'].write("Error parsing content into graph")

    output_file: str = join(output, "".join(os.path.basename(url).split(".")[0:-1])+".ttl")
    if output_file:
        # if isinstance(file_content, BytesIO):
        #     fh = open(output_file, "wb")
        # else:
        fh = open(output_file, "w", encoding='utf-8')
        fh.write(file_content.getvalue())
        fh.close()

    params['xbrl_zipfile'].close()

    return 0


def parse_xbrl(uri: str, params: dict) -> int:

    started = datetime.now()

    if (isHttpUrl(uri)) and (uri[0] != '/'):
        base = os.getcwd()
        if base[-1] != os.sep:
            base += os.sep
        uri = expandRelativePath(uri, base)

    if loadXML(processInstance, uri, None, params):
        return -1

    # process taxonomy files
    res = dispatchDtsQueue(params)

    finished = datetime.now()

    logging.info("turtle generation took " + str(finished - started) + " seconds\nfound:\n" +
                 str(params['factCount']) + " facts, \n" +
                 str(params['conceptCount']) + " concepts, \n" +
                 str(params['linkCount']) + " links, \n" +
                 str(params['xlinkCount']) + " xlinks, \n" +
                 str(params['arcCount']) + " arcs, \n" +
                 str(params['locCount']) + " locators and \n" +
                 str(params['resCount']) + " resources \nfrom processing "+str(params['fileCount'])+" files.")

    if params['errorCount'] > 0:
        res = 1

    return res


if __name__ == "__main__":
    sys.exit(main())
