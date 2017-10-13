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

from . import n_grams as ng
from . import prep
from . import scores


def test_ngram_similarity():
    universe_ng = ng.NGrams("a b c d")
    scorer = scores.NgramSimilarity(universe_n_grams=universe_ng)

    assert scorer.score(mklic(["a b c d"]), mksrc(["a b c d"])) == 1.0
    assert scorer.score(mklic(["a b c d"]), mksrc(["a b c"])) == \
        (3/4. + 2/3. * 6.0 + 1/2. * 8.0) / 15.0
    assert scorer.score(mklic(["a b c d"]), mksrc(["a"])) == 1/60.
    assert scorer.score(mklic(["a b c d"]), mksrc(["a x y"])) == 1/60.
    assert scorer.score(mklic(["a b c d"]), mksrc(["a b c x y"])) == \
        (3/4. + 2/3. * 6.0 + 1/2. * 8.0) / 15.0


def test_edit_weighted_similarity():
    scorer = scores.EditWeightedSimilarity(penalty_only_source=2.0,
                                           penalty_only_license=3.0,
                                           punct_weight=0.5)

    assert scorer.penalty_only_source == 2.0
    assert scorer.penalty_only_license == 3.0

    assert scorer.score(mklic([""]), mksrc([""])) == 0.0
    assert scorer.score(mklic(["a"]), mksrc(["a"])) == 1.0
    assert scorer.score(mklic(["."]), mksrc(["."])) == 1.0
    assert scorer.score(mklic(["a"]), mksrc([""])) == 0.0
    assert scorer.score(mklic([""]), mksrc(["a"])) == 0.0
    assert scorer.score(mklic(["a"]), mksrc(["a b"])) == 1/3.
    assert scorer.score(mklic(["a c"]), mksrc(["a b"])) == 1/6.
    assert scorer.score(mklic([". c"]), mksrc([". b"])) == 1/11.
    assert scorer.score(mklic(["a ."]), mksrc(["a b"])) == 2/9.
    assert scorer.score(mklic(["a c"]), mksrc(["a ."])) == 1/5.
    assert scorer.score(mklic(["a c"]), mksrc(["a"])) == 1/4.

    result = scorer.score_and_rationale(mklic(["a c"]), mksrc(["a"]),
                                        extras=False)
    assert "score" in result.keys()
    assert "diff_chunks" not in result.keys()


def test_edit_weighted_similarity_rationale():
    scorer = scores.EditWeightedSimilarity(
        penalty_only_source=2.0,
        penalty_only_license=3.0,
        punct_weight=0.5)

    result = scorer.score_and_rationale(
        lic=mklic(["a x\t", "b c d e f g"]),
        src=mksrc([" a  ", "b c m", "n g x x"]),
        extras=True)
    assert set(["score", "diff_chunks"]).issubset(set(result.keys()))

    assert result["init_ignored_src"] == " "
    assert result["init_ignored_lic"] == ""

    chunks = result["diff_chunks"]
    assert len(chunks) == 6

    assert chunks[0]["op"] == "equal"
    assert chunks[0]["tokens_src"] == ["a"]
    assert chunks[0]["tokens_lic"] == ["a"]
    assert chunks[0]["ignored_src"] == ["  \n"]
    assert chunks[0]["ignored_lic"] == [" "]

    assert chunks[1]["op"] == "insert"
    assert chunks[1]["tokens_src"] == []
    assert chunks[1]["tokens_lic"] == ["x"]
    assert chunks[1]["ignored_src"] == []
    assert chunks[1]["ignored_lic"] == ["\t\n"]

    assert chunks[2]["op"] == "equal"
    assert chunks[2]["tokens_src"] == ["b", "c"]
    assert chunks[2]["tokens_lic"] == ["b", "c"]
    assert chunks[2]["ignored_src"] == [" ", " "]
    assert chunks[2]["ignored_lic"] == [" ", " "]

    assert chunks[3]["op"] == "replace"
    assert chunks[3]["tokens_src"] == ["m", "n"]
    assert chunks[3]["tokens_lic"] == ["d", "e", "f"]
    assert chunks[3]["ignored_src"] == ["\n", " "]
    assert chunks[3]["ignored_lic"] == [" ", " ", " "]

    assert chunks[4]["op"] == "equal"
    assert chunks[4]["tokens_src"] == ["g"]
    assert chunks[4]["tokens_lic"] == ["g"]
    assert chunks[4]["ignored_src"] == [" "]
    assert chunks[4]["ignored_lic"] == ["\n"]

    assert chunks[5]["op"] == "delete"
    assert chunks[5]["tokens_src"] == ["x", "x"]
    assert chunks[5]["tokens_lic"] == []
    assert chunks[5]["ignored_src"] == [" ", "\n"]
    assert chunks[5]["ignored_lic"] == []


def mklic(lines):
    return prep.License.from_lines(lines)


def mksrc(lines):
    return prep.Source.from_lines(lines)
