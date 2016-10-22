import six
from collections import Counter

from . import util


class n_grams(object):

    def __init__(self, text=None):
        self.unigram_count = Counter()
        self.bigram_count = Counter()
        self.trigram_count = Counter()

        if text is not None:
            if isinstance(text, six.string_types):
                self.parse_text_str(text)
            else:
                self.parse_text_list_items(text)

    def __str__(self):
        return 'n_grams'

    def parse_text_list_items(self, list_text_line, universe_ng=None):
        prev2_word = ''
        prev_word = ''
        curr_word = ''

        for line in list_text_line:
            words = line.split()
            for word in words:
                if util.is_punctuation(word):
                    continue
                prev2_word = prev_word
                prev_word = curr_word
                curr_word = word
                if universe_ng is None:
                    self.insert_ngrams(curr_word, prev_word, prev2_word)
                else:
                    self.insert_ng_within_universe(curr_word, prev_word,
                                                   prev2_word, universe_ng)

    def parse_text_str(self, text_str, universe_ng=None):
        self.parse_text_list_items(text_str.split(), universe_ng)

    def insert_ngrams(self, first, second, third):
        if len(first) > 0:
            self.unigram_count[first] += 1
        if len(second) > 0:
            self.bigram_count[first, second] += 1
        if len(third) > 0:
            self.trigram_count[first, second, third] += 1

    def insert_ng_within_universe(self, first, second, third, universe_ng):
        if universe_ng.unigram_count[first] > 0:
            self.unigram_count[first] += 1
        if universe_ng.bigram_count[first, second] > 0:
            self.bigram_count[first, second] += 1
        if universe_ng.trigram_count[first, second, third] > 0:
            self.trigram_count[first, second, third] += 1

    def measure_similarity(self, other_n_grams):
        return self.measure_Jaccard_distance(other_n_grams)

    def measure_Jaccard_distance(self, other_n_grams):
        """
        |A intersection B| / |A union B|
        """
        uni_intersect = other_n_grams.unigram_count & self.unigram_count
        bi_intersect = other_n_grams.bigram_count & self.bigram_count
        tri_intersect = other_n_grams.trigram_count & self.trigram_count

        uni_union = other_n_grams.unigram_count | self.unigram_count
        bi_union = other_n_grams.bigram_count | self.bigram_count
        tri_union = other_n_grams.trigram_count | self.trigram_count

        if sum(uni_union.values()) > 0:
            uni_score = \
                float(sum(uni_intersect.values())) / sum(uni_union.values())
        else:
            uni_score = 0.0

        if sum(bi_union.values()) > 0:
            bi_score = \
                float(sum(bi_intersect.values())) / sum(bi_union.values())
        else:
            bi_score = 0.0
        if sum(tri_union.values()) > 0:
            tri_score = \
                float(sum(tri_intersect.values())) / sum(tri_union.values())
        else:
            tri_score = 0.0

        return (uni_score + (bi_score * 6.0) + (tri_score * 8.0)) / 15.0
