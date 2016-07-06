from collections import namedtuple
from os import linesep

COLUMN_LIMIT = 32767 - 10 # padding 10 for \'b and other formatting characters

def truncate_column(column):
    if isinstance(column, str) or isinstance(column, unicode):
        return column[0:COLUMN_LIMIT]
    else:
        return column

class MatchSummary(namedtuple("MatchSummary",
        ["input_fp",
         "matched_license",
         "score",
         "start_line_ind",
         "end_line_ind",
         "start_offset",
         "end_offset",
         "region_score",
         "found_region"])):

    @staticmethod
    def field_names():
        return [
            "input file name",
            "matched license type",
            "Score using whole input test",
            "Start line number",
            "End line number",
            "Start byte offset",
            "End byte offset",
            "Score using only the license text portion",
            "Found license text",
        ]

    def to_csv_row(self):
        csv_tuple = map(truncate_column, tuple(self))
        csv_tuple[0] = csv_tuple[0].encode('utf8', 'surrogateescape')
        csv_tuple[8] = csv_tuple[8].encode('utf8', 'surrogateescape')
        return csv_tuple

    def to_display_format(self):
        output_str = "Summary of the analysis" + linesep + linesep\
            + "Name of the input file: {}".format(self.input_fp) + linesep\
            + "Matched license type is {}".format(self.matched_license) + linesep\
            + "Score for the match is {:.3}".format(self.score) + linesep\
            + "License text beings at line {}.".format(self.start_line_ind) + linesep\
            + "License text ends at line {}.".format(self.end_line_ind) + linesep\
            + "Start byte offset for the license text is {}.".format(self.start_offset) + linesep\
            + "End byte offset for the license text is {}.".format(self.end_offset) +linesep\
            + "The found license text has the score of {:.3}".format(self.region_score) + linesep\
            + "The following text is found to be license text " + linesep\
            + "-----BEGIN-----" + linesep\
            + self.found_region \
            + "-----END-----" + linesep + linesep
        return output_str
