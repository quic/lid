#
# Unit Tests to go here
#
from . import n_grams as ng
from . import license_identifier as lcs_id

from collections import Counter
from os import getcwd
from os.path import join



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
BASE_DIR = join(getcwd(), "..")

def get_license_dir():
    license_dir = join(BASE_DIR, 'data', 'test', 'license')
    return license_dir

def test_init():
    lcs_id_obj = lcs_id.license_identifier(get_license_dir())
    assert 'test_license.txt' in lcs_id_obj.license_file_name_list
    assert lcs_id_obj._universe_n_grams.measure_similarity(n_gram_obj) == 1.0

def test_build_n_gram_univ_license():
    univ_ng_obj = ng.n_grams()
    license_dir = get_license_dir()
    license_file_list = ['test_license.txt']

def test_get_license_name():
    lcs_id_obj = lcs_id.license_identifier(get_license_dir())
    assert lcs_id_obj._get_license_name('myname.txt') == 'myname'

def test_analyze_file():
    lcs_id_obj = lcs_id.license_identifier(get_license_dir())
    fp = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    [lcs_match, summary_list] = lcs_id_obj.analyze_file(input_fp=fp)
    assert summary_list[2] == 1.0


def test_find_license_region():
    pass

