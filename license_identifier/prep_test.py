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

import os

from . import prep

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")


def test_span_tokenize():
    result = prep._span_tokenize("a bc\nde f")
    expected = [(0, 1), (2, 4), (5, 7), (8, 9)]
    assert result == expected

    result = prep._span_tokenize(["a bc", "de f"])
    assert result == expected


def test_tokens_and_positions_by_line():
    tok, pos = prep._tokens_and_positions_by_line(["a bc", "de f"])
    assert tok == [["a", "bc"], ["de", "f"]]
    assert pos == [[(0, 1), (2, 4)], [(0, 2), (3, 4)]]


def test_prep_license():
    path = os.path.join(BASE_DIR, "data", "test", "license",
                        "test_license.txt")
    lic = prep.License.from_filepath(path)
    assert len(lic.lines) == 1

    lic = prep.License.from_lines(["  ab c,d.  ", "\t", "   ef   "])
    assert list(lic.get_ignored_strings()) == [
        "  ", " ", "", "", "", "  \n\t\n   ", "   \n"]


def test_prep_source():
    path = os.path.join(BASE_DIR, "data", "test", "data", "test1.py")
    src = prep.Source.from_filepath(path)
    assert src.lines == ["zero", "one two three four", "five", "six", "seven"]

    src_subset_1 = src.subset(0, 2)
    assert src_subset_1.lines == ["zero", "one two three four"]
    assert src_subset_1.original_line_offset == 0

    src_subset_2 = src.subset(3, 5)
    assert src_subset_2.lines == ["six", "seven"]
    assert src_subset_2.original_line_offset == 3

    src_subset_3 = src_subset_2.subset(1, 2)
    assert src_subset_3.lines == ["seven"]
    assert src_subset_3.original_line_offset == 4


def test_source_tokens_by_line():
    src = prep.Source.from_lines(["  ab  cd  ", "", "   ef   "])
    assert src.tokens_by_line == [["ab", "cd"], [], ["ef"]]
    assert src.token_positions_by_line == [[(2, 4), (6, 8)], [], [(3, 5)]]


def test_source_get_ignored_strings():
    src = prep.Source.from_lines([])
    assert src.tokens_by_line == []
    assert list(src.get_ignored_strings()) == [""]

    src = prep.Source.from_lines(["   ", "  ", " "])
    assert src.tokens_by_line == [[], [], []]
    assert list(src.get_ignored_strings()) == ["   \n  \n \n"]

    src = prep.Source.from_lines(["  ab c,d.  ", "\t", "   ef   "])
    assert src.tokens_by_line == [["ab", "c", ",", "d", "."], [], ["ef"]]
    expected = ["  ", " ", "", "", "", "  \n\t\n   ", "   \n"]
    assert list(src.get_ignored_strings()) == expected


def test_source_original_indexing():
    src1 = prep.Source.from_lines([str(i) for i in range(100)])
    assert len(src1.lines) == 100

    src2 = src1.subset(40, 60)
    assert len(src2.lines) == 20

    assert src1.get_lines_original_indexing(42, 45) == ["42", "43", "44"]
    assert src2.get_lines_original_indexing(42, 45) == ["42", "43", "44"]

    assert src1.relative_line_index(42) == 42
    assert src2.relative_line_index(42) == 2


def test_license_library():
    license_dir = os.path.join(BASE_DIR, "data", "test", "license")
    license_library = prep.LicenseLibrary.from_path(license_dir)
    assert set(["test_license", "custom_license"]) == \
        set(license_library.licenses.keys())


def test_license_library_from_list():
    licenses = [
        prep.License.from_lines(["a"], name="L1"),
        prep.License.from_lines(["b"], name="L2"),
        prep.License.from_lines(["c"], name="L3"),
    ]
    license_library = prep.LicenseLibrary.from_licenses(licenses)
    assert list(license_library.licenses.keys()) == ["L1", "L2", "L3"]
    assert license_library.licenses["L1"].lines == ["a"]
    assert license_library.licenses["L2"].lines == ["b"]
    assert license_library.licenses["L3"].lines == ["c"]
