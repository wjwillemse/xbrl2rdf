from collections import defaultdict
from lxml import etree
import urllib
import DtsProcessor
import utilfunctions
import const
from utilfunctions import processAttribute

def processLinkBase(root, base, ns, params):
    # first phase searchs for schemas
    params['log'].write("checking linkbase "+base+"\n")
    missingSchemas = 0
    for node in root:
        node_type = node.attrib.get(const.XLINK_TYPE, None)
        if node_type == "extended":
            missingSchemas += checkExtendedLink(node, base, ns, params)
        elif node_type == "simple":
            missingSchemas += checkSimpleLink(node, base, ns, params)
    if missingSchemas > 0:
        DtsProcessor.appendDtsQueue(const.XBRL_LINKBASE, base, "", ns, 1, params)
        params['log'].write("missing schemas "+base+"\n")
        return 0
    # second phase translates links into RDF
    params['log'].write("processing linkbase "+base+"\n")
    for node in root:
        node_type = node.attrib.get(const.XLINK_TYPE, None)
        if node_type == "extended":
            processExtendedLink(node, base, ns, params)
        elif node_type == "simple":
            processSimpleLink(node, base, ns, params)
    return 0


def checkSimpleLink(node, base, ns, params):
    missingSchemas = 0
    href = node.attrib.get(const.XLINK_HREF, None)
    if href is not None:
        # suppress fragment id to avoid problems with loading resource
        uri = href
        if "#" in uri:
            uri = uri.split("#")[0]
        # if resource has relative uri then parent's namespace applies
        if ns and not utilfunctions.isHttpUrl(href):
            lns = ns
        else:
            lns = None
        uri = utilfunctions.expandRelativePath(uri, base)
        if uri not in params['dts_processed']:
            missingSchemas += 1
            params['log'].write("found unseen1: "+uri+"\n")
            DtsProcessor.prependDtsQueue(const.XBRL_SCHEMA, uri, base, lns, 0, params)
    return missingSchemas


def checkExtendedLink(element, base, ns, params):
    missingSchemas = 0
    for node in element:
        node_type = node.attrib.get(const.XLINK_TYPE, None)
        if node_type == "locator":
            href = node.attrib.get(const.XLINK_HREF, None)
            # suppress fragment id to avoid problems with loading resource
            if href is not None:
                uri = href
                if "#" in uri:
                    uri = uri.split("#")[0]
                # if resource has relative uri then parent's namespace applies
                if ns and not utilfunctions.isHttpUrl(href):
                    lns = ns
                else:
                    lns = None
                uri = utilfunctions.expandRelativePath(uri, base)
                if uri not in params['dts_processed']:
                    missingSchemas += 1
                    params['log'].write("found unseen2: "+uri+"\n")
                    DtsProcessor.prependDtsQueue(const.XBRL_SCHEMA, uri, base, lns, 0, params)
    return missingSchemas


def processSimpleLink(node, base, ns, params):
    node_role = node.attrib.get("roleURI", None)
    if node_role:
        declareRole(node_role, 0, params)
    node_arcrole = node.attrib.get("arcroleURI", None)
    if node_arcrole:
        declareRole(node_arcrole, 1, params)
    return 0


def processExtendedLink(element, base, ns, params):
    params['xlinkCount'] += 1
    localLocCount = 0
    xlink = {const.XLINK_ROLE: element.attrib.get(const.XLINK_ROLE),
             const.XLINK_ID: element.attrib.get(const.XLINK_ID),
             const.XLINK_BASE: element.attrib.get(const.XLINK_BASE),
             'locators': list(),
             'arcs': list()}
    for node in element:
        localLocCount += 1
        node_type = node.attrib.get(const.XLINK_TYPE, None)
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
                if key not in [const.XLINK_ROLE,
                               const.XLINK_TYPE,
                               const.XLINK_LABEL,
                               const.XLINK_TITLE,
                               const.XML_LANG,
                               const.ID,
                               const.AS,
                               const.ABSTRACT,
                               const.MERGE,
                               const.NILS,
                               const.STRICT,
                               const.IMPLICITFILTERING,
                               const.MATCHES,
                               const.MATCHANY,
                               const.BINDASSEQUENCE,
                               const.NAME,
                               const.OUTPUT,
                               const.FALLBACKVALUE,
                               const.ASPECTMODEL,
                               const.TEST,
                               const.PARENTCHILDORDER,
                               const.SELECT,
                               const.VARIABLE,
                               const.DIMENSION,
                               const.SCHEME]:
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
                if key not in [const.XLINK_FROM,
                               const.XLINK_TO,
                               const.XLINK_ARCROLE,
                               const.XLINK_TITLE,
                               const.XLINK_TYPE,
                               const.XBRLDT_CONTEXTELEMENT,
                               const.XBRLDT_CLOSED,
                               const.XBRLDT_TARGETROLE,
                               const.XBRLDT_USABLE,
                               const.ORDER,
                               const.USE,
                               const.PRIORITY,
                               const.WEIGHT,
                               const.NAME,
                               const.COVER,
                               const.COMPLEMENT,
                               const.AXIS]:
                    print("Not supported yet: arc attribute '"+str(key)+"'")
            arc = {key: node.attrib.get(key) for key
                   in node.attrib if node.attrib.get(key) is not None}
            arc['tag'] = node.tag
            xlink['arcs'].append(arc)
        else:
            params['log'].write("Unknown type found in xlink " + node_type +
                                "\n")

    labels_nodes = defaultdict(list)
    for locator in xlink['locators']:
        labels_nodes[locator[const.XLINK_LABEL]].append(locator)

    # fix up relations between arcs and locs
    for arc in xlink['arcs']:
        arc['fromloc'] = list()
        label = arc[const.XLINK_FROM]
        if label in labels_nodes.keys():
            arc['fromloc'] = labels_nodes[label]
        arc['toloc'] = list()
        label = arc[const.XLINK_TO]
        if label in labels_nodes.keys():
            arc['toloc'] = labels_nodes[label]

    if params['output_format'] == 1:
        XLink2RDF(element, xlink, base, ns, params)
    elif params['output_format'] == 2:
        XLink2RDFstar(element, xlink, base, ns, params)

    return 0


def process_resource(resource, base, ns, params):

    output = params['out']
    output.write(getTurtleName(resource, base, ns, params)+" \n")
    namespace = etree.QName(resource['node']).namespace
    name = etree.QName(resource['node']).localname
    prefix = params['namespaces'].get(namespace, None)
    if prefix is not None:
        output.write("    xl:type "+prefix+":"+name+" ;\n")
    else:
        output.write("    xl:type <"+namespace+"/"+name+"> ;\n")
        
    output.write(processAttribute(resource, const.XLINK_ROLE, attr_type=None, params=params))
    output.write(processAttribute(resource, const.XML_LANG, attr_type=str, params=params))
    output.write(processAttribute(resource, const.AS, attr_type=None, params=params))

    # arc_to boolean attributes
    output.write(processAttribute(resource, const.ABSTRACT, attr_type=bool, params=params))
    output.write(processAttribute(resource, const.MERGE, attr_type=bool, params=params))
    output.write(processAttribute(resource, const.NILS, attr_type=bool, params=params))
    output.write(processAttribute(resource, const.STRICT, attr_type=bool, params=params))
    output.write(processAttribute(resource, const.IMPLICITFILTERING, attr_type=bool, params=params))
    output.write(processAttribute(resource, const.MATCHES, attr_type=bool, params=params))
    output.write(processAttribute(resource, const.MATCHANY, attr_type=bool, params=params))
    output.write(processAttribute(resource, const.BINDASSEQUENCE, attr_type=bool, params=params))

    # arc_to literal attributes
    output.write(processAttribute(resource, const.NAME, attr_type=str, params=params))
    output.write(processAttribute(resource, const.OUTPUT, attr_type=str, params=params))
    output.write(processAttribute(resource, const.FALLBACKVALUE, attr_type=str, params=params))
    output.write(processAttribute(resource, const.ASPECTMODEL, attr_type=str, params=params))
    output.write(processAttribute(resource, const.TEST, attr_type=str, params=params))
    output.write(processAttribute(resource, const.PARENTCHILDORDER, attr_type=str, params=params))
    output.write(processAttribute(resource, const.SELECT, attr_type=str, params=params))
    output.write(processAttribute(resource, const.VARIABLE, attr_type=str, params=params))
    output.write(processAttribute(resource, const.DIMENSION, attr_type=str, params=params))
    output.write(processAttribute(resource, const.SCHEME, attr_type=str, params=params))

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


def XLink2RDF(node, xlink, base, ns, params):

    output = params['out']

    output.write("# XLINKS\n")
    output.write("# localname: "+etree.QName(node.tag).localname+"\n")
    output.write("# role: "+node.attrib.get(const.XLINK_ROLE, None)+"\n")
    output.write("# base: "+base+"\n\n")

    if etree.QName(node.tag).localname == "footnoteLink":
        print("Footnote link found, skipping")
        node_role = None
    else:
        node_role = genRoleName(xlink[const.XLINK_ROLE], 0, params)

    for arc in xlink['arcs']:

        for arc_from in arc['fromloc']:

            for arc_to in arc['toloc']:

                blank = genLinkName(params)

                triple_subject = getTurtleName(arc_from, base, ns, params)
                triple_predicate = genRoleName(arc[const.XLINK_ARCROLE],
                                               1, params)
                triple_object = getTurtleName(arc_to, base, ns, params)

                output.write(blank + " " + triple_predicate + " [\n")
                output.write("    xl:type xl:link ;\n")

                if node_role:
                    output.write("    xl:role "+node_role+" ;\n")

                # process_arc_attributes

                # addition to xbrlimport / Raggett
                output.write(processAttribute(arc, const.XBRLDT_CONTEXTELEMENT, attr_type=str, params=params))
                output.write(processAttribute(arc, const.XBRLDT_TARGETROLE, attr_type=None, params=params))
                output.write(processAttribute(arc, const.XBRLDT_CLOSED, attr_type=bool, params=params))
                output.write(processAttribute(arc, const.XBRLDT_USABLE, attr_type=bool, params=params))
                output.write(processAttribute(arc, const.COVER, attr_type=str, params=params))
                output.write(processAttribute(arc, const.AXIS, attr_type=str, params=params))
                output.write(processAttribute(arc, const.COMPLEMENT, attr_type=bool, params=params))
                output.write(processAttribute(arc, const.NAME, attr_type=str, params=params))
                # end of addition to xbrlimport / Raggett
 
                output.write(processAttribute(arc, const.USE, attr_type=str, params=params))
                output.write(processAttribute(arc, const.PRIORITY, attr_type=int, params=params))
                output.write(processAttribute(arc, const.ORDER, attr_type=float, params=params))
                output.write(processAttribute(arc, const.WEIGHT, attr_type=float, params=params))

                output.write("    xl:from "+triple_subject+" ;\n")
                output.write("    xl:to "+triple_object+" ;\n")
                output.write("    ] .\n\n")

                locator_type = arc_to.get(const.XLINK_TYPE, None)
                if locator_type == "resource":
                    process_resource(arc_to, base, ns, params)

    return 0


def XLink2RDFstar(node, xlink, base, ns, params):

    output = params['out']

    output.write("# XLINKS\n")
    output.write("# localname: "+etree.QName(node.tag).localname+"\n")
    output.write("# role: "+node.attrib.get(const.XLINK_ROLE, None)+"\n")
    output.write("# base: "+base+"\n\n")

    if etree.QName(node.tag).localname == "footnoteLink":
        print("Footnote link found, skipping")
        node_role = None
    else:
        node_role = genRoleName(xlink[const.XLINK_ROLE], 0, params)

    for arc in xlink['arcs']:
        for arc_from in arc['fromloc']:
            for arc_to in arc['toloc']:
                blank = genLinkName(params)
                triple_subject = getTurtleName(arc_from, base, ns, params)
                triple_predicate = genRoleName(arc[const.XLINK_ARCROLE],
                                               1, params)
                triple_object = getTurtleName(arc_to, base, ns, params)
                output.write(triple_subject+" "+triple_predicate+" "+triple_object+" .\n")

                found = False
                for a in arc.keys():
                    if a in [const.XLINK_ROLE,
                             const.USE,
                             const.PRIORITY,
                             const.ORDER,
                             const.WEIGHT,
                             const.XBRLDT_CONTEXTELEMENT,
                             const.XBRLDT_TARGETROLE,
                             const.XBRLDT_CLOSED,
                             const.XBRLDT_USABLE,
                             const.COVER,
                             const.AXIS,
                             const.COMPLEMENT,
                             const.NAME]:
                        found = True
                if found:
                    output.write("<<"+triple_subject + " " + triple_predicate + " " + triple_object+">> \n")
                    output.write(processAttribute(arc, const.XLINK_ROLE, attr_type=str, params=params))
                    output.write(processAttribute(arc, const.USE, attr_type=str, params=params))
                    output.write(processAttribute(arc, const.PRIORITY, attr_type=int, params=params))
                    output.write(processAttribute(arc, const.ORDER, attr_type=float, params=params))
                    output.write(processAttribute(arc, const.WEIGHT, attr_type=float, params=params))

                    # addition to xbrlimport / Raggett
                    output.write(processAttribute(arc, const.XBRLDT_CONTEXTELEMENT, attr_type=str, params=params))
                    output.write(processAttribute(arc, const.XBRLDT_TARGETROLE, attr_type=None, params=params))
                    output.write(processAttribute(arc, const.XBRLDT_CLOSED, attr_type=bool, params=params))
                    output.write(processAttribute(arc, const.XBRLDT_USABLE, attr_type=bool, params=params))
                    output.write(processAttribute(arc, const.COVER, attr_type=str, params=params))
                    output.write(processAttribute(arc, const.AXIS, attr_type=str, params=params))
                    output.write(processAttribute(arc, const.COMPLEMENT, attr_type=bool, params=params))
                    output.write(processAttribute(arc, const.NAME, attr_type=str, params=params))
                    output.write("    .\n")
                output.write("\n")
                locator_type = arc_to.get(const.XLINK_TYPE, None)
                if locator_type == "resource":
                    process_resource(arc_to, base, ns, params)

    return 0



def genLinkName(params):
    params['linkCount'] += 1
    name = "_:link"+str(params['linkCount'])
    return name


def getTurtleName(loc, base, ns, params):
    href = loc.get(const.XLINK_HREF, None)
    if href is not None:
        href = utilfunctions.expandRelativePath(href, base)
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
        name = loc.get(const.XLINK_LABEL, None)

    # if label ends with . then delete ., otherwise we get error in turtle
    if name[-1] == ".":
        name = name[0:-1]

    prefix = params['namespaces'].get(namespace, None)
    if prefix is None:
        prefix = "_"

    return prefix+":"+name


def genRoleName(role, arc, params):
    base, name = splitRole(role)
    prefix = params['namespaces'].get(base, None)
    if prefix is None:
        if arc:
            prefix = genArcRolePrefixName(params)
        else:
            prefix = genRolePrefixName(params)
        declareNamespace(prefix, base, params)
    return prefix+":"+name


def findId(uri, base, params):
    found = params['id2elementTbl'].get(uri, None)
    if found:
        return 0, found[0], found[1]
    return -1, '', ''


def declareNamespace(prefix, uri, params):
    params['namespaces'][uri] = prefix


# used for gensymmed names for nodes
def genArcRolePrefixName(params):
    params['arcroleNumber'] += 1
    name = "arcrole"+str(params['arcroleNumber'])
    return name


def genRolePrefixName(params):
    params['roleNumber'] += 1
    name = "role"+str(params['roleNumber'])
    return name


def declareRole(uri, arc, params):
    base, name = splitRole(uri)
    if base not in params['namespaces'].keys():
        if arc:
            prefix = genArcRolePrefixName(params)
        else:
            prefix = genRolePrefixName(params)
        params['namespaces'][base] = prefix


def splitRole(uri):
    name = uri.split("/")[-1]
    base = "/".join(uri.split("/")[0:-1])
    return base, name
