"""Example importer for PDF statements from ACME Bank.

This importer identifies the file from its contents and only supports filing, it
cannot extract any transactions from the PDF conersion to text. This is common,
and I figured I'd provide an example for how this works.

Furthermore, it uses an external library called PDFMiner2
(https://github.com/metachris/pdfminer), which may or may not be installed on
your machine. This example shows how to write a test that gets skipped
automatically when an external tool isn't installed.
"""
__author__ = 'Martin Blais <blais@furius.ca>'

import csv
import datetime
import re
import pprint
import logging
import subprocess
import unittest
from os import path

from dateutil.parser import parse as parse_datetime

from beancount.core.number import D
from beancount.core.number import ZERO
from beancount.core.number import MISSING
from beancount.core import data
from beancount.core import account
from beancount.core import amount
from beancount.core import position
from beancount.core import inventory
from beancount.ingest import importer
from beancount.ingest import regression


def is_pdfminer_installed():
    """Return true if the external PDFMiner2 tool installed."""
    returncode = subprocess.call(['pdf2txt.py', '-h'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
    return returncode == 0


def pdf_to_text(filename):
    """Convert a PDF file to a text equivalent.

    Args:
      filename: A string path, the filename to convert.
    Returns:
      A string, the text contents of the filename.
    """
    pipe = subprocess.Popen(['pdf2txt.py', filename],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    stdout, stderr = pipe.communicate()
    if stderr:
        raise ValueError(stderr.decode())
    else:
        return stdout.decode()


class Importer(importer.ImporterProtocol):
    """An importer for ACME Bank PDF statements."""

    def __init__(self, account_filing):
        self.account_filing = account_filing

    def identify(self, file):
        if file.mimetype() != 'application/pdf':
            return False

        # Look for some words in the PDF file to figure out if it's a statement
        # from ACME. The filename they provide (Statement.pdf) isn't useful.
        text = file.convert(pdf_to_text)
        if text:
            return re.match('ACME Bank', text) is not None

    def file_name(self, file):
        # Noramlize the name to something meaningful.
        return 'acmebank.pdf'

    def file_account(self, _):
        return self.account_filing

    def file_date(self, file):
        # Get the actual statement's date from the contents of the file.
        text = file.convert(pdf_to_text)
        match = re.search('Date: ([^\n]*)', text)
        if match:
            return parse_datetime(match.group(1)).date()


@unittest.skipIf(not is_pdfminer_installed(), "PDFMiner2 is not installed")
def test():
    # Create an importer instance for running the regression tests.
    importer = Importer("Assets:US:AcmeBank")
    yield from regression.compare_sample_files(importer, __file__)
