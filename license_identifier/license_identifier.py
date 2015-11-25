from os import listdir, walk, getcwd
from os.path import isfile, join, isdir, dirname
from collections import Counter, defaultdict
import sys
import argparse
import csv

from . import license_match
from . import n_grams as ng
from . import location_identifier as loc_id


DEFAULT_THRESH_HOLD=0.02
DEFAULT_LICENSE_DIR=join(getcwd(), "..", 'data','license_dir')

class license_identifier:
    def __init__(self, license_dir=DEFAULT_LICENSE_DIR,
                 threshold=DEFAULT_THRESH_HOLD,
                 input_path=None,
                 output_format=None,
                 output_path=None):
        self.license_dir = license_dir
        # holds n gram models for each license type
        #  used for matching input vs. each license
        self.license_n_grams = defaultdict()
        # holds n-gram models for all license types
        #  used for parsing input file words (only consider known words)
        self._universe_n_grams = ng.n_grams()
        self.license_file_name_list = self._get_license_file_names()
        self._build_n_gram_univ_license(self._universe_n_grams,
                                       self.license_n_grams,
                                       self.license_dir,
                                       self.license_file_name_list)
        if input_path:
            result_obj = self.analyze_input_path(input_path, threshold)
            self.format_output(result_obj, output_format, output_path=output_path)

    def format_output(self, result_obj, output_format, output_path):
        print('we are in this output format:{}'.format(output_format))
        import pdb; pdb.set_trace()
        if output_format == 'csv':
            self.write_csv_file(result_obj, output_path)
        elif output_format == 'license_match':
            pass
        elif output_format == 'easy_read':
            pass

    # TODO: add unicode output from unicode input (if necessary).
    def write_csv_file(self, result_obj_list, output_path):
        with open(output_path, 'wb') as f:
            writer = csv.writer(f)
            for (lm_res, sum_list_res) in result_obj_list:
                writer.writerows(lm_res)
        f.close()

    def _get_license_file_names(self):
        file_fp_list = [ f for f in listdir(self.license_dir) \
                           if isfile(join(self.license_dir,f)) and \
                           '.txt' in f ]
        return file_fp_list

    def _get_license_name(self, file_name):
        return file_name.split('.txt')[0]

    def _build_n_gram_univ_license(self, univ_ng, license_ng, license_dir, license_file_list):
        '''
        parses the license text file and builds n_gram models
        for each license type
          and
        for all license corpus combined
        '''
        for license_file_name in license_file_list:
            list_of_license_str = self.get_str_from_file(join(license_dir, license_file_name))
            license_name = self._get_license_name(license_file_name)
            univ_ng.parse_text_list_items(list_of_license_str)
            new_license_ng = ng.n_grams(list_text_line=list_of_license_str)
            license_ng[license_name] = new_license_ng

    def analyze_file(self, input_fp, threshold=DEFAULT_THRESH_HOLD):
        input_dir = dirname(input_fp)
        list_of_src_str = self.get_str_from_file(input_fp)
        my_file_ng = ng.n_grams()
        my_file_ng.parse_text_list_items(list_text_line=list_of_src_str,
                                         universe_ng=self._universe_n_grams)
        similarity_score_dict = self.measure_similarity(my_file_ng)
        [matched_license, score] = self.find_best_match(similarity_score_dict)

        if score >= threshold:
            [start_ind, end_ind, start_offset, end_offset, region_score] = \
                self.find_license_region(matched_license, input_fp)
            found_region = list_of_src_str[start_ind:end_ind]
            length = end_offset - start_offset + 1
            if region_score < threshold:
                matched_license = start_ind = start_offset = ''
                end_ind = end_offset = region_score = found_region = length = ''
        else:
            matched_license = start_ind = start_offset = ''
            end_ind = end_offset = region_score = found_region = length = ''
        lcs_match = license_match.LicenseMatch(file_name=input_fp,
                                file_path=input_fp,
                                license=matched_license,
                                start_byte=start_offset,
                                length = length)
        summary_list = [input_fp,
                        matched_license,
                        score,
                        start_ind,
                        end_ind,
                        start_offset,
                        end_offset,
                        region_score,
                        found_region]
        return [(lcs_match, summary_list)]

    def analyze_input_path(self, input_path, threshold=DEFAULT_THRESH_HOLD):
        if isdir(input_path):
            return self.apply_function_on_all_files(self.analyze_file, input_path, threshold=threshold)
        elif isfile(input_path):
            return self.analyze_file(input_path)
        else:
            raise OSError('Neither file nor directory{}'.format(input_path))

    def apply_function_on_all_files(self, function_ptr, top_dir_name, *args, **kwargs):
        list_of_result = []
        for root, dirs, files in walk(top_dir_name):
            for file in files:
                list_of_result.append(function_ptr(join(root, file), *args, **kwargs))
        return list_of_result

    def find_license_region(self, license_name, input_fp):
        license_fp = self.license_dir + '/' + license_name + '.txt'
        loc_finder = loc_id.Location_Finder()
        return loc_finder.main_process(license_fp, input_fp)

    def measure_similarity(self, input_ng):
        """
        Return the similarity measure.
        Assume that the license lookup is available.
        """
        similarity_dict = Counter()
        for license_name in self.license_n_grams:
            license_ng = self.license_n_grams[license_name]
            similarity_score = license_ng.measure_similarity(input_ng)
            similarity_dict[license_name] = similarity_score
        return similarity_dict

    def find_best_match(self, scores):
        license_found = max(scores, key=scores.get)
        max_val = scores[max(scores, key=scores.get)]
        return license_found, max_val

    def get_str_from_file(self, file_path):
        try:
            fp = open(file_path, encoding='ascii', errors='surrogateescape')
            list_of_str = fp.readlines()
            fp.close()
        except OSError as err:
            print('OS error: {0}'.format(err))
            list_of_str = None
        except:
            print(fp)
            print(sys.exc_info()[0])
            print(sys.exc_info())
            print()
            list_of_str = None
        return list_of_str

def main():
    # threshold, license folder, input file, input folder, output format
    aparse = argparse.ArgumentParser(
        description="License text identification and license text region finder")
    aparse.add_argument("-T", "--threshold",
                        default=DEFAULT_THRESH_HOLD,
                        help="threshold hold for similarity measure (ranging from 0 to 1)")
    aparse.add_argument("-L", "--license_folder",
                        help="Specify directory path where the license text files are",
                        default=join(getcwd(), 'data', 'license_dir'))
    aparse.add_argument("-I", "--input_path",
                        help="Specify directory or file path where the input source code files are",
                        default=join(getcwd(), 'data', 'test', 'data'),
                        required=True)
    aparse.add_argument("-O", "--output_path",
                        help="Specify a file name path where the result will be saved for csv file.",
                        default=join(getcwd(), 'output.csv'))
    aparse.add_argument("-F", "--output_format",
        help="Format the output accordingly", action="append",
        choices=["csv", "license_match", "easy_read"])
    args = aparse.parse_args()
    li_obj = license_identifier(license_dir=args.license_folder,
                                threshold=args.threshold,
                                input_path=args.input_path,
                                output_format=args.output_format,
                                output_path=args.output_path)

if __name__ == "__main__":
    main()