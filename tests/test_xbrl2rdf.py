#!/usr/bin/env python

"""Tests for `xbrl2rdf` package."""


import unittest
from click.testing import CliRunner
from os.path import join, isfile, basename
from os import listdir
import filecmp
import json

from xbrl2rdf import xbrl2rdf_cli, MainProcessor


class TestXbrl2rdf(unittest.TestCase):
    """Tests for `xbrl2rdf` package."""

    def test_FERC_FORM_1_cli(self):
        """ """
        runner = CliRunner()

        result = runner.invoke(
            xbrl2rdf_cli.main,
            [
                "--url",
                join(
                    "tests",
                    "instances",
                    "AepAppalachianTransmissionCompanyInc-436-2018Q1F1.xbrl",
                ),
                "--taxo",
                "6",
                "--output",
                join("tests", "actual"),
                "--output_format",
                "1",
            ],
        )

        assert result.exit_code == 0, "xbrl2rdf_cli did not return 0"

        actual = join(
            "tests",
            "actual",
            "data",
            "AepAppalachianTransmissionCompanyInc-436-2018Q1F1.ttl",
        )
        expected = join(
            "tests",
            "expected",
            "data",
            "AepAppalachianTransmissionCompanyInc-436-2018Q1F1.ttl",
        )

        result = filecmp.cmp(actual, expected, shallow=False)

        assert result == True, (
            "Not equal files: " + str(actual) + " and " + str(expected)
        )

    def test_FERC_FORM_1_main(self):
        """ """
        data_url = join(
            "tests",
            "instances",
            "AepAppalachianTransmissionCompanyInc-436-2018Q1F1.xbrl",
        )
        taxo_url = join(
            "data",
            "taxonomies",
            "TaxonomyFile_Form1_v2020-01-01.zip",
        )
        output = join("tests", "actual")

        # list of the files already processed
        dts_processed = list()
        # check to see if json file exists
        for filename in listdir(output):
            if filename == "preloads.json":
                with open(join(output, "preloads.json"), "r") as infile:
                    dts_processed = json.load(infile)

        result = MainProcessor(
            data_url=data_url,
            taxo_url=taxo_url,
            output=output,
            output_format=1,
            dts_processed=dts_processed,
        )

        assert result == 0, "MainProcessor did not return 0"

        # compare facts ttl
        actual_facts = join(
            "tests",
            "actual",
            "data",
            "AepAppalachianTransmissionCompanyInc-436-2018Q1F1.ttl",
        )
        expected_facts = join(
            "tests",
            "expected",
            "data",
            "AepAppalachianTransmissionCompanyInc-436-2018Q1F1.ttl",
        )
        result = filecmp.cmp(actual_facts, expected_facts, shallow=False)
        assert result == True, (
            "Not equal files: " + str(actual_facts) + " and " + str(expected_facts)
        )

        # compare taxonomy ttls
        # (a limited set of taxonomy ttls is compared (only those in the expected directory))
        actual_taxo_dir = join(
            "tests",
            "actual",
            "taxonomies",
            ".".join(basename(taxo_url).split(".")[0:-1]),
        )
        expected_taxo_dir = join(
            "tests",
            "expected",
            "taxonomies",
            ".".join(basename(taxo_url).split(".")[0:-1]),
        )
        for taxo_file in listdir(expected_taxo_dir):
            actual_taxo_file = join(actual_taxo_dir, taxo_file)
            expected_taxo_file = join(expected_taxo_dir, taxo_file)
            result = filecmp.cmp(actual_taxo_file, expected_taxo_file, shallow=False)
            assert result == True, (
                "Not equal files: "
                + str(actual_taxo_file)
                + " and "
                + str(expected_taxo_file)
            )

    def test_SOLVENCY2_QRS_cli(self):
        """ """
        runner = CliRunner()

        result = runner.invoke(
            xbrl2rdf_cli.main,
            [
                "--url",
                join("tests", "instances", "qrs_260_instance.xbrl"),
                "--taxo",
                "2",
                "--output",
                join("tests", "actual"),
                "--output_format",
                "1",
            ],
        )

        assert result.exit_code == 0, "xbrl2rdf_cli did not return 0"

        actual = join("tests", "actual", "data", "qrs_260_instance.ttl")
        expected = join("tests", "expected", "data", "qrs_260_instance.ttl")

        result = filecmp.cmp(actual, expected, shallow=False)

        assert result == True, (
            "Not equal files: " + str(actual) + " and " + str(expected)
        )

    def test_SOLVENCY2_QRS_main(self):
        """ """
        data_url = join("tests", "instances", "qrs_260_instance.xbrl")
        taxo_url = join(
            "data",
            "taxonomies",
            "EIOPA_SolvencyII_XBRL_Taxonomy_2.6.0_PWD_with_External_Files.zip",
        )
        output = join("tests", "actual")

        # list of the files already processed
        dts_processed = list()
        # check to see if json file exists
        for filename in listdir(output):
            if filename == "preloads.json":
                with open(join(output, "preloads.json"), "r") as infile:
                    dts_processed = json.load(infile)

        result = MainProcessor(
            data_url=data_url,
            taxo_url=taxo_url,
            output=output,
            output_format=1,
            dts_processed=dts_processed,
        )

        assert result == 0, "MainProcessor did not return 0"

        # compare facts ttl
        actual_facts = join("tests", "actual", "data", "qrs_260_instance.ttl")
        expected_facts = join("tests", "expected", "data", "qrs_260_instance.ttl")
        result = filecmp.cmp(actual_facts, expected_facts, shallow=False)
        assert result == True, (
            "Not equal files: " + str(actual_facts) + " and " + str(expected_facts)
        )

        # compare taxonomy ttls
        # (a limited set of taxonomy ttls is compared (only those in the expected directory))
        actual_taxo_dir = join(
            "tests",
            "actual",
            "taxonomies",
            ".".join(basename(taxo_url).split(".")[0:-1]),
        )
        expected_taxo_dir = join(
            "tests",
            "expected",
            "taxonomies",
            ".".join(basename(taxo_url).split(".")[0:-1]),
        )
        for taxo_file in listdir(expected_taxo_dir):
            actual_taxo_file = join(actual_taxo_dir, taxo_file)
            expected_taxo_file = join(expected_taxo_dir, taxo_file)
            result = filecmp.cmp(actual_taxo_file, expected_taxo_file, shallow=False)
            assert result == True, (
                "Not equal files: "
                + str(actual_taxo_file)
                + " and "
                + str(expected_taxo_file)
            )
