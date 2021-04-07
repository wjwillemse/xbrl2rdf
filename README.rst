========
xbrl2rdf
========


.. image:: https://img.shields.io/pypi/v/xbrl2rdf.svg
        :target: https://pypi.python.org/pypi/xbrl2rdf

.. image:: https://img.shields.io/travis/wjwillemse/xbrl2rdf.svg
        :target: https://travis-ci.com/wjwillemse/xbrl2rdf

.. image:: https://readthedocs.org/projects/xbrl2rdf/badge/?version=latest
        :target: https://xbrl2rdf.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

> #### DISCLAIMER - BETA PHASE
> This XBRL to RDF parser is currently in a beta phase.
> 

Python package to convert XBRL instance and taxonomy files to RDF

* Free software: GNU GENERAL PUBLIC LICENSE, v2
* Documentation: https://xbrl2rdf.readthedocs.io.

Features
========

Here is what the package does:
- convert XBRL instance file and related taxonomy files (schemas and linkbases) to RDF and RDF-star

Quick overview
==============

To install the package

::

    pip install xbrl2rdf

To install the package from Github

::

	pip install -e git+https://github.com/wjwillemse/xbrl2rdf.git#egg=xbrl2rdf


How to run
==========

To parse an XBRL-instance file run in the root of the project

::

	python -m xbrl2rdf.xbrl2rdf


Contributing
============

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/wjwillemse/xbrl2rdf/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/wjwillemse/xbrl2rdf/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.



Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
