import math
import nltk
import difflib
import argparse

from . import location_result as lr
from . import n_grams as ng
from . import util


DEFAULT_CONTEXT = 0
DEFAULT_PENALTY_ONLY_SOURCE = 1.0
DEFAULT_PENALTY_ONLY_LICENSE = 50.0
DEFAULT_OVERSHOOT = 5
DEFAULT_STRATEGY = "one_line_then_expand"
DEFAULT_VERBOSITY = 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("license_file")
    parser.add_argument("input_src_file")
    parser.add_argument("-v", "--verbose", action="count", dest="verbosity")
    parser.add_argument("--context_lines", type=int)
    parser.add_argument("--strategy", default=DEFAULT_STRATEGY)
    parser.add_argument("--overshoot", type=int, default=DEFAULT_OVERSHOOT)
    parser.add_argument("--penalty_only_source", type=float,
        default=DEFAULT_PENALTY_ONLY_SOURCE)
    parser.add_argument("--penalty_only_license", type=float,
        default=DEFAULT_PENALTY_ONLY_LICENSE)
    args = parser.parse_args()
    loc_obj = Location_Finder(
        context_lines = args.context_lines,
        penalty_only_source = args.penalty_only_source,
        penalty_only_license = args.penalty_only_license,
        overshoot = args.overshoot,
        strategy = args.strategy,
        verbosity = args.verbosity)
    print loc_obj.main_process(args.license_file, args.input_src_file)


class Location_Finder(object):

    def __init__(self,
            context_lines = DEFAULT_CONTEXT,
            penalty_only_source = DEFAULT_PENALTY_ONLY_SOURCE,
            penalty_only_license = DEFAULT_PENALTY_ONLY_LICENSE,
            overshoot = DEFAULT_OVERSHOOT,
            strategy = DEFAULT_STRATEGY,
            verbosity = DEFAULT_VERBOSITY):
        self.context_lines = context_lines
        self.penalty_only_source = penalty_only_source
        self.penalty_only_license = penalty_only_license
        self.overshoot = overshoot
        self.strategy = strategy
        self.verbosity = verbosity

    def main_process(self, license_file, input_src_file):
        license_lines, license_offsets = util.read_lines_offsets(license_file)
        src_lines, src_offsets = util.read_lines_offsets(input_src_file)

        if self.strategy == "exhaustive":
            start_line, end_line, best_score = \
                self.best_region_exhaustive(license_lines, src_lines)
        elif self.strategy == "one_line_then_expand":
            start_line, end_line, best_score = \
                self.one_line_then_expand(license_lines, src_lines)
        elif self.strategy == "ngram":
            start_line, end_line, best_score = \
                self.best_region_ngram(license_lines, src_lines)
        else:
            raise Exception("Unrecognized strategy: {}".format(self.strategy))

        start_line, end_line, start_offset, end_offset = \
            self.determine_offsets(start_line, end_line, src_lines, src_offsets)

        return lr.LocationResult(
            start_line = start_line,
            end_line = end_line,
            start_offset = start_offset,
            end_offset = end_offset,
            score = best_score)

    def best_region_exhaustive(self, license_lines, src_lines):
        results = []
        for start_line in range(len(src_lines)):
            for end_line in range(start_line + 1, len(src_lines)):
                score = self.measure_similarity_difflib(
                    other_lines = license_lines,
                    src_lines = src_lines,
                    start_ind = start_line,
                    end_ind = end_line)
                results.append((start_line, end_line, score))

        if self.verbosity >= 1:
            sorted_results = sorted(results, key = lambda x: x[2])
            for r in sorted_results:
                print "lines {}-{}: score = {:.06f}".format(*r)
            print "=" * 40

        start_line, end_line, best_score = max(results, key = lambda x: x[2])
        return start_line, end_line, best_score

    def one_line_then_expand(self, license_lines, src_lines):
        # First, find best single line
        results = []
        for line in range(len(src_lines)):
            score = self.measure_similarity_difflib(
                    other_lines = license_lines,
                    src_lines = src_lines,
                    start_ind = line,
                    end_ind = line + 1)
            results.append((line, line + 1, score))

        if self.verbosity >= 1:
            sorted_results = sorted(results, key = lambda x: x[2])
            for r in sorted_results:
                print "lines {}-{}: score = {:.06f}".format(*r)
            print "=" * 40

        start_line, end_line, best_score = max(results, key = lambda x: x[2])
        prev_start_line, prev_end_line = None, None

        # Alternate between expanding region upward and downward
        # until the selected region no longer changes
        while True:
            if self.verbosity >= 1:
                print "Current region: {}-{}".format(start_line, end_line)

            # Expand region upward
            start_line, end_line, best_score = self.expand_difflib(
                license_lines, src_lines,
                start_line, end_line, best_score, top = True)

            if self.verbosity >= 1:
                print "Current region: {}-{}".format(start_line, end_line)

            # Expand region downward
            start_line, end_line, best_score = self.expand_difflib(
                license_lines, src_lines,
                start_line, end_line, best_score, top = False)

            if start_line == prev_start_line and end_line == prev_end_line:
                break

            prev_start_line = start_line
            prev_end_line = end_line

        return start_line, end_line, best_score

    def expand_difflib(self, license_lines, src_lines,
            start_line, end_line, score_to_beat, top):
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
            if start_line < 0: break
            if end_line > len(src_lines): break
            if overshoot_remaining <= 0: break

            start_line, end_line = update(start_line, end_line)
            score = self.measure_similarity_difflib(
                    other_lines = license_lines,
                    src_lines = src_lines,
                    start_ind = start_line,
                    end_ind = end_line)

            current_result = (start_line, end_line, score)
            results.append(current_result)
            if self.verbosity >= 1:
                print "Considering expansion (top = {}): {}-{}: score = {}" \
                    .format(top, *current_result)

            if score >= best_score:
                best_start_line = start_line
                best_end_line = end_line
                best_score = score
                overshoot_remaining = self.overshoot  # reset overshoot
            else:
                overshoot_remaining -= 1

        return best_start_line, best_end_line, best_score

    def best_region_ngram(self, license_lines, src_lines):
        # 1. configure the text window size
        window_size = len(license_lines)
        src_size = len(src_lines)

        license_n_grams = ng.n_grams(license_lines)

        # 2. split up the window and loop over the windows
        # for small source file case
        # TODO: check if they match & score
        [similarity_scores, window_start_index] = \
            self.split_and_measure_similarities(
                src_size = src_size,
                src_lines = src_lines,
                window_size = window_size,
                license_n_grams = license_n_grams)

        # Find the window with maximum scores.
        [max_score, max_index] = self.find_max_score_ind(similarity_scores)

        # Expand and find the region with maximum score
        return self.find_best_region(
            max_index = max_index,
            license_n_grams = license_n_grams,
            src_lines = src_lines,
            window_start_index = window_start_index,
            window_size = window_size)

    def find_best_region(self, max_index, license_n_grams,
                         src_lines, window_start_index, window_size):
        # for maximum scores that share the same value
        final_score = []
        start_index = []
        end_index =[]

        # find the region that has the best score (if a tie, pick the first)
        for max_ind in max_index:
            # 5. Expand until the line addition does not add any gain in similarity measure
            [s_ind, e_ind, final_s] = self.expand_window(
                license_n_grams = license_n_grams,
                src_lines = src_lines,
                start_ind = window_start_index[max_ind],
                window_size = window_size)
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

    def split_and_measure_similarities(self, src_size, src_lines,
            window_size, license_n_grams):
        '''split up the window and loop over the windows
        for small source file case
        TODO: check if they match & score
        '''
        window_start_ind = 0
        window_end_ind = window_size

        similarity_scores = []
        window_start_index = []

        index_increment = math.floor(window_size / 2)

        if index_increment == 0:
            index_increment = 1
        while (window_start_ind < src_size):
            # create the sliding window
            # 3. find the similarity measure for each window
            similarity_score = self.measure_similarity(
                license_n_grams, src_lines, window_start_ind, window_end_ind)

            # keep track of the scores
            similarity_scores.append(similarity_score)

            # bookkeeping of the indices
            window_start_index.append(window_start_ind)

            # increment the indices for the next window
            window_start_ind += index_increment
            window_end_ind += index_increment
        return similarity_scores, window_start_index


    def expand_window(self, license_n_grams, src_lines, start_ind, window_size):

        # find the baseline score
        end_ind = start_ind + window_size
        score_to_keep = self.measure_similarity(
            license_n_grams, src_lines, start_ind, end_ind)
        # TODO: possibly use regular expression to find the start and end
        for increment in [3, 2, 1]:
            start_ind, end_ind, score_to_keep = self.expand_generic(
                license_n_grams, src_lines, start_ind, end_ind,
                score_to_keep, start_increment = increment, end_increment = 0)
        for increment in [5, 4, 3, 2, 1]:
            start_ind, end_ind, score_to_keep = self.expand_generic(
                license_n_grams, src_lines, start_ind, end_ind,
                score_to_keep, start_increment = 0, end_increment = increment)
        return int(start_ind), int(end_ind), score_to_keep

    def expand_generic(self, license_n_grams, src_lines, start_ind, end_ind,
            score_to_keep, start_increment, end_increment):
        assert start_increment >= 0 and end_increment >= 0, \
            "Cannot use negative increments"
        assert start_increment != 0 or end_increment != 0, \
            "Start and end increments are both zero"
        while True:
            start_ind -= start_increment
            end_ind += end_increment

            if start_ind >= 0 and end_ind < len(src_lines):

                score = self.measure_similarity(license_n_grams, src_lines,
                                                start_ind, end_ind)
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
        return int(start_ind), int(end_ind), score_to_keep

    def measure_similarity_difflib(self, other_lines, src_lines, start_ind, end_ind):
        list_text = src_lines[int(start_ind):int(end_ind)]

        tok = nltk.tokenize.WordPunctTokenizer()
        this_tokens = tok.tokenize('\n'.join(list_text))
        other_tokens = tok.tokenize('\n'.join(other_lines))

        matcher = difflib.SequenceMatcher(
            isjunk = None,
            a = this_tokens,
            b = other_tokens,
            autojunk = False)

        unchanged = 0.0
        changed = 0.0
        for op, ts1, te1, ts2, te2 in matcher.get_opcodes():
            num_tokens_this  = te1 - ts1
            num_tokens_other = te2 - ts2
            if op == "equal":
                unchanged += num_tokens_this
            else:
                changed += \
                    self.penalty_only_source * num_tokens_this + \
                    self.penalty_only_license * num_tokens_other

        similarity = unchanged / (changed + unchanged)
        return similarity

    def measure_similarity(self, other_n_grams, src_lines, start_ind, end_ind):
        list_text = src_lines[int(start_ind):int(end_ind)]
        this_n_grams = ng.n_grams(list_text)
        return other_n_grams.measure_similarity(this_n_grams)

if __name__ == "__main__":
    main()

