from lxml import etree
import utilfunctions
import SchemaProcessor
import LinkbaseProcessor


def processDtsFile(root, base, ns, params):
    if etree.QName(root).localname == "schema":
        res = SchemaProcessor.processSchema(root, base, params)
    elif etree.QName(root).localname == "linkbase":
        res = LinkbaseProcessor.processLinkBase(root, base, ns, params)
    return res


def prependDtsQueue(uri_type, uri, base, ns, force, params):
    """ put uri at start of dtsqueue
        an item in the DtsQueue consists of uri_type
        (linkbase, schema), uri and namespace
    """
    uri = utilfunctions.expandRelativePath(uri, base)
    if force != 0:
        params['dts_processed'].remove(uri)
    for entry in params['dts_queue']:
        if entry[1] == uri:
            params['dts_queue'].remove(entry)
    params['dts_queue'].insert(0, (uri_type, uri, ns))
    return 0


def appendDtsQueue(uri_type, uri, base, ns, force, params):
    """ put uri at end of dtsqueue if not already present
    """
    uri = utilfunctions.expandRelativePath(uri, base)
    if force != 0:
        params['dts_processed'].remove(uri)
    for entry in params['dts_queue']:
        if entry[1] == uri:
            params['dts_queue'].remove(entry)
    #     return -1

    params['dts_queue'].append((uri_type, uri, ns))
    return 0


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
        res = utilfunctions.loadXML(processDtsFile, item[1], item[2], params)
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
