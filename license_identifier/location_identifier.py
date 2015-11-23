import math

from . import n_grams as ng
from . import util


DEFAULT_THRESHOLD = 0.02

class Location_Finder:

    def __init__(self):
        pass

    def main_process(self, license_file, input_src_file, threshold=DEFAULT_THRESHOLD):
        # 1. configure the text window size
        [license_lines, license_offsets]= util.read_lines_offsets(license_file)
        [src_lines, src_offsets] = util.read_lines_offsets(input_src_file)

        window_size = len(license_lines)
        src_size = len(src_lines)

        license_n_grams = ng.n_grams(list_text_line=license_lines)

        # 2. split up the window and loop over the windows
        # for small source file case
        # TODO: check if they match & score
        [similarity_scores, window_start_index] = self.split_and_measure_similarities(src_size=src_size,
                                                                src_offsets=src_offsets,
                                                                src_lines=src_lines,
                                                                window_size=window_size,
                                                                license_n_grams=license_n_grams)

        # Find the window with maximum scores.
        [max_score, max_index] = self.find_max_score_ind(similarity_scores=similarity_scores)

        # Expand and find the region with maximum score
        return self.find_best_region(threshold= threshold,
                                     max_index = max_index,
                                     license_n_grams = license_n_grams,
                                     src_lines = src_lines,
                                     src_offsets = src_offsets,
                                     window_start_index = window_start_index,
                                     window_size = window_size)

    def find_best_region(self, threshold, max_index, license_n_grams,
                         src_lines, src_offsets, window_start_index, window_size):
        # for maximum scores that share the same value
        final_score = []
        start_index = []
        end_index =[]

        # find the region that has the best score (if a tie, pick the first)
        for max_ind in max_index:
            # 5. Expand until the line addition does not add any gain in similarity measure
            [s_ind, e_ind, final_s] = self.expand_window(license_n_grams,
                                                      src_lines,
                                                      window_start_index[max_ind],
                                                      window_size)
            start_index.append(s_ind)
            end_index.append(e_ind)
            final_score.append(final_s)
        max_score = max(final_score)
        max_index = [i for i, j in enumerate(final_score) if j == max_score]
        first_max_ind = max_index[0]

        if end_index[first_max_ind] > len(src_lines):
            end_index[first_max_ind] = len(src_lines)

        if max_score > threshold: # 0.02 is just randomly chosen low number
            self.print_license(src_lines, start_index[first_max_ind], end_index[first_max_ind])

        return start_index[first_max_ind],\
               end_index[first_max_ind], \
               src_offsets[start_index[first_max_ind]], \
               src_offsets[end_index[first_max_ind]], \
               final_score[first_max_ind]


    def find_max_score_ind(self, similarity_scores):
        max_score = max(similarity_scores)
        max_index = [i for i, j in enumerate(similarity_scores) if j == max_score]
        return max_score, max_index

    def split_and_measure_similarities(self, src_size, src_offsets, src_lines,
                                       window_size, license_n_grams):
        '''split up the window and loop over the windows
        for small source file case
        TODO: check if they match & score
        '''
        if (src_size <= window_size):
            return 0, src_size, \
                   src_offsets[0], src_offsets[src_size-1],\
                   self.measure_similarity(license_n_grams,
                                           src_lines, 0, src_size)
        else:
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
                similarity_score = self.measure_similarity(license_n_grams,
                                  src_lines, window_start_ind, window_end_ind)

                # keep track of the scores
                similarity_scores.append(similarity_score)

                # bookkeeping of the indices
                window_start_index.append(window_start_ind)

                # increment the indices for the next window
                window_start_ind += index_increment
                window_end_ind += index_increment
        return similarity_scores, window_start_index


    def print_license (self, src_lines, start_ind, end_ind):
        for line in src_lines[start_ind:end_ind]:
            print(line)

    def expand_window(self, license_n_grams, src_lines, start_ind, window_size):

        # find the baseline score
        end_ind = start_ind + window_size
        score_to_keep = self.measure_similarity(license_n_grams, src_lines,
                                                     start_ind, end_ind)
        # TODO: possibly use regular expression to find the start and end
        start_ind, end_ind, score_to_keep = self.expand_to_top(license_n_grams, src_lines, start_ind, end_ind, score_to_keep, 3)
        start_ind, end_ind, score_to_keep = self.expand_to_top(license_n_grams, src_lines, start_ind, end_ind, score_to_keep, 2)
        start_ind, end_ind, score_to_keep = self.expand_to_top(license_n_grams, src_lines, start_ind, end_ind, score_to_keep, 1)
        start_ind, end_ind, score_to_keep = self.expand_to_bottom(license_n_grams, src_lines, start_ind, end_ind, score_to_keep, 5)
        start_ind, end_ind, score_to_keep = self.expand_to_bottom(license_n_grams, src_lines, start_ind, end_ind, score_to_keep, 4)
        start_ind, end_ind, score_to_keep = self.expand_to_bottom(license_n_grams, src_lines, start_ind, end_ind, score_to_keep, 3)
        start_ind, end_ind, score_to_keep = self.expand_to_bottom(license_n_grams, src_lines, start_ind, end_ind, score_to_keep, 2)
        start_ind, end_ind, score_to_keep = self.expand_to_bottom(license_n_grams, src_lines, start_ind, end_ind, score_to_keep, 1)
        return start_ind, end_ind, score_to_keep

    def expand_to_top(self, license_n_grams, src_lines, start_ind, end_ind, score_to_keep, increment ):
        # expand to the lower area
        while True:
            start_ind -= increment

            if start_ind >= 0:
                score = self.measure_similarity(license_n_grams, src_lines,
                                                start_ind, end_ind)
                if (score <= score_to_keep):
                    start_ind += increment
                    break
                # score improved
                else:
                    # keep the score and the index
                    score_to_keep = score
                    # pass to the next loop
                    # print 'incrementing to bottom'
            else:
                start_ind += increment # end_ind = src_size
                break
        return start_ind, end_ind, score_to_keep


    def expand_to_bottom(self, license_n_grams, src_lines, start_ind, end_ind, score_to_keep, increment ):
        # expand to the lower area
        while True:
            end_ind += increment

            if end_ind < len(src_lines):
                score = self.measure_similarity(license_n_grams, src_lines,
                                                start_ind, end_ind)
                if (score <= score_to_keep):
                    end_ind -= increment
                    break
                # score improved
                else:
                    # keep the score and the index
                    score_to_keep = score
                    # pass to the next loop
                    # print 'incrementing to bottom'
            else:
                end_ind -= increment # end_ind = src_size
                break
        return start_ind, end_ind, score_to_keep

    def measure_similarity(self, other_n_grams, src_lines, start_ind, end_ind):
        list_text = src_lines[start_ind:end_ind]
        this_n_grams = ng.n_grams(list_text_line=list_text)
        return other_n_grams.measure_similarity(this_n_grams)

license_file_path = '/Users/phshin/work/git/phshin/analysis/license/data/license_dir/LGPL-2.0-license-PS.txt'
src_file_path = '/Users/phshin/work/git/phshin/analysis/license/data/scanner_evaluation_files-1.0.0/open_source/GNU_2.0/aswp401.qualcomm.com_deploy_qcom_qct_platform_wpci_prod_woa_performance_main_latest_Applications_Native_Spec2K_Spec2000_src_177.mesa_feedback.c'
lf = Location_Finder()
print ((lf.main_process(license_file_path, src_file_path)))