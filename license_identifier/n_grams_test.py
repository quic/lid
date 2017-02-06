from collections import Counter

from . import n_grams as ng


text_list = ['#', 'one', 'two', 'three', 'four']
text_line = '# one\ntwo\nthree\nfour'
text_line_crlf = '# one\r\ntwo\r\nthree\r\nfour'

unigram_counter = Counter(['one', 'two', 'three', 'four'])
bigram_counter = Counter([('two', 'one'), ('three', 'two'), ('four', 'three')])
trigram_counter = Counter([('three', 'two', 'one'), ('four', 'three', 'two')])


def test_init_list_input():
    n_grams_obj = ng.NGrams(text_list)

    assert n_grams_obj.unigram_count == unigram_counter
    assert n_grams_obj.bigram_count == bigram_counter
    assert n_grams_obj.trigram_count == trigram_counter


def test_to_string():
    n_grams_obj = ng.NGrams(text_list)

    assert str(n_grams_obj) == 'n_grams'


def test_init_text_input():
    n_grams_obj = ng.NGrams(text_line)

    assert n_grams_obj.unigram_count == unigram_counter
    assert n_grams_obj.bigram_count == bigram_counter
    assert n_grams_obj.trigram_count == trigram_counter


def test_init_text_input_with_crlf():
    n_grams_obj = ng.NGrams(text_line_crlf)

    assert n_grams_obj.unigram_count == unigram_counter
    assert n_grams_obj.bigram_count == bigram_counter
    assert n_grams_obj.trigram_count == trigram_counter


def test_insert_ngrams():
    n_grams_obj = ng.NGrams()

    n_grams_obj.insert_ngrams('one', '', '')
    assert sum(n_grams_obj.unigram_count.values()) == 1
    assert sum(n_grams_obj.bigram_count.values()) == 0
    assert sum(n_grams_obj.trigram_count.values()) == 0

    n_grams_obj.insert_ngrams('two', 'one', '')
    assert sum(n_grams_obj.unigram_count.values()) == 2
    assert sum(n_grams_obj.bigram_count.values()) == 1
    assert sum(n_grams_obj.trigram_count.values()) == 0

    n_grams_obj.insert_ngrams('three', 'two', 'one')
    assert sum(n_grams_obj.unigram_count.values()) == 3
    assert sum(n_grams_obj.bigram_count.values()) == 2
    assert sum(n_grams_obj.trigram_count.values()) == 1


def test_parse_text_items():
    n_grams_obj = ng.NGrams()

    n_grams_obj.parse_text_list_items(text_list)
    assert n_grams_obj.unigram_count == unigram_counter
    assert n_grams_obj.bigram_count == bigram_counter
    assert n_grams_obj.trigram_count == trigram_counter


def test_parse_text_str():
    n_grams_obj = ng.NGrams()

    n_grams_obj.parse_text_str(text_line)
    assert n_grams_obj.unigram_count == unigram_counter
    assert n_grams_obj.bigram_count == bigram_counter
    assert n_grams_obj.trigram_count == trigram_counter


def test_measure_jaccard_index():
    n_grams_obj = ng.NGrams(text_list)
    n_grams_obj2 = ng.NGrams(text_list)
    n_grams_obj3 = ng.NGrams()

    assert n_grams_obj.measure_jaccard_index(n_grams_obj2) == 1.0
    assert n_grams_obj.measure_jaccard_index(n_grams_obj3) == 0.0

    n_grams_obj3.insert_ngrams('one', '', '')
    # total space
    # unigram = 4
    # bigram = 3
    # trigram = 2
    # (1/4 + 0 + 0) / 15
    assert n_grams_obj.measure_jaccard_index(n_grams_obj3) == 1.0 / 4 / 15


def test_measure_jaccard_index_zero_denom():
    ng0 = ng.NGrams("")
    assert ng0.measure_jaccard_index(ng0) == 0.0
