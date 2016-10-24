import difflib
from collections import Counter, namedtuple

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
            result["init_ignored_src"] = ignored_strings_src.next()
            result["init_ignored_lic"] = ignored_strings_lic.next()

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
                    ignored_src.append(ignored_strings_src.next())

                ignored_lic = []
                for token_index in range(ts2, te2):
                    ignored_lic.append(ignored_strings_lic.next())

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
        count = 0
        for token in tokens:
            if util.is_punctuation(token):
                count += 1
        return count
