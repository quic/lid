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