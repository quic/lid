from . import n_grams as ng
from . import license_identifier
from . import license_match as l_match
from . import match_summary
from . import location_result as lr
from . import location_identifier
from . import prep
from collections import Counter
from os import getcwd
from os.path import join, dirname, exists, abspath
from mock import mock_open
from mock import patch, Mock
import csv
import random
import string
import six

import pytest
from StringIO import StringIO


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

threshold=0.888
output_path = 'test_path'

lcs_id_obj = license_identifier.LicenseIdentifier(license_dir=license_dir,
                                          threshold=threshold,
                                          input_path=input_dir,
                                          output_format='easy_read',
                                          run_in_parellal=False)
lcs_id_obj_context = license_identifier.LicenseIdentifier(license_dir=license_dir,
                                          threshold=threshold,
                                          input_path=input_dir,
                                          output_format='easy_read',
                                          context_length=1,
                                          run_in_parellal=False)
result_obj = lcs_id_obj.analyze_input_path(input_path=input_dir)
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
    assert 'test_license' in license_identifier._license_library.licenses.keys()
    assert license_identifier._license_library.universe_n_grams.measure_similarity(n_gram_obj) > 0.5

@patch('pickle.dump')
@patch('pickle.load')
def test_init_pickle(mock_pickle_load, mock_pickle_dump):
    test_pickle_file = join(BASE_DIR, "test.pickle")
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
        pickle_file_path=test_pickle_file,
        output_format='easy_read')

    assert mock_pickle_load.call_count == 1
    assert abspath(mock_pickle_load.call_args[0][0].name) \
        == abspath(test_pickle_file)

    universe_ng = license_identifier._license_library.universe_n_grams
    assert universe_ng.measure_similarity(universe_ng) == 1.0

def test_write_csv_file():
    lid_obj = license_identifier.LicenseIdentifier(license_dir=license_dir,
                                          threshold=threshold,
                                          input_path=input_dir,
                                          output_format='csv',
                                          output_path=output_path)

    result_obj = lid_obj.analyze_input_path(input_path=input_dir)

    mock_open_name = '{}.open'.format(six.moves.builtins.__name__)
    with patch(mock_open_name, mock_open()) as mo:
        with patch('csv.writer', Mock(spec=csv.writer)) as m:
            lid_obj.output(result_obj)
            handle = m()
            handle.writerow.assert_any_call(field_names)

            m.reset_mock()
            lid_obj.write_csv_file(result_obj, output_path)
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
            result_obj = [[[],result_obj_dict]]
            expected_res_string = ['data/test/data/test1.py','test_license','1.0','0','5',\
                                   '0','40','1.0'," +zero\none two three four\n"]
            lid_obj.write_csv_file(result_obj, output_path)
            handle = m()
            handle.writerow.assert_any_call(expected_res_string)

@patch('sys.stdout', new_callable=StringIO)
def test_build_summary_list_str(mock_stdout):
    display_str = lcs_id_obj.display_easy_read(result_obj)
    assert mock_stdout.getvalue().find('Summary of the analysis') >= 0

def test_forward_args_to_loc_id():
    test_file_path = join(input_dir, 'test1.py')
    lid_obj = license_identifier.LicenseIdentifier(
        license_dir = license_dir,
        context_length = 0,
        location_strategy = "exhaustive",
        location_similarity = "ngram",
        penalty_only_license = 3.0,
        penalty_only_source = 4.0)
    with patch.object(location_identifier, 'Location_Finder') as m:
        m.return_value.main_process.return_value = lr.LocationResult(0, 0, 0, 0, 0)
        lcs_match_obj = lid_obj.analyze_file(test_file_path)
        m.assert_called_with(
            context_lines = 0,
            strategy = "exhaustive",
            similarity = "ngram",
            penalty_only_license = 3.0,
            penalty_only_source = 4.0)

def test_analyze_file_lcs_match_output():
    test_file_path = join(input_dir, 'test1.py')
    lcs_match_obj = lcs_id_obj.analyze_file_lcs_match_output(test_file_path)
    assert lcs_match_obj.length == 20

    lcs_match_obj = lcs_id_obj.analyze_input_path_lcs_match_output(test_file_path)
    assert len(lcs_match_obj) == 1
    assert lcs_match_obj[0].length == 20

    lcs_match_obj = lcs_id_obj.analyze_input_path_lcs_match_output(input_dir)
    assert len(lcs_match_obj) == 6
    assert lcs_match_obj[0].length == 19
    assert lcs_match_obj[1].length == 20
    assert lcs_match_obj[2].length == ''
    assert lcs_match_obj[3].length == ''
    assert lcs_match_obj[4].length == 20
    assert lcs_match_obj[5].length == ''

    test_file_path2 = join(input_dir, 'subdir', 'subdir2', 'test3.py')
    lcs_match_obj2 = lcs_id_obj.analyze_file_lcs_match_output(test_file_path2)
    assert lcs_match_obj2.license == ''

def test_analyze_file():
    fp = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    lcs_match, summary_obj = lcs_id_obj.analyze_file(input_fp=fp)
    assert summary_obj["matched_license"] == 'test_license'
    assert summary_obj["score"] == 1.0
    assert summary_obj["found_region"] == "one two three four\n"            

def test_analyze_input_path():
    fp = join(BASE_DIR, 'data', 'test', 'data')
    list_of_result_obj = lcs_id_obj.analyze_input_path(input_path=fp)
    assert len(list_of_result_obj) == 6
    assert list_of_result_obj[0][1]["matched_license"] == 'custom_license'
    assert list_of_result_obj[1][1]["matched_license"] == 'test_license'
    assert list_of_result_obj[2][1]["matched_license"] == ''
    assert list_of_result_obj[3][1]["matched_license"] == ''
    assert list_of_result_obj[4][1]["matched_license"] == 'test_license'
    assert list_of_result_obj[5][1]["matched_license"] == ''

def test_find_license_region():
    lic = license_identifier._license_library.licenses['test_license']
    src_fp = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    src = prep.Source.from_filename(src_fp)
    test1_loc_result = lcs_id_obj.find_license_region(lic, src)
    assert test1_loc_result == (1, 2, 5, 24, 1.0)
    test1_loc_result = lcs_id_obj_context.find_license_region(lic, src)
    assert test1_loc_result == (0, 3, 0, 29, 1.0)

def test_postprocess_comments():
    fp = join(BASE_DIR, 'data', 'test', 'data', 'subdir', 'subdir2', 'test4.bogus')
    result_obj = lcs_id_obj.analyze_input_path(input_path=fp)
    start_ind = result_obj[0][1]["start_line_ind"]
    end_ind = result_obj[0][1]["end_line_ind"]
    list_of_src_str = lcs_id_obj.get_str_from_file(fp)
    postprocess_obj = lcs_id_obj.postprocess_strip_off_comments(result_obj)
    assert postprocess_obj[0][1]["stripped_region"] == ''.join(list_of_src_str[start_ind:end_ind])
    result_obj[0][1]["score"] = 0
    postprocess_obj = lcs_id_obj.postprocess_strip_off_comments(result_obj)
    assert postprocess_obj[0][1]["stripped_region"] == ''

    lcs_id_low_threshold = license_identifier.LicenseIdentifier(
        license_dir = license_dir,
        threshold = 0.001)
    fp = join(BASE_DIR, 'data', 'test', 'data', 'subdir', 'subdir2', 'test5.py')
    result_obj = lcs_id_low_threshold.analyze_input_path(input_path=fp)
    postprocess_obj = lcs_id_low_threshold.postprocess_strip_off_comments(result_obj)
    stripped_region_lines = postprocess_obj[0][1]["stripped_region"].splitlines()
    expected_lines = ['# one', '', '# two three', '', '# four']
    assert [line.strip() for line in stripped_region_lines] == expected_lines

def test_get_str_from_file():
    fp = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    list_of_str = lcs_id_obj.get_str_from_file(fp)
    assert list_of_str == ['zero\n', 'one two three four\n', 'five\n', 'six\n', 'seven']
    fp = "what"
    with pytest.raises(IOError):
        lcs_id_obj.get_str_from_file(fp)

def test_truncate_column():
    data = ''.join(random.choice(string.lowercase) for x in range(40000))
    assert len(match_summary.truncate_column(data)) == match_summary.COLUMN_LIMIT
    assert match_summary.truncate_column(3.0) == 3.0

def test_main():
    arg_string = "-I {} -L {}".format(input_dir, license_dir)
    license_identifier.main(arg_string.split())

@patch('pickle.dump')
def test_main_process_pickle(mock_pickle_dump):
    test_pickle_file = join(BASE_DIR, "test.pickle")
    license_identifier.LicenseIdentifier(
        license_dir = license_dir,
        pickle_file_path = test_pickle_file)

    assert mock_pickle_dump.call_count == 1
    dump_args = mock_pickle_dump.call_args[0]
    assert abspath(dump_args[1].name) == abspath(test_pickle_file)

@patch.object(prep.LicenseLibrary, 'deserialize')
def test_default_pickle_path(mock_deserialize):
    mock_deserialize.return_value = prep.LicenseLibrary(
        licenses = dict(),
        universe_n_grams = n_gram_obj)
    lic_obj = license_identifier.LicenseIdentifier()
    result = lic_obj.analyze()
    lic_obj.output(result)
    assert mock_deserialize.call_count == 1
    assert abspath(mock_deserialize.call_args[0][0]) \
        == abspath(license_identifier.DEFAULT_PICKLED_LIBRARY_FILE)

def test_analyze_file_near_ties():
    # Note: as long as license_identifier uses a global _license_library
    # as a multiprocessing workaround, this test should come after any other
    # uses of lcs_id_obj.
    fp = join(BASE_DIR, 'data', 'test', 'near_tie', 'data', 'source')
    near_tie_license_dir = join(BASE_DIR, 'data', 'test', 'near_tie', 'license')

    lid_obj = license_identifier.LicenseIdentifier(
        license_dir = near_tie_license_dir,
        threshold = 0.1,
        input_path = fp,
        location_similarity = "edit_weighted",
        keep_fraction_of_best = 0.5,
        run_in_parellal = False)

    src = prep.Source.from_filename(fp)
    top_candidates = lid_obj.get_top_candidates(src)
    lcs_match, summary_obj = lid_obj.analyze_file(input_fp=fp)

    assert set(top_candidates.keys()) == set(['license1', 'license2'])
    assert top_candidates['license1'] > top_candidates['license2']
    assert lcs_match.license == 'license2'
