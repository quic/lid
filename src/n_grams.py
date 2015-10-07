import os
from os import listdir, walk
from os.path import isfile, join
from collections import Counter, defaultdict
import pprint
import sys
import string
import util


class n_grams:
    def __init__(self, list_text_line=None, text_str=None):
        self.unigram_count = Counter()
        self.bigram_count = Counter()
        self.trigram_count = Counter()

        if list_text_line is not None:
            self.parse_text_items(list_text_line)
        elif text_str is not None:
            self.parse_text_str(text_str)

    def __str__(self):
        # print (self.unigram_count)
        # print (self.bigram_count)
        return 'n_grams'

    def parse_text_items(self, list_text_line):
        prev2_word =""
        prev_word = ""
        curr_word = ""

        for line in list_text_line:
            words = line.split()
            for word in words:
                prev2_word = prev_word
                prev_word = curr_word
                curr_word = word
                self.insert_ngrams(curr_word, prev_word, prev2_word)

    def parse_text_str(self, text_str):
        prev2_word =""
        prev_word = ""
        curr_word = ""

        words = text_str.split()
        for word in words:
            prev2_word = prev_word
            prev_word = curr_word
            curr_word = word
            self.insert_ngrams(curr_word, prev_word, prev2_word)

    def insert_ngrams(self, first, second, third):
        self.unigram_count[first] += 1
        self.bigram_count [first, second]  += 1
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

        if (sum(uni_union.values()) > 0):
            uni_score = float(sum(uni_intersect.values())) / sum(uni_union.values())
        else:
            uni_score = 0.0

        if (sum(bi_union.values()) > 0):
            bi_score = float(sum(bi_intersect.values())) / sum(bi_union.values())
        else:
            bi_score = 0.0
        if (sum(tri_union.values()) > 0):
            tri_score = float(sum(tri_intersect.values())) / sum(tri_union.values())
        else:
            tri_score = 0.0

        return (uni_score + bi_score*6.0 + tri_score*8.0 )/15.0
