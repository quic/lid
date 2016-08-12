import difflib
from collections import Counter, namedtuple

from . import prep
from . import n_grams as ng
from . import util


class Similarity(object):
    def score(self, lic, src):  # pragma: no cover
        raise NotImplementedError


class NgramSimilarity(Similarity, namedtuple("NgramSimilarity",
        ["universe_n_grams"])):

    def score(self, lic, src):
        src_ngrams = ng.n_grams()
        src_ngrams.parse_text_list_items(src.lines, universe_ng = self.universe_n_grams)
    
        similarity = lic.n_grams.measure_similarity(src_ngrams)
        return similarity


class EditWeightedSimilarity(Similarity, namedtuple("EditWeightedSimilarity",
        ["penalty_only_source",
         "penalty_only_license",
         "punct_weight"])):

    def score(self, lic, src):
        src_tokens = reduce(lambda x, y: x+y, src.tokens_by_line, [])
    
        matcher = difflib.SequenceMatcher(
            isjunk = None,
            a = src_tokens,
            b = lic.tokens,
            autojunk = False)
    
        total_counts = Counter()
        for op, ts1, te1, ts2, te2 in matcher.get_opcodes():
            num_tokens_src = te1 - ts1
            num_tokens_lic = te2 - ts2

            num_punct_src = self._count_punctuation(src_tokens[ts1:te1])
            num_punct_lic = self._count_punctuation(lic.tokens[ts2:te2])

            local_counts = Counter()

            if op == "equal":
                local_counts[("both", "non_punct")] += num_tokens_src - num_punct_src
                local_counts[("both", "punct")] += num_punct_src
            else:
                local_counts[("only_src", "non_punct")] += num_tokens_src - num_punct_src
                local_counts[("only_src", "punct")] += num_punct_src
                local_counts[("only_lic", "non_punct")] += num_tokens_lic - num_punct_lic
                local_counts[("only_lic", "punct")] += num_punct_lic

            total_counts += local_counts

        unchanged = total_counts[("both", "non_punct")] + self.punct_weight * total_counts[("both", "punct")]
        only_src = total_counts[("only_src", "non_punct")] + self.punct_weight * total_counts[("only_src", "punct")]
        only_lic = total_counts[("only_lic", "non_punct")] + self.punct_weight * total_counts[("only_lic", "punct")]
        denom = float(unchanged \
            + self.penalty_only_source * only_src \
            + self.penalty_only_license * only_lic)

        if denom == 0.0:
            similarity = 0.0
        else:
            similarity = unchanged / denom

        return similarity

    def _count_punctuation(self, tokens):
        count = 0
        for token in tokens:
            if util.is_punctuation(token):
                count += 1
        return count
