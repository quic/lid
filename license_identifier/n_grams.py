# Copyright (c) 2017, The Linux Foundation. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#     * Neither the name of The Linux Foundation nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# SPDX-License-Identifier: BSD-3-Clause

import six
from collections import Counter

from . import util


class NGrams(object):

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
        return self.measure_jaccard_index(other_n_grams)

    def measure_jaccard_index(self, other_n_grams):
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
