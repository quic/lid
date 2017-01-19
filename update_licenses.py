#!/usr/bin/env python

import rdflib
import urllib
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

def get_exception_ids():
    graph = rdflib.Graph()
    graph.parse('http://spdx.org/licenses/exceptions-index.html', 'rdfa')
    ref = rdflib.URIRef('http://spdx.org/rdf/terms#licenseId')
    objs = graph.subject_objects(ref)
    return map(lambda x: x[1].value, objs)

def get_license_text_and_header(licenseId):
    graph = rdflib.Graph()

    try:
        graph.parse('http://spdx.org/licenses/' + urllib.quote(licenseId) + '.html')
    except:
        return (None, None)

    text = get_sub_objs("http://spdx.org/rdf/terms#licenseText", graph)
    header = get_sub_objs("http://spdx.org/rdf/terms#standardLicenseHeader", graph)
    return (text, header)

def get_sub_objs(uri, graph):
    ref = rdflib.URIRef(uri)
    objs = graph.subject_objects(ref)
    try:
        value = objs.next()
        return xml_to_text(value[1])
    except StopIteration:
        return None

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

def write_licenses_dir(ids, exception_ids):
    licenseDir = './license_identifier/data/license_dir'
    if not os.path.exists(licenseDir):
        os.makedirs(licenseDir)

    for licenseId in ids:
        sys.stdout.write("Updating license text for '{}'\n".format(licenseId))
        text, header = get_license_text_and_header(licenseId)
        if text is None:
            continue

        with open('{}/{}.txt'.format(licenseDir, licenseId), 'w') as hdl:
            hdl.write(text)
        if header and "There is no standard license header for the license" not in header:
            with open('{}/headers/{}.txt'.format(licenseDir, licenseId), 'w') as hdl:
                hdl.write(header)

    for exception in exception_ids:
        sys.stdout.write("Updating exception text for '{}'\n".format(exception))

with open('./license_identifier/licenses.py', 'w') as out:
    ids = get_license_ids()
    ids.sort()
    exception_ids = get_exception_ids()
    out.write('license_ids = ')
    pprint(ids, indent=4, stream=out)

    write_licenses_dir(ids, exception_ids)
