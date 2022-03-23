========
xbrl2rdf
========

.. image:: https://img.shields.io/pypi/v/xbrl2rdf.svg
        :target: https://pypi.python.org/pypi/xbrl2rdf

.. image:: https://readthedocs.org/projects/xbrl2rdf/badge/?version=latest
        :target: https://xbrl2rdf.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
        :target: https://github.com/psf/black
        :alt: Code style: black

> #### DISCLAIMER - BETA PHASE
> This XBRL to RDF parser is currently in a beta phase.
> 

Python package to convert XBRL instance and taxonomy files to RDF

* Free software: GNU GENERAL PUBLIC LICENSE, v2
* Documentation: https://xbrl2rdf.readthedocs.io.

Installation
============

To install the package

::

    pip install xbrl2rdf

To install the package from Github

::

	pip install -e git+https://github.com/wjwillemse/xbrl2rdf.git#egg=xbrl2rdf


The idea of this package
========================

This package started with two observations:

* the meta data contained in XBRL taxonomies are very useful but not often used outside IT departments and XBRL specialists;

* the data in XBRL reports is not very well suited for combining with other data sources and with text data.

The idea of this package was to transform the XBRL format to a semantic data format / knowledge graph based on RDF/OWL. The XBRL format already uses XML and URIs, so parsing XBRL to RDF is relatively straightforward (especially if compared to parsing XBRL to a relational database). The RDF representation makes it easier to combine XBRL data with internal and external data, and data from other taxonomies. Furthermore it allows semantic reasoning.

See also: `Short overview <https://github.com/wjwillemse/xbrl2rdf/blob/main/docs/XBRL%20to%20RDF.pdf>`_

Features
========

This Python package converts XBRL instance files (reports) and related taxonomy files (schemas and linkbases) to RDF and RDF-star

A resulting fact from an example instance looks like this::

        :fact57     
            rdf:type xbrli:fact ;    
            xl:provenance _:provenance1 ;    
            xl:type s2md_met:mi1808 ;    
            rdf:value "607706294.02"^^xsd:decimal ;    
            xbrli:decimals "2"^^xsd:integer ;    
            xbrli:unit _:unit_u;     
            xbrli:context _:context_BLx10

The corresponding context is::

        :context_BLx10
            xl:type xbrli:context;    
            xbrli:entity [
                xbrli:identifier "0LFF1WMNTWG5PTIYYI38" ;
                xbrli:scheme <http://standards.iso.org/iso/17442> ;
            ];
            xbrli:scenario [
                xbrldi:explicitMember s2c_LB:x10 ;
                xbrldi:explicitMember s2c_DI:x5 ;
                xbrldi:explicitMember s2c_LB:x28 ;
                xbrldi:explicitMember s2c_AM:x84 ;
            ] ;
            xbrli:instant "2019-12-31"^^xsd:date.

Meta data from an XBRL taxonomy looks like this::

        _:link1270 arcrole3:domain-member [
            xl:type xl:link ;
            xl:role s2md_tab_S.05.01.02.01:11 ;
            xl:order "4"^^xsd:decimal ;
            xl:from s2md_met:mi281 ;
            xl:to s2md_met:mi1808 ;    
            ]

        _:link107873 arcrole1:concept-label [
            xl:type xl:link ;
            xl:role s2c_LB:5 ;
            xlink:role role1:label ;
            rdf:lang "en" ;
            xl:from s2c_LB:x10 ;
            rdf:value """Annuities stemming from non-life insurance contracts"""@en ;
            ].

With XBRL in RDF format you can then query the data, for example for the labels of group tables of the qrs entrypoint (quarterly reports from solo undertakings of Solvency 2)::

        SELECT ?grouptable ?label
        WHERE {
            ?link1 arcrole4:group-table ?s ; 
            ?s xl:from s2md_mod_qrs:qrs ;
               xl:to ?grouptable ;
            ?link2 arcrole3:concept-label ?labellink ;
            ?labellink xl:from ?grouptable ;
                       rdf:value ?label ; }

This query gives the following output::

        tgS.01.01.02: Appendix I: Quantitative reporting templates
        tgS.01.02.01: Basic Information - General
        tgS.02.01.02: Balance sheet
        tgS.05.01.02: Premiums, claims and expenses by line of business
        tgS.06.02.01: List of assets
        tgS.06.03.01: Collective investment undertakings - look-through approach
        tgS.08.01.01: Open derivatives
        tgS.08.02.01: Derivatives Transactions
        tgS.12.01.02: Life and Health SLT Technical Provisions
        tgS.17.01.02: Non-Life Technical Provisions
        tgS.23.01.01: Own funds
        tgS.28.01.01: Minimum Capital Requirement - Only life or only non-life insurance or reinsurance activity
        tgS.28.02.01: Minimum Capital Requirement - Both life and non-life insurance activity
        tgT.99.01.01: Technical table

How to run
==========

Put the taxonomy .zip files in data/taxonomies (do not extract the zip file).

Put the instance .xbrl files in data/instances.

Make sure you have the corresponding taxonomy of the instance you want to parse.

To parse an XBRL-instance file run in the root of the project

::

	python -m xbrl2rdf.xbrl2rdf

Example:

Download from https://www.eiopa.europa.eu/tools-and-data/supervisory-reporting-dpm-and-xbrl_en
the file EIOPA_SolvencyII_XBRL_Taxonomy_2.4.0_with_external_hotfix.zip and put the file in data/taxonomies.

Download from the same location the file EIOPA_SolvencyII_XBRL_Instance_documents_2.4.0.zip. Extract from this EIOPA_SolvencyII_XBRL_Instance_documents_2.4.0/random/qrs_240_instance.xbrl (or another instance file) and put the file in data/instances.

Then run the command above to parse this file.

Acknowledgments
===============

This code is based on Dave Raggett's work on the translation of XBRL into RDF (https://sourceforge.net/projects/xbrlimport/).

Collaboration
=============

I am open to collaboration within this free and open source project.
