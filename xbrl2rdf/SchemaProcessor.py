from .const import XLINK_HREF, XBRL_LINKBASE
from .const import XBRLI_PERIODTYPE
from .const import MODEL_CREATIONDATE, MODEL_TODATE, MODEL_FROMDATE, \
                   MODEL_MODIFICATIONDATE
from .const import MODEL_HIERARCHY, MODEL_DOMAIN, MODEL_ISDEFAULTMEMBER
from .const import ENUM_LINKROLE, ENUM_DOMAIN
from .const import XBRLDT_TYPEDDOMAINREF, SUBSTITUTIONGROUP, NILLABLE, \
                   ABSTRACT, BALANCE

from .utilfunctions import processAttribute, registerNamespaces, \
                           appendDtsQueue, prependDtsQueue
from datetime import datetime
from lxml import etree
import logging

def processSchema(root: etree._Element, base: str, params: dict) -> int:

    # skip core schemas
    targetNs = root.attrib.get("targetNamespace", None)
    if targetNs in params['namespaces_to_skip']:
        return 0

    logging.info("processing schema "+base)

    registerNamespaces(root, base, params)
    processElements(root, base, targetNs, params)
    xpathobj = root.xpath("//link:linkbaseRef",
                          namespaces={"link":
                                      "http://www.xbrl.org/2003/linkbase"})
    res1 = processLinkBases(xpathobj, base, targetNs, params)
    res2 = processImportedSchema(root, base, targetNs, params)
    return res1 or res2


def processLinkBases(nodes: etree._Element, base: str, targetNs: str, params: dict) -> int:
    res = 0
    logging.info("importing linkbases for base "+base)
    for node in nodes:
        uri = node.attrib.get(XLINK_HREF, None)
        if uri is None:
            logging.error("couldn't identify schema location.")
            return -1
        logging.info("importing "+uri)
        # if linkbase has relative uri then schema namespace applies
        if targetNs and (uri[0:7] != 'http://'):
            lns = targetNs
        else:
            lns = None
        appendDtsQueue(XBRL_LINKBASE, uri, base, lns, 0, params)
    return res


def processImportedSchema(root: etree._Element, base: str, ns: str, params: dict) -> int:
    res = 0
    logging.info("importing schema for base "+base)
    if len(root) == 0:
        logging.error("couldn't find first child element.")
        return -1
    for node in root:
        if (node.tag != "{http://www.w3.org/2001/XMLSchema}import") and \
           (node.tag != "{http://www.w3.org/2001/XMLSchema}include"):
            continue
        schema = node.attrib.get("schemaLocation", None)
        namespace = node.attrib.get("namespace", None)
        prependDtsQueue(XBRL_LINKBASE, schema, base, namespace, 0, params)
    return res


def processElements(root: etree._Element, base: str, targetNs: str, params: dict) -> int:

    output = params['out']
    namespaces = params['namespaces']

    # child_name = etree.QName(child).localname
    # child_namespace = etree.QName(child).namespace

    output.write("# SCHEMAS\n")
    output.write("# target namespace:" + targetNs)
    output.write("# base: "+base+"\n\n")

    for child in root:
        if child.tag == "{http://www.w3.org/2001/XMLSchema}element":
            for item in child.attrib.keys():
                if item not in ['name',
                                'id',
                                'type',
                                XBRLI_PERIODTYPE,
                                MODEL_CREATIONDATE,
                                MODEL_TODATE,
                                MODEL_FROMDATE,
                                MODEL_MODIFICATIONDATE,
                                MODEL_HIERARCHY,
                                MODEL_DOMAIN,
                                MODEL_ISDEFAULTMEMBER,
                                ENUM_LINKROLE,
                                ENUM_DOMAIN,
                                XBRLDT_TYPEDDOMAINREF,
                                SUBSTITUTIONGROUP,
                                NILLABLE,
                                ABSTRACT,
                                BALANCE]:
                    print("Unknown attribute in element: " + str(item))

            child_name = child.attrib.get('name', None)
            prefix = namespaces.get(targetNs, None)
            output.write(prefix+":"+child_name+" \n")

            child_id = child.attrib.get('id', None)

            child_type = child.attrib.get('type', None)
            if child_type:
                # hack for type="string" not type="xsd:string"
                if ":" not in child_type:
                    child_type = "xsd:"+child_type
                elif child_type[0:3] == "xs:":  # strange error, in xbrl?
                    child_type = "xsd:"+child_type[3:]
                output.write("    rdf:type "+child_type+" ;\n")

            output.write(processAttribute(child, XBRLI_PERIODTYPE,
                                          attr_type=str, params=params))
            output.write(processAttribute(child, XBRLDT_TYPEDDOMAINREF,
                                          attr_type=str, params=params))

            output.write(processAttribute(child, MODEL_CREATIONDATE,
                                          attr_type=datetime, params=params))
            output.write(processAttribute(child, MODEL_TODATE,
                                          attr_type=datetime, params=params))
            output.write(processAttribute(child, MODEL_MODIFICATIONDATE,
                                          attr_type=datetime, params=params))

            output.write(processAttribute(child, MODEL_DOMAIN,
                                          attr_type=str, params=params))
            output.write(processAttribute(child, MODEL_HIERARCHY,
                                          attr_type=str, params=params))
            output.write(processAttribute(child, MODEL_ISDEFAULTMEMBER,
                                          attr_type=str, params=params))

            output.write(processAttribute(child, ENUM_DOMAIN,
                                          attr_type=str, params=params))
            output.write(processAttribute(child, ENUM_LINKROLE,
                                          attr_type=str, params=params))

            output.write(processAttribute(child, SUBSTITUTIONGROUP,
                                          attr_type=None, params=params))
            output.write(processAttribute(child, NILLABLE,
                                          attr_type=bool, params=params))
            output.write(processAttribute(child, ABSTRACT,
                                          attr_type=bool, params=params))
            output.write(processAttribute(child, BALANCE,
                                          attr_type=str, params=params))

            output.write('    . \n\n')

            params['conceptCount'] += 1

            # add base#id, targetnamespace:name to dictionary
            if child_id is None:
                logging.info("name = "+child_name)
            else:
                addId(base, child_id, targetNs, child_name, params)
    return 0

def addId(xsdUri: str, child_id: str, targetNs: str, name: str, params: dict) -> int:
    key = xsdUri + "#" + child_id
    value = (targetNs, name)
    if key[0] == '#':
        logging.info('addId: uri = "' + key +
                     '", ns = "' + targetNs +
                     '", name="' + name)
    params['id2elementTbl'][key] = value
    return 0
