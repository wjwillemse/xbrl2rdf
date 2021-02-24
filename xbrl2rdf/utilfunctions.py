import os
import urllib.parse
import DtsProcessor
from lxml import etree
try:
    import regex as re
except ImportError:
    import re


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
    # struct stat st
    res = 0
    if DtsProcessor.addDtsUri(params, uri)!=0:
        return 0 # already loaded

    # if (uri[0:7]=="http://"):
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

        # load file into cache if not already present
        # contentType = None
        # if (stat(filePath, &st) != 0)
        #     res = xmlNanoHTTPFetch((const char *)uri, (const char *)filePath, &contentType);
        #     if contentType is not None:
        #         if (! (!strcmp(contentType, "application/xml") ||
        #                 !strcmp(contentType, "text/xml")) )
        #             unlink((const char *)filePath);
        #             res = -1
        #     xmlNanoHTTPCleanup()
        #     if res:
        #         params['log'].write("Error: couldn't retrieve "+uri+"\n")
        #         params['errorCount'] += 1
        #         return -1

    else: # treat as local file

        if uri[0:6]=="file:/":
            filePath = uri[6:]
        else:
            filePath = uri

        try:
            fp = open(filePath, "rb")
            content = fp.read()
            fp.close()
        except:
            params['log'].write("Error: "+uri+" is malformed\n")
            params['errorCount'] += 1
            return -1

    root = etree.fromstring(content, parser=etree.XMLParser(remove_comments=True))
    if root is None:
        params['log'].write("Error: document has no root element.\n")
        params['errorCount'] += 1
        return -1

    # if root.tag != XML_ELEMENT_NODE:
    #     params['log'].write("Error: document root is not an element.\n")
    #     params['errorCount'] += 1
    #     return -1

    res = handler(root, uri, ns, params)
    
    params['fileCount'] += 1

    return res


# publish namespaces from xbrl root element plus others
# this doesn't deal with the schema or linkbase URIs
# a better solution would be to keep a dictionary and to
# (re)declare namespaces as needed

def registerNamespaces(root, base, params):
    nsmap = root.nsmap
    # if len(nsmap.keys()):
    #     params['out'].write("\n# "+etree.QName(root).localname+" in "+base+"\n")
    for ns in nsmap.keys():
        prefix = ns
        uri = nsmap[ns]
        if uri and prefix and (uri!="http://www.xbrl.org/2003/instance") and \
                              (uri!="http://www.xbrl.org/2003/linkbase") and \
                              (uri!="http://www.w3.org/1999/xlink") and \
                              (uri!="http://www.w3.org/2001/XMLSchema-instance") and \
                              (uri!="http://www.xbrl.org/2003/iso4217"):
            addNamespace(prefix, uri, params)
    # params['prefixes'].write("\n")
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

    # if relPath[0]==os.sep:
    #     i = 0
    #     if base[0:7]=="http://":
    #         # char *p = strchr(base+7, '/')
    #         # if (p != 0)
    #         #    i = (p - base);
    #         p = base[7:].find("/")
    #         if p:
    #            i = (p - base)
    #     return base[0:i] + relPath

    # # strip leading ../ from relPath 
    # up = 0
    # while (relPath[0:3]=="../"):
    #     up += 1
    #     relPath = relPath[3:]

    # # strip leading ./ from relative path 
    # while (relPath[0:2]=="./"):
    #     relPath = relPath[2:]

    # i = len(base)
    # if (up > 0):
    #     # # find where to attach rel path 
    #     last = base.rfind('/')
    #     # if last!=-1:

    #     # while up>0:
    #     #     i -= 1
    #     #     if i<1:
    #     #         return None
    #     #     if base[i-1] == '/':
    #     #         up -= 1
    # elif (base[i-1] != '/'):

    #     # last = base.rfind('/')
    #     # if last:
    #     #     i = last-base+1
    #     res = os.path.join(base, relPath)

    # return res


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


