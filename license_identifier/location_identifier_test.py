from . import license_identifier as lcs_id
from . import location_identifier as loc_id
from . import util
from . import prep
from . import scores

from collections import Counter
from os import getcwd
from os.path import join, abspath
from StringIO import StringIO
from mock import patch, mock_open
import six


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
    lic = prep.License.from_filename(lcs_file)
    src = prep.Source.from_filename(input_file)
    loc_result = loc_id_obj.main_process(lic, src)
    assert loc_result==(1, 2, 5, 24, 1.0)

    loc_id_obj = loc_id.Location_Finder(context_lines = 1)
    loc_result = loc_id_obj.main_process(lic, src)
    assert loc_result==(0, 3, 0, 29, 1.0)

def test_main_process_ngram():
    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    loc_id_obj = loc_id.Location_Finder(strategy = "window_then_expand", similarity = "ngram")
    lic = prep.License.from_filename(lcs_file)
    src = prep.Source.from_filename(input_file)
    loc_result = loc_id_obj.main_process(lic, src)
    assert loc_result==(1, 2, 5, 24, 1.0)

    loc_id_obj = loc_id.Location_Finder(context_lines = 1)
    loc_result = loc_id_obj.main_process(lic, src)
    assert loc_result==(0, 3, 0, 29, 1.0)

def test_main_process_exhaustive():
    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    loc_id_obj = loc_id.Location_Finder(strategy = "exhaustive", similarity = "edit_weighted")
    lic = prep.License.from_filename(lcs_file)
    src = prep.Source.from_filename(input_file)
    loc_result = loc_id_obj.main_process(lic, src)
    assert loc_result==(1, 2, 5, 24, 1.0)

    loc_id_obj = loc_id.Location_Finder(context_lines = 1)
    loc_result = loc_id_obj.main_process(lic, src)
    assert loc_result==(0, 3, 0, 29, 1.0)

def test_find_best_window_expansion():
    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    loc_id_obj = loc_id.Location_Finder()

    lic = prep.License.from_filename(lcs_file)
    src = prep.Source.from_filename(input_file)

    [similarity_scores, window_start_index] = \
        loc_id_obj.split_and_measure_similarities(lic = lic, src = src)
    [max_score, max_index] = loc_id_obj.find_max_score_ind(similarity_scores=similarity_scores)

    loc_result = loc_id_obj.find_best_window_expansion(
        max_index = max_index,
        lic = lic,
        src = src,
        window_start_index = window_start_index)
    assert loc_result == (1, 2, 1.0)

def test_find_max_score_ind():
    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    loc_id_obj = loc_id.Location_Finder()

    lic = prep.License.from_filename(lcs_file)
    src = prep.Source.from_filename(input_file)

    [similarity_scores, window_start_index] = \
        loc_id_obj.split_and_measure_similarities(lic = lic, src = src)
    [max_score, max_index] = loc_id_obj.find_max_score_ind(similarity_scores=similarity_scores)
    assert max_score == 1.0
    assert max_index[0] == 1


def test_split_and_measure_similarities():
    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    loc_id_obj = loc_id.Location_Finder()

    lic = prep.License.from_filename(lcs_file)
    src = prep.Source.from_filename(input_file)

    [similarity_scores, window_start_index] = \
        loc_id_obj.split_and_measure_similarities(lic = lic, src = src)
    assert similarity_scores == [0.0, 1.0, 0.0, 0.0, 0.0]
    assert window_start_index == [0, 1, 2, 3, 4]


def test_expand_window():
    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'subdir', 'subdir2', 'test3.py')
    loc_id_obj = loc_id.Location_Finder()

    lic = prep.License.from_filename(lcs_file)
    src = prep.Source.from_filename(input_file)

    [similarity_scores, window_start_index] = \
        loc_id_obj.split_and_measure_similarities(lic = lic, src = src)
    [max_score, max_index] = loc_id_obj.find_max_score_ind(similarity_scores=similarity_scores)

    # for maximum scores that share the same value
    final_score = []
    start_index = []
    end_index =[]

    for max_ind in max_index:
        [s_ind, e_ind, final_s] = loc_id_obj.expand_window(
            lic = lic, src = src, start_ind = window_start_index[max_ind])
        start_index.append(s_ind)
        end_index.append(e_ind)
        final_score.append(final_s)
    max_score = max(final_score)
    max_index = [i for i, j in enumerate(final_score) if j == max_score]
    first_max_ind = max_index[0]
    assert start_index == [0, 1, 2]
    assert end_index == [1, 2, 3]
    assert s_ind == 2
    assert e_ind == 3
    assert final_s == 0.0
    assert max_score == 0.0


def test_expand_to_top():
    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'subdir', 'subdir2', 'test3.py')
    loc_id_obj = loc_id.Location_Finder()

    lic = prep.License.from_filename(lcs_file)
    src = prep.Source.from_filename(input_file)

    [similarity_scores, window_start_index] = \
        loc_id_obj.split_and_measure_similarities(lic = lic, src = src)
    [max_score, max_index] = loc_id_obj.find_max_score_ind(similarity_scores=similarity_scores)

    # for maximum scores that share the same value
    final_score = []
    start_index = []
    end_index =[]


def test_one_line_then_expand():
    loc_id_obj = loc_id.Location_Finder(
        similarity = "edit_weighted",
        overshoot = 5,
        penalty_only_source = 2.0,
        penalty_only_license = 3.0)
    lic = prep.License.from_lines(["a b c", "d e f"])
    src = prep.Source.from_lines(
        ["x", "x", "a", "x", "x", "b y d e", "x", "f", "x", "x"])
    result = loc_id_obj.one_line_then_expand(lic, src)
    expected_score = 5.0 / (5.0 + 2.0 * 4 + 3.0 * 1)
    assert result == (2, 8, expected_score)

    # Test without any overshoot
    loc_id_obj = loc_id.Location_Finder(
        similarity = "edit_weighted",
        overshoot = 0,
        penalty_only_source = 2.0,
        penalty_only_license = 3.0)
    result = loc_id_obj.one_line_then_expand(lic, src)
    expected_score = 3.0 / (3.0 + 2.0 * 1 + 3.0 * 3)
    assert result == (5, 6, expected_score)

    # Test case where this heuristic fails to find the global optimum
    src = prep.Source.from_lines(
        ["x", "x", "b c d e", "x", "x", "a b", "c d", "e f", "x", "x"])
    result = loc_id_obj.one_line_then_expand(lic, src)
    expected_score = 4.0 / (4.0 + 3.0 * 2)
    assert result == (2, 3, expected_score)


def test_exhaustive():
    loc_id_obj = loc_id.Location_Finder(
        similarity = "edit_weighted",
        overshoot = 5,
        penalty_only_source = 2.0,
        penalty_only_license = 3.0)
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
    assert loc_id_obj.determine_offsets(0, 2, src_lines, src_offsets) == (0, 2, 0, 20)
    assert loc_id_obj.determine_offsets(2, 3, src_lines, src_offsets) == (2, 3, 20, 30)
    assert loc_id_obj.determine_offsets(3, 5, src_lines, src_offsets) == (3, 5, 30, 50)
    assert loc_id_obj.determine_offsets(4, 5, src_lines, src_offsets) == (4, 5, 40, 50)
    loc_id_obj = loc_id.Location_Finder(1)
    assert loc_id_obj.determine_offsets(0, 2, src_lines, src_offsets) == (0, 3, 0, 30)
    assert loc_id_obj.determine_offsets(2, 3, src_lines, src_offsets) == (1, 4, 10, 40)
    assert loc_id_obj.determine_offsets(3, 5, src_lines, src_offsets) == (2, 5, 20, 50)
    assert loc_id_obj.determine_offsets(4, 5, src_lines, src_offsets) == (3, 5, 30, 50)


def test_expand_generic():
    loc_id_obj = loc_id.Location_Finder(similarity = "ngram")
    src = prep.Source.from_lines(["x y", "a b", "c", "d e", "x y"])
    lic = prep.License.from_lines(["a b c d e"])

    result = loc_id_obj.expand_generic(
        lic = lic,
        src = src,
        start_ind = 2,
        end_ind = 3,
        score_to_keep = 0.0,
        start_increment = 1,
        end_increment = 0)
    assert result[:2] == (1, 3)

    result = loc_id_obj.expand_generic(
        lic = lic,
        src = src,
        start_ind = 2,
        end_ind = 3,
        score_to_keep = 0.0,
        start_increment = 0,
        end_increment = 1)
    assert result[:2] == (2, 4)


@patch("sys.stdout", new_callable=StringIO)
def test_top_level_main(mock_stdout):
    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    loc_id.main([lcs_file, input_file])
    expected_output = "LocationResult(start_line=1, end_line=2, start_offset=5, end_offset=24, score=1.0)\n"
    assert mock_stdout.getvalue() == expected_output


@patch("pickle.load")
@patch("sys.stdout", new_callable=StringIO)
def test_top_level_main_pickled_license_library(mock_stdout, mock_pickle_load):
    pickle_file = join(BASE_DIR, "test.pickle")
    mock_pickle_load.return_value = prep.LicenseLibrary(
        licenses = dict(), universe_n_grams = None)

    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')

    loc_id.main([lcs_file, input_file, "-P", pickle_file])

    expected_output = "LocationResult(start_line=1, end_line=2, start_offset=5, end_offset=24, score=1.0)\n"
    assert mock_stdout.getvalue() == expected_output
    assert abspath(mock_pickle_load.call_args[0][0].name) == abspath(pickle_file)


def mklic(lines):
    return prep.License.from_lines(lines)

def mksrc(lines):
    return prep.Source.from_lines(lines)
