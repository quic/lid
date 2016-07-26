import difflib
from collections import namedtuple

from . import prep
from . import n_grams as ng


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
         "penalty_only_license"])):

    def score(self, lic, src):
        src_tokens = reduce(lambda x, y: x+y, src.tokens_by_line, [])
    
        matcher = difflib.SequenceMatcher(
            isjunk = None,
            a = src_tokens,
            b = lic.tokens,
            autojunk = False)
    
        unchanged = 0.0
        changed = 0.0
        for op, ts1, te1, ts2, te2 in matcher.get_opcodes():
            num_tokens_src = te1 - ts1
            num_tokens_license = te2 - ts2
            if op == "equal":
                unchanged += num_tokens_src
            else:
                changed += \
                    self.penalty_only_source * num_tokens_src + \
                    self.penalty_only_license * num_tokens_license
    
        similarity = unchanged / (changed + unchanged)
        return similarity
