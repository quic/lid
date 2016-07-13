from . import scores
from . import prep
from . import n_grams as ng


def test_ngram_similarity():
    universe_ng = ng.n_grams("a b c d")
    scorer = scores.NgramSimilarity(
        universe_n_grams = universe_ng)

    assert scorer.score(mklic(["a b c d"]), mksrc(["a b c d"])) == 1.0
    assert scorer.score(mklic(["a b c d"]), mksrc(["a b c"])) == (3/4. + 2/3. * 6.0 + 1/2. * 8.0) / 15.0
    assert scorer.score(mklic(["a b c d"]), mksrc(["a"])) == 1/60.
    assert scorer.score(mklic(["a b c d"]), mksrc(["a x y"])) == 1/60.
    assert scorer.score(mklic(["a b c d"]), mksrc(["a b c x y"])) == (3/4. + 2/3. * 6.0 + 1/2. * 8.0) / 15.0

def test_edit_weighted_similarity():
    scorer = scores.EditWeightedSimilarity(
        penalty_only_source = 2.0,
        penalty_only_license = 3.0)

    assert scorer.penalty_only_source == 2.0
    assert scorer.penalty_only_license == 3.0

    assert scorer.score(mklic(["a"]), mksrc(["a"])) == 1.0
    assert scorer.score(mklic(["a"]), mksrc([""])) == 0.0
    assert scorer.score(mklic([""]), mksrc(["a"])) == 0.0
    assert scorer.score(mklic(["a"]), mksrc(["a b"])) == 1/3.
    assert scorer.score(mklic(["a c"]), mksrc(["a b"])) == 1/6.
    assert scorer.score(mklic(["a c"]), mksrc(["a"])) == 1/4.


def mklic(lines):
    return prep.License.from_lines(lines)

def mksrc(lines):
    return prep.Source.from_lines(lines)
