#
# Unit Tests to go here
#
from . import n_grams as ng
from . import license_identifier
from . import license_match as l_match
from collections import Counter
from os import getcwd
from os.path import join, dirname, exists
from mock import mock_open
from mock import patch, Mock
import csv
import random
import string

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

threshold='0.888'
output_path = 'test_path'

lcs_id_obj = license_identifier.LicenseIdentifier(license_dir=license_dir,
                                          threshold=threshold,
                                          input_path=input_dir,
                                          output_format='easy_read')
lcs_id_obj_context = license_identifier.LicenseIdentifier(license_dir=license_dir,
                                          threshold=threshold,
                                          input_path=input_dir,
                                          output_format='easy_read',
                                          context_length=1)
result_obj = lcs_id_obj.analyze_input_path(input_path=input_dir,
                                           threshold=threshold)
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
    assert 'test_license.txt' in lcs_id_obj.license_file_name_list
    assert lcs_id_obj._universe_n_grams.measure_similarity(n_gram_obj) > 0.5

def test_init_pickle():
    test_pickle_file = join(BASE_DIR, "test.pickle")
    lcs_id_obj._create_pickled_library(pickle_file=test_pickle_file)
    assert exists(test_pickle_file)==True
    lcs_id_pickle_obj = license_identifier.LicenseIdentifier(
        threshold=threshold,
        input_path=input_dir,
        pickle_file_path=test_pickle_file,
        output_format='easy_read')
    sim_score = lcs_id_obj._universe_n_grams.measure_similarity(lcs_id_pickle_obj._universe_n_grams)
    assert sim_score == 1.0

def test_write_csv_file():
    # def format_output(self, result_obj, output_format, output_path):
    lid_obj = license_identifier.LicenseIdentifier(license_dir=license_dir,
                                          threshold=threshold,
                                          input_path=input_dir,
                                          output_format='csv',
                                          output_path=output_path)

    result_obj = lid_obj.analyze_input_path(input_path=input_dir, threshold=threshold)
    lid_obj.output(result_obj)
    m = Mock(spec=csv.writer)
    with patch('csv.writer', m, create=True):
        lid_obj.write_csv_file(result_obj, output_path)
    handle = m()
    handle.writerow.assert_any_call(field_names)

@patch('sys.stdout', new_callable=StringIO)
def test_build_summary_list_str(mock_stdout):
    display_str = lcs_id_obj.display_easy_read(result_obj)
    assert mock_stdout.getvalue().find('Summary of the analysis') >= 0


def test_analyze_file_lcs_match_output():
    # input_fp, threshold=DEFAULT_THRESH_HOLD
    test_file_path = join(input_dir, 'test1.py')
    lcs_match_obj = lcs_id_obj.analyze_file_lcs_match_output(test_file_path)
    assert lcs_match_obj.length == 20

    test_file_path2 = join(input_dir, 'subdir', 'subdir2', 'test3.py')
    lcs_match_obj2 = lcs_id_obj.analyze_file_lcs_match_output(test_file_path2)
    assert lcs_match_obj2.license == ''

def test_get_license_name():
    assert lcs_id_obj._get_license_name('myname.txt') == 'myname'

def test_analyze_file():
    fp = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    lcs_match, summary_list = lcs_id_obj.analyze_file(input_fp=fp)
    assert summary_list[2] == 1.0

def test_analyze_input_path():
    fp = join(BASE_DIR, 'data', 'test', 'data')
    list_of_result_obj = lcs_id_obj.analyze_input_path(input_path=fp)
    assert list_of_result_obj[0][1][1] == 'test_license'

def test_find_license_region():
    fp = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    license_name = 'test_license'
    test1_loc_result = lcs_id_obj.find_license_region(license_name, fp)
    assert test1_loc_result == (1, 2, 5, 24, 1.0)
    test1_loc_result = lcs_id_obj_context.find_license_region(license_name, fp)
    assert test1_loc_result == (0, 3, 0, 29, 1.0)


def test_get_str_from_file():
    fp = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    list_of_str = lcs_id_obj.get_str_from_file(fp)
    assert list_of_str == ['zero\n', 'one two three four\n', 'five\n', 'six\n', 'seven']
    fp = "what"
    with pytest.raises(IOError):
        lcs_id_obj.get_str_from_file(fp)

def test_truncate_column():
    data = ''.join(random.choice(string.lowercase) for x in range(40000))
    assert len(license_identifier.truncate_column(data)) == license_identifier.COLUMN_LIMIT
    assert license_identifier.truncate_column(3.0) == 3.0

def test_main():
    pass
