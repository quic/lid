import csv
import random
import string
from collections import Counter
from os.path import abspath, dirname, join

import six
from StringIO import StringIO
from mock import Mock, mock_open, patch

from . import license_identifier
from . import license_match as l_match
from . import location_identifier
from . import match_summary
from . import n_grams as ng
from . import prep


text_list = ['one', 'two', 'three', 'four']
text_line = 'one\ntwo\nthree\nfour'
text_line_crlf = 'one\r\ntwo\r\nthree\r\nfour'

unigram_counter = Counter(['one', 'two', 'three', 'four'])
bigram_counter = Counter([('two', 'one'),
                          ('three', 'two'),
                          ('four', 'three')])
trigram_counter = Counter([('three', 'two', 'one'),
                           ('four', 'three', 'two')])
n_gram_obj = ng.n_grams(text_list)
curr_dir = dirname(__file__)
BASE_DIR = join(curr_dir, "..")
license_dir = join(BASE_DIR, 'data', 'test', 'license')
input_dir = join(BASE_DIR, 'data', 'test', 'data')

threshold = 0.888
output_path = 'test_path'

lcs_id_obj = license_identifier.LicenseIdentifier(
    license_dir=license_dir,
    threshold=threshold,
    input_path=input_dir,
    run_in_parallel=False
)
lcs_id_obj_context = license_identifier.LicenseIdentifier(
    license_dir=license_dir,
    threshold=threshold,
    input_path=input_dir,
    context_length=1,
    run_in_parallel=False
)
lcs_id_obj_origmatched = license_identifier.LicenseIdentifier(
    license_dir=license_dir,
    threshold=threshold,
    input_path=input_dir,
    run_in_parallel=False,
    original_matched_text_flag=True
)
lcs_id_obj_context_origmatched = license_identifier.LicenseIdentifier(
    license_dir=license_dir,
    threshold=threshold,
    input_path=input_dir,
    context_length=5,
    run_in_parallel=False,
    original_matched_text_flag=True
)

result_dict = lcs_id_obj.analyze_input_path(input_path=input_dir)
l_match_obj = l_match.LicenseMatch(file_name='f_name',
                                   file_path='some_path',
                                   license='test_license',
                                   start_byte=0,
                                   length=10)
field_names = ['input file name',
               "matched license type",
               "Score using whole input test",
               "Start line number",
               "End line number",
               "Start byte offset",
               "End byte offset",
               "Score using only the license text portion",
               "Found license text"]


def test_init():
    assert 'test_license' in lcs_id_obj._license_library.licenses.keys()
    assert lcs_id_obj.\
        _license_library.universe_n_grams.measure_similarity(n_gram_obj) > 0.5


@patch('pickle.dump')
@patch('pickle.load')
def test_init_pickle(mock_pickle_load, mock_pickle_dump):
    test_pickle_file = join(BASE_DIR, 'test.pickle')
    lcs_id_obj._create_pickled_library(pickle_file=test_pickle_file)

    assert mock_pickle_dump.call_count == 1
    dump_args = mock_pickle_dump.call_args[0]
    assert abspath(dump_args[1].name) == abspath(test_pickle_file)

    # Mock version of pickle.load will produce previous inputs to pickle.dump
    # without touching the filesystem
    mock_pickle_load.return_value = dump_args[0]

    lcs_id_pickle_obj = license_identifier.LicenseIdentifier(
        threshold=threshold,
        input_path=input_dir,
        pickle_file_path=test_pickle_file)

    assert mock_pickle_load.call_count == 1
    assert abspath(mock_pickle_load.call_args[0][0].name) == \
        abspath(test_pickle_file)

    universe_ng = lcs_id_pickle_obj._get_license_library().universe_n_grams
    assert universe_ng.measure_similarity(universe_ng) == 1.0


def test_write_csv_file():
    lid = license_identifier.LicenseIdentifier(license_dir=license_dir,
                                               threshold=threshold,
                                               input_path=input_dir)

    result_dict = lid.analyze_input_path(input_path=input_dir)

    mock_open_name = '{}.open'.format(six.moves.builtins.__name__)
    with patch(mock_open_name, mock_open()):
        with patch('csv.writer', Mock(spec=csv.writer)) as m:
            license_identifier._output_results(result_dict, 'csv', output_path,
                                               False)
            handle = m()
            handle.writerow.assert_any_call(field_names)

            m.reset_mock()
            license_identifier._write_csv_file(result_dict, output_path, False)
            handle = m()
            handle.writerow.assert_any_call(field_names)

            m.reset_mock()
            result_obj_dict = license_identifier.match_summary.MatchSummary(
                input_fp='data/test/data/test1.py',
                matched_license='test_license',
                score='1.0',
                start_line_ind='0',
                end_line_ind='5',
                start_offset='0',
                end_offset='40',
                region_score='1.0',
                found_region='+zero\none two three four\n')
            result_dict = \
                {'data/test/data/test1.py': [(None, result_obj_dict)]}
            expected_res_string = ['data/test/data/test1.py', 'test_license',
                                   '1.0', '0', '5', '0', '40', '1.0',
                                   " +zero\none two three four\n"]
            license_identifier._write_csv_file(result_dict, output_path, False)
            handle = m()
            handle.writerow.assert_any_call(expected_res_string)


def test_init_using_license_library_object():
    # Make sure that two instances of LID can have license libraries
    # that don't interfere with each other
    path1 = join(BASE_DIR, 'data', 'test', 'near_tie', 'license')
    lid1 = license_identifier.LicenseIdentifier(
        license_library=prep.LicenseLibrary.from_path(path1))

    path2 = join(BASE_DIR, 'data', 'test', 'license')
    lid2 = license_identifier.LicenseIdentifier(
        license_library=prep.LicenseLibrary.from_path(path2))

    assert lid1._license_library.licenses.keys() == ['license1', 'license2']
    assert lid2._license_library.licenses.keys() == ['test_license',
                                                     'custom_license']


@patch('sys.stdout', new_callable=StringIO)
def test_build_summary_list_str(mock_stdout):
    license_identifier._display_easy_read(result_dict)
    assert mock_stdout.getvalue().find('Summary of the analysis') >= 0


def test_forward_args_to_loc_id():
    test_file_path = join(input_dir, 'test1.py')
    lid = license_identifier.LicenseIdentifier(
        license_dir=license_dir,
        context_length=0,
        location_strategy='exhaustive',
        location_similarity='ngram',
        penalty_only_license=3.0,
        penalty_only_source=4.0
    )
    with patch.object(location_identifier, 'Location_Finder',
                      wraps=location_identifier.Location_Finder) as m:
        lid.analyze_file(test_file_path)
        m.assert_called_with(
            context_lines=0,
            strategy='exhaustive',
            similarity='ngram',
            penalty_only_license=3.0,
            penalty_only_source=4.0
        )


def test_analyze_file_lcs_match_output():
    test_file_path = join(input_dir, 'test1.py')
    result = lcs_id_obj.analyze_file_lcs_match_output(test_file_path)
    assert len(result) == 1
    assert result[0].length == 20

    test_file_path = join(input_dir, 'subdir', 'subdir2', 'test3.py')
    result = lcs_id_obj.analyze_file_lcs_match_output(test_file_path)
    assert len(result) == 0


def test_analyze_input_path_lcs_match_output():
    test_file_path = join(input_dir, 'test1.py')
    result = lcs_id_obj.analyze_input_path_lcs_match_output(test_file_path)
    assert len(result) == 1
    assert len(result[test_file_path]) == 1
    assert result[test_file_path][0].length == 20

    result = lcs_id_obj.analyze_input_path_lcs_match_output(input_dir)
    assert len(result) == 6
    files = [
        join(input_dir, "test0.py"),
        join(input_dir, "test1.py"),
        join(input_dir, "subdir", "test2.py"),
        join(input_dir, "subdir", "subdir2", "test3.py"),
        join(input_dir, "subdir", "subdir2", "test4.bogus"),
        join(input_dir, "subdir", "subdir2", "test5.py"),
    ]
    for f in files:
        assert f in result
    assert result[files[0]][0].file_name.endswith("test0.py")
    assert result[files[0]][0].length == 19
    assert result[files[1]][0].file_name.endswith("test1.py")
    assert result[files[1]][0].length == 20
    assert len(result[files[2]]) == 0
    assert len(result[files[3]]) == 0
    assert result[files[4]][0].file_name.endswith("test4.bogus")
    assert result[files[4]][0].length == 20
    assert len(result[files[5]]) == 0


def test_analyze_file():
    fp = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    result = lcs_id_obj.analyze_file(filepath=fp)
    assert len(result) == 1
    lcs_match, summary_obj = result[0]
    assert summary_obj["matched_license"] == 'test_license'
    assert summary_obj["score"] == 1.0
    assert summary_obj["found_region"] == "one two three four\r\n"

    result = lcs_id_obj_origmatched.analyze_file(filepath=fp)
    assert len(result) == 1
    lcs_match, summary_obj = result[0]
    assert summary_obj["original_region"] == "one two three four\r\n"

    result = lcs_id_obj_context.analyze_file(filepath=fp)
    assert len(result) == 1
    lcs_match, summary_obj = result[0]
    assert summary_obj["found_region"] == \
        "zero\r\none two three four\r\nfive\r\n"

    result = lcs_id_obj_context_origmatched.analyze_file(filepath=fp)
    assert len(result) == 1
    lcs_match, summary_obj = result[0]
    assert summary_obj["found_region"] == \
        "zero\r\none two three four\r\nfive\r\nsix\r\nseven\r\n"
    assert summary_obj["original_region"] == "one two three four\r\n"


def test_analyze_file_source():
    src = prep.Source.from_lines(["a", "one two three four", "b"])
    result = lcs_id_obj.analyze_source(src)
    assert len(result) == 1

    lcs_match, summary_obj = result[0]
    assert summary_obj["matched_license"] == 'test_license'
    assert summary_obj["score"] == 1.0
    assert summary_obj["found_region"] == "one two three four\r\n"


def test_analyze_input_path():
    fp = join(BASE_DIR, 'data', 'test', 'data')
    result = lcs_id_obj.analyze_input_path(input_path=fp)
    assert len(result) == 6
    files = [
        join(input_dir, "test0.py"),
        join(input_dir, "test1.py"),
        join(input_dir, "subdir", "test2.py"),
        join(input_dir, "subdir", "subdir2", "test3.py"),
        join(input_dir, "subdir", "subdir2", "test4.bogus"),
        join(input_dir, "subdir", "subdir2", "test5.py"),
    ]
    for f in files:
        assert f in result
    assert result[files[0]][0][1]["input_fp"].endswith('test0.py')
    assert result[files[0]][0][1]["matched_license"] == 'custom_license'
    assert result[files[1]][0][1]["input_fp"].endswith('test1.py')
    assert result[files[1]][0][1]["matched_license"] == 'test_license'
    assert len(result[files[2]]) == 0
    assert len(result[files[3]]) == 0
    assert result[files[4]][0][1]["input_fp"].endswith('test4.bogus')
    assert result[files[4]][0][1]["matched_license"] == 'test_license'
    assert len(result[files[5]]) == 0


def test_find_license_region():
    lic = lcs_id_obj._get_license_library().licenses['test_license']
    src_fp = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    src = prep.Source.from_filepath(src_fp)
    test1_loc_result = lcs_id_obj.find_license_region(lic, src)
    assert test1_loc_result == (1, 2, 5, 24, 1.0, 1, 2)
    test1_loc_result = lcs_id_obj_context.find_license_region(lic, src)
    assert test1_loc_result == (0, 3, 0, 29, 1.0, 1, 2)


def test_postprocess_comments():
    fp = join(BASE_DIR, 'data', 'test', 'data', 'subdir', 'subdir2',
              'test4.bogus')
    result_dict = lcs_id_obj.analyze_input_path(input_path=fp)
    postprocess_dict = lcs_id_obj.postprocess_strip_off_code(result_dict)
    assert postprocess_dict[fp][0][1]["stripped_region"] == \
        'one two three four\r\n'

    result_dict[fp][0][1]["score"] = 0
    postprocess_dict = lcs_id_obj.postprocess_strip_off_code(result_dict)
    assert postprocess_dict[fp][0][1]["stripped_region"] == ''

    lcs_id_low_threshold = license_identifier.LicenseIdentifier(
        license_dir=license_dir,
        threshold=0.001)
    fp = join(BASE_DIR, 'data', 'test', 'data', 'subdir', 'subdir2',
              'test5.py')
    result_dict = lcs_id_low_threshold.analyze_input_path(input_path=fp)
    postprocess_dict = \
        lcs_id_low_threshold.postprocess_strip_off_code(result_dict)
    stripped_region_lines = \
        postprocess_dict[fp][0][1]["stripped_region"].splitlines()
    expected_lines = ['# one', '', '# two three', '', '# four']
    assert [line.strip() for line in stripped_region_lines] == expected_lines


def test_truncate_column():
    data = ''.join(random.choice(string.lowercase) for x in range(40000))
    assert len(match_summary.truncate_column(data)) == \
        match_summary.COLUMN_LIMIT
    assert match_summary.truncate_column(3.0) == 3.0


def test_main():
    arg_string = "-I {} -L {}".format(input_dir, license_dir)
    license_identifier.main(arg_string.split())


@patch('pickle.dump')
def test_main_process_pickle(mock_pickle_dump):
    test_pickle_file = join(BASE_DIR, "test.pickle")
    license_identifier.LicenseIdentifier(
        license_dir=license_dir,
        pickle_file_path=test_pickle_file)

    assert mock_pickle_dump.call_count == 1
    dump_args = mock_pickle_dump.call_args[0]
    assert abspath(dump_args[1].name) == abspath(test_pickle_file)


@patch.object(prep.LicenseLibrary, 'deserialize')
def test_default_pickle_path(mock_deserialize):
    mock_deserialize.return_value = prep.LicenseLibrary(
        licenses=dict(),
        universe_n_grams=n_gram_obj)

    license_identifier.LicenseIdentifier().analyze()

    assert mock_deserialize.call_count == 1
    assert abspath(mock_deserialize.call_args[0][0]) == \
        abspath(license_identifier.DEFAULT_PICKLED_LIBRARY_FILE)


def test_analyze_file_multiple_licenses():
    lib = prep.LicenseLibrary.from_licenses([
        prep.License.from_lines(["a b c d"], name="L0"),
        prep.License.from_lines(["e f g h"], name="L1"),
        prep.License.from_lines(["i j k l"], name="L2"),
    ])

    lid = license_identifier.LicenseIdentifier(
        license_library=lib,
        threshold=0.001,
        location_similarity="edit_weighted",
        run_in_parallel=False)

    src = prep.Source.from_lines(
        ["x", "a b", "c d", "y", "e f", "g h", "z", "i j", "k l", "w"])
    result = lid.analyze_source(src)
    assert len(result) == 3

    assert result[0][1]["matched_license"] == 'L0'
    assert result[0][1]["found_region"].splitlines() == ['a b', 'c d']
    assert result[0][1]["start_line_ind"] == 1
    assert result[0][1]["end_line_ind"] == 3

    assert result[1][1]["matched_license"] == 'L1'
    assert result[1][1]["found_region"].splitlines() == ['e f', 'g h']
    assert result[1][1]["start_line_ind"] == 4
    assert result[1][1]["end_line_ind"] == 6

    assert result[2][1]["matched_license"] == 'L2'
    assert result[2][1]["found_region"].splitlines() == ['i j', 'k l']
    assert result[2][1]["start_line_ind"] == 7
    assert result[2][1]["end_line_ind"] == 9

    src = prep.Source.from_lines(
        ["a b", "c d", "e f", "g h", "i j", "k l"])
    result = lid.analyze_source(src)
    assert len(result) == 3

    assert result[0][1]["matched_license"] == 'L0'
    assert result[0][1]["found_region"].splitlines() == ['a b', 'c d']
    assert result[0][1]["start_line_ind"] == 0
    assert result[0][1]["end_line_ind"] == 2

    assert result[1][1]["matched_license"] == 'L1'
    assert result[1][1]["found_region"].splitlines() == ['e f', 'g h']
    assert result[1][1]["start_line_ind"] == 2
    assert result[1][1]["end_line_ind"] == 4

    assert result[2][1]["matched_license"] == 'L2'
    assert result[2][1]["found_region"].splitlines() == ['i j', 'k l']
    assert result[2][1]["start_line_ind"] == 4
    assert result[2][1]["end_line_ind"] == 6


def test_analyze_file_near_ties():
    fp = join(BASE_DIR, 'data', 'test', 'near_tie', 'data', 'source')
    near_tie_license_dir = join(BASE_DIR, 'data', 'test', 'near_tie',
                                'license')

    lid = license_identifier.LicenseIdentifier(
        license_dir=near_tie_license_dir,
        threshold=0.1,
        input_path=fp,
        location_similarity="edit_weighted",
        keep_fraction_of_best=0.5,
        run_in_parallel=False)

    src = prep.Source.from_filepath(fp)
    top_candidates = lid.get_top_candidates(src)
    results = lid.analyze_file(filepath=fp)

    # Assert that license1 has a higher initial (ngram) score, but license2
    # ends up being selected as the best region match based on edit distance.
    assert set(top_candidates.keys()) == set(['license1', 'license2'])
    assert top_candidates['license1'] > top_candidates['license2']
    assert len(results) == 1
    assert results[0][0].license == 'license2'
