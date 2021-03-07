from lxml import etree
from .utilfunctions import loadXML
from .SchemaProcessor import processSchema
from .LinkbaseProcessor import processLinkBase


def processDtsFile(root, base, ns, params):
    if etree.QName(root).localname == "schema":
        res = processSchema(root, base, params)
    elif etree.QName(root).localname == "linkbase":
        res = processLinkBase(root, base, ns, params)
    return res


def popDtsQueue(params):
    # pop entry from start of queue
    dts_queue = params['dts_queue']
    if dts_queue != []:
        return dts_queue.pop(0)
    return None


def dispatchDtsQueue(params):
    res = 0
    item = popDtsQueue(params)
    while item is not None:
        res = loadXML(processDtsFile, item[1], item[2], params)
        item = popDtsQueue(params)
    return res


def showDtsQueue(params):
    count = 0
    for uri_type, uri, ns in params['dts_queue']:
        params['log'].write(str(count)+": "+uri+"\n")
        count += 1


def dtsQueueLength(params):
    return len(params['dts_queue'])


def addDtsUri(params, uri):
    # Processed dts elements
    dts = params['dts_processed']
    if uri in dts:
        return -1
    else:
        dts.append(uri)
        return 0
