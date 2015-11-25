from . import util
import os

def test_read_lines_offsets():
    assert util.read_lines_offsets(os.path.join(os.getcwd(), '../data/test/data/test1.py'))[0] == ["zero",
        "one two three four",
        "five",
        "six",
        "seven"]
    assert util.read_lines_offsets(os.path.join(os.getcwd(), '../data/test/data/test1.py'))[1] == [0, 5, 24, 29, 33, 38]
