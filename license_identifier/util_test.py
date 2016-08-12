from . import util
import os

def test_read_lines_offsets():
    input_fp = os.path.join(os.getcwd(), '../data/test/data/test1.py')
    lines, offsets = util.read_lines_offsets(input_fp)
    assert lines == [
        "zero",
        "one two three four",
        "five",
        "six",
        "seven"]
    assert offsets == [0, 5, 24, 29, 33, 38]

def test_get_lines_and_line_offsets():
    lines, offsets = util.get_lines_and_line_offsets(["a b c\n", "d e\n", "f\n", "g h i j\n"])
    assert lines == ["a b c", "d e", "f", "g h i j"]
    assert offsets == [0, 6, 10, 12, 20]

def test_get_user_date_time_str():
    assert len(util.get_user_date_time_str()) > 15

def test_is_punctuation():
    assert util.is_punctuation("#")
    assert util.is_punctuation("//")
    assert util.is_punctuation("/*")
    assert util.is_punctuation("*")
    assert util.is_punctuation("1.0") == False
    assert util.is_punctuation("abc123") == False

def test_files_from_path():
    # Process a directory
    input_dir = os.path.join(os.getcwd(), '../data/test/data')
    result = util.files_from_path(input_dir)
    assert len(result) == 6
    assert result[0].endswith("test/data/test0.py")
    assert result[1].endswith("test/data/test1.py")
    assert result[2].endswith("test/data/subdir/test2.py")
    assert result[3].endswith("test/data/subdir/subdir2/test3.py")
    assert result[4].endswith("test/data/subdir/subdir2/test4.bogus")
    assert result[5].endswith("test/data/subdir/subdir2/test5.py")

    # Process a single file
    input_file = os.path.join(os.getcwd(), '../data/test/data/test1.py')
    result = util.files_from_path(input_file)
    assert len(result) == 1
    assert result[0].endswith("test/data/test1.py")
