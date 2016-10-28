#!/usr/bin/env python

import os

from setuptools import setup
from setuptools.command.install import install


class CustomInstall(install):

    def run(self):
        # Perform original install steps
        install.run(self)

        # Perform custom install steps
        from license_identifier.license_identifier import LicenseIdentifier

        license_dir = os.path.join(
            self.install_lib, 'license_identifier/data/license_dir'
        )
        pickle_file_path = os.path.join(
            self.install_lib,
            'license_identifier/data/license_n_gram_lib.pickle'
        )

        LicenseIdentifier(license_dir=license_dir,
                          pickle_file_path=pickle_file_path)


setup(
    name='license_identifier',
    version='1.0.1',
    description='Scans a file or folder for predefined licenses',
    author='Peter Shin',
    author_email='phshin@qti.qualcomm.com',
    url='https://www.python.org/sigs/distutils-sig/',
    packages=['license_identifier'],
    entry_points={
        'console_scripts': [
            'license-identifier = license_identifier.cli:main',
        ],
    },
    install_requires=[
        "comment-parser==0.2.5",
        # Note: Using a pinned version of comment_parser for disambiguation
        #       (this package name clashes with an existing PyPI package)
        "chardet",
        "future",
        "nltk",
        "rdflib",
        "six",
    ],
    package_data={
        'license_identifier': [
            'data/license_n_gram_lib.pickle',
            'data/license_dir/*.txt',
            'data/license_dir/custom/*.txt',
        ]
    },
    cmdclass={'install': CustomInstall},
)
