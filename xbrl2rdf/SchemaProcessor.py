import DtsProcessor
import utilfunctions
import const
from utilfunctions import processAttribute

def processSchema(root, base, params):

    # skip core schemas
    targetNs = root.attrib.get("targetNamespace", None)
    if targetNs in params['namespaces_to_skip']:
        return 0

    params['log'].write("processing schema "+base+"\n")

    utilfunctions.registerNamespaces(root, base, params)
    processElements(root, base, targetNs, params)
    xpathobj = root.xpath("//link:linkbaseRef", namespaces={"link": "http://www.xbrl.org/2003/linkbase"})
    res1 = processLinkBases(xpathobj, base, targetNs, params)
    res2 = processImportedSchema(root, base, targetNs, params)
    return res1 or res2


def processLinkBases(nodes, base, targetNs, params):
    res = 0
    params['log'].write("importing linkbases for base "+base+"\n")
    for node in nodes:
        uri = node.attrib.get(const.XLINK_HREF, None)
        if uri is None:
            params['log'].write("couldn't identify schema location\n")
            return -1
        params['log'].write("importing "+uri+"\n")
        # if linkbase has relative uri then schema namespace applies
        if targetNs and (uri[0:7] != 'http://'):
            lns = targetNs
        else:
            lns = None
        DtsProcessor.appendDtsQueue(const.XBRL_LINKBASE,
                                    uri, base, lns, 0, params)
    return res


def processImportedSchema(root, base, ns, params):
    res = 0
    params['log'].write("importing schema for base "+base+"\n")
    if len(root) == 0:
        params['log'].write("couldn't find first child element\n")
        return -1
    for node in root:
        # if (strcmp((char *)(node->name), "import") &&
        #       strcmp((char *)(node->name), "include"))
        #     continue;

        if (node.tag != "{http://www.w3.org/2001/XMLSchema}import") and \
           (node.tag != "{http://www.w3.org/2001/XMLSchema}include"):
            continue
        schema = node.attrib.get("schemaLocation", None)
        namespace = node.attrib.get("namespace", None)
        DtsProcessor.prependDtsQueue(const.XBRL_LINKBASE,
                                     schema,
                                     base,
                                     namespace,
                                     0,
                                     params)
    return res


def processElements(root, base, targetNs, params):

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
                                const.XBRLI_PERIODTYPE,
                                const.MODEL_CREATIONDATE,
                                const.MODEL_TODATE,
                                const.MODEL_FROMDATE,
                                const.MODEL_MODIFICATIONDATE,
                                const.MODEL_HIERARCHY,
                                const.MODEL_DOMAIN,
                                const.MODEL_ISDEFAULTMEMBER,
                                const.ENUM_LINKROLE,
                                const.ENUM_DOMAIN,
                                const.XBRLDT_TYPEDDOMAINREF,
                                const.SUBSTITUTIONGROUP,
                                const.NILLABLE,
                                const.ABSTRACT,
                                const.BALANCE]:
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

            output.write(processAttribute(child, const.XBRLI_PERIODTYPE, str))
            output.write(processAttribute(child, const.XBRLDT_TYPEDDOMAINREF, str))
            
            output.write(processAttribute(child, const.MODEL_CREATIONDATE, str))
            output.write(processAttribute(child, const.MODEL_TODATE, str))
            output.write(processAttribute(child, const.MODEL_MODIFICATIONDATE, str))
            output.write(processAttribute(child, const.MODEL_TODATE, str))
            output.write(processAttribute(child, const.MODEL_DOMAIN, str))
            output.write(processAttribute(child, const.MODEL_HIERARCHY, str))
            output.write(processAttribute(child, const.MODEL_ISDEFAULTMEMBER, str))
            
            output.write(processAttribute(child, const.ENUM_DOMAIN, str))
            output.write(processAttribute(child, const.ENUM_LINKROLE, str))
            
            output.write(processAttribute(child, const.SUBSTITUTIONGROUP, None))
            output.write(processAttribute(child, const.NILLABLE, bool))
            output.write(processAttribute(child, const.ABSTRACT, bool))
            output.write(processAttribute(child, const.BALANCE, str))

            output.write('    . \n\n')

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
        params['log'].write('addId: uri = "' + key +
                            '", ns = "' + targetNs +
                            '", name="' + name + '"\n')
    params['id2elementTbl'][key] = value
    return 0
