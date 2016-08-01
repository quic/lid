#!/usr/bin/env python

from setuptools import setup
from setuptools.command.install import install

import os

class CustomInstall(install):
    def run(self):
        # Perform original install steps
        install.run(self)

        # Perform custom install steps
        from license_identifier.license_identifier import LicenseIdentifier
        license_dir = os.path.join(self.install_lib, 'license_identifier/data/license_dir')
        pickle_file_path = os.path.join(self.install_lib, 'license_identifier/data/license_n_gram_lib.pickle')
        lcs_id_obj = LicenseIdentifier(
            license_dir = license_dir,
            pickle_file_path = pickle_file_path)

setup(
    name='license_identifier',
    version='0.31',
    description='Scans a file or folder for predefined licenses',
    author='Peter Shin',
    author_email='phshin@qti.qualcomm.com',
    url='https://www.python.org/sigs/distutils-sig/',
    packages=['license_identifier'],
    install_requires=[
        'future',
        'isodate',
        'pyparsing',
        'rdflib',
        'six',
        'nltk',
        'comment_parser==0.2.5',
    ],
    dependency_links=[
        'git+https://github.qualcomm.com/qosp/comment-parser.git@0.2.5#egg=comment_parser-0.2.5',
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
