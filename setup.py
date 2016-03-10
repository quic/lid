#!/usr/bin/env python

from distutils.core import setup

setup(name='license_identifier',
            version='1.0',
            description='Scans a file or folder for predefined licenses',
            author='Peter Shin',
            author_email='phshin@qti.qualcomm.com',
            url='https://www.python.org/sigs/distutils-sig/',
            packages=['license_identifier'],
            package_data={'license_identifier': ['data/license_n_gram_lib.pickle']}
           )
