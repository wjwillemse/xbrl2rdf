import os
import urllib.parse
from lxml import etree
try:
    import regex as re
except ImportError:
    import re
import const
from datetime import datetime

def processAttribute(node, attr, attr_type=None, text_prefix='    ', params=None):
    if text_prefix == '    ':
        line_end = ' ;\n'
    else:
        line_end = ' .\n'

    if isinstance(node, dict):
        attr_value = node.get(attr, None)
    else:
        attr_value = node.attrib.get(attr, None)
    if attr_value:
        attr_value = attr_value.replace("\\", "\\\\")
        if attr_type == bool:
            return text_prefix+const.predicates[attr] + ' "' + attr_value + '"^^xsd:boolean'+line_end
        elif attr_type == str:
            return text_prefix+const.predicates[attr] + ' """' + attr_value + '"""^^rdf:XMLLiteral'+line_end
        elif attr_type == int:
            return text_prefix+const.predicates[attr] + ' "' + attr_value + '"^^xsd:integer'+line_end
        elif attr_type == float:
            return text_prefix+const.predicates[attr] + ' "' + attr_value + '"^^xsd:decimal'+line_end
        elif attr_type == datetime:
            return text_prefix+const.predicates[attr] + ' "' + attr_value + '"^^xsd:dateTime'+line_end
        else:
            name = attr_value.split("/")[-1]
            base = "/".join(attr_value.split("/")[0:-1])
            prefix = params['namespaces'].get(base, None)
            if prefix:
                attr_value = prefix+":"+name
            return text_prefix+const.predicates[attr]+' '+attr_value+line_end
    else:
        return ''


def isHttpUrl(url):
    return isinstance(url, str) and (url.startswith("http://") or url.startswith("https://"))


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

    res = 0

    if uri in params['dts_processed']:
        return 0 # already loaded
    else:
        params['dts_processed'].append(uri)

    if isHttpUrl(uri):
        mappedUri = os.path.abspath(params['xbrl_zipfile'].mappedUrl(uri))
        if mappedUri not in params['uri2file'].keys():
            params['log'].write('xbrl uri "'+uri+'" not found in zip file.\n')
            return 0
        filePath = params['uri2file'][mappedUri]
        try:
            fp = params['xbrl_zipfile'].fs.open(filePath, "r")
            content = fp.read()
        except:
            params['log'].write("Could not read "+uri+" from zip-file.\n")
            params['errorCount'] += 1
            return -1

    else:  # treat as local file

        if uri[0:6]=="file:/":
            filePath = uri[6:]
        else:
            filePath = uri

        try:
            fp = open(filePath, "rb")
            content = fp.read()
            fp.close()
        except e:
            params['log'].write("Error: "+uri+" is malformed\n")
            params['errorCount'] += 1
            raise(e)
            return -1

    root = etree.fromstring(content, parser=etree.XMLParser(remove_comments=True))
    if root is None:
        params['log'].write("Error: document has no root element.\n")
        params['errorCount'] += 1
        return -1

    res = handler(root, uri, ns, params)
    
    params['fileCount'] += 1

    return res


def registerNamespaces(root, base, params):
    nsmap = root.nsmap
    for prefix in nsmap.keys():
        uri = nsmap[prefix]
        if uri not in params['namespaces_to_skip']:
            addNamespace(prefix, uri, params)
    return 0

def addNamespace(prefix, uri, params):
    namespaces = params['namespaces']
    found = namespaces.get(uri, None)
    if found:
        if prefix!=found:
            # print("error!!! prefix with different uris")
            # print(prefix+ ", " + found + ", " + uri)
            return -1
        del namespaces[uri]
    namespaces[uri] = prefix
    # params['prefixes'].write("@prefix "+prefix+": <"+uri+">.\n")
    return 0


def printNamespaces(params):
    namespaces = params['namespaces']
    for uri in namespaces:
        if uri[-1]!="#":
            params['prefix'].write("@prefix "+namespaces[uri]+": <"+uri+"#>.\n")
        else:
            params['prefix'].write("@prefix "+namespaces[uri]+": <"+uri+">.\n")


def expandRelativePath(relPath, base):

    # if relPath[0:7]=="http://":
    if isHttpUrl(relPath):
        return relPath
    elif relPath[0]=='#':
        return base+relPath
    else:
        return urllib.parse.urljoin(base, relPath)

xmlEncodingPattern = re.compile(r"\s*<\?xml\s.*encoding=['\"]([^'\"]*)['\"].*\?>")


def encoding(xml, default="utf-8"):
    if isinstance(xml,bytes):
        s = xml[0:120]
        if s.startswith(b'\xef\xbb\xbf'):
            return 'utf-8-sig'
        if s.startswith(b'\xff\xfe'):
            return 'utf-16'
        if s.startswith(b'\xfe\xff'):
            return 'utf-16'
        if s.startswith(b'\xff\xfe\x00\x00'):
            return 'utf-32'
        if s.startswith(b'\x00\x00\xfe\xff'):
            return 'utf-32'
        if s.startswith(b'# -*- coding: utf-8 -*-'):
            return 'utf-8'  # python utf=encoded
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
