from collections import defaultdict
from lxml import etree
import urllib
import DtsProcessor
import utilfunctions
import const


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
                               'order',
                               'use',
                               'priority',
                               'weight',
                               'name',
                               'cover',
                               'complement',
                               'axis']:
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

    translateXLink(element, xlink, base, ns, params)

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

    resource_role = resource.get(const.XLINK_ROLE, None)
    if resource_role is not None:
        role_base, role_name = splitRole(resource_role)
        role_prefix = params['namespaces'].get(role_base, None)
        if role_prefix is not None:
            output.write("    xlink:role " + role_prefix +
                         ":"+role_name+" ;\n")
        else:
            output.write("    xlink:role <" + role_base +
                         "/"+role_name+"> ;\n")

    resource_lang = resource.get("{http://www.w3.org/XML/1998/namespace}lang", None)
    if resource_lang:
        output.write('    rdf:lang "'+resource_lang+'" ;\n')

    for key in ['as']:
        value = resource.get(key, None)
        if value is not None:
            value = value.replace("\\", "\\\\")
            output.write('    xl:'+key+' '+value+' ;\n')

    # arc_to boolean attributes
    for key in ['abstract',
                'merge',
                'nils',
                'strict',
                'implicitFiltering',
                'matches',
                'matchAny']:
        value = resource.get(key, None)
        if value is not None:
            value = value.replace("\\", "\\\\")
            output.write('    xl:'+key+' "'+value+'"^^xsd:boolean ;\n')

    # arc_to literal attributes
    for key in ['name', 'output', 'fallbackValue', 'bindAsSequence',
                'aspectModel', 'test', 'parentChildOrder',
                'select', 'variable', 'dimension',
                'scheme']:
        value = resource.get(key, None)
        if value is not None:
            value = value.replace("\\", "\\\\")
            output.write('    xl:' + key + ' """' + value +
                         '"""^^rdf:XMLLiteral ;\n')

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


def translateXLink(node, xlink, base, ns, params):

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
                arc_contextElement = arc.get(const.XBRLDT_CONTEXTELEMENT, None)
                if arc_contextElement:
                    output.write('    xbrldt:contextElement "' +
                                 arc_contextElement + '" ;\n')

                arc_targetRole = arc.get(const.XBRLDT_TARGETROLE, None)
                if arc_targetRole:
                    target_base, target_name = splitRole(arc_targetRole)
                    target_prefix = params['namespaces'].get(target_base, None)
                    if target_prefix:
                        output.write('    xbrldt:targetRole ' + target_prefix +
                                     ':'+target_name+' ;\n')
                    else:
                        output.write('    xbrldt:targetRole <' + target_base +
                                     ':'+target_name+'> ;\n')
                arc_closed = arc.get(const.XBRLDT_CLOSED, None)
                if arc_closed:
                    output.write('    xbrldt:closed "' + arc_closed +
                                 '"^^xsd:boolean ;\n')

                arc_usable = arc.get(const.XBRLDT_USABLE, None)
                if arc_usable:
                    output.write('    xbrldt:usable "' + arc_usable +
                                 '"^^xsd:boolean ;\n')

                arc_cover = arc.get('cover', None)
                if arc_cover:
                    output.write('    xl:cover "' + arc_cover +
                                 '" ;\n')

                arc_axis = arc.get('axis', None)
                if arc_axis:
                    output.write('    xl:axis "' + arc_axis +
                                 '" ;\n')

                arc_complement = arc.get('complement', None)
                if arc_complement:
                    output.write('    xl:complement """' +
                                 arc_complement + '"""^^xsd:boolean ;\n')

                arc_name = arc.get('name', None)
                if arc_name:
                    output.write('    xl:name "'+arc_name+'" ;\n')

                # end of addition to xbrlimport / Raggett

                arc_use = arc.get('use', None)
                if arc_use:
                    output.write('    xl:use "prohibited" ;\n')

                arc_priority = arc.get('priority', None)
                if arc_priority:
                    output.write('    xl:priority "' + str(arc_priority) +
                                 '"^^xsd:integer ;\n')

                arc_order = arc.get('order', None)
                if arc_order and (float(arc_order) >= 0):
                    output.write('    xl:order "' + arc_order +
                                 '"^^xsd:decimal ;\n')

                arc_weight = arc.get('weight', None)
                if arc_weight and (float(arc_weight) >= 0):
                    output.write('    xl:weight "' + arc_weight +
                                 '"^^xsd:decimal ;\n')

                output.write("    xl:from "+triple_subject+" ;\n")
                output.write("    xl:to "+triple_object+" ;\n")
                output.write("    ] .\n\n")

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
