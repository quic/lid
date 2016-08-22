import math
import nltk
import difflib
import argparse
import sys

from . import location_result as lr
from . import n_grams as ng
from . import util
from . import scores
from . import prep


DEFAULT_CONTEXT = 0
DEFAULT_PENALTY_ONLY_SOURCE = 1.0
DEFAULT_PENALTY_ONLY_LICENSE = 50.0
DEFAULT_OVERSHOOT = 5
DEFAULT_STRATEGY = "one_line_then_expand"
DEFAULT_SIMILARITY = "edit_weighted"
DEFAULT_VERBOSITY = 0
DEFAULT_PUNCT_WEIGHT = 0.01


def main(argv = []):
    parser = argparse.ArgumentParser()
    parser.add_argument("license_file")
    parser.add_argument("input_src_file")
    parser.add_argument("-v", "--verbose", action="count", dest="verbosity")
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
        license_library = prep.LicenseLibrary.deserialize(
            args.pickled_license_library)
        universe_n_grams = license_library.universe_n_grams
    else:
        universe_n_grams = None

    loc_obj = Location_Finder(
        context_lines = args.context_lines,
        penalty_only_source = args.penalty_only_source,
        penalty_only_license = args.penalty_only_license,
        punct_weight = args.punct_weight,
        universe_n_grams = universe_n_grams,
        overshoot = args.overshoot,
        similarity = args.similarity,
        strategy = args.strategy,
        verbosity = args.verbosity)

    lic = prep.License.from_filename(args.license_file)
    src = prep.Source.from_filename(args.input_src_file)

    print(loc_obj.main_process(lic, src))


class Location_Finder(object):

    def __init__(self,
            context_lines = DEFAULT_CONTEXT,
            penalty_only_source = DEFAULT_PENALTY_ONLY_SOURCE,
            penalty_only_license = DEFAULT_PENALTY_ONLY_LICENSE,
            punct_weight = DEFAULT_PUNCT_WEIGHT,
            universe_n_grams = None,
            overshoot = DEFAULT_OVERSHOOT,
            strategy = DEFAULT_STRATEGY,
            similarity = DEFAULT_SIMILARITY,
            verbosity = DEFAULT_VERBOSITY):
        self.context_lines = context_lines
        self.penalty_only_source = penalty_only_source
        self.penalty_only_license = penalty_only_license
        self.punct_weight = punct_weight
        self.universe_n_grams = universe_n_grams
        self.overshoot = overshoot
        self.strategy = Location_Finder._check_strategy(strategy)
        self.similarity = Location_Finder._check_similarity(similarity)
        self.verbosity = verbosity
        self._init_similarity_obj()

    @staticmethod
    def _check_similarity(similarity):
        allowed_similarity_types = [
            "edit_weighted",
            "ngram",
        ]
        assert similarity in allowed_similarity_types, \
            "Unrecognized similarity: {}".format(similarity)
        return similarity

    @staticmethod
    def _check_strategy(strategy):
        allowed_strategies = [
            "exhaustive",
            "one_line_then_expand",
            "window_then_expand",
        ]
        assert strategy in allowed_strategies, \
            "Unrecognized strategy: {}".format(strategy)
        return strategy

    def _init_similarity_obj(self):
        if self.similarity == "edit_weighted":
            self.similarity_obj = scores.EditWeightedSimilarity(
                penalty_only_source = self.penalty_only_source,
                penalty_only_license = self.penalty_only_license,
                punct_weight = self.punct_weight)
        elif self.similarity == "ngram":
            self.similarity_obj = scores.NgramSimilarity(
                universe_n_grams = self.universe_n_grams)

    def main_process(self, lic, src):
        if self.strategy == "exhaustive":
            start_line, end_line, best_score = \
                self.best_region_exhaustive(lic, src)
        elif self.strategy == "one_line_then_expand":
            start_line, end_line, best_score = \
                self.one_line_then_expand(lic, src)
        elif self.strategy == "window_then_expand":
            start_line, end_line, best_score = \
                self.window_then_expand(lic, src)
        else:  # pragma: no cover
            raise Exception("Unrecognized strategy: {}".format(self.strategy))

        start_line, end_line, start_offset, end_offset = \
            self.determine_offsets(start_line, end_line,
            src.lines, src.offsets_by_line)

        return lr.LocationResult(
            start_line = start_line,
            end_line = end_line,
            start_offset = start_offset,
            end_offset = end_offset,
            score = best_score)

    def best_region_exhaustive(self, lic, src):
        results = []
        for start_line in range(len(src.lines)):
            for end_line in range(start_line + 1, len(src.lines) + 1):
                src_subset = src.subset(start_line, end_line)
                score = self.similarity_obj.score(lic, src_subset)
                results.append((start_line, end_line, score))

        if self.verbosity >= 1:  # pragma: no cover
            sorted_results = sorted(results, key = lambda x: x[2])
            for r in sorted_results:
                print("lines {}-{}: score = {:.06f}".format(*r))
            print("=" * 40)

        start_line, end_line, best_score = max(results, key = lambda x: x[2])
        return start_line, end_line, best_score

    def one_line_then_expand(self, lic, src):
        # First, find best single line
        results = []
        for line_index in range(len(src.lines)):
            src_subset = src.subset(line_index, line_index + 1)
            score = self.similarity_obj.score(lic, src_subset)
            results.append((line_index, line_index + 1, score))

        if self.verbosity >= 1:  # pragma: no cover
            sorted_results = sorted(results, key = lambda x: x[2])
            for r in sorted_results:
                print("lines {}-{}: score = {:.06f}".format(*r))
            print("=" * 40)

        start_line, end_line, best_score = max(results, key = lambda x: x[2])
        prev_start_line, prev_end_line = None, None

        # Alternate between expanding region upward and downward
        # until the selected region no longer changes
        while True:
            if self.verbosity >= 1:  # pragma: no cover
                print("Current region: {}-{}".format(start_line, end_line))

            # Expand region upward
            start_line, end_line, best_score = self.expand(
                lic, src, start_line, end_line, best_score, top = True)

            if self.verbosity >= 1:  # pragma: no cover
                print("Current region: {}-{}".format(start_line, end_line))

            # Expand region downward
            start_line, end_line, best_score = self.expand(
                lic, src, start_line, end_line, best_score, top = False)

            if start_line == prev_start_line and end_line == prev_end_line:
                break

            prev_start_line = start_line
            prev_end_line = end_line

        return start_line, end_line, best_score

    def expand(self, lic, src, start_line, end_line, score_to_beat, top):
        if top:
            update = lambda x,y: (x-1,y)
        else:
            update = lambda x,y: (x,y+1)

        overshoot_remaining = self.overshoot
        results = []
        best_start_line = start_line
        best_end_line = end_line
        best_score = score_to_beat

        while True:
            if overshoot_remaining < 0: break

            start_line, end_line = update(start_line, end_line)
            if start_line < 0: break
            if end_line > len(src.lines): break

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
                print("Considering expansion (top = {}): {}-{}: score = {}{}" \
                    .format(top, start_line, end_line, score, suffix))

        return best_start_line, best_end_line, best_score

    def window_then_expand(self, lic, src):
        # split up the window and loop over the windows
        # for small source file case
        # TODO: check if they match & score
        [similarity_scores, window_start_index] = \
            self.split_and_measure_similarities(lic, src)

        # Find the window with maximum scores.
        [max_score, max_index] = self.find_max_score_ind(similarity_scores)

        # Expand and find the region with maximum score
        return self.find_best_window_expansion(
            max_index = max_index,
            lic = lic,
            src = src,
            window_start_index = window_start_index)

    def find_best_window_expansion(
            self, max_index, lic, src, window_start_index):
        # for maximum scores that share the same value
        final_score = []
        start_index = []
        end_index =[]

        # find the region that has the best score (if a tie, pick the first)
        for max_ind in max_index:
            # 5. Expand until the line addition does not add any gain in similarity measure
            [s_ind, e_ind, final_s] = self.expand_window(
                lic = lic,
                src = src,
                start_ind = window_start_index[max_ind])
            start_index.append(s_ind)
            end_index.append(e_ind)
            final_score.append(final_s)
        max_score = max(final_score)
        max_index = [i for i, j in enumerate(final_score) if j == max_score]
        first_max_ind = max_index[0]

        start_line = start_index[first_max_ind]
        end_line = end_index[first_max_ind]

        return start_line, \
               end_line, \
               final_score[first_max_ind]

    def determine_offsets(self, start_line, end_line, src_lines, src_offsets):
        if self.context_lines:
            end_line = end_line + self.context_lines
            start_line -= self.context_lines
            if start_line < 0:
                start_line = 0

        # use the start of the next line as the offset, unless it's the last line
        if end_line >= len(src_offsets):
            end_line = len(src_lines)
            end_offset = src_offsets[-1]
        else:
            end_offset = src_offsets[end_line]

        return start_line, end_line, src_offsets[start_line], end_offset

    def find_max_score_ind(self, similarity_scores):
        max_score = max(similarity_scores)
        max_index = [i for i, j in enumerate(similarity_scores) if j == max_score]
        return max_score, max_index

    def split_and_measure_similarities(self, lic, src):
        '''split up the window and loop over the windows
        for small source file case
        TODO: check if they match & score
        '''
        window_size = len(lic.lines)
        window_start_ind = 0
        window_end_ind = window_size

        similarity_scores = []
        window_start_index = []

        index_increment = int(math.floor(window_size / 2))

        if index_increment == 0:
            index_increment = 1
        while (window_start_ind < len(src.lines)):
            # create the sliding window
            # find the similarity measure for each window
            src_subset = src.subset(window_start_ind, window_end_ind)
            similarity_score = self.similarity_obj.score(lic, src_subset)

            # keep track of the scores
            similarity_scores.append(similarity_score)

            # bookkeeping of the indices
            window_start_index.append(window_start_ind)

            # increment the indices for the next window
            window_start_ind += index_increment
            window_end_ind += index_increment
        return similarity_scores, window_start_index

    def expand_window(self, lic, src, start_ind):
        # find the baseline score
        window_size = len(lic.lines)
        end_ind = start_ind + window_size
        src_subset = src.subset(start_ind, end_ind)
        score_to_keep = self.similarity_obj.score(lic, src_subset)
        # TODO: possibly use regular expression to find the start and end
        for increment in [3, 2, 1]:
            start_ind, end_ind, score_to_keep = self.expand_generic(
                lic, src, start_ind, end_ind,
                score_to_keep, start_increment = increment, end_increment = 0)
        for increment in [5, 4, 3, 2, 1]:
            start_ind, end_ind, score_to_keep = self.expand_generic(
                lic, src, start_ind, end_ind,
                score_to_keep, start_increment = 0, end_increment = increment)
        return start_ind, end_ind, score_to_keep

    def expand_generic(self, lic, src, start_ind, end_ind,
            score_to_keep, start_increment, end_increment):
        assert start_increment >= 0 and end_increment >= 0, \
            "Cannot use negative increments"
        assert start_increment != 0 or end_increment != 0, \
            "Start and end increments are both zero"
        while True:
            start_ind -= start_increment
            end_ind += end_increment

            if start_ind >= 0 and end_ind <= len(src.lines):
                src_subset = src.subset(start_ind, end_ind)
                score = self.similarity_obj.score(lic, src_subset)
                if (score <= score_to_keep):
                    start_ind += start_increment
                    end_ind -= end_increment
                    break
                # score improved
                else:
                    # keep the score and the index
                    score_to_keep = score
                    # pass to the next loop
            else:
                start_ind += start_increment
                end_ind -= end_increment
                break
        return start_ind, end_ind, score_to_keep


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
