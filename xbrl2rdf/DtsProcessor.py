from lxml import etree
import os

import utilfunctions
from SchemaProcessor import *
from InstanceProcessor import *
from LinkbaseProcessor import *

# examine root element to determine what needs to be done
def processDtsFile(root, base, ns, params):
    if etree.QName(root).localname=="schema":
        res = processSchema(root, base, params);
    elif etree.QName(root).localname=="linkbase":
        res = processLinkBase(root, base, ns, params);
    return res

# push entry onto start of queue if not already present
# the uri was copied as part of expanding relative uris
# but the target namespace needs to be copied here

def prependDtsQueue(uri_type, uri, base, ns, force, params):
    """ put uri at end of dtsqueue
        an item in the DtsQueue consists of uri_type (linkbase, schema), uri and namespace
    """ 
    uri = utilfunctions.expandRelativePath(uri, base)
    if force!=0:
        params['dts_processed'].remove(uri)
    if uri in params['dts_processed']:
        return -1;
    for entry in params['dts_queue']:
        if entry[1]==uri:
            return 0
    params['dts_queue'].insert(0, (uri_type, uri, ns))
    return 0

def appendDtsQueue(uri_type, uri, base, ns, force, params):
    """ put uri at end of dtsqueue if not already present
    """ 
    uri = utilfunctions.expandRelativePath(uri, base)
    if force!=0:
        params['dts_processed'].remove(uri)
    elif uri in params['dts_processed']:
        return -1
    for entry in params['dts_queue']:
        if entry[1]==uri:
            return 0
    params['dts_queue'].append((uri_type, uri, ns))
    return 0

# pop entry from start of queue
# caller responsible for freeing uri
def popDtsQueue(params):
    dts_queue = params['dts_queue']
    if dts_queue!=[]:
        return dts_queue.pop(0)
    return None

def dispatchDtsQueue(params):
    res = 0
    item = popDtsQueue(params)
    while item is not None:
        res = utilfunctions.loadXML(processDtsFile, item[1], item[2], params)
        item = popDtsQueue(params) 
    return res

def showDtsQueue(params):
    count = 0
    for uri_type, uri, ns in params['dts_queue']:
        params['log'].write(srt(count)+": "+uri+"\n")
        count += 1

def dtsQueueLength(params):
    return len(params['dts_queue'])

# Processed dts elements
def addDtsUri(params, uri):
    dts = params['dts_processed']
    if uri in dts:
        return -1
    else:
        dts.append(uri)
        return 0
