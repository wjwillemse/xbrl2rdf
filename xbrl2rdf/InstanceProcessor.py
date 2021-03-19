from lxml import etree
import logging

from .DtsProcessor import processSchema, processLinkBase
from .LinkbaseProcessor import processExtendedLink
from .utilfunctions import registerNamespaces, prependDtsQueue
from .const import XLINK_HREF, XBRL_SCHEMA


def processInstance(root: etree._Element, base: str, ns: str, params: dict) -> int:

    if etree.QName(root).localname == "schema":
        return processSchema(root, base)
    if etree.QName(root).localname == "linkbase":
        return processLinkBase(root, base, ns)

    logging.info("Processing instance "+base+"\n")

    registerNamespaces(root, base, params)

    footnote_links: list = list()

    provenance = genProvenanceName(base, params)

    for child in root:
        child_name: str = etree.QName(child).localname
        # child_namespace = etree.QName(child).namespace
        if child_name == "context":
            processContext(child, params)
        elif child_name == "unit":
            processUnit(child, params)
        elif child_name == "schemaRef":
            uri = child.attrib.get(XLINK_HREF, None)
            if uri is None:
                logging.error("Couldn't identify schema location.")
                return -1
            processSchemaRef(child, provenance, params)
            res = prependDtsQueue(XBRL_SCHEMA, uri, base, ns, 0, params)
        elif child_name == "footnoteLink":
            footnote_links.append(child)
        else:
            child_name = processFact(child, provenance, base, params)

    for child in footnote_links:
        # if (child->type != XML_ELEMENT_NODE)
        #     continue
        processExtendedLink(child, base, "")

    return res


def processContext(context: etree._Element, params: dict) -> int:

    context_id = context.attrib.get('id', None)
    output = params['facts']
    output.write("_:context_"+context_id+"\n")
    output.write("    xl:type xbrli:context;\n")
    output.write("    xbrli:entity [\n")

    # identifier = context[0][0]
    # scheme = identifier.attrib.get('scheme', None)

    # entity element has optional segment
    segment = getContextSegment(context, params)
    if segment is not None:
        if len(segment) == 1:
            segment = segment[0]
        xml = segment.text
        output.write('        xbrli:segment """' + xml +
                     '"""^^rdf:XMLLiteral;\n')

    context_identifier = getContextIdentifier(context, params)
    context_value = context_identifier.text
    output.write('        xbrli:identifier "'+context_value+'" ;\n')

    context_scheme = context_identifier.attrib.get("scheme", None)
    output.write("        xbrli:scheme <"+context_scheme+"> ;\n        ];\n")

    # each context may have one scenario element
    scenario = getContextScenario(context, params)
    if scenario is not None:
        members: list = list()
        for child in scenario:
            namespace = etree.QName(child).namespace
            name = etree.QName(child).localname
            prefix = params['namespaces'].get(namespace, None)
            members.append((prefix+":"+name, child.text))
        output.write('    xbrli:scenario [\n')
        for member in members:
            if member[1] is not None:
                params['facts'].write('        ' + str(member[0]) +
                                      ' '+str(member[1])+" ;\n")
        output.write('        ] ;\n')

    # every context element has one period element
    period = getContextPeriod(context, params)
    period_child = period[0]

    if etree.QName(period_child).localname == "instant":
        instant = period_child.text
        output.write('    xbrli:instant "'+instant+'"^^xsd:date.\n\n')
    elif etree.QName(period_child).localname == "forever":
        output.write('    xbrli:period xbrli:forever.\n\n')
    # expect sequence of startDate/endDate pairs
    else:
        output.write("    xbrli:period (\n")
        while period_child is not None:
            value = period_child.text
            output.write('        [ xbrli:startDate "' + value +
                         '"^^xsd:date;\n')
            period_child = child.getnext()
            value = period_child.text
            output.write('          xbrli:endDate "' + value +
                         '"^^xsd:date; ]\n')
            period_child = child.getnext()
        output.write("        ).\n\n")
   
    return 0


def genFactName(params: dict) -> str:
    params['factCount'] += 1
    return "_:fact"+str(params['factCount'])


def genProvenanceName(base: str, params: dict) -> str:
    base = base.replace("\\", "\\\\")
    output = params['facts']
    params['provenanceNumber'] += 1
    name: str = "_:provenance"+str(params['provenanceNumber'])
    output.write("# provenance for facts from same filing\n")
    output.write(name+" \n")
    output.write('    xl:instance "'+base+'".\n\n')
    return name


def getContextIdentifier(context: etree._Element, params: dict) -> etree._Element:
    entity = context[0]
    return entity[0]


def getContextSegment(context: etree._Element, params: dict) -> etree._Element:
    for node in context:
        if etree.QName(node).localname == "segment":
            return node
    return None


def getContextScenario(context: etree._Element, params: dict) -> etree._Element:
    for node in context:
        if etree.QName(node).localname == "scenario":
            return node
    return None


def getContextPeriod(context: etree._Element, params: dict) -> etree._Element:
    for node in context:
        if etree.QName(node).localname == "period":
            return node
    return None


# this needs further work to cope with more than one
# child element for the unit element, e.g. 2 measures for
# multiple pairs or numerator/denominator this could use
# one collection for numerator and another for denominator
def processUnit(unit: etree._Element, params: dict) -> int:
    output = params['facts']
    unit_id = unit.attrib.get("id", None)
    unit_child = unit[0]
    if (unit_child is not None) and (
          etree.QName(unit_child).localname == "measure"):
        measure = unit_child.text
        if ":" in measure:
            output.write("_:unit_" + unit_id +
                                  " xbrli:measure "+measure+" .\n\n")
        else:
            output.write("_:unit_" + unit_id +
                                  " xbrli:measure xbrli:"+measure+" .\n\n")
    elif etree.QName(unit).localname == "divide":
        numerator = getNumerator(unit_child, params)
        denominator = getDenominator(unit_child, params)
        output.write("_:unit_"+unit_id+"\n")
        output.write("    xbrli:numerator "+numerator+" ;\n")
        output.write("    xbrli:denominator "+denominator+" .\n\n")
    return 0

def processFact(fact: etree._Element, provenance: str, base: str, params: dict) -> str:
    # fact_id = fact.attrib.get('id', None)
    output = params['facts']
    contextRef = fact.attrib.get("contextRef", None)
    prefix = params['namespaces'].get(etree.QName(fact).namespace, None)

    # this implies that the fact is a tuple
    if contextRef is None:

        # todo prefix
        logging.info("tuple: " + etree.QName(fact).localname+
                     "\nprefix: "+prefix)

        child_fact_name = []
        for child in fact:
            processFact(child, provenance, base, params)
            child_fact_name.append("_:fact"+str(params['factCount'])+"\n")

        factName = genFactName(params)
        output.write(factName+"\n")
        output.write("    xl:type xbrli:tuple ;\n")
        output.write("    xl:provenance "+provenance+" ;\n")
        output.write("    rdf:type " + prefix +
                              ":"+etree.QName(fact).localname+" ;\n")
        output.write("    xbrli:content (\n")

        for item in child_fact_name:
            output.write("        "+item)

        output.write("    ).\n")

        return factName

    factName = genFactName(params)
    # change to Raggett-> rdf:type is xl:type and vice versa
    output.write(factName+" \n")
    output.write("    rdf:type xbrli:fact ;\n")
    output.write("    xl:provenance "+provenance+" ;\n")
    output.write("    xl:type " + prefix +
                          ":"+etree.QName(fact).localname+" ;\n")

    unitRef = fact.attrib.get("unitRef", None)

    if unitRef is not None:
        value = fact.text

        if "." in value:
            output.write('    rdf:value "' + value +
                                  '"^^xsd:decimal ;\n')
        else:
            output.write('    rdf:value "' + value +
                                  '"^^xsd:integer ;\n')

        decimals = fact.attrib.get("decimals", None)
        if decimals is not None:
            output.write('    xbrli:decimals "' + decimals +
                                  '"^^xsd:integer ;\n')

        precision = fact.attrib.get("precision", None)
        if precision is not None:
            output.write('    xbrli:precision "' + precision +
                                  '"^^xsd:integer ;\n')

        # does xmlGetProp ignore namespace prefix for attribute names?
        balance = fact.attrib.get("balance", None)
        if balance is not None:
            output.write('    xbrli:balance "'+balance+'"\n')

        output.write("    xbrli:unit _:unit_"+unitRef+";\n")
    # non-numeric fact
    else:
        count = len(fact)
        if count >= 1:
            xml = ''
            for child in fact:
                # use single quotation mark if string has quotation marks
                xml += etree.tostring(child).replace('"', "'")
            output.write('    xbrli:resource """' + xml +
                                  '"""^^rdf:XMLLiteral.\n')
        else:
            content = fact.text.replace('"', "'")
            if content.split(":")[0] in params['namespaces'].values():
                output.write('    xbrli:resource ' + content +
                                      ' ;\n')
            else:
                lang = fact.attrib.get("lang", None)
                if lang is not None:
                    output.write('    xbrli:resource """' + content +
                                          '"""@'+lang+' ;\n')
                else:
                    output.write('    xbrli:resource """' + content +
                                          '""" ;\n')

    output.write("    xbrli:context _:context_"+contextRef+" .\n\n")

    return factName


def getNumerator(divide: etree._Element, params: dict) -> str:
    for child in divide:
        if etree.QName(child).localname == "unitNumerator":
            divide_child = child[0]
            if divide_child:
                content = divide_child.text
            break
    return content


def getDenominator(divide: etree._Element, params: dict) -> str:
    for child in divide:
        if etree.QName(child).localname == "unitDenominator":
            divide_child = child[0]
            if divide_child:
                content = divide_child.text
    return content


def processSchemaRef(child: etree._Element, provenance: str, params: dict) -> int:
    output = params['facts']
    schemaRef = child.attrib.get(XLINK_HREF, None)
    schemaRef = schemaRef.replace("eu/eu/", "eu/")
    if schemaRef:
        output.write("_:schemaRef \n")
        output.write("    xl:provenance "+provenance+" ;\n")
        output.write("    link:schemaRef <"+schemaRef+"> .\n\n")
    return 0
