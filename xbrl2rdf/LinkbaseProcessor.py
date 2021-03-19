from collections import defaultdict
from lxml import etree
import urllib
import logging

from .const import XLINK_TYPE, XLINK_HREF, XLINK_ID, XLINK_BASE, \
                   XLINK_ROLE, XLINK_LABEL, XBRL_LINKBASE, XBRL_SCHEMA
from .const import XML_LANG
from .const import ID, AS, ABSTRACT, MERGE, NILS, STRICT, IMPLICITFILTERING, \
                   MATCHES, MATCHANY, BINDASSEQUENCE, OUTPUT, \
                   FALLBACKVALUE, ASPECTMODEL, TEST, PARENTCHILDORDER, \
                   SELECT, VARIABLE, DIMENSION, SCHEME
from .const import XLINK_FROM, XLINK_TO, XLINK_ARCROLE, XLINK_TITLE
from .const import XBRLDT_CONTEXTELEMENT, XBRLDT_CLOSED, XBRLDT_TARGETROLE, \
                   XBRLDT_USABLE
from .const import ORDER, USE, PRIORITY, WEIGHT, NAME, COVER, COMPLEMENT, AXIS

from .utilfunctions import processAttribute, isHttpUrl, expandRelativePath, \
                           appendDtsQueue, prependDtsQueue


def processLinkBase(root: etree._Element, base: str, ns: str, params: dict) -> int:
    # first phase searchs for schemas
    logging.info("checking linkbase "+base)
    missingSchemas: int = 0
    for node in root:
        node_type = node.attrib.get(XLINK_TYPE, None)
        if node_type == "extended":
            missingSchemas += checkExtendedLink(node, base, ns, params)
        elif node_type == "simple":
            missingSchemas += checkSimpleLink(node, base, ns, params)
    if missingSchemas > 0:
        appendDtsQueue(XBRL_LINKBASE, base, "", ns, 1, params)
        logging.info("missing schemas "+base)
        return 0
    # second phase translates links into RDF
    logging.info("processing linkbase "+base)
    for node in root:
        node_type = node.attrib.get(XLINK_TYPE, None)
        if node_type == "extended":
            processExtendedLink(node, base, ns, params)
        elif node_type == "simple":
            processSimpleLink(node, base, ns, params)
    return 0


def checkSimpleLink(node: etree._Element, base: str, ns: str, params: dict) -> int:
    missingSchemas = 0
    href = node.attrib.get(XLINK_HREF, None)
    if href is not None:
        # suppress fragment id to avoid problems with loading resource
        uri = href
        if "#" in uri:
            uri = uri.split("#")[0]
        # if resource has relative uri then parent's namespace applies
        if ns and not isHttpUrl(href):
            lns = ns
        else:
            lns = None
        uri = expandRelativePath(uri, base)
        if uri not in params['dts_processed']:
            missingSchemas += 1
            logging.info("found unseen1: "+uri)
            prependDtsQueue(XBRL_SCHEMA, uri, base, lns, 0, params)
    return missingSchemas


def checkExtendedLink(element: etree._Element, base: str, ns: str, params: dict) -> int:
    missingSchemas = 0
    for node in element:
        node_type = node.attrib.get(XLINK_TYPE, None)
        if node_type == "locator":
            href = node.attrib.get(XLINK_HREF, None)
            # suppress fragment id to avoid problems with loading resource
            if href is not None:
                uri = href
                if "#" in uri:
                    uri = uri.split("#")[0]
                # if resource has relative uri then parent's namespace applies
                if ns and not isHttpUrl(href):
                    lns = ns
                else:
                    lns = None
                uri = expandRelativePath(uri, base)
                if uri not in params['dts_processed']:
                    missingSchemas += 1
                    logging.info("found unseen2: "+uri)
                    prependDtsQueue(XBRL_SCHEMA, uri, base, lns, 0, params)
    return missingSchemas


def processSimpleLink(node: etree._Element, base: str, ns: str, params: dict) -> int:
    node_role = node.attrib.get("roleURI", None)
    if node_role:
        declareRole(node_role, 0, params)
    node_arcrole = node.attrib.get("arcroleURI", None)
    if node_arcrole:
        declareRole(node_arcrole, 1, params)
    return 0


def processExtendedLink(element: etree._Element, base: str, ns: str, params: dict) -> int:
    params['xlinkCount'] += 1
    localLocCount = 0
    xlink = {XLINK_ROLE: element.attrib.get(XLINK_ROLE),
             XLINK_ID: element.attrib.get(XLINK_ID),
             XLINK_BASE: element.attrib.get(XLINK_BASE),
             'locators': list(),
             'arcs': list()}
    for node in element:
        localLocCount += 1
        node_type = node.attrib.get(XLINK_TYPE, None)
        if node_type == "locator":
            params['locCount'] += 1
            localLocCount += 1
            locator = {key: node.attrib.get(key) for key
                       in node.attrib if node.attrib.get(key) is not None}
            locator['tag'] = node.tag
            xlink['locators'].append(locator)
        elif node_type == "resource":
            params['resCount'] += 1
            for key in node.attrib:
                if key not in [XLINK_ROLE,
                               XLINK_TYPE,
                               XLINK_LABEL,
                               XLINK_TITLE,
                               XML_LANG,
                               ID,
                               AS,
                               ABSTRACT,
                               MERGE,
                               NILS,
                               STRICT,
                               IMPLICITFILTERING,
                               MATCHES,
                               MATCHANY,
                               BINDASSEQUENCE,
                               NAME,
                               OUTPUT,
                               FALLBACKVALUE,
                               ASPECTMODEL,
                               TEST,
                               PARENTCHILDORDER,
                               SELECT,
                               VARIABLE,
                               DIMENSION,
                               SCHEME]:
                    print("Not supported yet: resource attribute '"+str(key)+"'")

            localLocCount += 1
            resource = {key: node.attrib.get(key) for key
                        in node.attrib if node.attrib.get(key) is not None}
            resource['node'] = node
            resource['tag'] = node.tag
            xlink['locators'].append(resource)
        elif node_type == "arc":
            params['arcCount'] += 1
            for key in node.attrib:
                if key not in [XLINK_FROM,
                               XLINK_TO,
                               XLINK_ARCROLE,
                               XLINK_TITLE,
                               XLINK_TYPE,
                               XBRLDT_CONTEXTELEMENT,
                               XBRLDT_CLOSED,
                               XBRLDT_TARGETROLE,
                               XBRLDT_USABLE,
                               ORDER,
                               USE,
                               PRIORITY,
                               WEIGHT,
                               NAME,
                               COVER,
                               COMPLEMENT,
                               AXIS]:
                    print("Not supported yet: arc attribute '"+str(key)+"'")
            arc = {key: node.attrib.get(key) for key
                   in node.attrib if node.attrib.get(key) is not None}
            arc['tag'] = node.tag
            xlink['arcs'].append(arc)
        else:
            logging.error("Unknown type found in xlink "+node_type)

    labels_nodes = defaultdict(list)
    for locator in xlink['locators']:
        labels_nodes[locator[XLINK_LABEL]].append(locator)

    # fix up relations between arcs and locs
    for arc in xlink['arcs']:
        arc['fromloc'] = list()
        label = arc[XLINK_FROM]
        if label in labels_nodes.keys():
            arc['fromloc'] = labels_nodes[label]
        arc['toloc'] = list()
        label = arc[XLINK_TO]
        if label in labels_nodes.keys():
            arc['toloc'] = labels_nodes[label]

    if params['output_format'] == 1:
        XLink2RDF(element, xlink, base, ns, params)
    elif params['output_format'] == 2:
        XLink2RDFstar(element, xlink, base, ns, params)

    return 0


def process_resource(name: str, resource: dict, base: str, ns: str, params: dict) -> int:

    output = params['out']
    output.write(name+" \n")
    namespace = etree.QName(resource['node']).namespace
    name = etree.QName(resource['node']).localname
    prefix = params['namespaces'].get(namespace, None)
    if prefix is not None:
        output.write("    xl:type "+prefix+":"+name+" ;\n")
    else:
        output.write("    xl:type <"+namespace+"/"+name+"> ;\n")
        
    output.write(processAttribute(resource, XLINK_ROLE,
                                  attr_type=None, params=params))
    output.write(processAttribute(resource, XML_LANG,
                                  attr_type=str, params=params))
    output.write(processAttribute(resource, AS,
                                  attr_type=None, params=params))

    # arc_to boolean attributes
    output.write(processAttribute(resource, ABSTRACT,
                                  attr_type=bool, params=params))
    output.write(processAttribute(resource, MERGE,
                                  attr_type=bool, params=params))
    output.write(processAttribute(resource, NILS,
                                  attr_type=bool, params=params))
    output.write(processAttribute(resource, STRICT,
                                  attr_type=bool, params=params))
    output.write(processAttribute(resource, IMPLICITFILTERING,
                                  attr_type=bool, params=params))
    output.write(processAttribute(resource, MATCHES,
                                  attr_type=bool, params=params))
    output.write(processAttribute(resource, MATCHANY,
                                  attr_type=bool, params=params))
    output.write(processAttribute(resource, BINDASSEQUENCE,
                                  attr_type=bool, params=params))

    # arc_to literal attributes
    output.write(processAttribute(resource, NAME, attr_type=str, params=params))
    output.write(processAttribute(resource, OUTPUT, attr_type=str, params=params))
    output.write(processAttribute(resource, FALLBACKVALUE, attr_type=str, params=params))
    output.write(processAttribute(resource, ASPECTMODEL, attr_type=str, params=params))
    output.write(processAttribute(resource, TEST, attr_type=str, params=params))
    output.write(processAttribute(resource, PARENTCHILDORDER, attr_type=str, params=params))
    output.write(processAttribute(resource, SELECT, attr_type=str, params=params))
    output.write(processAttribute(resource, VARIABLE, attr_type=str, params=params))
    output.write(processAttribute(resource, DIMENSION, attr_type=str, params=params))
    output.write(processAttribute(resource, SCHEME, attr_type=str, params=params))

    # we did not yet do 'id' to Literal

    resource_text = resource['node'].text
    if resource_text and (resource_text) != '\n      ':
        lang = resource.get('{http://www.w3.org/XML/1998/namespace}lang', None)
        if lang is not None:
            output.write('    rdf:value """'+resource_text+'"""@'+lang+' ;\n')
        else:
            output.write('    rdf:value """'+resource_text+'"""; \n')
    # else:
    #     resource_label = getTurtleName(resource, base, ns, params)
    #     if resource_label is not None:
    #         output.write('    xlink:label '+resource_label+' ;\n')

    for child in resource['node']:
        namespace = etree.QName(child).namespace
        name = etree.QName(child).localname
        prefix = params['namespaces'].get(namespace, None)
        if (len(child) > 0) and (child[0].text != '\n          '):
            output.write("    "+prefix+":"+name+' '+child[0].text+' ;\n')
        elif child.text and (child.text != '\n        '):
            output.write("    "+prefix+":"+name+' """'+child.text+'"""^^rdf:XMLLiteral ;\n')

    output.write("    .\n\n")

    return 0


def XLink2RDF(node: etree._Element, xlink: dict, base: str, ns: str, params: dict) -> int:

    output = params['out']

    output.write("# XLINKS\n")
    output.write("# localname: "+etree.QName(node.tag).localname+"\n")
    output.write("# role: "+node.attrib.get(XLINK_ROLE, None)+"\n")
    output.write("# base: "+base+"\n\n")

    if etree.QName(node.tag).localname == "footnoteLink":
        print("Footnote link found, skipping")
        node_role = None
    else:
        node_role = genRoleName(xlink[XLINK_ROLE], 0, params)

    for arc in xlink['arcs']:

        for arc_from in arc['fromloc']:

            for arc_to in arc['toloc']:

                blank = genLinkName(params)

                triple_subject = getTurtleName(arc_from, base, ns, params)
                triple_predicate = genRoleName(arc[XLINK_ARCROLE],
                                               1, params)
                triple_object = getTurtleName(arc_to, base, ns, params)

                output.write(blank + " " + triple_predicate + " [\n")
                output.write("    xl:type xl:link ;\n")

                if node_role:
                    output.write("    xl:role "+node_role+" ;\n")

                # process_arc_attributes

                # addition to xbrlimport / Raggett
                output.write(processAttribute(arc, XBRLDT_CONTEXTELEMENT, attr_type=str, params=params))
                output.write(processAttribute(arc, XBRLDT_TARGETROLE, attr_type=None, params=params))
                output.write(processAttribute(arc, XBRLDT_CLOSED, attr_type=bool, params=params))
                output.write(processAttribute(arc, XBRLDT_USABLE, attr_type=bool, params=params))
                output.write(processAttribute(arc, COVER, attr_type=str, params=params))
                output.write(processAttribute(arc, AXIS, attr_type=str, params=params))
                output.write(processAttribute(arc, COMPLEMENT, attr_type=bool, params=params))
                output.write(processAttribute(arc, NAME, attr_type=str, params=params))
                # end of addition to xbrlimport / Raggett
 
                output.write(processAttribute(arc, USE, attr_type=str, params=params))
                output.write(processAttribute(arc, PRIORITY, attr_type=int, params=params))
                output.write(processAttribute(arc, ORDER, attr_type=float, params=params))
                output.write(processAttribute(arc, WEIGHT, attr_type=float, params=params))

                output.write("    xl:from "+triple_subject+" ;\n")

                locator_type = arc_to.get(XLINK_TYPE, None)
                if locator_type == "resource":
                    name = genResourceName(params)
                    output.write("    xl:to "+name+" ;\n")
                    output.write("    ] .\n\n")
                    process_resource(name, arc_to, base, ns, params)
                else:
                    output.write("    xl:to "+triple_object+" ;\n")
                    output.write("    ] .\n\n")


    return 0


def XLink2RDFstar(node: etree._Element, xlink: dict, base: str, ns: str, params: dict) -> int:

    output = params['out']

    output.write("# XLINKS\n")
    output.write("# localname: "+etree.QName(node.tag).localname+"\n")
    output.write("# role: "+node.attrib.get(XLINK_ROLE, None)+"\n")
    output.write("# base: "+base+"\n\n")

    if etree.QName(node.tag).localname == "footnoteLink":
        print("Footnote link found, skipping")
        node_role = None
    else:
        node_role = genRoleName(xlink[XLINK_ROLE], 0, params)

    for arc in xlink['arcs']:
        for arc_from in arc['fromloc']:
            for arc_to in arc['toloc']:
                triple_subject = getTurtleName(arc_from, base, ns, params)
                triple_predicate = genRoleName(arc[XLINK_ARCROLE],
                                               1, params)
                triple_object = getTurtleName(arc_to, base, ns, params)
                output.write(triple_subject+" "+triple_predicate+" "+triple_object+" .\n")

                found = False
                for a in arc.keys():
                    if a in [XLINK_ROLE,
                             USE,
                             PRIORITY,
                             ORDER,
                             WEIGHT,
                             XBRLDT_CONTEXTELEMENT,
                             XBRLDT_TARGETROLE,
                             XBRLDT_CLOSED,
                             XBRLDT_USABLE,
                             COVER,
                             AXIS,
                             COMPLEMENT,
                             NAME]:
                        found = True
                if found:
                    output.write("<<"+triple_subject + " " + triple_predicate + " " + triple_object+">> \n")
                    output.write(processAttribute(arc, XLINK_ROLE, attr_type=str, params=params))
                    output.write(processAttribute(arc, USE, attr_type=str, params=params))
                    output.write(processAttribute(arc, PRIORITY, attr_type=int, params=params))
                    output.write(processAttribute(arc, ORDER, attr_type=float, params=params))
                    output.write(processAttribute(arc, WEIGHT, attr_type=float, params=params))

                    # addition to xbrlimport / Raggett
                    output.write(processAttribute(arc, XBRLDT_CONTEXTELEMENT, attr_type=str, params=params))
                    output.write(processAttribute(arc, XBRLDT_TARGETROLE, attr_type=None, params=params))
                    output.write(processAttribute(arc, XBRLDT_CLOSED, attr_type=bool, params=params))
                    output.write(processAttribute(arc, XBRLDT_USABLE, attr_type=bool, params=params))
                    output.write(processAttribute(arc, COVER, attr_type=str, params=params))
                    output.write(processAttribute(arc, AXIS, attr_type=str, params=params))
                    output.write(processAttribute(arc, COMPLEMENT, attr_type=bool, params=params))
                    output.write(processAttribute(arc, NAME, attr_type=str, params=params))
                    output.write("    .\n")
                output.write("\n")
                locator_type = arc_to.get(XLINK_TYPE, None)
                if locator_type == "resource":
                    process_resource(arc_to, base, ns, params)

    return 0


def genLinkName(params: dict) -> str:
    params['linkCount'] += 1
    name = "_:link"+str(params['linkCount'])
    return name


def genResourceName(params: dict) -> str:
    params['resourceCount'] += 1
    name = "_:resource"+str(params['resourceCount'])
    return name


def getTurtleName(loc: dict, base: str, ns: str, params: dict) -> str:
    href = loc.get(XLINK_HREF, None)
    if href is not None:
        href = expandRelativePath(href, base)
        res, namespace, name = findId(href, base, params)
        if res != 0:
            # check if href path is in namespaces, presumable a bug in the eiopa taxonomy
            corrected_path = "/".join(href.split("/")[0:-1]).replace("s.", "S.").replace("eu/eu/", "eu/")
            if corrected_path in params['namespaces'].keys():
                namespace = corrected_path
            else:
                # if not found then use parent's namespace and url fragment
                namespace = ns
            name = urllib.parse.urlparse(href).fragment
    else:
        # if no href then use parent's namespace with label
        namespace = ns
        name = loc.get(XLINK_LABEL, None)

    # if label ends with . then delete ., otherwise we get error in turtle
    if name[-1] == ".":
        name = name[0:-1]

    prefix = params['namespaces'].get(namespace, None)
    if prefix is None:
        prefix = "_"

    return prefix+":"+name


def genRoleName(role: str, arc: int, params: dict) -> str:
    base, name = splitRole(role)
    prefix = params['namespaces'].get(base, None)
    if prefix is None:
        if arc:
            prefix = genArcRolePrefixName(params)
        else:
            prefix = genRolePrefixName(params)
        declareNamespace(prefix, base, params)
    return prefix+":"+name


def findId(uri: str, base: str, params: dict) -> tuple([int, str, str]):
    found = params['id2elementTbl'].get(uri, None)
    if found:
        return 0, found[0], found[1]
    return -1, '', ''


def declareNamespace(prefix: str, uri: str, params: dict) -> None:
    params['namespaces'][uri] = prefix
    return None

# used for gensymmed names for nodes
def genArcRolePrefixName(params: dict) -> str:
    params['arcroleNumber'] += 1
    name = "arcrole"+str(params['arcroleNumber'])
    return name


def genRolePrefixName(params: dict) -> str:
    params['roleNumber'] += 1
    name = "role"+str(params['roleNumber'])
    return name


def declareRole(uri: str, arc: int, params: dict) -> None:
    base, name = splitRole(uri)
    if base not in params['namespaces'].keys():
        if arc:
            prefix = genArcRolePrefixName(params)
        else:
            prefix = genRolePrefixName(params)
        params['namespaces'][base] = prefix
    return None

def splitRole(uri: str) -> tuple([str, str]):
    name = uri.split("/")[-1]
    base = "/".join(uri.split("/")[0:-1])
    return base, name
