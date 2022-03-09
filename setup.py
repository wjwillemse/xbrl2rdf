#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=7.0', 'rdflib', 'lxml' ]

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="Willem Jan Willemse",
    author_email='w.j.willemse@xs4all.nl',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Python package to convert XBRL instance and taxonomy files to RDF",
    entry_points={
        'console_scripts': [
            'xbrl2rdf=xbrl2rdf.xbrl2rdf:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='xbrl2rdf',
    name='xbrl2rdf',
    packages=find_packages(include=['xbrl2rdf', 'xbrl2rdf.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/wjwillemse/xbrl2rdf',
    version='0.1.1',
    zip_safe=False,
)
