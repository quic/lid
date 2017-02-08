#!/usr/bin/env python

# Copyright (c) 2017, The Linux Foundation. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#     * Neither the name of The Linux Foundation nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
