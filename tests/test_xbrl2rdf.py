#!/usr/bin/env python

"""Tests for `xbrl2rdf` package."""


import unittest
from click.testing import CliRunner
from os.path import join
import filecmp

from xbrl2rdf import xbrl2rdf

class TestXbrl2rdf(unittest.TestCase):
    """Tests for `xbrl2rdf` package."""

    # def test_appalachian(self):
    #   xbrl2rdf.main(url="AepAppalachianTransmissionCompanyInc-436-2018Q1F1.xbrl", 
    #                 taxo=6,
    #                 output=join("data", "rdf"), 
    #                 output_format=1)

    def test_FERC_FORM_1(self):
        """
        """
        runner = CliRunner()
        
        result = runner.invoke(xbrl2rdf.main, 
                ['--url', join("tests", "instances", "AepAppalachianTransmissionCompanyInc-436-2018Q1F1.xbrl"),
                 '--taxo', "6",
                 '--output', join("tests", "actual"),
                 '--output_format', "1"])
        
        assert result.exit_code == 0

        actual = join("tests", "actual", "AepAppalachianTransmissionCompanyInc-436-2018Q1F1.ttl")
        expected = join("tests", "expected", "AepAppalachianTransmissionCompanyInc-436-2018Q1F1.ttl")

        result = filecmp.cmp(actual, expected, shallow=False)

        assert result == True
        # assert 'xbrl2rdf.cli.main' in result.output
        # help_result = runner.invoke(cli.main, ['--help'])
        # assert help_result.exit_code == 0
        # assert '--help  Show this message and exit.' in help_result.output

    def test_SOLVENCY2_QRS(self):
        """
        """
        runner = CliRunner()
        
        result = runner.invoke(xbrl2rdf.main, 
                ['--url', join("tests", "instances", "qrs_240_instance.xbrl"),
                 '--taxo', "2",
                 '--output', join("tests", "actual"),
                 '--output_format', "1"])
        
        assert result.exit_code == 0

        actual = join("tests", "actual", "qrs_240_instance.ttl")
        expected = join("tests", "expected", "qrs_240_instance.ttl")

        result = filecmp.cmp(actual, expected, shallow=False)

        assert result == True
