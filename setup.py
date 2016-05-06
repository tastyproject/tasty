#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

import sys
from ts_commands import *
from tasty_version import TASTY_VERSION

extras = {}

if sys.version_info >= (3,):
    extras['use_2to3'] = True
    extras['convert_2to3_doctests'] = ['src/your/module/README.txt']

setup(
    name='Tasty',
    version=TASTY_VERSION,
    packages=find_packages(),
    requires = [],
    install_requires = ["gmpy2"],
    extras_require = {
        "PROFILING" : ["epydoc", "pylint", "figleaf"]
    },

    # important non-python files goes in here
    package_data = {
        "circuit" :  ["circuit/circuits/*",],
        "resources" :  ["resources/*",]},

    # installing unzipped
    zip_safe = False,

    # predefined extension points, e.g. for plugins
    entry_points = """
    [console_scripts]
    tasty_init = tasty.scripts.tasty_init:main
    tasty_post = tasty.scripts.tasty_post:start
    tasty = tasty.scripts.main:start
    """,

    # custom commands
    cmdclass = commands,

    author = "Stefan Koegl, Thomas Schneider, Immo Wehrenberg",

    author_email = "stefan dot koegl at rub dot de, thomas dot schneider at trust dot rub dot de, immo dot wehrenberg at rub dot de",
    description = "Toolbox for Automatic Secure Two-partY computation",

    # FIXME: add long_description
    long_description = """
    """,

    # FIXME: add license
    license = "GPL3",

    # FIXME: add keywords
    keywords = "compiler, encryption, garbled circuits, homomorphic, Paillier, benchmark, graph",

    # FIXME: add download url
    url = "http://tastyproject.net",

    test_suite = 'tasty.tests.all_tests',
    **extras
)
