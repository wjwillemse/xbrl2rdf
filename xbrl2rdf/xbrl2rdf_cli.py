"""Main module."""

import json
import sys
import click
import os
from os import listdir
from os.path import join, isfile, basename

from .MainProcessor import MainProcessor


@click.command()
@click.option(
    "--url",
    default=join("data", "instances", "qrs_260_instance.xbrl"),
    prompt="input file",
)
@click.option("--output", default=join("data", "rdf"), prompt="output directory")
@click.option(
    "--output_format", default=1, prompt="1: rdf-turtle\n2: rdf-star-turtle\n"
)
def main(url: str, output: str, output_format: int) -> int:
    """Command line interface for converting XBRL to RDF"""

    MainProcessor(
        data_url=url,
        output=output,
        output_format=output_format,
    )


if __name__ == "__main__":
    sys.exit(main())
