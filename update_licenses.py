#!/usr/bin/env python

import rdflib
from collections import OrderedDict
from pprint import pprint
import os
import sys

def get_license_ids():
    graph = rdflib.Graph()
    graph.parse('http://spdx.org/licenses/index.html', 'rdfa')
    ref = rdflib.URIRef('http://spdx.org/rdf/terms#licenseId')
    objs = graph.subject_objects(ref)
    return map(lambda x: x[1].value, objs)

def get_license_text(licenseId):
    graph = rdflib.Graph()

    try:
        graph.parse('http://spdx.org/licenses/' + licenseId + '.html')
    except:
        return None

    ref = rdflib.URIRef("http://spdx.org/rdf/terms#licenseText")
    objs = graph.subject_objects(ref)
    return objs.next()[1].value.encode('utf-8')

def write_licenses_dir(ids):
    licenseDir = '../data/license_dir'
    if not os.path.exists(licenseDir):
        os.makedirs(licenseDir)

    for licenseId in ids:
        sys.stdout.write("Updating license text for '{}'\n".format(licenseId))
        text = get_license_text(licenseId)
        if text is None:
            continue

        with open('{}/{}.txt'.format(licenseDir, licenseId), 'w') as hdl:
            hdl.write(text)

with open('./licenses.py', 'w') as out:
    ids = get_license_ids()
    ids.sort()
    out.write('license_ids = ')
    pprint(ids, indent=4, stream=out)

    write_licenses_dir(ids)
