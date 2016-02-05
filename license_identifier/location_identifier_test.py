#
# Unit Tests to go here
#
from . import n_grams as ng
from . import license_identifier as lcs_id
from . import location_identifier as loc_id
from . import util

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

def test_main_process():
    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    loc_id_obj = loc_id.Location_Finder()
    loc_result = loc_id_obj.main_process(lcs_file, input_file)
    assert loc_result==(1, 2, 5, 24, 1.0)

def test_find_best_region():
    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    loc_id_obj = loc_id.Location_Finder()

    [license_lines, license_offsets]= util.read_lines_offsets(lcs_file)
    [src_lines, src_offsets] = util.read_lines_offsets(input_file)

    window_size = len(license_lines)
    src_size = len(src_lines)

    license_n_grams = ng.n_grams(list_text_line=license_lines)

    [similarity_scores, window_start_index] = loc_id_obj.split_and_measure_similarities(src_size=src_size,
                                                            src_offsets=src_offsets,
                                                            src_lines=src_lines,
                                                            window_size=window_size,
                                                            license_n_grams=license_n_grams)
    [max_score, max_index] = loc_id_obj.find_max_score_ind(similarity_scores=similarity_scores)

    loc_result = loc_id_obj.find_best_region(threshold=0.02,
                                             max_index = max_index,
                                             license_n_grams = license_n_grams,
                                             src_lines = src_lines,
                                             src_offsets = src_offsets,
                                             window_start_index = window_start_index,
                                             window_size = window_size)
    assert loc_result==(1, 2, 5, 24, 1.0)

def test_find_max_score_ind():
    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    loc_id_obj = loc_id.Location_Finder()

    [license_lines, license_offsets]= util.read_lines_offsets(lcs_file)
    [src_lines, src_offsets] = util.read_lines_offsets(input_file)

    window_size = len(license_lines)
    src_size = len(src_lines)

    license_n_grams = ng.n_grams(list_text_line=license_lines)

    [similarity_scores, window_start_index] = loc_id_obj.split_and_measure_similarities(src_size=src_size,
                                                            src_offsets=src_offsets,
                                                            src_lines=src_lines,
                                                            window_size=window_size,
                                                            license_n_grams=license_n_grams)
    [max_score, max_index] = loc_id_obj.find_max_score_ind(similarity_scores=similarity_scores)
    assert max_score == 1.0
    assert max_index[0] == 1


def test_split_and_measure_similarities():
    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'test1.py')
    loc_id_obj = loc_id.Location_Finder()

    [license_lines, license_offsets]= util.read_lines_offsets(lcs_file)
    [src_lines, src_offsets] = util.read_lines_offsets(input_file)

    window_size = len(license_lines)
    src_size = len(src_lines)

    license_n_grams = ng.n_grams(list_text_line=license_lines)

    [similarity_scores, window_start_index] = loc_id_obj.split_and_measure_similarities(src_size=src_size,
                                                            src_offsets=src_offsets,
                                                            src_lines=src_lines,
                                                            window_size=window_size,
                                                            license_n_grams=license_n_grams)
    assert similarity_scores == [0.0, 1.0, 0.0, 0.0, 0.0]
    assert window_start_index == [0, 1, 2, 3, 4]


def test_expand_window():
    lcs_file = join(get_license_dir(), 'test_license.txt')
    input_file = join(BASE_DIR, 'data', 'test', 'data', 'subdir', 'subdir2', 'test3.py')
    loc_id_obj = loc_id.Location_Finder()

    [license_lines, license_offsets]= util.read_lines_offsets(lcs_file)
    [src_lines, src_offsets] = util.read_lines_offsets(input_file)

    window_size = len(license_lines)
    src_size = len(src_lines)

    license_n_grams = ng.n_grams(list_text_line=license_lines)

    [similarity_scores, window_start_index] = loc_id_obj.split_and_measure_similarities(src_size=src_size,
                                                            src_offsets=src_offsets,
                                                            src_lines=src_lines,
                                                            window_size=window_size,
                                                            license_n_grams=license_n_grams)
    [max_score, max_index] = loc_id_obj.find_max_score_ind(similarity_scores=similarity_scores)

    # for maximum scores that share the same value
    final_score = []
    start_index = []
    end_index =[]

    for max_ind in max_index:
        [s_ind, e_ind, final_s] = loc_id_obj.expand_window(license_n_grams,
                                                  src_lines,
                                                  window_start_index[max_ind],
                                                  window_size)
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

    [license_lines, license_offsets]= util.read_lines_offsets(lcs_file)
    [src_lines, src_offsets] = util.read_lines_offsets(input_file)

    window_size = len(license_lines)
    src_size = len(src_lines)

    license_n_grams = ng.n_grams(list_text_line=license_lines)

    [similarity_scores, window_start_index] = loc_id_obj.split_and_measure_similarities(src_size=src_size,
                                                            src_offsets=src_offsets,
                                                            src_lines=src_lines,
                                                            window_size=window_size,
                                                            license_n_grams=license_n_grams)
    [max_score, max_index] = loc_id_obj.find_max_score_ind(similarity_scores=similarity_scores)

    # for maximum scores that share the same value
    final_score = []
    start_index = []
    end_index =[]



def test_expand_to_bottom():
    pass

def test_measure_similarity():
    pass




