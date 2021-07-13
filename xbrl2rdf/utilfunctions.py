import os
import urllib.parse
from io import StringIO
from lxml import etree

try:
    import regex as re
except ImportError:
    import re
from .const import predicates, rdf_file
from datetime import datetime
import logging


def processAttribute(
    node, attr, attr_type=None, text_prefix="    ", base=None, params=None
):
    if text_prefix == "    ":
        line_end: str = " ;\n"
    else:
        line_end: str = " .\n"

    if isinstance(node, dict):
        attr_value = node.get(attr, None)
    else:
        attr_value = node.attrib.get(attr, None)
    if attr_value:
        attr_value = attr_value.replace("\\", "\\\\")
        if attr_type == bool:
            return (
                text_prefix
                + predicates[attr]
                + ' "'
                + attr_value
                + '"^^xsd:boolean'
                + line_end
            )
        elif attr_type == str:
            return (
                text_prefix
                + predicates[attr]
                + ' """'
                + attr_value
                + '"""^^rdf:XMLLiteral'
                + line_end
            )
        elif attr_type == int:
            return (
                text_prefix
                + predicates[attr]
                + ' "'
                + attr_value
                + '"^^xsd:integer'
                + line_end
            )
        elif attr_type == float:
            return (
                text_prefix
                + predicates[attr]
                + ' "'
                + attr_value
                + '"^^xsd:decimal'
                + line_end
            )
        elif attr_type == datetime:
            return (
                text_prefix
                + predicates[attr]
                + ' "'
                + attr_value
                + '"^^xsd:dateTime'
                + line_end
            )
        else:
            if base is not None:
                attr_value = (
                    expandRelativePath(attr_value, base)
                    .replace("s.", "S.")
                    .replace("eu/eu/", "eu/")
                )
            name = attr_value.split("/")[-1]
            base = "/".join(attr_value.split("/")[0:-1])
            prefix = params["namespaces"].get(base, None)
            if prefix:
                attr_value = prefix + ":" + name
            elif isHttpUrl(attr_value):
                attr_value = "<" + attr_value + ">"
            return text_prefix + predicates[attr] + " " + attr_value + line_end
    else:
        return ""


def prependDtsQueue(uri_type, uri, base, ns, force, params):
    """put uri at start of dtsqueue
    an item in the DtsQueue consists of uri_type
    (linkbase, schema), uri and namespace
    """
    uri = expandRelativePath(uri, base)
    if force != 0:
        params["dts_processed"].remove(uri)
    for entry in params["dts_queue"]:
        if entry[1] == uri:
            params["dts_queue"].remove(entry)
    params["dts_queue"].insert(0, (uri_type, uri, ns))
    return 0


def appendDtsQueue(uri_type, uri, base, ns, force, params):
    """put uri at end of dtsqueue if not already present"""
    uri = expandRelativePath(uri, base)
    if force != 0:
        if uri is params["dts_processed"]:
            params["dts_processed"].remove(uri)
    for entry in params["dts_queue"]:
        if entry[1] == uri:
            params["dts_queue"].remove(entry)
    #     return -1

    params["dts_queue"].append((uri_type, uri, ns))
    return 0


def isHttpUrl(url):
    return isinstance(url, str) and (
        url.startswith("http://") or url.startswith("https://")
    )


def getLanguageCode():
    return "en"


def isAbsolute(url):
    if url is not None:
        scheme, sep, path = url.partition(":")
        if scheme in ("http", "https", "ftp"):
            return path.startswith("//")
        if scheme == "urn":
            return True
    return False


def loadXML(handler, uri, ns, params):

    if uri in params["dts_processed"]:
        return 0

    res = 0

    if isHttpUrl(uri):

        filePath = None
        for package in params["packages"].values():
            m = package["xbrl_zipfile"].mappedUrl(uri)
            if m is not None:
                mappedUri = os.path.abspath(package["xbrl_zipfile"].mappedUrl(uri))
                if mappedUri in params["uri2file"].keys():
                    filePath = params["uri2file"][mappedUri]
                    xbrl_zipfile = package["xbrl_zipfile"]
                    break

        if filePath == None:
            logging.info('xbrl uri "' + uri + '" not found in zip file.\n')
            return 0

        try:
            fp = xbrl_zipfile.fs.open(filePath, "r")
            content = fp.read()
        except:
            logging.info('Could not read "+uri+" from zip-file.\n')
            params["errorCount"] += 1
            return -1
    else:  # treat as local file
        if uri[0:6] == "file:/":
            filePath = uri[6:]
        else:
            filePath = uri
        try:
            fp = open(filePath, "rb")
            content = fp.read()
            fp.close()
        except:
            logging.error("Error: " + uri + " is malformed\n")
            params["errorCount"] += 1
            return -1

    root = etree.fromstring(content, parser=etree.XMLParser(remove_comments=True))
    if root is None:
        logging.error("Error: document has no root element.\n")
        params["errorCount"] += 1
        return -1

    if handler.__name__ == "processInstance":
        addNamespace("instance", os.path.basename(uri), params)
        handlerPrefix = "instance"
    elif handler.__name__ == "processDtsFile":
        params["dtsCount"] = params["dtsCount"] + 1
        dtsCount = str(params["dtsCount"])
        currentDts = "dts" + dtsCount
        # safeUri = urllib.parse.quote(uri, safe='')
        # full https filenames are too long for OS sometimes
        simpleUri = ".".join(os.path.basename(uri).split(".")[0:-1])
        addNamespace(currentDts, uri, params)
        taxo_dir = ".".join(os.path.basename(package["package_uri"]).split(".")[0:-1])
        params["rdf"][currentDts] = rdf_file(
            StringIO(), uri, os.path.join("taxonomies", taxo_dir, simpleUri)
        )
        handlerPrefix = currentDts
    else:
        assert False, "unregistered handler: " + handler.__name__

    res = handler(root, uri, ns, params, handlerPrefix)

    params["dts_processed"].append(uri)
    params["fileCount"] += 1

    return res


def registerNamespaces(root, base, params):
    nsmap = root.nsmap
    for prefix in nsmap.keys():
        uri = nsmap[prefix]
        if uri not in params["namespaces_to_skip"]:
            addNamespace(prefix, uri, params)
    return 0


def addNamespace(prefix, uri, params):
    namespaces = params["namespaces"]
    found = namespaces.get(uri, None)
    if found:
        if prefix != found:
            # print("error!!! prefix with different uris")
            # print(prefix+ ", " + found + ", " + uri)
            return -1
        del namespaces[uri]
    namespaces[uri] = prefix
    # params['prefixes'].write("@prefix "+prefix+": <"+uri+">.\n")
    return 0


def printNamespaces(params: dict, triples: str):
    namespaces = params["namespaces"]
    res: str = ""
    for uri in namespaces:
        if triples is not None:
            if namespaces[uri] + ":" in triples:
                if uri[-1] != "#":
                    res += "@prefix " + namespaces[uri] + ": <" + uri + "#>.\n"
                else:
                    res += "@prefix " + namespaces[uri] + ": <" + uri + ">.\n"
        else:
            if uri[-1] != "#":
                res += "@prefix " + namespaces[uri] + ": <" + uri + "#>.\n"
            else:
                res += "@prefix " + namespaces[uri] + ": <" + uri + ">.\n"
    return res


def expandRelativePath(relPath, base):

    # if relPath[0:7]=="http://":
    if isHttpUrl(relPath):
        return relPath
    elif relPath[0] == "#":
        return base + relPath
    else:
        return urllib.parse.urljoin(base, relPath)


xmlEncodingPattern = re.compile(r"\s*<\?xml\s.*encoding=['\"]([^'\"]*)['\"].*\?>")


def encoding_type(xml, default="utf-8"):
    if isinstance(xml, bytes):
        s = xml[0:120]
        if s.startswith(b"\xef\xbb\xbf"):
            return "utf-8-sig"
        if s.startswith(b"\xff\xfe"):
            return "utf-16"
        if s.startswith(b"\xfe\xff"):
            return "utf-16"
        if s.startswith(b"\xff\xfe\x00\x00"):
            return "utf-32"
        if s.startswith(b"\x00\x00\xfe\xff"):
            return "utf-32"
        if s.startswith(b"# -*- coding: utf-8 -*-"):
            return "utf-8"  # python utf=encoded
        if b"x\0m\0l" in s:
            str = s.decode("utf-16")
        else:
            str = s.decode("latin-1")
    else:
        str = xml[0:80]
    match = xmlEncodingPattern.match(str)
    if match and match.lastindex == 1:
        return match.group(1)
    return default
