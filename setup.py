# -*- coding: utf-8 -*-
from setuptools import setup

long_description = None
INSTALL_REQUIRES = [
    "sphinx>=5.1.1",
    "sphinxcontrib-restbuilder>=0.3",
]

setup_kwargs = {
    "name": "doccer",
    "version": "0.1.0",
    "description": "Documentation generator and checker for Python projects.",
    "long_description": long_description,
    "license": "Proprietary",
    "author": "",
    "author_email": "Eric Burgess <ericdb@gmail.com>",
    "maintainer": None,
    "maintainer_email": None,
    "url": "",
    "packages": [
        "doccer",
    ],
    "package_data": {"": ["*"]},
    "install_requires": INSTALL_REQUIRES,
    "python_requires": ">=3.8",
    "entry_points": {
        "console_scripts": [
            "doccer_hook = doccer:precommit_hook",
        ]
    },
}


setup(**setup_kwargs)
