from lxml import etree
import logging

from .DtsProcessor import processSchema, processLinkBase
from .LinkbaseProcessor import processExtendedLink
from .utilfunctions import registerNamespaces, prependDtsQueue
from .const import XLINK_HREF, XBRL_SCHEMA

# change this to true to write types in ttl, false to not
write_types = False


def processInstance(
    root: etree._Element, base: str, ns: str, params: dict, handlerPrefix
) -> int:

    if etree.QName(root).localname == "schema":
        return processSchema(root, base, handlerPrefix)
    if etree.QName(root).localname == "linkbase":
        return processLinkBase(root, base, ns)

    logging.info("Processing instance " + base + "\n")

    registerNamespaces(root, base, params)

    footnote_links: list = list()

    provenance = genProvenanceName(base, params, handlerPrefix)

    for child in root:
        child_name: str = etree.QName(child).localname
        # child_namespace = etree.QName(child).namespace
        if child_name == "context":
            processContext(child, params, handlerPrefix, provenance)
        elif child_name == "unit":
            processUnit(child, params, handlerPrefix, provenance)
        elif child_name == "schemaRef":
            uri = child.attrib.get(XLINK_HREF, None)
            if uri is None:
                logging.error("Couldn't identify schema location.")
                return -1
            processSchemaRef(child, provenance, params, handlerPrefix)
            res = prependDtsQueue(XBRL_SCHEMA, uri, base, ns, 0, params)
        elif child_name == "footnoteLink":
            footnote_links.append(child)
        else:
            child_name = processFact(child, provenance, base, params, handlerPrefix)

    # for child in footnote_links:
    #     # if (child->type != XML_ELEMENT_NODE)
    #     #     continue
    #     processExtendedLink(child, base, "")

    return res


def processContext(
    context: etree._Element, params: dict, handlerPrefix, provenance
) -> int:

    context_id = context.attrib.get("id", None)
    output = params["rdf"]["instance"].content
    output.write(handlerPrefix + ":context_" + context_id + "\n")
    output.write("    xl:type xbrli:context;\n")
    output.write("    xl:provenance " + provenance + ";\n")
    output.write("    xbrli:entity [\n")
    # every context element has one period element
    period = getContextPeriod(context, params)
    period_child = period[0]

    if etree.QName(period_child).localname == "instant":
        instant = period_child.text
        if write_types:
            output.write('        xbrli:instant "' + instant + '"^^xsd:date;\n\n')
        else:
            output.write('        xbrli:instant "' + instant + '";\n')
    elif etree.QName(period_child).localname == "forever":
        output.write("        xbrli:period xbrli:forever;\n\n")
    # expect sequence of startDate/endDate pairs
    else:
        output.write("        xbrli:period \n")
        while period_child is not None:
            value = period_child.text
            if write_types:
                output.write(
                    '            [ xbrli:startDate "' + value + '"^^xsd:date;\n'
                )
            else:
                output.write('            [ xbrli:startDate "' + value + '";\n')
            period_child = period_child.getnext()
            value = period_child.text
            if write_types:
                output.write(
                    '              xbrli:endDate "' + value + '"^^xsd:date; ]\n'
                )
            else:
                output.write('              xbrli:endDate "' + value + '"; ]\n')
            period_child = period_child.getnext()
        output.write("        ;\n")

    context_identifier = getContextIdentifier(context, params)
    context_value = context_identifier.text
    output.write('        xbrli:identifier "' + context_value + '" ;\n')

    context_scheme = context_identifier.attrib.get("scheme", None)

    # identifier = context[0][0]
    # scheme = identifier.attrib.get('scheme', None)

    # entity element has optional segment

    segmentData = getContextSegment(context, params)
    scenarioData = getContextScenario(context, params)
    if len(segmentData) > 0 or len(scenarioData) > 0:
        output.write("        xbrli:scheme <" + context_scheme + "> ;\n    ];\n")
    else:
        output.write("        xbrli:scheme <" + context_scheme + "> ;\n    ].\n")
    if len(segmentData) > 0:
        output.write("    xbrli:segment [\n")
        for data in segmentData:
            dimension, tag, value = data
            output.write("        xbrldt:dimensionItem [\n")
            if tag is None:
                output.write("                xbrldt:dimension " + dimension + ";\n")
                output.write("                xbrldi:explicitMember " + value + "];\n")
            else:
                output.write("                xbrldt:dimension " + dimension + ";\n")
                output.write("                xbrldt:dimension-domain " + tag + ";\n")
                if write_types:
                    output.write(
                        '                xbrldi:typedMember """'
                        + value
                        + '"""^^rdf:XMLLiteral;] ;\n'
                    )
                else:
                    output.write(
                        '                xbrldi:typedMember """' + value + '""";] ;\n'
                    )
        if len(scenarioData) > 0:
            output.write("    ];\n")
        else:
            output.write("    ].\n")

    if len(scenarioData) > 0:
        output.write("    xbrli:scenario [\n")
        for data in scenarioData:
            dimension, tag, value = data
            output.write("        xbrldt:dimensionItem [\n")
            if tag is None:
                output.write("                xbrldt:dimension " + dimension + ";\n")
                output.write("                xbrldi:explicitMember " + value + "];\n")
            else:
                output.write("                xbrldt:dimension " + dimension + ";\n")
                output.write("                xbrldt:dimension-domain " + tag + ";\n")
                if write_types:
                    output.write(
                        '                xbrldi:typedMember """'
                        + value
                        + '"""^^rdf:XMLLiteral;] ;\n'
                    )
                else:
                    output.write(
                        '                xbrldi:typedMember """' + value + '""";] ;\n'
                    )
        output.write("    ].\n\n")

    return 0


def genFactName(params: dict, handlerPrefix) -> str:
    params["factCount"] += 1
    return handlerPrefix + ":fact" + str(params["factCount"])


def genProvenanceName(base: str, params: dict, handlerPrefix) -> str:
    base = base.replace("\\", "\\\\")
    output = params["rdf"]["instance"].content
    params["provenanceNumber"] += 1
    name: str = handlerPrefix + ":provenance" + str(params["provenanceNumber"])
    output.write("# provenance for facts from same filing\n")
    output.write(name + " \n")
    output.write('    xlink:href "' + base + '";\n')
    filename = base[base.rfind("/") + 1 :]
    output.write('    xl:instance "' + filename + '".\n\n')
    return name


def getContextIdentifier(context: etree._Element, params: dict) -> etree._Element:
    entity = context[0]
    return entity[0]


def getContextSegment(context: etree._Element, params: dict) -> etree._Element:
    return getContextDimensions(context, params, "segment")
    """
    dimensionlist = list()
    for node in context.iter():
        if etree.QName(node).localname == "segment":
            for subnode in node.iter():
                if etree.QName(subnode).localname == "explicitMember":
                    dimensionlist.add (subnode.get('dimension'), None, subnode.text)
                elif etree.QName(subnode).localname == "typedMember":
                    dimension = subnode.get('dimension')
                    inner = subnode[0]
                    tagdata = inner.prefix + ":" + etree.QName(inner.tag).localname
                    dimensionlist.add (dimension, tagdata, inner.text)
    return dimensionlist
    """


def getContextDimensions(
    context: etree._Element, params: dict, keyword
) -> etree._Element:
    dimensionlist = list()
    for node in context.iter():
        if etree.QName(node).localname == keyword:
            for subnode in node.iter():
                if etree.QName(subnode).localname == "explicitMember":
                    dimensionlist.append((subnode.get("dimension"), None, subnode.text))
                elif etree.QName(subnode).localname == "typedMember":
                    dimension = subnode.get("dimension")
                    inner = subnode[0]
                    tagdata = inner.prefix + ":" + etree.QName(inner.tag).localname
                    dimensionlist.append((dimension, tagdata, inner.text))
    return dimensionlist


def getContextScenario(context: etree._Element, params: dict) -> etree._Element:
    return getContextDimensions(context, params, "scenario")
    """
    for node in context.iter():
        if etree.QName(node).localname == "scenario":
            return node
    return None
    """


def getContextPeriod(context: etree._Element, params: dict) -> etree._Element:
    for node in context:
        if etree.QName(node).localname == "period":
            return node
    return None


# this needs further work to cope with more than one
# child element for the unit element, e.g. 2 measures for
# multiple pairs or numerator/denominator this could use
# one collection for numerator and another for denominator
def processUnit(unit: etree._Element, params: dict, handlerPrefix, provenance) -> int:
    output = params["rdf"]["instance"].content
    unit_id = unit.attrib.get("id", None)
    unit_child = unit[0]
    if (unit_child is not None) and (etree.QName(unit_child).localname == "measure"):
        measure = unit_child.text
        output.write(handlerPrefix + ":unit_" + unit_id + "\n")
        output.write("    xl:provenance " + provenance + ";\n")
        if ":" in measure:
            output.write("    xbrli:measure " + measure + " .\n\n")
        else:
            output.write("    xbrli:measure xbrli:" + measure + " .\n\n")
    elif etree.QName(unit_child).localname == "divide":
        numerator = getNumerator(unit_child, params)
        denominator = getDenominator(unit_child, params)
        output.write("    xbrli:numerator " + numerator + " ;\n")
        output.write("    xbrli:denominator " + denominator + " .\n\n")
    return 0


def processFact(
    fact: etree._Element, provenance: str, base: str, params: dict, handlerPrefix
) -> str:
    # fact_id = fact.attrib.get('id', None)
    output = params["rdf"]["instance"].content
    contextRef = fact.attrib.get("contextRef", None)
    prefix = params["namespaces"].get(etree.QName(fact).namespace, None)

    # this implies that the fact is a tuple
    if contextRef is None:

        # todo prefix
        logging.info("tuple: " + etree.QName(fact).localname + "\nprefix: " + prefix)

        child_fact_name = []
        for child in fact:
            processFact(child, provenance, base, params, handlerPrefix)
            child_fact_name.append(
                handlerPrefix + ":fact" + str(params["factCount"]) + "\n"
            )

        factName = genFactName(params, handlerPrefix)
        output.write(factName + "\n")
        output.write("    xl:type xbrli:tuple ;\n")
        output.write("    xl:provenance " + provenance + " ;\n")
        output.write(
            "    rdf:type " + prefix + ":" + etree.QName(fact).localname + " ;\n"
        )
        output.write("    xbrli:content (\n")

        for item in child_fact_name:
            output.write("        " + item)

        output.write("    ).\n")

        return factName

    factName = genFactName(params, handlerPrefix)
    # change to Raggett-> rdf:type is xl:type and vice versa
    output.write(factName + " \n")
    output.write("    rdf:type xbrli:fact ;\n")
    output.write("    xl:provenance " + provenance + " ;\n")
    output.write("    xl:type " + prefix + ":" + etree.QName(fact).localname + " ;\n")

    unitRef = fact.attrib.get("unitRef", None)
    isNil = fact.attrib.get("{http://www.w3.org/2001/XMLSchema-instance}nil", None)
    if unitRef is not None:
        # print('sourceline', fact.sourceline, 'attrib', fact.attrib, 'nill?', isNil)
        # need to check for xsi:nil 'true' attribute, if so, put rdf:nil
        if isNil:
            output.write("    rdf:value " + "rdf:nil;\n")
        else:
            value = fact.text
            if "." in value:
                if write_types:
                    output.write('    rdf:value "' + value + '"^^xsd:decimal ;\n')
                else:
                    output.write('    rdf:value "' + value + '" ;\n')
            else:
                if write_types:
                    output.write('    rdf:value "' + value + '"^^xsd:integer ;\n')
                else:
                    output.write('    rdf:value "' + value + '" ;\n')

        decimals = fact.attrib.get("decimals", None)
        if decimals is not None:
            if write_types:
                output.write('    xbrli:decimals "' + decimals + '"^^xsd:integer ;\n')
            else:
                output.write('    xbrli:decimals "' + decimals + '" ;\n')
        precision = fact.attrib.get("precision", None)
        if precision is not None:
            if write_types:
                output.write('    xbrli:precision "' + precision + '"^^xsd:integer ;\n')
            else:
                output.write('    xbrli:precision "' + precision + '" ;\n')

        # does xmlGetProp ignore namespace prefix for attribute names?
        balance = fact.attrib.get("balance", None)
        if balance is not None:
            output.write('    xbrli:balance "' + balance + '"\n')

        output.write("    xbrli:unit " + handlerPrefix + ":unit_" + unitRef + ";\n")
    # non-numeric fact
    else:
        count = len(fact)
        if count >= 1:
            xml = ""
            for child in fact:
                # print(type(child), child.sourceline, 'child:', child)
                # use single quotation mark if string has quotation marks
                xml += etree.tostring(child, encoding="unicode").replace('"', "'")
            if write_types:
                output.write('    xbrli:resource """' + xml + '"""^^rdf:XMLLiteral.\n')
            else:
                output.write('    xbrli:resource """' + xml + '""".\n')
        elif not isNil:
            content = fact.text.replace('"', "'")
            if content.split(":")[0] in params["namespaces"].values():
                output.write("    xbrli:resource " + content + " ;\n")
            else:
                lang = fact.attrib.get("lang", None)
                if lang is not None:
                    output.write(
                        '    xbrli:resource """' + content + '"""@' + lang + " ;\n"
                    )
                else:
                    output.write('    xbrli:resource """' + content + '""" ;\n')

    output.write(
        "    xbrli:context " + handlerPrefix + ":context_" + contextRef + " .\n\n"
    )

    return factName


def getNumerator(divide: etree._Element, params: dict) -> str:
    for child in divide:
        if etree.QName(child).localname == "unitNumerator":
            divide_child = child[0]
            if divide_child is not None:
                return divide_child.text
    assert False, "Didn't find a numerator in getNumerator!"


def getDenominator(divide: etree._Element, params: dict) -> str:
    for child in divide:
        if etree.QName(child).localname == "unitDenominator":
            divide_child = child[0]
            if divide_child is not None:
                return divide_child.text
    assert False, "Didn't find a denominator in getDenominator!"


def processSchemaRef(
    child: etree._Element, provenance: str, params: dict, handlerPrefix
) -> int:
    output = params["rdf"]["instance"].content
    schemaRef = child.attrib.get(XLINK_HREF, None)
    schemaRef = schemaRef.replace("eu/eu/", "eu/")
    if schemaRef:
        output.write(handlerPrefix + ":schemaRef \n")
        output.write("    xl:provenance " + provenance + " ;\n")
        output.write("    link:schemaRef <" + schemaRef + "> .\n\n")
    return 0
