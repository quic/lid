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

import difflib
from collections import Counter, namedtuple
import string

from . import n_grams as ng
from . import util


class Similarity(object):

    def score(self, lic, src):
        return self.score_and_rationale(lic, src, extras=False)["score"]

    def score_and_rationale(self, lic, src, extras):  # pragma: no cover
        raise NotImplementedError


NgramSimilarityBase = namedtuple('NgramSimilarity', ['universe_n_grams'])


class NgramSimilarity(Similarity, NgramSimilarityBase):

    def score_and_rationale(self, lic, src, extras):
        src_ngrams = ng.NGrams()
        src_ngrams.parse_text_list_items(src.lines,
                                         universe_ng=self.universe_n_grams)

        similarity = lic.n_grams.measure_similarity(src_ngrams)

        return {'score': similarity}


EditWeightedSimilarityBase = namedtuple(
    'EditWeightedSimilary',
    ['penalty_only_source', 'penalty_only_license', 'punct_weight'])


class EditWeightedSimilarity(Similarity, EditWeightedSimilarityBase):

    def score_and_rationale(self, lic, src, extras):
        src_tokens = []
        for token_list in src.tokens_by_line:
            src_tokens.extend(token_list)

        matcher = difflib.SequenceMatcher(isjunk=None,
                                          a=src_tokens,
                                          b=lic.tokens,
                                          autojunk=False)

        diff_chunks = []

        ignored_strings_src = src.get_ignored_strings()
        ignored_strings_lic = lic.get_ignored_strings()

        result = dict()

        if extras:
            result["init_ignored_src"] = next(ignored_strings_src)
            result["init_ignored_lic"] = next(ignored_strings_lic)

        total_counts = Counter()
        for op, ts1, te1, ts2, te2 in matcher.get_opcodes():
            num_tokens_src = te1 - ts1
            num_tokens_lic = te2 - ts2

            num_punct_src = self._count_punctuation(src_tokens[ts1:te1])
            num_punct_lic = self._count_punctuation(lic.tokens[ts2:te2])

            local_counts = Counter()

            if op == "equal":
                local_counts[("both", "non_punct")] += \
                    num_tokens_src - num_punct_src
                local_counts[("both", "punct")] += num_punct_src
            else:
                local_counts[("only_src", "non_punct")] += \
                    num_tokens_src - num_punct_src
                local_counts[("only_src", "punct")] += num_punct_src
                local_counts[("only_lic", "non_punct")] += \
                    num_tokens_lic - num_punct_lic
                local_counts[("only_lic", "punct")] += num_punct_lic

            total_counts += local_counts

            if extras:
                ignored_src = []
                for token_index in range(ts1, te1):
                    ignored_src.append(next(ignored_strings_src))

                ignored_lic = []
                for token_index in range(ts2, te2):
                    ignored_lic.append(next(ignored_strings_lic))

                diff_chunks.append({
                    "op": op,
                    "local_counts": local_counts,
                    "tokens_src": src_tokens[ts1:te1],
                    "tokens_lic": lic.tokens[ts2:te2],
                    "ignored_src": ignored_src,
                    "ignored_lic": ignored_lic,
                })

        unchanged = total_counts[("both", "non_punct")] + self.punct_weight * \
            total_counts[("both", "punct")]
        only_src = total_counts[("only_src", "non_punct")] + \
            self.punct_weight * total_counts[("only_src", "punct")]
        only_lic = total_counts[("only_lic", "non_punct")] + \
            self.punct_weight * total_counts[("only_lic", "punct")]

        denom = float(unchanged +
                      self.penalty_only_source * only_src +
                      self.penalty_only_license * only_lic)

        if denom == 0.0:
            similarity = 0.0
        else:
            similarity = unchanged / denom

        result["score"] = similarity

        if extras:
            result["penalty_only_source"] = self.penalty_only_source
            result["penalty_only_license"] = self.penalty_only_license
            result["total_counts"] = total_counts
            result["diff_chunks"] = diff_chunks

        return result

    def _count_punctuation(self, tokens):
        count = lambda l1,l2: sum([1 for x in l1 if x in l2])
        return count(tokens,set(string.punctuation))
