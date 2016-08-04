from os.path import isfile, join, isdir, dirname, splitext
from collections import OrderedDict
from contextlib import closing
import multiprocessing
import sys
import argparse
import csv
import codecs
import pickle

from . import license_match
from . import match_summary
from . import n_grams as ng
from . import location_identifier as loc_id
from . import util
from . import prep
from comment_parser import language
import comment_parser

from future.utils.surrogateescape import register_surrogateescape

register_surrogateescape()

base_dir = dirname(__file__)

DEFAULT_THRESH_HOLD = 0.04
DEFAULT_LICENSE_DIR = join(base_dir, 'data', 'license_dir')
DEFAULT_PICKLED_LIBRARY_FILE = join(base_dir, 'data',
                               'license_n_gram_lib.pickle')

# Use a global license library, as a workaround to improve multiprocessing
# performance.
# TODO: Find a better way to share the license library between workers
#       (ideally avoiding global objects).
# For ideas, see https://docs.python.org/2/library/multiprocessing.html#sharing-state-between-processes
_license_library = None

class LicenseIdentifier:
    def __init__(
            self,
            threshold=DEFAULT_THRESH_HOLD,
            input_path=None,
            output_format=None,
            output_path='',
            license_dir = None,
            context_length = None,
            location_strategy=None,
            location_similarity=None,
            penalty_only_source=None,
            penalty_only_license=None,
            pickle_file_path=None,
            run_in_parellal=True):

        self.threshold = threshold
        self.context_length = context_length
        self.input_path = input_path
        self.output_format = output_format
        self.run_in_parellal = run_in_parellal
        self.location_strategy = location_strategy
        self.location_similarity = location_similarity
        self.penalty_only_source = penalty_only_source
        self.penalty_only_license = penalty_only_license

        if output_path:
            self.output_path = output_path + '_' + util.get_user_date_time_str() + '.csv'
        else:
            self.output_path = None

        # Use pickled library
        if license_dir is None:
            if pickle_file_path is None:
                pickle_file_path = DEFAULT_PICKLED_LIBRARY_FILE
            self._init_pickled_library(pickle_file_path)
        else:
            self._init_using_lic_dir(license_dir)
            if pickle_file_path is not None:
                self._create_pickled_library(pickle_file_path)

    def analyze(self):
        if self.input_path is not None:
            return self.analyze_input_path(self.input_path, self.threshold)
        else:
            print "No input path; no analysis to perform"
            return None

    def output(self, result_obj):
        self.format_output(result_obj, self.output_format, output_path=self.output_path)

    def _init_pickled_library(self, pickle_file_path):
        global _license_library
        with open(pickle_file_path, 'rb') as f:
            _license_library = pickle.load(f)
        # Sanity check: make sure we're not opening an old pickle file
        assert isinstance(_license_library, prep.LicenseLibrary)

    def _init_using_lic_dir(self, license_dir):
        global _license_library
        _license_library = prep.LicenseLibrary.from_path(license_dir)

    def _create_pickled_library(self, pickle_file):
        with open(pickle_file, 'wb') as f:
            pickle.dump(_license_library, f)

    def format_output(self, result_obj, output_format, output_path):
        if output_format == 'csv':
            self.write_csv_file(result_obj, output_path)
        elif output_format == 'easy_read':
            self.display_easy_read(result_obj)
        elif output_format is None:
            pass
        else:  # pragma: no cover
            raise Exception("Unrecognized output format: {}".format(output_format))

    def write_csv_file(self, result_obj_list, output_path):
        if sys.version_info >= (3,0,0):  # pragma: no cover
            f = open(output_path, 'w', newline='')
        else:  # pragma: no cover
            f = open(output_path, 'wb')
        writer = csv.writer(f)
        writer.writerow(match_summary.MatchSummary.field_names())
        for result_obj in result_obj_list:
            row = result_obj[1].to_csv_row()
            writer.writerow(row)
        f.close()

    def display_easy_read(self, result_obj_list):
        for result_obj in result_obj_list:
            print(result_obj[1].to_display_format())

    def analyze_file(self, input_fp, threshold=DEFAULT_THRESH_HOLD):
        src = prep.Source.from_filename(input_fp)
        similarity_score_dict = self.measure_similarity(src)
        matched_license, score = max(similarity_score_dict.items(), key = lambda x: x[1])
        lic = _license_library.licenses[matched_license]

        if score >= threshold:
            [start_line_ind, end_line_ind, start_offset, end_offset, region_score] = \
                self.find_license_region(lic, src)
            found_region = src.lines[start_line_ind:end_line_ind]
            found_region = '\n'.join(found_region) + '\n'
            length = end_offset - start_offset + 1
            if region_score < threshold:
                matched_license = start_line_ind = start_offset = ''
                end_line_ind = end_offset = region_score = found_region = length = ''
        else:
            matched_license = start_line_ind = start_offset = ''
            end_line_ind = end_offset = region_score = found_region = length = ''
        lcs_match = license_match.LicenseMatch(file_name=input_fp,
                                file_path=input_fp,
                                license=matched_license,
                                start_byte=start_offset,
                                length = length)
        summary_obj = match_summary.MatchSummary(
            input_fp = input_fp,
            matched_license = matched_license,
            score = score,
            start_line_ind = start_line_ind,
            end_line_ind = end_line_ind,
            start_offset = start_offset,
            end_offset = end_offset,
            region_score = region_score,
            found_region = found_region)
        return lcs_match, summary_obj

    def postprocess_strip_off_comments(self, result_obj, threshold=DEFAULT_THRESH_HOLD):
        for res in result_obj:
            input_fp = res[1][0]
            matched_license = res[1][1]
            score = res[1][2]
            list_of_src_str = self.get_str_from_file(input_fp)
            if matched_license and score >= threshold:
                _, ext = splitext(input_fp)
                lang = language.extension_to_lang_map.get(ext, None)
                if lang:                    
                    stripped_file_lines = \
                        list(comment_parser.parse_file(lang, list_of_src_str))
                else:
                    stripped_file_lines = list_of_src_str
                [start_ind, end_ind, start_offset, end_offset, region_score] = \
                        self.find_license_region(matched_license, input_fp)
                stripped_region = stripped_file_lines[start_ind:end_ind]
                stripped_region = ''.join(stripped_region)
                if region_score < threshold:
                    stripped_region  = ''
            else:
                stripped_region = '' 
            res[1].append(stripped_region)
        return result_obj

    def analyze_file_lcs_match_output(self, input_fp, threshold=DEFAULT_THRESH_HOLD):
        lcs_match, summary_obj = self.analyze_file(input_fp, threshold)
        return lcs_match

    def analyze_input_path(self, input_path, threshold=DEFAULT_THRESH_HOLD):
        if isdir(input_path):
            return self.apply_function_on_all_files(analyze, input_path, threshold)
        elif isfile(input_path):
            return [self.analyze_file(input_path, threshold)]
        else:  # pragma: no cover
            raise OSError('Neither file nor directory{}'.format(input_path))

    def analyze_input_path_lcs_match_output(self, input_path, threshold=DEFAULT_THRESH_HOLD):
        if isdir(input_path):
            return self.apply_function_on_all_files(analyze_lcs_match, input_path, threshold)
        elif isfile(input_path):
            return [self.analyze_file_lcs_match_output(input_path, threshold)]
        else:  # pragma: no cover
            raise OSError('Neither file nor directory{}'.format(input_path))


    def apply_function_on_all_files(self, function_ptr, top_dir_name, threshold):
        list_of_result = []
        with closing(multiprocessing.Pool()) as pool:
            apply_func = self.run_in_parellal and pool.apply_async or apply_sync
            for f in util.files_from_path(top_dir_name):
                list_of_result.append(apply_func(function_ptr, [self, f, threshold]))
        output = []
        for entry in list_of_result:
            output += entry.get()
        return output

    def find_license_region(self, lic, src):
        # Pass along only the location args that were explicitly specified
        loc_args_raw = dict(
            context_lines = self.context_length,
            strategy = self.location_strategy,
            similarity = self.location_similarity,
            penalty_only_source = self.penalty_only_source,
            penalty_only_license = self.penalty_only_license,
        )
        loc_args = { k: v for k, v in loc_args_raw.items() if v is not None }

        loc_finder = loc_id.Location_Finder(**loc_args)
        return loc_finder.main_process(lic, src)

    def measure_similarity(self, src):
        """
        Return the similarity measure.
        Assume that the license lookup is available.
        """
        # First, compute n-grams for all lines in the source file
        src_ng = ng.n_grams()
        src_ng.parse_text_list_items(src.lines, universe_ng = _license_library.universe_n_grams)

        similarity_dict = OrderedDict()
        for license_name, lic in _license_library.licenses.items():
            similarity_score = lic.n_grams.measure_similarity(src_ng)
            similarity_dict[license_name] = similarity_score
        return similarity_dict

    def get_str_from_file(self, file_path):
        fp = codecs.open(file_path, encoding='ascii', errors='surrogateescape')
        list_of_str = fp.readlines()
        fp.close()
        return list_of_str

def main(argv = []):
    # threshold, license folder, input file, input folder, output format
    aparse = argparse.ArgumentParser(
        description="License text identification and license text region finder")
    aparse.add_argument(
        "-T", "--threshold",
        default=DEFAULT_THRESH_HOLD,
        help="threshold hold for similarity measure (ranging from 0 to 1)")
    aparse.add_argument(
        "-L", "--license_folder",
        help="Specify directory path where the license text files are",
        default=DEFAULT_LICENSE_DIR)
    aparse.add_argument(
        "-C", "--context",
        help="Specify an amount of context to add to the license text output",
        default=0, type=int)
    aparse.add_argument(
        "-P", "--pickle_file_path",
        help="Specify the name of the pickle file where license template library will be saved.",
        default=None)
    aparse.add_argument(
        "-I", "--input_path",
        help="Specify directory or file path where the input source code files are",
        required=False)
    aparse.add_argument(
        "-F", "--output_format",
        help="Format the output accordingly",
        choices=["csv", "easy_read"])
    aparse.add_argument(
        "-O", "--output_file_path",
        help="Specify a output path with data info (user name, date, time and .csv info will be automatically added).",
        default=None)
    aparse.add_argument(
        "-S", "--single_thread",
        help="Run as a single thread",
        action='store_true',
        default=False)
    aparse.add_argument("--location_strategy",
        help=argparse.SUPPRESS)
    aparse.add_argument("--location_similarity",
        help=argparse.SUPPRESS)
    aparse.add_argument("--penalty_only_source",
        help=argparse.SUPPRESS,
        type=float)
    aparse.add_argument("--penalty_only_license",
        help=argparse.SUPPRESS,
        type=float)
    args = aparse.parse_args(argv)
    if args.input_path is not None and args.output_format is None:
        # Use easy_read as the default output format, but only
        # if a source-code analysis will be run
        args.output_format = 'easy_read'
    li_obj = LicenseIdentifier(license_dir=args.license_folder,
                                threshold=float(args.threshold),
                                input_path=args.input_path,
                                output_format=args.output_format,
                                output_path=args.output_file_path,
                                context_length=args.context,
                                location_strategy=args.location_strategy,
                                penalty_only_source=args.penalty_only_source,
                                penalty_only_license=args.penalty_only_license,
                                pickle_file_path=args.pickle_file_path,
                                run_in_parellal=not args.single_thread)
    results = li_obj.analyze()
    li_obj.output(results)

def analyze(lid_obj, input_path, threshold):
    return lid_obj.analyze_input_path(input_path, threshold)

def analyze_lcs_match(lid_obj, input_path, threshold):
    return lid_obj.analyze_input_path_lcs_match_output(input_path, threshold)

class SyncResult(object):
    """Mimic the interface of multiprocessing.pool.AsyncResult"""
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

def apply_sync(f, args):
    """Behave like multiprocessing.pool.apply_async, but run synchronously"""
    return SyncResult(f(*args))

if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
