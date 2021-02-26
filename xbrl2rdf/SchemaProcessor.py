from lxml import etree
import DtsProcessor
import utilfunctions

XBRL_LINKBASE = 1

def processSchema(root, base, params):

    targetNs = root.attrib.get("targetNamespace", None)

    # skip core schemas
    if targetNs in params['namespaces_to_skip']:
        return 0

    params['log'].write("processing schema "+base+"\n")

    utilfunctions.registerNamespaces(root, base, params)

    processElements(root, base, targetNs, params)

    # xmlXPathContextPtr xpathCtx = xmlXPathNewContext(root->doc);

    # if xpathCtx is None:
    #     params['log'].write("Error: unable to create new XPath context\n")
    #     return -1

    # # register linkbase namespace
    # if xmlXPathRegisterNs(xpathCtx, "link", "http://www.xbrl.org/2003/linkbase")!=0:
    #     params['log'].write("Error: unable to register linkbase name space\n")
    #     return -1

    # # Evaluate xpath expression
    # xpathExpr = "//link:linkbaseRef"

    # xmlXPathObjectPtr  xpathObj = xmlXPathEvalExpression(xpathExpr, xpathCtx)

    # if xpathObj is None:
    #     params['log'].write('Error: unable to evaluate xpath expression "'+xpathExpr+'"\n')
    #     return -1

    xpathobj = root.xpath("//link:linkbaseRef", namespaces={"link": "http://www.xbrl.org/2003/linkbase"})

    res1 = processLinkBases(xpathobj, base, targetNs, params)

    res2 = processImportedSchema(root, base, targetNs, params)

    return res1 or res2

def processLinkBases(nodes, base, targetNs, params):
    res = 0
    params['log'].write("importing linkbases for base "+base+"\n")
    for node in nodes:
        # if(node.type == XML_ELEMENT_NODE):
        uri = node.attrib.get("{http://www.w3.org/1999/xlink}href", None)
        if uri is None:
            params['log'].write("couldn't identify schema location\n")
            return -1
        params['log'].write("importing "+uri+"\n")
        # if linkbase has relative uri then schema namespace applies
        # lns = (ns && (uri[0:7]=="http://") ? ns : NULL)
        if targetNs and (uri[0:7]!='http://'):
            lns = targetNs
        else:
            lns = None
        DtsProcessor.appendDtsQueue(XBRL_LINKBASE, uri, base, lns, 0, params)
    return res

def processImportedSchema(root, base, ns, params):
    res = 0
    params['log'].write("importing schema for base "+base+"\n")
    if len(root)==0:
        params['log'].write("couldn't find first child element\n")
        return -1
    for node in root:
#         if (node->type != XML_ELEMENT_NODE)
#              continue;
        # if (strcmp((char *)(node->name), "import") &&
        #       strcmp((char *)(node->name), "include"))
        #     continue;
        
        if (node.tag!="{http://www.w3.org/2001/XMLSchema}import") and \
           (node.tag!="{http://www.w3.org/2001/XMLSchema}include"):
            continue
        schema = node.attrib.get("schemaLocation", None)
        namespace = node.attrib.get("namespace", None)
        DtsProcessor.prependDtsQueue(XBRL_LINKBASE, schema, base, namespace, 0, params)
    return res

# examine element declarations to build dictionary that maps
# schema URI and id into target namespace and element name
def processElements(root, base, targetNs, params):

    # child_name = etree.QName(child).localname
    # child_namespace = etree.QName(child).namespace

    namespaces = params['namespaces']

    # char *prefix = getNsPrefix((const char *)targetNs);
    prefix = namespaces.get(targetNs, None)

    params['out'].write("# SCHEMAS\n")
    params['out'].write("# target namespace:" + targetNs)
    params['out'].write("# base: "+base+"\n\n")

    for child in root:

        if child.tag=="{http://www.w3.org/2001/XMLSchema}element":

            child_name = child.attrib.get('name', None)
            child_id = child.attrib.get('id', None)
            child_type = child.attrib.get('type', None)
            child_periodType = child.attrib.get('{http://www.xbrl.org/2003/instance}periodType', None)
            child_creationDat = child.attrib.get('{http://www.eurofiling.info/xbrl/ext/model}creationDate', None)
            child_substitutionGroup = child.attrib.get('substitutionGroup', None)
            child_nillable = child.attrib.get('nillable', None)
            child_abstract = child.attrib.get('abstract', None)
            child_balance = child.attrib.get('balance', None)

            if child_type or child_periodType or child_balance:

                params['out'].write(prefix+":"+child_name+" \n")

                if child_type:

                    # hack for type="string" not type="xsd:string"
                    if ":" not in child_type:
                        child_type = "xsd:"+child_type
                    elif child_type[0:3]=="xs:": # strange error, in xbrl?
                        child_type = "xsd:"+child_type[3:]
                    params['out'].write("    rdf:type "+child_type)
                    if child_periodType or child_balance:
                        params['out'].write(" ;\n")
                    else:
                        params['out'].write(" .\n")

                if child_periodType:
                    params['out'].write('    xbrli:periodType "'+child_periodType+'"')
                    if child_balance:
                        params['out'].write(" ;\n")
                    else:
                        params['out'].write(" .\n")

                if child_balance:
                    params['out'].write('    xbrli:balance "'+child_balance+'".\n')

                params['out'].write('\n')

                params['conceptCount'] += 1

            # add base#id, targetnamespace:name to dictionary
            if child_id is None:
                params['log'].write("name = "+child_name+"\n")
            else:
                addId(base, child_id, targetNs, child_name, params)

def addId(xsdUri, child_id, targetNs, name, params):
    key = xsdUri + "#" + child_id
    value = (targetNs, name)
    if key[0] == '#':
        params['log'].write('addId: uri = "'+key+'", ns = "'+targetNs+'", name="'+name+'"\n')
    params['id2elementTbl'][key] = value
    return 0