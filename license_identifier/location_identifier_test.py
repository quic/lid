try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from os import getcwd
from os.path import join, abspath

from mock import patch

from . import location_identifier as loc_id
from . import prep


BASE_DIR = join(getcwd(), "..")


def get_license_dir():
    license_dir = join(BASE_DIR, 'data', 'test', 'license')
    return license_dir


def test_main_process_default():
    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    loc_id_obj = loc_id.Location_Finder()
    assert loc_id_obj.strategy == "one_line_then_expand"
    assert loc_id_obj.similarity == "edit_weighted"
    lic = prep.License.from_filepath(lcs_file)
    src = prep.Source.from_filepath(input_file)
    loc_result = loc_id_obj.main_process(lic, src)
    assert loc_result == (1, 2, 5, 24, 1.0, 1, 2)

    loc_id_obj = loc_id.Location_Finder(context_lines=1)
    loc_result = loc_id_obj.main_process(lic, src)
    assert loc_result == (0, 3, 0, 29, 1.0, 1, 2)


def test_main_process_ngram():
    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    loc_id_obj = loc_id.Location_Finder(similarity="ngram")
    lic = prep.License.from_filepath(lcs_file)
    src = prep.Source.from_filepath(input_file)
    loc_result = loc_id_obj.main_process(lic, src)
    assert loc_result == (1, 2, 5, 24, 1.0, 1, 2)

    loc_id_obj = loc_id.Location_Finder(context_lines=1)
    loc_result = loc_id_obj.main_process(lic, src)
    assert loc_result == (0, 3, 0, 29, 1.0, 1, 2)


def test_main_process_exhaustive():
    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    loc_id_obj = loc_id.Location_Finder(strategy="exhaustive",
                                        similarity="edit_weighted")
    lic = prep.License.from_filepath(lcs_file)
    src = prep.Source.from_filepath(input_file)
    loc_result = loc_id_obj.main_process(lic, src)
    assert loc_result == (1, 2, 5, 24, 1.0, 1, 2)

    loc_id_obj = loc_id.Location_Finder(context_lines=1)
    loc_result = loc_id_obj.main_process(lic, src)
    assert loc_result == (0, 3, 0, 29, 1.0, 1, 2)


def test_main_process_full_text_only():
    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    loc_id_obj = loc_id.Location_Finder(strategy="full_text_only",
                                        similarity="edit_weighted")
    lic = prep.License.from_filepath(lcs_file)
    src = prep.Source.from_filepath(input_file)
    loc_result = loc_id_obj.main_process(lic, src)
    assert loc_result == (0, 5, 0, 38, 0.5, 0, 5)


def test_one_line_then_expand():
    loc_id_obj = loc_id.Location_Finder(
        similarity="edit_weighted",
        overshoot=5,
        penalty_only_source=2.0,
        penalty_only_license=3.0)
    lic = prep.License.from_lines(["a b c", "d e f"])
    src = prep.Source.from_lines(
        ["x", "x", "a", "x", "x", "", "b y", "d e", "x", "f", "x", "x"])
    result = loc_id_obj.one_line_then_expand(lic, src)
    expected_score = 5.0 / (5.0 + 2.0 * 4 + 3.0 * 1)
    assert result == (2, 10, expected_score)

    # Test without any overshoot
    loc_id_obj = loc_id.Location_Finder(
        similarity="edit_weighted",
        overshoot=0,
        penalty_only_source=2.0,
        penalty_only_license=3.0)
    result = loc_id_obj.one_line_then_expand(lic, src)
    expected_score = 3.0 / (3.0 + 2.0 * 1 + 3.0 * 3)
    assert result == (5, 8, expected_score)

    # Test case where this heuristic fails to find the global optimum
    loc_id_obj = loc_id.Location_Finder(
        similarity="edit_weighted",
        overshoot=5,
        penalty_only_source=2.0,
        penalty_only_license=3.0)
    src = prep.Source.from_lines(
        ["x", "x", "b c d e", "x", "x", "a b", "c d", "e f", "x", "x"])
    result = loc_id_obj.one_line_then_expand(lic, src)
    expected_score = 4.0 / (4.0 + 3.0 * 2)
    assert result == (2, 3, expected_score)


def test_one_line_then_expand_edge_cases():
    loc_id_obj = loc_id.Location_Finder(
        similarity="edit_weighted",
        overshoot=5,
        penalty_only_source=2.0,
        penalty_only_license=3.0)
    lic = prep.License.from_lines(["a b c", "d e f"])

    # License appears on last 2 lines
    src = prep.Source.from_lines(["x", "x", "a b", "c d e f"])
    result = loc_id_obj.one_line_then_expand(lic, src)
    assert result == (2, 4, 1.0)

    # License appears on last line
    src = prep.Source.from_lines(["x", "x", "a b c d e f"])
    result = loc_id_obj.one_line_then_expand(lic, src)
    assert result == (2, 3, 1.0)

    # License appears on first 2 lines
    src = prep.Source.from_lines(["a b c d", "e f", "x", "x"])
    result = loc_id_obj.one_line_then_expand(lic, src)
    assert result == (0, 2, 1.0)

    # License appears on first line
    src = prep.Source.from_lines(["a b c d e f", "x", "x"])
    result = loc_id_obj.one_line_then_expand(lic, src)
    assert result == (0, 1, 1.0)

    # License appears on first (and only) line
    src = prep.Source.from_lines(["a b c d e f"])
    result = loc_id_obj.one_line_then_expand(lic, src)
    assert result == (0, 1, 1.0)

    # License spans entire file
    src = prep.Source.from_lines(["a b", "c d", "e f"])
    result = loc_id_obj.one_line_then_expand(lic, src)
    assert result == (0, 3, 1.0)


def test_exhaustive():
    loc_id_obj = loc_id.Location_Finder(
        similarity="edit_weighted",
        overshoot=5,
        penalty_only_source=2.0,
        penalty_only_license=3.0)
    lic = prep.License.from_lines(["a b c", "d e f"])
    src = prep.Source.from_lines(
        ["x", "x", "b c d e", "x", "x",
            "a b", "c d", "e f", "x", "x"])
    result = loc_id_obj.best_region_exhaustive(lic, src)
    assert result == (5, 8, 1.0)


def test_determine_offsets():
    src_lines = ["", "", "", "", ""]
    src_offsets = [0, 10, 20, 30, 40, 50]

    loc_id_obj = loc_id.Location_Finder(0)
    assert loc_id_obj.\
        determine_offsets(0, 2, src_lines, src_offsets) == (0, 2, 0, 20)
    assert loc_id_obj.\
        determine_offsets(2, 3, src_lines, src_offsets) == (2, 3, 20, 30)
    assert loc_id_obj.\
        determine_offsets(3, 5, src_lines, src_offsets) == (3, 5, 30, 50)
    assert loc_id_obj.\
        determine_offsets(4, 5, src_lines, src_offsets) == (4, 5, 40, 50)

    loc_id_obj = loc_id.Location_Finder(1)
    assert loc_id_obj.\
        determine_offsets(0, 2, src_lines, src_offsets) == (0, 3, 0, 30)
    assert loc_id_obj.\
        determine_offsets(2, 3, src_lines, src_offsets) == (1, 4, 10, 40)
    assert loc_id_obj.\
        determine_offsets(3, 5, src_lines, src_offsets) == (2, 5, 20, 50)
    assert loc_id_obj.\
        determine_offsets(4, 5, src_lines, src_offsets) == (3, 5, 30, 50)


@patch("sys.stdout", new_callable=StringIO)
def test_top_level_main(mock_stdout):
    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    loc_id.main([lcs_file, input_file])
    expected_output = \
        "LocationResult(start_line=1, end_line=2, start_offset=5, " + \
        "end_offset=24, score=1.0, start_line_orig=1, end_line_orig=2)\n"
    assert mock_stdout.getvalue() == expected_output


@patch.object(prep.LicenseLibrary, "deserialize")
@patch("sys.stdout", new_callable=StringIO)
def test_top_level_main_pickled_license_library(mock_stdout, mock_deserialize):
    pickle_file = join(BASE_DIR, "test.pickle")
    mock_deserialize.return_value = prep.LicenseLibrary(licenses=dict(),
                                                        universe_n_grams=None)

    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')

    loc_id.main([lcs_file, input_file, "-P", pickle_file])

    expected_output = \
        "LocationResult(start_line=1, end_line=2, start_offset=5, " + \
        "end_offset=24, score=1.0, start_line_orig=1, end_line_orig=2)\n"
    assert mock_stdout.getvalue() == expected_output
    assert mock_deserialize.call_count == 1
    assert abspath(mock_deserialize.call_args[0][0]) == abspath(pickle_file)


def mklic(lines):
    return prep.License.from_lines(lines)


def mksrc(lines):
    return prep.Source.from_lines(lines)
