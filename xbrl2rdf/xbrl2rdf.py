"""Main module."""

import sys
import click
from io import StringIO, BytesIO
import logging
import os
from os import listdir
from os.path import join, isfile, abspath
from lxml import etree
import datetime
import rdflib

import PackageManager
import FileSource

import DtsProcessor
import utilfunctions
from InstanceProcessor import *

TAXONOMY_PATH = join("data", "taxonomies")

taxonomies = [f for f in listdir(TAXONOMY_PATH) if isfile(join(TAXONOMY_PATH, f)) and f[-3:]=='zip']
manager = PackageManager.Taxonomies(TAXONOMY_PATH)
for taxonomy in taxonomies:
    manager.addPackage(join(TAXONOMY_PATH, taxonomy))
manager.rebuildRemappings()
manager.save()
taxo_choice = "\n".join([str(idx)+": "+str(item['name']) for idx, item in enumerate(manager.config['packages'])])

@click.command()
@click.option('--url', default=join("data", "instances", "qrs_240_instance.xbrl"), prompt = "input file")
@click.option('--taxo', default=2, prompt=taxo_choice)
@click.option('--output', default=join("data", "rdf"), prompt = "output directory")
@click.option('--output_format', default=1, prompt="1: rdf-turtle\n2: rdf-star-turtle\n")

def main(url, taxo, output, output_format):

    # click.echo("-----------------------------------------------")
    # click.echo("xbrl2rdf: a Python tool to convert XBRL to RDF.")
    # click.echo("-----------------------------------------------")
    # click.echo("XBRL instance file: "+url)
    # click.echo("XBRL taxonomy location: "+out)
    # click.echo("RDF output file: "+out)
    # click.echo("Log file: "+log)
    # click.echo("-----------------------------------------------")

    output_file = join(output, "".join(os.path.basename(url).split(".")[0:-1])+".ttl")
    log_file = join(output, "".join(os.path.basename(url).split(".")[0:-1])+".log")

    fp_taxo_zipfile = FileSource.openFileSource(manager.config['packages'][taxo]['URL'])
    fp_taxo_zipfile.mappedPaths = manager.config['packages'][taxo]["remappings"]
    fp_taxo_zipfile.open()

    params = dict()

    params['log'] = StringIO()
    params['out'] = StringIO()
    params['facts'] = StringIO()
    params['prefix'] = StringIO()

    params['xbrl_zipfile'] = fp_taxo_zipfile
    params['uri2file'] = {abspath(join(params['xbrl_zipfile'].url, file)): file for file in params['xbrl_zipfile'].dir}

    params['package_name'] = manager.config['packages'][taxo]['name']
    params['package_uri'] = manager.config['packages'][taxo]['URL']
    params['output_format'] = output_format

    params['namespaces'] = dict()
    params['dts_processed'] = list()
    params['id2elementTbl'] = dict()
    params['dts_queue'] = list()
    params['factCount'] = 0
    params['conceptCount'] = 0
    params['xlinkCount'] = 0
    params['arcCount'] = 0
    params['locCount'] = 0
    params['resCount'] = 0
    params['linkCount'] = 0
    params['fileCount'] = 0
    params['errorCount'] = 0
    params['provenanceNumber'] = 0
    params['arcroleNumber'] = 0
    params['roleNumber'] = 0

    utilfunctions.addNamespace("xbrli", "http://www.xbrl.org/2003/instance", params)
    utilfunctions.addNamespace("link", "http://www.xbrl.org/2003/linkbase", params)
    utilfunctions.addNamespace("xl", "http://www.xbrl.org/2003/XLink", params)
    utilfunctions.addNamespace("arcrole", "http://www.xbrl.org/2003/arcrole/", params)
    utilfunctions.addNamespace("arcroledim", "http://xbrl.org/int/dim/arcrole/", params)
    utilfunctions.addNamespace("role", "http://www.xbrl.org/2003/role/", params)
    utilfunctions.addNamespace("xsd", "http://www.w3.org/2001/XMLSchema", params)
    utilfunctions.addNamespace("xlink", "http://www.w3.org/1999/xlink", params)
    utilfunctions.addNamespace("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#", params)
    utilfunctions.addNamespace("rdfs", "http://www.w3.org/2000/01/rdf-schema#", params)
    utilfunctions.addNamespace("eurofiling", "http://www.eurofiling.info/xbrl/role", params)

    utilfunctions.addNamespace("enum", "http://xbrl.org/2014/extensible-enumerations", params)
    utilfunctions.addNamespace("gen", "http://xbrl.org/2008/generic", params)
    utilfunctions.addNamespace("iso4217", "http://www.xbrl.org/2003/iso4217", params)
    utilfunctions.addNamespace("label", "http://xbrl.org/2008/label", params)
    utilfunctions.addNamespace("nonnum", "http://www.xbrl.org/dtr/type/non-numeric", params)
    utilfunctions.addNamespace("num", "http://www.xbrl.org/dtr/type/numeric", params)
    utilfunctions.addNamespace("table", "http://xbrl.org/2014/table", params)
    utilfunctions.addNamespace("variable", "http://xbrl.org/2008/variable", params)
    utilfunctions.addNamespace("xbrldi", "http://xbrl.org/2006/xbrldi", params)
    utilfunctions.addNamespace("xbrldt", "http://xbrl.org/2005/xbrldt", params)
    utilfunctions.addNamespace("xbrli", "http://www.xbrl.org/2003/instance", params)
    utilfunctions.addNamespace("xs", "http://www.w3.org/2001/XMLSchema", params)

    utilfunctions.addNamespace("cf", "http://xbrl.org/2008/filter/concept", params)
    utilfunctions.addNamespace("tf", "http://xbrl.org/2008/filter/tuple", params)
    utilfunctions.addNamespace("df", "http://xbrl.org/2008/filter/dimension", params)
    utilfunctions.addNamespace("acf", "http://xbrl.org/2010/filter/aspect-cover", params)
    utilfunctions.addNamespace("mf", "http://xbrl.org/2008/filter/match", params)
    utilfunctions.addNamespace("gf", "http://xbrl.org/2008/filter/general", params)

    utilfunctions.addNamespace("va", "http://xbrl.org/2008/assertion/value", params)
    utilfunctions.addNamespace("ea", "http://xbrl.org/2008/assertion/existence", params)

    # schemas not to include
    params['namespaces_to_skip'] = ["http://www.xbrl.org/2003/instance",
                                   "http://xbrl.org/2005/xbrldt",
                                   "http://www.xbrl.org/2003/XLink",
                                   "http://xbrl.org/2008/variable",
                                   "http://www.xbrl.org/2003/linkbase"]

    # utilfunctions.printNamespaces(params)
    
    res = parse_xbrl(params, url)
    if res:
        params['log'].write("WARNING: "+str(params['errorCount'])+" error(s) found when importing "+url+"\n")

    file_content = StringIO()
    file_content.write("# RDF triples (turtle syntax)\n\n")
    file_content.write("# INSTANCE URI  '"+url+"'\n")
    file_content.write("# TAXONOMY NAME '"+params['package_name']+"'\n")
    file_content.write("# TAXONOMY URI  '"+params['package_uri']+"'\n")
    file_content.write("\n")

    utilfunctions.printNamespaces(params)

    file_content.write(params['prefix'].getvalue())

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

    if output_file:
        # if isinstance(file_content, BytesIO):
        #     fh = open(output_file, "wb")
        # else:
        fh = open(output_file, "w", encoding = 'utf-8')
        fh.write(file_content.getvalue())
        fh.close()

    if log_file:
        fh = open(log_file, "w", encoding = "utf-8")
        fh.write(params['log'].getvalue().replace('\u2264', ''))
        fh.close()

    params['xbrl_zipfile'].close()

    return 0


def parse_xbrl(params, uri):

    started = datetime.datetime.now()

    if (utilfunctions.isHttpUrl(uri)) and (uri[0]!='/'):
        base = os.getcwd()
        if base[-1]!=os.sep:
            base += os.sep
        uri = expandRelativePath(uri, base)

    if utilfunctions.loadXML(processInstance, uri, None, params):
        return -1

    # process taxonomy files
    res = DtsProcessor.dispatchDtsQueue(params)

    finished = datetime.datetime.now()

    params['log'].write("turtle generation took "+str(finished-started)+" seconds\nfound:\n"+
                str(params['factCount'])+" facts, \n" + \
                str(params['conceptCount'])+" concepts, \n"+\
                str(params['linkCount'])+" links, \n"+\
                str(params['xlinkCount'])+" xlinks, \n"+\
                str(params['arcCount'])+" arcs, \n"+\
                str(params['locCount'])+" locators and \n"+\
                str(params['resCount'])+" resources \nfrom processing "+str(params['fileCount'])+" files.\n")

    if params['errorCount'] > 0:
        res = 1

    return res

if __name__ == "__main__":
    sys.exit(main())
