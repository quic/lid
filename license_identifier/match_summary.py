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

from collections import OrderedDict
from os import linesep
import six

COLUMN_LIMIT = 32767 - 100 # padding 100 for \'b and other formatting characters

def truncate_column(column):
    if isinstance(column, six.string_types):
        return column[0:COLUMN_LIMIT]
    else:
        return column

class MatchSummary(dict):
    @staticmethod
    def field_names():
        return OrderedDict([
            ("input_fp", "input file path"),
            ("matched_license", "matched license type"),
            ("score", "Score using whole input test"),
            ("rank", "Rank based on score"),
            ("start_line_ind", "Start line number"),
            ("end_line_ind", "End line number"),
            ("start_offset", "Start byte offset"),
            ("end_offset", "End byte offset"),
            ("region_score", "Score using only the license text portion"),
            ("found_region", "Found license text"),
            ("original_region", "Matched license text without context")
        ])

    def to_display_format(self):
        output_str = "Summary of the analysis" + linesep + linesep\
            + u"Name of the input file: {}".format(self["input_fp"]) + linesep\
            + u"Matched license type is {}".format(self["matched_license"]) + linesep\
            + u"Score for the match is {:.3}".format(self["score"]) + linesep\
            + u"Rank for the match is {}".format(self["rank"]) + linesep\
            + u"License text beings at line {}.".format(self["start_line_ind"]) + linesep\
            + u"License text ends at line {}.".format(self["end_line_ind"]) + linesep\
            + u"Start byte offset for the license text is {}.".format(self["start_offset"]) + linesep\
            + u"End byte offset for the license text is {}.".format(self["end_offset"]) +linesep\
            + u"The found license text has the score of {:.3}".format(self["region_score"]) + linesep\
            + "The following text is found to be license text" + linesep\
            + "-----BEGIN-----" + linesep\
            + self["found_region"] \
            + "-----END-----" + linesep + linesep
        if "original_region" in self:
            output_str = output_str[:-1] \
                + "The following text is found to be " \
                + "original matched license text without context" + linesep \
                + "-----BEGIN-----" + linesep \
                + self["original_region"] \
                + "-----END-----" + linesep + linesep
        return output_str

    def to_csv_row(self):
        csv_row = []
        for key in self.field_names().keys():
            try:
                if key in self:
                    if key in ("input_fp", "found_region", "original_region"):
                        value = self[key]
                        if value.startswith(('+','-','@','=')):
                            value = ' ' + value
                        value = value.encode('utf8', 'replace')
                        csv_row.append(truncate_column(value))
                    else:
                        csv_row.append(truncate_column(self[key]))
            except:
                csv_row.append("Errors in encoding/decoding unicode characters.")
        return csv_row
