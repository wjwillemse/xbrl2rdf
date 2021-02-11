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
    dts_queue = params['dts_queue']
    uri = utilfunctions.expandRelativePath(uri, base)
    if force:
        removeDtsUri(uri, params)
    if seenDtsUri(uri, params):
        return -1;
    for entry in dts_queue:
        if entry[1]==uri:
            return 0
    dts_queue.insert(0, (uri_type, uri, ns))
    return 0

def appendDtsQueue(uri_type, uri, base, ns, force, params):
    """ put uri at end of dtsqueue if not already present
    """ 
    dts_queue = params['dts_queue']
    uri = utilfunctions.expandRelativePath(uri, base)
    if force:
        removeDtsUri(uri, params)
    elif seenDtsUri(uri, params):
        return -1
    for entry in dts_queue:
        if entry[1]==uri:
            return 0
    dts_queue.append((uri_type, uri, ns))
    return 0

# pop entry from start of queue
# caller responsible for freeing uri
def popDtsQueue(params):
    dts_queue = params['dts_queue']
    if dts_queue!=[]:
        uri = dts_queue.pop(0)
        return uri
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
    found = hashtable_search(dts, uri)
    if found:
        return -1
    res = hashtable_insert(dts, uri, uri)
    return 0

def seenDtsUri(uri, params):
    dts = params['dts_processed']
    found = hashtable_search(dts, uri)
    return found is not None

def removeDtsUri(uri, params):
    dts = params['dts_processed']
    hashtable_remove(dts, uri)
    return None

# the hash table is implemented as a Python dict

def create_hashtable():
    return dict()

def hashtable_search(d, key):
    return d.get(key, None)

def hashtable_remove(d, key):
    del d[key]

def hashtable_insert(d, key, value):
    d[key] = value
