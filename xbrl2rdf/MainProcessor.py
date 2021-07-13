"""Main module."""

import json
import sys
import click
from io import StringIO, BytesIO
import logging
import os
from os import listdir, mkdir
from os.path import join, isfile, abspath, exists, basename
from datetime import datetime
import rdflib
from pathlib import Path
import hashlib

from .PackageManager import Taxonomies
from .FileSource import openFileSource
from .InstanceProcessor import processInstance
from .DtsProcessor import dispatchDtsQueue
from .utilfunctions import (
    addNamespace,
    printNamespaces,
    expandRelativePath,
    isHttpUrl,
    loadXML,
)
from .const import rdf_file


def MainProcessor(data_url: str, output: str, output_format: int) -> int:
    """Main function to convert one XBRL url to RDF"""

    # list of the files already processed
    dts_processed = list()
    # check to see if json file exists
    for filename in listdir(output):
        if filename == "preloads.json":
            with open(join(output, "preloads.json"), "r") as infile:
                dts_processed = json.load(infile)

    if data_url in dts_processed:
        return 0

    # setup logging
    log_file: str = join(
        output, "".join(os.path.basename(data_url).split(".")[0:-1]) + ".log"
    )
    logging.basicConfig(filename=log_file, level=logging.DEBUG, filemode="w")

    # setup the params dictionary
    params: dict = dict()

    params["packages"] = dict()
    params["uri2file"] = dict()
    params["output_format"] = output_format

    params["namespaces"] = dict()
    params["dts_processed"] = dts_processed
    params["id2elementTbl"] = dict()
    params["dts_queue"] = list()
    params["factCount"] = 0
    params["conceptCount"] = 0
    params["xlinkCount"] = 0
    params["arcCount"] = 0
    params["locCount"] = 0
    params["resCount"] = 0
    params["linkCount"] = 0
    params["fileCount"] = 0
    params["errorCount"] = 0
    params["provenanceNumber"] = 0
    params["arcroleNumber"] = 0
    params["roleNumber"] = 0
    params["resourceCount"] = 0
    params["dtsCount"] = 0
    params[
        "write_types"
    ] = False  # change this to true to write types in ttl, false to not
    params[
        "pagedata"
    ] = dict()  # dict: key: namespace, value stringIO containing document data
    params["sources"] = dict()
    params["urlfilename"] = dict()

    # setup packages
    TAXONOMY_PATH = join(
        os.path.dirname(os.path.abspath(__file__)), "..", "data", "taxonomies"
    )
    taxonomies: list = [
        f
        for f in listdir(TAXONOMY_PATH)
        if isfile(join(TAXONOMY_PATH, f)) and f[-3:] == "zip"
    ]
    manager = Taxonomies(TAXONOMY_PATH)
    for taxonomy in taxonomies:
        manager.addPackage(join(TAXONOMY_PATH, taxonomy))
    manager.rebuildRemappings()
    manager.save()
    for package in manager.config["packages"]:
        taxo_dict = dict()
        taxo_dict["package_name"] = package["name"]
        taxo_dict["package_uri"] = package["URL"]

        fp_taxo_zipfile = openFileSource(package["URL"])
        fp_taxo_zipfile.mappedPaths = package["remappings"]
        fp_taxo_zipfile.open()

        taxo_dict["xbrl_zipfile"] = fp_taxo_zipfile
        params["uri2file"].update(
            {
                abspath(join(taxo_dict["xbrl_zipfile"].url, file)): file
                for file in taxo_dict["xbrl_zipfile"].dir
            }
        )
        params["packages"][package["URL"]] = taxo_dict

    # register standard namespaces
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
    addNamespace("formula", "http://xbrl.org/2008/formula", params)
    addNamespace("customfunction", "http://xbrl.org/2010/custom-function", params)

    # schemas not to include
    params["namespaces_to_skip"] = [
        "http://www.xbrl.org/2003/instance",
        "http://xbrl.org/2005/xbrldt",
        "http://www.xbrl.org/2003/XLink",
        "http://xbrl.org/2008/variable",
        "http://www.xbrl.org/2003/linkbase",
    ]

    params["rdf"] = dict()
    params["rdf"]["instance"] = rdf_file(
        StringIO(),
        os.path.basename(data_url),
        join("data", ".".join(os.path.basename(data_url).split(".")[0:-1])),
    )

    # setup output directories
    Path(join(output, "data")).mkdir(parents=True, exist_ok=True)
    for package in params["packages"].values():
        taxo_dir = ".".join(basename(package["package_uri"]).split(".")[0:-1])
        Path(join(output, "taxonomies", taxo_dir)).mkdir(parents=True, exist_ok=True)

    res = parse_xbrl(data_url, params)
    if res:
        logging.warning(
            "WARNING: "
            + str(params["errorCount"])
            + " error(s) found when importing "
            + data_url
        )

    # save rdf content
    # taxo_complete_content = ""
    for key, item in params["rdf"].items():

        triples: str = item.content.getvalue().replace("\u2264", "")
        if triples != "":

            file_content: str = "# Source HREF: " + item.source + "\n\n"
            file_content += "# RDF triples (turtle syntax)\n\n"
            file_content += printNamespaces(params, triples) + "\n\n" + triples

            # if key != "instance":
            #     taxo_complete_content += file_content

            if key != "instance":
                hashcode = "-" + hashlib.md5(item.source.encode("utf-8")).hexdigest()
            else:
                hashcode = ""

            output_file: str = join(output, item.basename + hashcode + ".ttl")
            assert output_file, "unable to open " + output_file + " for writing!"

            fh = open(output_file, "w", encoding="utf-8")
            fh.write(file_content)
            fh.close()

    # check is rdf triples can be read into graph
    # try:
    #     g = rdflib.Graph()
    #     g.parse(data = file_content.getvalue(), format='turtle')
    #     content = BytesIO()
    #     content.write(g.serialize(format='turtle'))
    # except:
    #     params['log'].write("Error parsing content into graph")

    # write preloads
    with open(join(output, "preloads.json"), "w") as outfile:
        json.dump(params["dts_processed"], outfile, indent=4)

    for package in params["packages"].values():
        package["xbrl_zipfile"].close()

    return 0


def parse_xbrl(uri: str, params: dict) -> int:

    started = datetime.now()

    if (isHttpUrl(uri)) and (uri[0] != "/"):
        base = os.getcwd()
        if base[-1] != os.sep:
            base += os.sep
        uri = expandRelativePath(uri, base)

    if loadXML(processInstance, uri, None, params):
        return -1

    # process taxonomy files
    res = dispatchDtsQueue(params)

    finished = datetime.now()

    logging.info(
        "turtle generation took "
        + str(finished - started)
        + " seconds\nfound:\n"
        + str(params["factCount"])
        + " facts, \n"
        + str(params["conceptCount"])
        + " concepts, \n"
        + str(params["linkCount"])
        + " links, \n"
        + str(params["xlinkCount"])
        + " xlinks, \n"
        + str(params["arcCount"])
        + " arcs, \n"
        + str(params["locCount"])
        + " locators and \n"
        + str(params["resCount"])
        + " resources \nfrom processing "
        + str(params["fileCount"])
        + " files."
    )

    if params["errorCount"] > 0:
        res = 1

    return res
