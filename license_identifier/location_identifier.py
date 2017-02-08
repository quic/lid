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

import argparse
import sys

from . import location_result
from . import prep
from . import scores


DEFAULT_CONTEXT = 0
DEFAULT_PENALTY_ONLY_SOURCE = 1.0
DEFAULT_PENALTY_ONLY_LICENSE = 50.0
DEFAULT_OVERSHOOT = 5
DEFAULT_STRATEGY = "one_line_then_expand"
DEFAULT_SIMILARITY = "edit_weighted"
DEFAULT_VERBOSITY = 0
DEFAULT_PUNCT_WEIGHT = 0.01


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("license_file")
    parser.add_argument("input_src_file")
    parser.add_argument("-v", "--verbose", action="count", dest="verbosity",
                        default=DEFAULT_VERBOSITY)
    parser.add_argument("--context_lines", type=int)
    parser.add_argument("--strategy", default=DEFAULT_STRATEGY)
    parser.add_argument("--similarity", default=DEFAULT_SIMILARITY)
    parser.add_argument("--overshoot", type=int, default=DEFAULT_OVERSHOOT)
    parser.add_argument("-P", "--pickled_license_library")
    parser.add_argument("--penalty_only_source", type=float,
                        default=DEFAULT_PENALTY_ONLY_SOURCE)
    parser.add_argument("--penalty_only_license", type=float,
                        default=DEFAULT_PENALTY_ONLY_LICENSE)
    parser.add_argument("--punct_weight", type=float,
                        default=DEFAULT_PUNCT_WEIGHT)
    args = parser.parse_args(argv)

    if args.pickled_license_library is not None:
        license_library = \
            prep.LicenseLibrary.deserialize(args.pickled_license_library)
        universe_n_grams = license_library.universe_n_grams
    else:
        universe_n_grams = None

    location = Location_Finder(context_lines=args.context_lines,
                               penalty_only_source=args.penalty_only_source,
                               penalty_only_license=args.penalty_only_license,
                               punct_weight=args.punct_weight,
                               universe_n_grams=universe_n_grams,
                               overshoot=args.overshoot,
                               similarity=args.similarity,
                               strategy=args.strategy,
                               verbosity=args.verbosity)

    license = prep.License.from_filepath(args.license_file)
    source = prep.Source.from_filepath(args.input_src_file)

    print(location.main_process(license, source))


class Location_Finder(object):

    def __init__(self,
                 context_lines=DEFAULT_CONTEXT,
                 penalty_only_source=DEFAULT_PENALTY_ONLY_SOURCE,
                 penalty_only_license=DEFAULT_PENALTY_ONLY_LICENSE,
                 punct_weight=DEFAULT_PUNCT_WEIGHT,
                 universe_n_grams=None,
                 overshoot=DEFAULT_OVERSHOOT,
                 strategy=DEFAULT_STRATEGY,
                 similarity=DEFAULT_SIMILARITY,
                 verbosity=DEFAULT_VERBOSITY):

        self.context_lines = context_lines
        self.penalty_only_source = penalty_only_source
        self.penalty_only_license = penalty_only_license
        self.punct_weight = punct_weight
        self.universe_n_grams = universe_n_grams
        self.overshoot = overshoot
        self.strategy = Location_Finder._check_strategy(strategy)
        self.similarity = Location_Finder._check_similarity(similarity)
        self.verbosity = verbosity
        self.similarity_obj = self._similarity_factory()

    @staticmethod
    def _check_similarity(similarity):
        allowed = ['edit_weighted', 'ngram']
        unrecognized = 'Unrecognized similary: {}'.format(similarity)

        assert similarity in allowed, unrecognized

        return similarity

    @staticmethod
    def _check_strategy(strategy):
        allowed = ['exhaustive', 'one_line_then_expand', 'full_text_only']
        unrecognized = 'Unrecognized strategy: {}'.format(strategy)

        assert strategy in allowed, unrecognized

        return strategy

    def _similarity_factory(self):
        similarity_obj = None

        if self.similarity == 'edit_weighted':
            similarity_obj = scores.EditWeightedSimilarity(
                penalty_only_source=self.penalty_only_source,
                penalty_only_license=self.penalty_only_license,
                punct_weight=self.punct_weight)
        elif self.similarity == 'ngram':
            similarity_obj = scores.NgramSimilarity(
                universe_n_grams=self.universe_n_grams)

        return similarity_obj

    def main_process(self, lic, src):
        if self.strategy == 'exhaustive':
            start_line, end_line, best_score = \
                self.best_region_exhaustive(lic, src)
        elif self.strategy == 'one_line_then_expand':
            start_line, end_line, best_score = \
                self.one_line_then_expand(lic, src)
        elif self.strategy == 'full_text_only':
            start_line = 0
            end_line = len(src.lines)
            best_score = self.similarity_obj.score(lic, src)
        else:  # pragma: no cover
            raise Exception("Unrecognized strategy: {}".format(self.strategy))

        start_line_orig, end_line_orig = start_line, end_line
        start_line, end_line, start_offset, end_offset = \
            self.determine_offsets(start_line, end_line, src.lines,
                                   src.offsets_by_line)

        # Adjust line indices if we're dealing with a subset of the source
        start_line_orig += src.original_line_offset
        end_line_orig += src.original_line_offset
        start_line += src.original_line_offset
        end_line += src.original_line_offset

        return location_result.LocationResult(start_line=start_line,
                                              end_line=end_line,
                                              start_offset=start_offset,
                                              end_offset=end_offset,
                                              score=best_score,
                                              start_line_orig=start_line_orig,
                                              end_line_orig=end_line_orig)

    def best_region_exhaustive(self, lic, src):
        results = []
        for start_line in range(len(src.lines)):
            for end_line in range(start_line + 1, len(src.lines) + 1):
                src_subset = src.subset(start_line, end_line)
                score = self.similarity_obj.score(lic, src_subset)
                results.append((start_line, end_line, score))

        if self.verbosity >= 1:  # pragma: no cover
            sorted_results = sorted(results, key=lambda x: x[2])
            for r in sorted_results:
                print("lines {}-{}: score = {:.06f}".format(*r))

            print("=" * 40)

        start_line, end_line, best_score = max(results, key=lambda x: x[2])

        return start_line, end_line, best_score

    def one_line_then_expand(self, lic, src):
        # First, find best single line
        results = []
        for line_index in range(len(src.lines)):
            src_subset = src.subset(line_index, line_index + 1)
            score = self.similarity_obj.score(lic, src_subset)
            results.append((line_index, line_index + 1, score))

        if self.verbosity >= 1:  # pragma: no cover
            sorted_results = sorted(results, key=lambda x: x[2])
            for r in sorted_results:
                print("lines {}-{}: score = {:.06f}".format(*r))
            print("=" * 40)

        start_line, end_line, best_score = max(results, key=lambda x: x[2])
        prev_start_line, prev_end_line = None, None

        # Alternate between expanding region upward and downward
        # until the selected region no longer changes
        while True:
            if self.verbosity >= 1:  # pragma: no cover
                print("Current region: {}-{}".format(start_line, end_line))

            # Expand region upward
            start_line, end_line, best_score = self.expand(
                lic, src, start_line, end_line, best_score, top=True)

            if self.verbosity >= 1:  # pragma: no cover
                print("Current region: {}-{}".format(start_line, end_line))

            # Expand region downward
            start_line, end_line, best_score = self.expand(
                lic, src, start_line, end_line, best_score, top=False)

            if start_line == prev_start_line and end_line == prev_end_line:
                break

            prev_start_line = start_line
            prev_end_line = end_line

        return start_line, end_line, best_score

    def expand(self, lic, src, start_line, end_line, score_to_beat, top):
        if top:
            def update(x, y):
                return x - 1, y
        else:
            def update(x, y):
                return x, y + 1

        overshoot_remaining = self.overshoot
        results = []
        best_start_line = start_line
        best_end_line = end_line
        best_score = score_to_beat

        while True:
            if overshoot_remaining < 0:
                break

            start_line, end_line = update(start_line, end_line)
            if start_line < 0:
                break
            if end_line > len(src.lines):
                break

            src_subset = src.subset(start_line, end_line)
            score = self.similarity_obj.score(lic, src_subset)

            current_result = (start_line, end_line, score)
            results.append(current_result)

            if score >= best_score:
                best_start_line = start_line
                best_end_line = end_line
                best_score = score
                overshoot_remaining = self.overshoot  # reset overshoot
                new_best = True
            else:
                overshoot_remaining -= 1
                new_best = False

            if self.verbosity >= 1:  # pragma: no cover
                suffix = " *" if new_best else ""
                print("Considering expansion (top = {}): {}-{}: score = {}{}".
                      format(top, start_line, end_line, score, suffix))

        return best_start_line, best_end_line, best_score

    def determine_offsets(self, start_line, end_line, src_lines, src_offsets):
        if self.context_lines:
            end_line = end_line + self.context_lines
            start_line -= self.context_lines
            if start_line < 0:
                start_line = 0

        # use the start of the next line as offset, unless it's the last line
        if end_line >= len(src_offsets):
            end_line = len(src_lines)
            end_offset = src_offsets[-1]
        else:
            end_offset = src_offsets[end_line]

        return start_line, end_line, src_offsets[start_line], end_offset


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
