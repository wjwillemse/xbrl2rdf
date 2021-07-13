"""Main module."""

import tkinter as tk
from tkinter import filedialog, simpledialog
from tkinter import ttk
from tkinter import messagebox
import json, re
import sys
import click
from io import StringIO, BytesIO
import logging
import os
from os import listdir
from os.path import join, isfile, abspath
from datetime import datetime
import rdflib
import time
from pathlib import Path
from .MainProcessor import MainProcessor


def main():
    """User interface for converting XBRL to RDF"""

    # list of the files already processed
    dts_processed = list()
    # extensions_to_process = ['.xbrl']
    directory = tk.filedialog.askdirectory(title="Select input directory")
    output = tk.filedialog.askdirectory(title="Select output directory")
    extensions = tk.simpledialog.askstring(
        title="Enter extensions separated by whitespace",
        prompt="Enter extensions separated by whitespace",
    )
    extensions = re.split("\s+", extensions)
    # setup output directories
    Path(output + "/data").mkdir(parents=True, exist_ok=True)
    Path(output + "/taxonomies").mkdir(parents=True, exist_ok=True)

    for filename in os.listdir(directory):
        extension = os.path.splitext(filename)[1][1:]
        if extension in extensions:
            url = os.path.join(directory, filename)
            # setting the default taxo since isn't used with local files
            # and ttl rather than ttl* since those are the options we need
            MainProcessor(url, 2, output, 1)


if __name__ == "__main__":
    sys.exit(main())
