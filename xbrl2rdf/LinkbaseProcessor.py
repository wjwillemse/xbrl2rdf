import DtsProcessor
import utilfunctions
from collections import defaultdict
from lxml import etree
import urllib

XBRL_LINKBASE = 1
XBRL_SCHEMA = 0

def processLinkBase(root, base, ns, params):

    missingSchemas = 0

    params['log'].write("checking linkbase "+base+"\n")

    # first phase searchs for schemas
    for node in root:
#         if (node->type != XML_ELEMENT_NODE)
#              continue;
        node_type = node.attrib.get('{http://www.w3.org/1999/xlink}type', None)
        if node_type=="extended":
            missingSchemas += checkExtendedLink(node, base, ns, params)
        elif node_type=="simple":
            missingSchemas += checkSimpleLink(node, base, ns, params)

    if missingSchemas > 0:
        DtsProcessor.appendDtsQueue(XBRL_LINKBASE, base, "", ns, 1, params)
        params['log'].write("missing schemas "+base+"\n")
        return 0

    params['log'].write("processing linkbase "+base+"\n")

    # second phase translates links into RDF
    for node in root:
#         if (node->type != XML_ELEMENT_NODE)
#              continue;
        node_type = node.attrib.get('{http://www.w3.org/1999/xlink}type', None)
        if node_type=="extended":
            processExtendedLink(node, base, ns, params)
        elif node_type=="simple":
            processSimpleLink(node, base, ns, params)

    return 0


def checkSimpleLink(node, base, ns, params):
    missingSchemas = 0
    href = node.attrib.get("{http://www.w3.org/1999/xlink}href", None)
    if href is not None:
        # suppress fragment id to avoid problems with loading resource
        uri = href
        if "#" in uri:
            uri = uri.split("#")[0]
        # if resource has relative uri then parent's namespace applies
        # const char *lns = (ns && strncmp((char *)href, "http://", 7) ? ns : NULL);
        if ns and not utilfunctions.isHttpUrl(href):
            lns = ns
        else:
            lns = None
        # returns false if uri has already been processed
        if DtsProcessor.prependDtsQueue(XBRL_SCHEMA, uri, base, lns, 0, params)!=-1:
            missingSchemas += 1
            params['log'].write("found unseen1: "+uri+"\n")

    return missingSchemas


def checkExtendedLink(element, base, ns, params):
    missingSchemas = 0
    for node in element:
        # if (node->type != XML_ELEMENT_NODE)
        #     continue;
        node_type = node.attrib.get('{http://www.w3.org/1999/xlink}type', None)
        if node_type=="locator":
            href = node.attrib.get("{http://www.w3.org/1999/xlink}href", None)
            # suppress fragment id to avoid problems with loading resource
            if href is not None:
                uri = href
                if "#" in uri:
                    uri = uri.split("#")[0]
                uri = utilfunctions.expandRelativePath(uri, base)
                # if resource has relative uri then parent's namespace applies
                # const char *lns = (ns && strncmp((char *)href, "http://", 7) ? ns : NULL);
                if ns and not utilfunctions.isHttpUrl(href):
                    lns = ns
                else:
                    lns = None
                # returns false if uri has already been processed
                if DtsProcessor.prependDtsQueue(XBRL_SCHEMA, uri, base, lns, 0, params)!=-1:
                    missingSchemas += 1
                    params['log'].write("found unseen2: "+uri+"\n")

    return missingSchemas

# simple links are used to point to linkbases and taxonomy schemas
# with the xlink:href attribute. If defined use xml:base in place
# of the document URI for resolving relative links. The xlink:role
# attribute may be used to describe the link's role. I am unsure as
# to whether simple links add triples or just aid in Dts discovery
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
    
    xlink = {'{http://www.w3.org/1999/xlink}role': element.attrib.get('{http://www.w3.org/1999/xlink}role'),
             '{http://www.w3.org/1999/xlink}id': element.attrib.get('{http://www.w3.org/1999/xlink}id'),
             '{http://www.w3.org/1999/xlink}base': element.attrib.get('{http://www.w3.org/1999/xlink}base'),
             'locators': list(),
             'arcs': list()}

    for node in element:

#         if (node->type != XML_ELEMENT_NODE)
#             continue;

        localLocCount += 1 

        node_type = node.attrib.get("{http://www.w3.org/1999/xlink}type", None)

        if node_type=="locator":
            params['locCount'] += 1
            localLocCount += 1
            locator = {key: node.attrib.get(key) for key in node.attrib if node.attrib.get(key) is not None}
            locator['tag'] = node.tag
            xlink['locators'].append(locator)

        elif node_type=="resource":
            params['resCount'] += 1
            localLocCount += 1
            resource = {key: node.attrib.get(key) for key in node.attrib if node.attrib.get(key) is not None}
            resource['node'] = node
            resource['tag'] = node.tag
            xlink['locators'].append(resource)

        elif node_type=="arc":
            params['arcCount'] += 1
            for key in node.attrib:
                    if key not in ['{http://www.w3.org/1999/xlink}from',
                                   '{http://www.w3.org/1999/xlink}to',
                                   '{http://www.w3.org/1999/xlink}arcrole',
                                   '{http://www.w3.org/1999/xlink}title',
                                   '{http://www.w3.org/1999/xlink}type',
                                   '{http://xbrl.org/2005/xbrldt}contextElement',
                                   '{http://xbrl.org/2005/xbrldt}closed',
                                   '{http://xbrl.org/2005/xbrldt}targetRole',
                                   '{http://xbrl.org/2005/xbrldt}usable',
                                   'order', 
                                   'use', 
                                   'priority', 
                                   'weight',
                                   'name',
                                   'cover',
                                   'complement',
                                   'axis']:
                        print("Not supported yet: arc attribute '"+str(key)+"'")

            arc = {key: node.attrib.get(key) for key in node.attrib if node.attrib.get(key) is not None}
            arc['tag'] = node.tag
            xlink['arcs'].append(arc)
#             float f = -1.0;
#             xmlChar *order = xmlGetProp(node, (const xmlChar *)"order");
#             if (order)
#             {
#                sscanf((char *)order, "%f", &f);
#                 xmlFree(order);
#             }
#             arc->order = f;

#             xmlChar *use = xmlGetProp(node, (const xmlChar *)"use");
#             arc->use = (use && samestring(use, "prohibited") ? 1 : 0);
#             xmlFree(use);

#             int d = -1;
#             xmlChar *priority = xmlGetProp(node, (const xmlChar *)"priority");
#             if (priority)
#             {
#                 sscanf((char *)priority, "%d", &d);
#                 xmlFree(priority);
#             }
#             arc->priority = d;

#             f = -1.0;
#             xmlChar *weight = xmlGetProp(node, (const xmlChar *)"weight");
#             if (weight)
#             {
#                 sscanf((char *)weight, "%f", &f);
#                 xmlFree(weight);
#             }
#             arc->weight = f;

#             if (xlink->arc)
#                 xlink->lastArc->next = arc;
#             else
#                 xlink->arc = arc;

        else:
            params['log'].write("Unknown type found in xlink " + node_type + "\n")

    labels_nodes = defaultdict(list)

    for locator in xlink['locators']:
        labels_nodes[locator['{http://www.w3.org/1999/xlink}label']].append(locator)

    # fix up pointers between arcs and locs
    for arc in xlink['arcs']:
        arc['fromloc'] = list()
        label = arc['{http://www.w3.org/1999/xlink}from']
        if label in labels_nodes.keys():
            arc['fromloc'] = labels_nodes[label]
        arc['toloc'] = list()
        label = arc['{http://www.w3.org/1999/xlink}to']
        if label in labels_nodes.keys():
            arc['toloc'] = labels_nodes[label]

    # fix up pointers between arcs and locs
#     Arc *arc;
#     for (arc = xlink->arc; arc; arc = arc->next)
#     {
#         Locator *loc;
#         char *label = (char *)(arc->fromLabel);

#         if (localLocCount > BIG_XLINK)
#             loc = findLabel(label);
#         else
#         {
#             for (loc = xlink->loc; loc; loc = loc->next)
#             {
#                 if (samestring(loc->label, label))
#                     break;
#             }
#         }

#         assert(loc);
#         LocList *item = malloc(sizeof(LocList));
#         assert(item);
#         item->loc = loc;
#         item->next = arc->fromLoc;
#         arc->fromLoc = item;

#         label = (char *)(arc->toLabel);

#         if (localLocCount > BIG_XLINK)
#             loc = findLabel(label);
#         else
#         {
#             for (loc = arc->prevLoc; loc; loc = loc->prev)
#             {
#                 if (samestring(loc->label, label))
#                     break;
#             }

#             if (!loc)
#             {
#                 loc = (arc->prevLoc ? arc->prevLoc->next : xlink->loc);

#                 for (; loc; loc = loc->next)
#                 {
#                     if (samestring(loc->label, label))
#                         break;
#                 }
#             }
#         }

#         assert(loc);
#         item = malloc(sizeof(LocList));
#         assert(item);
#         item->loc = loc;
#         item->next = arc->toLoc;
#         arc->toLoc = item;
#     }

    # translateXLink_resources(element, xlink, base, ns, params)

    # translateXLink_locators(element, xlink, base, ns, params)

    translateXLink(element, xlink, base, ns, params)

    return 0

def process_resource(resource, base, ns, params):

    params['out'].write("    xl:to [ \n")

    namespace = etree.QName(resource['node']).namespace
    name = etree.QName(resource['node']).localname
    prefix = params['namespaces'].get(namespace, None)

    params['out'].write("        xl:type "+prefix+":"+name+" ;\n")

    resource_lang = resource.get("{http://www.w3.org/XML/1998/namespace}lang", None)
    if resource_lang:
        params['out'].write('        rdf:lang "'+resource_lang+'" ;\n')

    for key in ['as']:
        value = resource.get(key, None)
        if value is not None:
            value = value.replace("\\", "\\\\")
            params['out'].write('    xl:'+key+' '+value+' ;\n')

    # arc_to boolean attributes
    for key in ['abstract', 'merge', 'nils', 'strict','implicitFiltering', 'matches', 'matchAny']:
        value = resource.get(key, None)
        if value is not None:
            value = value.replace("\\", "\\\\")
            params['out'].write('        xl:'+key+' "'+value+'"^^xsd:boolean ;\n')

    # arc_to literal attributes
    for key in ['name', 'output', 'fallbackValue', 'bindAsSequence',
                'aspectModel', 'test', 'parentChildOrder',
                'select', 'variable', 'dimension', 
                'scheme']:
        value = resource.get(key, None)
        if value is not None:
            value = value.replace("\\", "\\\\")
            params['out'].write('        xl:'+key+' """'+value+'"""^^rdf:XMLLiteral ;\n')

    # we did not yet do 'id' to Literal

    resource_text = resource['node'].text
    if resource_text and (resource_text)!='\n      ':
        lang = resource.get('{http://www.w3.org/XML/1998/namespace}lang', None)
        if lang is not None:
            params['out'].write('        rdf:value """'+resource_text+'"""@'+lang+' ;\n')
        else:
            params['out'].write('        rdf:value """'+resource_text+'"""; \n')

    for child in resource['node']:
        namespace = etree.QName(child).namespace
        name = etree.QName(child).localname
        prefix = params['namespaces'].get(namespace, None)
        if len(child)>0:
            params['out'].write("        "+prefix+":"+name+' '+child[0].text+' ;\n')
        elif child.text:
            params['out'].write("        "+prefix+":"+name+' """'+child.text+'"""^^rdf:XMLLiteral ;\n')

    params['out'].write("        ] ;\n")
    return 0

def translateXLink_locators(node, xlink, base, ns, params):

    return 0

def translateXLink(node, xlink, base, ns, params):

    params['out'].write("# XLINKS\n")
    params['out'].write("# localname: "+etree.QName(node.tag).localname+"\n")
    params['out'].write("# role: "+node.attrib.get('{http://www.w3.org/1999/xlink}role', None)+"\n")
    params['out'].write("# base: "+base+"\n\n")

    # footnoteLink has xlink:role="http://www.xbrl.org/2003/role/link"
    # which isn't really worth noting in the RDF, so suppress it here
    
    # char *role = samestring(node->name, "footnoteLink") ? NULL :
    #                       shortRoleName((char *)(xlink->role), 0);
    if etree.QName(node.tag).localname=="footnoteLink":
        node_role = None
    else:
        node_role = shortRoleName(xlink["{http://www.w3.org/1999/xlink}role"], 0, params)

    for arc in xlink['arcs']:

        for arc_from in arc['fromloc']:

            for arc_to in arc['toloc']:

                blank = genLinkName(params)

                triple_subject = getTurtleName(arc_from, base, ns, params)
                triple_predicate = shortRoleName(arc['{http://www.w3.org/1999/xlink}arcrole'], 1, params)
                triple_object = getTurtleName(arc_to, base, ns, params)

                params['out'].write(blank + " " +triple_predicate+ " [\n")
                params['out'].write("    xl:type xl:link ;\n")

                if node_role:
                    params['out'].write("    xl:role "+node_role+" ;\n")

                # process_arc_attributes
                # addition to xbrlimport / Raggett
                arc_contextElement = arc.get('{http://xbrl.org/2005/xbrldt}contextElement', None)
                if arc_contextElement:
                    params['out'].write('    xbrldt:contextElement "'+arc_contextElement+'" ;\n')

                arc_targetRole = arc.get('{http://xbrl.org/2005/xbrldt}targetRole', None)
                if arc_targetRole:
                    target_base, target_name = splitRole(arc_targetRole)
                    target_prefix = params['namespaces'].get(target_base, None)
                    if target_prefix:
                        params['out'].write('    xbrldt:targetRole '+target_prefix+":"+target_name+' ;\n')
                    else:
                        params['out'].write('    xbrldt:targetRole <'+target_base+":"+target_name+'> ;\n')
                arc_closed = arc.get('{http://xbrl.org/2005/xbrldt}closed', None)
                if arc_closed:
                    params['out'].write('    xbrldt:closed "'+arc_closed+'"^^xsd:boolean ;\n')

                arc_usable = arc.get('{http://xbrl.org/2005/xbrldt}usable', None)
                if arc_usable:
                    params['out'].write('    xbrldt:usable "'+arc_usable+'"^^xsd:boolean ;\n')

                arc_cover = arc.get('cover', None)
                if arc_cover:
                    params['out'].write('    xl:cover "'+arc_cover+'" ;\n')

                arc_axis = arc.get('axis', None)
                if arc_axis:
                    params['out'].write('    xl:axis "'+arc_axis+'" ;\n')

                arc_complement = arc.get('complement', None)
                if arc_complement:
                    params['out'].write('    xl:complement "'+arc_complement+'" ;\n')

                arc_name = arc.get('name', None)
                if arc_name:
                    params['out'].write('    xl:name "'+arc_name+'" ;\n')
                # end of addition to xbrlimport / Raggett

                arc_use = arc.get('use', None)
                if arc_use:
                    params['out'].write('    xl:use "prohibited" ;\n')

                arc_priority = arc.get('priority', None)
                if arc_priority:
                    params['out'].write('    xl:priority "'+ str(arc_priority) + '"^^xsd:integer ;\n')

                arc_order = arc.get('order', None)
                if arc_order and (float(arc_order) >= 0):
                    params['out'].write('    xl:order "'+arc_order+'"^^xsd:decimal ;\n')

                arc_weight = arc.get('weight', None)
                if arc_weight and (float(arc_weight)>=0):
                    params['out'].write('    xl:weight "'+arc_weight+'"^^xsd:decimal ;\n')

                params['out'].write("    xl:from "+triple_subject+" ;\n")
                
                # arc to node attributes
                locator_type = arc_to.get("{http://www.w3.org/1999/xlink}type", None)
                if locator_type=="resource":

                    process_resource(arc_to, base, ns, params)
                    # # process children of the arc_to object
                    # if len(arc_to_node)>=1:
                    #     # char *xml = xmlFragmentToString(node->children);
                    #     xml = ''
                    #     for child in arc_to_node:
                    #         if child.text and child.text!='\n        ':
                    #             xml += child.text
                    #     if xml and xml!='\n        ':
                    #         params['out'].write('    rdf:value """'+xml+'"""^^rdf:XMLLiteral ;\n')
                    #     else:
                    #         params['out'].write("    xl:to "+triple_object+" ;\n")
                    # else:
                    #     # xmlChar *content = xmlNodeGetContent(node->children);
                    #     xml = arc_to_node.text
                    #     if xml:
                    #         lang = arc_to.get('{http://www.w3.org/XML/1998/namespace}lang', None)
                    #         if lang is not None:
                    #             params['out'].write('    rdf:value """'+xml+'"""@'+lang+' ;\n')
                    #         else:
                    #             params['out'].write('    rdf:value """'+xml+'"""; \n')
                    #     else:
                    #         params['out'].write("    xl:to "+triple_object+" ;\n")
                else:
                    params['out'].write("    xl:to "+triple_object+" ;\n")

                params['out'].write("    ] .\n\n")

    return 0

def genLinkName(params):
    params['linkCount'] += 1
    name = "_:link"+str(params['linkCount'])
    return name

def getTurtleName(loc, base, ns, params):
    href = loc.get('{http://www.w3.org/1999/xlink}href', None)
    if href is not None:
        href = utilfunctions.expandRelativePath(href, base)
        res, namespace, name = findId(href, base, params)
        if res!=0:
            # if not found the use parent's namespace and url fragment
            namespace = ns
            name = urllib.parse.urlparse(href).fragment
    else:
        # if no href then use parent's namespace with label
        namespace = ns
        name = loc.get('{http://www.w3.org/1999/xlink}label', None)

    # if label ends with . then delete ., otherwise we get error in turtle
    if name[-1]==".": 
        name = name[0:-1]

    prefix = params['namespaces'].get(namespace, None)
    if prefix is None:
        prefix = "_"

    return prefix+":"+name


def shortRoleName(role, arc, params):
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
    # if (uri[0]!='/' && strncmp(uri, "http://", 7) != 0)
    found = params['id2elementTbl'].get(uri, None)
    if found:
        return 0, found[0], found[1]
    return -1, '', ''


def declareNamespace(prefix, uri, params):
    params['namespaces'][uri] = prefix
    # params['out'].write("@prefix "+prefix+": <"+uri+"> .\n")

# used for gensymmed names for nodes
def genArcRolePrefixName(params):
    params['arcroleNumber'] += 1
    name = "arcrole"+str(params['arcroleNumber'])
    return name

    # static int arcroleNumber = 0;
    # char *name = calloc(1, 20);
    # sprintf(name, "arcrole%d", ++arcroleNumber);
    # return name;

# used for gensymmed names for nodes
def genRolePrefixName(params):
    params['roleNumber'] += 1
    name = "role"+str(params['roleNumber'])
    return name

    # static int roleNumber = 0;
    # char *name = calloc(1, 16);
    # sprintf(name, "role%d", ++roleNumber);
    # return name;

# used for roleRef and arcRoleRef elements to
# declare namespace, and prefix
def declareRole(uri, arc, params):
    base, name = splitRole(uri)
    if base not in params['namespaces'].keys():
        if arc:
            prefix = genArcRolePrefixName(params)
        else: 
            prefix = genRolePrefixName(params)
        params['namespaces'][base] = prefix


# generate base, prefix and name from role or arcrole URI
# the generated strings must be freed by the caller
def splitRole(uri):
    name = uri.split("/")[-1]
    base = "/".join(uri.split("/")[0:-1])
    return base, name

    # int n, len = strlen(roleUri);
    # char *last = strrchr(roleUri, '/');

    # n = last - roleUri + 2;
    # base = roleUri[0:n-1]

    # n = roleUri+len-last;
    # char *name = malloc(n);
    # name = 
    # memcpy(name, last+1, n-1);
    # name[n-1] = '\0';
    # *pname = name;

    # return pbase, pname
