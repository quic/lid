from . import util
import os

def test_detect_file_encoding():
    input_fp = os.path.join(os.getcwd(), '../data/test/encodings/test-utf-8')
    encoding = util.detect_file_encoding(input_fp)
    assert encoding == "utf-8"

    input_fp = os.path.join(os.getcwd(), '../data/test/encodings/test-windows-1252')
    encoding = util.detect_file_encoding(input_fp)
    assert encoding == "windows-1252"

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

def test_read_lines_offsets_non_ascii():
    input_fp = os.path.join(os.getcwd(), '../data/test/encodings/test-utf-8')
    lines, offsets = util.read_lines_offsets(input_fp)
    assert lines == [u"\u3053\u3093\u306b\u3061\u306f"]
    assert offsets == [0, 6]

    input_fp = os.path.join(os.getcwd(), '../data/test/encodings/test-windows-1252')
    lines, offsets = util.read_lines_offsets(input_fp)
    assert lines == [u"Non-ascii: \u00a3100"]
    assert offsets == [0, 16]

def test_get_lines_and_line_offsets():
    lines, offsets = util.get_lines_and_line_offsets(["a b c\n", "d e\n", "f\n", "g h i j\n"])
    assert lines == ["a b c", "d e", "f", "g h i j"]
    assert offsets == [0, 6, 10, 12, 20]

    lines, offsets = util.get_lines_and_line_offsets(["a b c\r\n", "d e\r\n", "f\r\n", "g h i j\r\n"])
    assert lines == ["a b c", "d e", "f", "g h i j"]
    assert offsets == [0, 7, 12, 15, 24]

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
