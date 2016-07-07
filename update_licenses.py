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
    return xml_to_text(objs.next()[1])

def xml_to_text(literal):
    # appears to be a series of <p> elements under the top level node
    if isinstance(literal.value, unicode):
        return literal.value.encode('utf-8')
    output = ""
    for child in literal.value.firstChild.childNodes:
        if child.nodeValue:
            output += child.nodeValue.encode('utf-8')
        output += output_tree(child)
    return output

def output_tree(parent):
    output = ""
    for node in parent.childNodes:
        if node.nodeValue:
            output += node.nodeValue.encode('utf-8')
        output += output_tree(node)
    return output

def write_licenses_dir(ids):
    licenseDir = './license_identifier/data/license_dir'
    if not os.path.exists(licenseDir):
        os.makedirs(licenseDir)

    for licenseId in ids:
        sys.stdout.write("Updating license text for '{}'\n".format(licenseId))
        text = get_license_text(licenseId)
        if text is None:
            continue

        with open('{}/{}.txt'.format(licenseDir, licenseId), 'w') as hdl:
            hdl.write(text)

with open('./license_identifier/licenses.py', 'w') as out:
    ids = get_license_ids()
    ids.sort()
    out.write('license_ids = ')
    pprint(ids, indent=4, stream=out)

    write_licenses_dir(ids)
