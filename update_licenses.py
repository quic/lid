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
#
# SPDX-License-Identifier: BSD-3-Clause

import datetime
import os
from pprint import pprint
import sys
import rdflib
import urlparse


BASE_URL = 'http://spdx.org/licenses/'


def main():
    """
    This file updates our collection of license template files and should be
    run when SPDX updates to a new version. After updating license_dir, make
    sure to remake the license_n_gram_lib.pickle file.

    It also updates some fixture data in licenses.py that the core module may
    use to add license metadata to the results.
    """
    update_spdx_metadata()
    update_license_dir()


def get_license_version():
    full_url = urlparse.urljoin(BASE_URL, 'index.html')
    graph = rdflib.Graph()
    graph.parse(full_url, 'rdfa')
    ref = rdflib.URIRef('http://spdx.org/rdf/terms#licenseListVersion')
    objs = graph.subject_objects(ref)
    version_str = objs.next()[1].decode()
    return version_str


def get_license_ids_from_spdx():
    full_url = urlparse.urljoin(BASE_URL, 'index.html')
    graph = rdflib.Graph()
    graph.parse(full_url, 'rdfa')
    ref = rdflib.URIRef('http://spdx.org/rdf/terms#licenseId')
    objs = graph.subject_objects(ref)
    return map(lambda x: x[1].value, objs)


def get_exception_ids():
    full_url = urlparse.urljoin(BASE_URL, 'exceptions-index.html')
    graph = rdflib.Graph()
    graph.parse(full_url, 'rdfa')
    ref = rdflib.URIRef('http://spdx.org/rdf/terms#licenseExceptionId')
    objs = graph.subject_objects(ref)
    return map(lambda x: x[1].value, objs)


def get_license_text_and_header(license_id):
    graph = rdflib.Graph()
    full_url = urlparse.urljoin(BASE_URL, '{}.html'.format(license_id))

    try:
        graph.parse(full_url)
    except:
        return (None, None)

    text_location = "http://spdx.org/rdf/terms#licenseText"
    text = remove_extraneous_text(get_sub_objs(text_location, graph))
    header_location = "http://spdx.org/rdf/terms#standardLicenseHeader"
    header = get_sub_objs(header_location, graph)

    return text, header

def remove_extraneous_text(text):
    # per condition 12 https://spdx.org/spdx-license-list/matching-guidelines
    # this is not indicated in markdown, so just need to find the 
    # text that indicates the end of the license and remove the rest
    end_index = text.find("END OF TERMS AND CONDITIONS")
    if end_index != -1:
        text = text[0:end_index]
    return text    

def get_exception_text(exception_id):
    graph = rdflib.Graph()
    full_url = urlparse.urljoin(BASE_URL, '{}.html'.format(exception_id))

    try:
        graph.parse(full_url)
    except:
        return None

    exception_location = "http://spdx.org/rdf/terms#licenseExceptionText"
    text = get_sub_objs(exception_location, graph)

    return text


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

    license_dir = './license_identifier/data/license_dir'

    try:
        os.makedirs(license_dir)
    except:
        pass

    for license_id in ids:
        log_license_text = "Updating license text for '{}'\n"
        sys.stdout.write(log_license_text.format(license_id))
        text, header = get_license_text_and_header(license_id)
        if text is None:
            continue

        full_text_file = os.path.join(license_dir, '{}.txt'.format(license_id))
        with open(full_text_file, 'w') as hdl:
            hdl.write(text)

        no_header = "There is no standard license header for the license"
        if header and no_header not in header:
            header_file = os.path.join(license_dir, 'headers',
                                       '{}.txt'.format(license_id))
            with open(header_file, 'w') as hdl:
                hdl.write(header)

    for exception in exception_ids:
        log_exception_text = "Updating exception text for '{}'\n"
        sys.stdout.write(log_exception_text.format(exception))
        text = get_exception_text(exception)
        if text is None:
            continue
        exception_file = os.path.join(license_dir, 'exceptions',
                                      '{}.txt'.format(exception))
        with open(exception_file, 'w') as hdl:
            hdl.write(text)


def update_spdx_metadata():
    spdx_version = get_license_version()
    curr_datetime = datetime.datetime.now().strftime("%c")
    ids = sorted(get_license_ids_from_spdx())
    with open('./license_identifier/licenses.py', 'w') as out:
        out.write("# Copyright (c) %s, The Linux Foundation. All rights reserved.\n" % 
            datetime.datetime.now().year)
        out.write("# SPDX-License-Identifier: BSD-3-Clause\n")
        out.write("spdx_version = '{}'\n".format(spdx_version))
        out.write("date_updated_license_dir = '{}'\n".format(curr_datetime))
        out.write("license_ids = ")
        pprint(ids, indent=4, stream=out)


def update_license_dir():
    ids = get_license_ids_from_spdx()
    exception_ids = get_exception_ids()
    write_licenses_dir(ids, exception_ids)


if __name__ == '__main__':
    main()
