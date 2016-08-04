from collections import OrderedDict
from os import linesep
import six

COLUMN_LIMIT = 32767 - 10 # padding 10 for \'b and other formatting characters

def truncate_column(column):
    if isinstance(column, six.string_types):
        return column[0:COLUMN_LIMIT]
    else:
        return column

class MatchSummary(dict):
    @staticmethod
    def field_names():
        return OrderedDict([
            ("input_fp", "input file name"),
            ("matched_license", "matched license type"),
            ("score", "Score using whole input test"),
            ("start_line_ind", "Start line number"),
            ("end_line_ind", "End line number"),
            ("start_offset", "Start byte offset"),
            ("end_offset", "End byte offset"),
            ("region_score", "Score using only the license text portion"),
            ("found_region", "Found license text"),
        ])

    def to_csv_row(self):
        csv_row = [truncate_column(self[key]) for key in MatchSummary.field_names().keys()]
        csv_row[0] = csv_row[0].encode('utf8', 'surrogateescape')
        csv_row[8] = csv_row[8].encode('utf8', 'surrogateescape')
        return csv_row

    def to_display_format(self):
        output_str = "Summary of the analysis" + linesep + linesep\
            + "Name of the input file: {}".format(self["input_fp"]) + linesep\
            + "Matched license type is {}".format(self["matched_license"]) + linesep\
            + "Score for the match is {:.3}".format(self["score"]) + linesep\
            + "License text beings at line {}.".format(self["start_line_ind"]) + linesep\
            + "License text ends at line {}.".format(self["end_line_ind"]) + linesep\
            + "Start byte offset for the license text is {}.".format(self["start_offset"]) + linesep\
            + "End byte offset for the license text is {}.".format(self["end_offset"]) +linesep\
            + "The found license text has the score of {:.3}".format(self["region_score"]) + linesep\
            + "The following text is found to be license text " + linesep\
            + "-----BEGIN-----" + linesep\
            + self["found_region"] \
            + "-----END-----" + linesep + linesep
        return output_str
