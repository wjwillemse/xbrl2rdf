from io import StringIO, BytesIO
from lxml import etree
import DtsProcessor
import utilfunctions

XBRL_SCHEMA = 0

# reference to provenance is used for gensymmed names for nodes
def genFactName(params):
    params['factCount'] += 1
    return "_:fact"+str(params['factCount'])


def genProvenanceName(base, params):
    base = base.replace("\\", "\\\\")
    params['provenanceNumber'] += 1
    name = "_:provenance"+str(params['provenanceNumber'])
    params['facts'].write("# provenance is used to speed selection of facts from same filing\n")
    params['facts'].write(name+" \n")
    params['facts'].write('    xl:instance "'+base+'".\n\n')
    return name


def processInstance(root, base, ns, params):

    # if starting from schema document
    if etree.QName(root).localname=="schema":
        return processSchema(root, base)

    if etree.QName(root).localname=="linkbase":
        return processLinkBase(root, base, ns)

    params['log'].write("processing instance "+base+"\n")
    
    utilfunctions.registerNamespaces(root, base, params)

    provenance = genProvenanceName(base, params)

    footnote_links = list()

    for child in root:

        # if (child->type != XML_ELEMENT_NODE)
        #     continue
        child_name = etree.QName(child).localname
        child_namespace = etree.QName(child).namespace
        
        if child_name=="context":
            printContext(child, params)
        elif child_name=="unit":
            printUnit(child, params)
        elif child_name=="schemaRef":
            uri = child.attrib.get("{http://www.w3.org/1999/xlink}href", None )
            if uri is None:
                params['log'].write("couldn't identify schema location\n")
                return -1
            printSchemaRef(child, provenance, params)
            res = DtsProcessor.prependDtsQueue(XBRL_SCHEMA, uri, base, ns, 0, params)
        elif child_name=="footnoteLink":
            footnotelinks.append(child)
        else:
            child_name = printFact(child, provenance, base, params)

    for child in footnote_links:
        # if (child->type != XML_ELEMENT_NODE)
        #     continue
        processExtendedLink(child, base, "")

    return res


def printContext(context, params):

    context_id = context.attrib.get('id', None)
    params['facts'].write("_:context_"+context_id+"\n")
    params['facts'].write("    xl:type xbrli:context;\n")

    # every context element has one entity element
    # and that must have an identifier and scheme
    params['facts'].write("    xbrli:entity [\n")

    # identifier = context[0][0]
    # scheme = identifier.attrib.get('scheme', None)

    # entity element has optional segment
    segment = getContextSegment(context, params)
    if segment is not None:
        if len(segment)==1:
            segment = segment[0]
        xml = segment.text
        params['facts'].write('        xbrli:segment """'+xml+'"""^^rdf:XMLLiteral;\n')

    context_identifier = getContextIdentifier(context, params)
    context_value = context_identifier.text
    params['facts'].write('        xbrli:identifier "'+context_value+'" ;\n')

    context_scheme = context_identifier.attrib.get("scheme", None)
    params['facts'].write("        xbrli:scheme <"+context_scheme+"> ;\n        ];\n")

    # each context may have one scenario element
    scenario = getContextScenario(context, params)
    if scenario is not None:
        members = []
        for child in scenario:
            namespace = etree.QName(child).namespace
            name = etree.QName(child).localname
            prefix = params['namespaces'].get(namespace, None)
            members.append((prefix+":"+name, child.text))
        params['facts'].write('    xbrli:scenario [\n')
        for member in members:
            if member[1] is not None:
                params['facts'].write('        '+str(member[0])+' '+str(member[1])+" ;\n")
        params['facts'].write('        ] ;\n')
                
    # every context element has one period element
    period = getContextPeriod(context, params)
    period_child = period[0]

    if etree.QName(period_child).localname=="instant":
        instant = period_child.text
        params['facts'].write('    xbrli:instant "'+instant+'"^^xsd:date.\n\n')
    elif etree.QName(period_child).localname=="forever":
        params['facts'].write('    xbrli:period xbrli:forever.\n\n')
    else: # expect sequence of startDate/endDate pairs
        params['facts'].write("    xbrli:period (\n")
        while period_child is not None:
            value = period_child.text
            params['facts'].write('        [ xbrli:startDate "'+value+'"^^xsd:date;\n')
            period_child = child.getnext()
            value = period_child.text
            params['facts'].write('          xbrli:endDate "'+value+'"^^xsd:date; ]\n')
            period_child = child.getnext()
        params['facts'].write("        ).\n\n")


def getContextIdentifier(context, params):
    entity = context[0]
    return entity[0]


def getContextSegment(context, params):
    for node in context:
        # if (node->type != XML_ELEMENT_NODE)
        #     continue;
        if etree.QName(node).localname=="segment":
            return node
    return None


def getContextScenario(context, params):
    for node in context:
        # if (node->type != XML_ELEMENT_NODE)
        #     continue;
        if etree.QName(node).localname=="scenario":
            return node
    return None


def getContextPeriod(context, params):
    for node in context:
#         if (node->type != XML_ELEMENT_NODE)
#             continue;
        if etree.QName(node).localname=="period":
            return node
    return None


# this needs further work to cope with more than one
# child elment for the unit element, e.g. 2 measures for
# multiple pairs or numerator/denominator this could use
# one collection for numerator and another for denominator
def printUnit(unit, params):
    unit_id = unit.attrib.get("id", None)
    unit_child = unit[0]
    if (unit_child is not None) and (etree.QName(unit_child).localname=="measure"):
        measure = unit_child.text
        if ":" in measure:
            params['facts'].write("_:unit_"+unit_id+" xbrli:measure "+measure+" .\n")
        else:
            params['facts'].write("_:unit_"+unit_id+" xbrli:measure xbrli:"+measure+" .\n")
    elif etree.QName(node).localname=="divide":
        numerator = getNumerator(unit_child, params)
        denominator = getDenominator(unit_child, params)
        geparams['facts'].write("_:unit_"+unit_id+"\n")
        params['facts'].write("    xbrli:numerator "+numerator+" ;\n")
        params['facts'].write("    xbrli:denominator "+denominator+" .\n")

# used for linked
# struct _fact_struct {
#     struct _fact_struct *next;
#     char *name;
# };

# typedef struct _fact_struct FactName;

# currently limited to numeric facts *** FIX ME
# looks at children as needed for contextRef and unitRef
def printFact(fact, provenance, base, params):

    fact_id = fact.attrib.get('id', None)
    contextRef = fact.attrib.get("contextRef", None)
    prefix = params['namespaces'].get(etree.QName(fact).namespace, None)

    # this implies that the fact is a tuple
    if contextRef is None:

        # todo prefix
        params['log'].write("tuple: "+etree.QName(fact).localname+"\nprefix: "+prefix+"\n")

        child_fact_name = []
        for child in fact:
#             if (child->type != XML_ELEMENT_NODE)
#                 continue;
            
            printFact(child, provenance, base, params)
            child_fact_name.append("_:fact"+str(params['factCount'])+"\n")

        factName = genFactName(params)
        params['facts'].write(factName+"\n")
        params['facts'].write("    xl:type xbrli:tuple ;\n")
        params['facts'].write("    xl:provenance "+provenance+" ;\n")
        params['facts'].write("    rdf:type "+prefix+":"+etree.QName(fact).localname+" ;\n")
        params['facts'].write("    xbrli:content (\n")

        for item in child_fact_name:
            params['facts'].write("        "+item+"\n")

        params['facts'].write("    ).\n")

        return factName

    factName = genFactName(params)
    # change to Raggett-> rdf:type is xl:type and vice versa
    params['facts'].write(factName+" \n")
    params['facts'].write("    rdf:type xbrli:fact ;\n")
    params['facts'].write("    xl:provenance "+provenance+" ;\n")
    params['facts'].write("    xl:type "+prefix+":"+etree.QName(fact).localname+" ;\n")

    unitRef = fact.attrib.get("unitRef", None)

    if unitRef is not None:
        value = fact.text

        if "." in value:
            params['facts'].write('    rdf:value "'+value+'"^^xsd:decimal ;\n')
        else:
            params['facts'].write('    rdf:value "'+value+'"^^xsd:integer ;\n')

        decimals = fact.attrib.get("decimals", None)
        if decimals is not None:
            params['facts'].write('    xbrli:decimals "'+decimals+'"^^xsd:integer ;\n')

        precision = fact.attrib.get("precision", None)
        if precision is not None:
            params['facts'].write('    xbrli:precision "'+precision+'"^^xsd:integer ;\n')

        # does xmlGetProp ignore namespace prefix for attribute names?
        balance = fact.attrib.get("balance", None)
        if balance is not None:
            params['facts'].write('    xbrli:balance "'+balance+'"\n')

        params['facts'].write("    xbrli:unit _:unit_"+unitRef+";\n")
    else: # non-numeric fact
        count = len(fact)
        if count>=1:
            xml = ''
            for child in fact:
                xml += etree.tostring(child).replace('"',"'") # use single quotation mark if string has quotation marks
            params['facts'].write('    xbrli:resource """'+xml+'"""^^rdf:XMLLiteral.\n')
        else:
            content = fact.text.replace('"',"'")
            if content.split(":")[0] in params['namespaces'].values():
                params['facts'].write('    xbrli:resource '+content+' ;\n')
            else:
                lang = fact.attrib.get("lang", None)
                if lang is not None:
                    params['facts'].write('    xbrli:resource """'+content+'"""@'+lang+' ;\n')
                else:
                    params['facts'].write('    xbrli:resource """'+content+'""" ;\n')

    params['facts'].write("    xbrli:context _:context_"+contextRef+" .\n\n")

    return factName


def getNumerator(divide, params):
    for child in divide:
        # if (child->type != XML_ELEMENT_NODE)
        #     continue;
        if etree.QName(root).localname=="unitNumerator":
            divide_child = child[0]
            if divide_child:
                content = divide_child.text
            break;
    return content


def getDenominator(divide, params):
    for child in divide:
#         if (child->type != XML_ELEMENT_NODE)
#             continue;
        if etree.QName(root).localname=="unitDenominator":
            divide_child = child[0]
            if divide_child:
                content = divide_child.text
            break;
    return content


def printSchemaRef(child, provenance, params):
    schemaRef = child.attrib.get('{http://www.w3.org/1999/xlink}href', None)
    schemaRef = schemaRef.replace("eu/eu/", "eu/")
    if schemaRef:
        params['facts'].write("_:schemaRef \n")
        params['facts'].write("    xl:provenance "+provenance+" ;\n")
        params['facts'].write("    link:schemaRef <"+schemaRef+"> .\n\n")
    return 0
