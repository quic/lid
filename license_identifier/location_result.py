from collections import namedtuple

LocationResult = namedtuple("LocationResult",
    ["start_line",
     "end_line",
     "start_offset",
     "end_offset",
     "score",
     "start_line_orig",
     "end_line_orig"])
