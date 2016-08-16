from os.path import isfile, join, isdir, dirname, splitext
from collections import OrderedDict
from contextlib import closing
import multiprocessing
import sys
import argparse
import csv
import codecs
import logging

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

DEFAULT_THRESHOLD = 0.04
DEFAULT_PICKLED_LIBRARY_FILE = join(base_dir, 'data',
                               'license_n_gram_lib.pickle')
DEFAULT_KEEP_FRACTION_OF_BEST = 0.9

# Use a global license library, as a workaround to improve multiprocessing
# performance.
# TODO: Find a better way to share the license library between workers
#       (ideally avoiding global objects).
# For ideas, see https://docs.python.org/2/library/multiprocessing.html#sharing-state-between-processes
_license_library = None

# Set up a logger for this module
_logger_name = "main" if __name__ == "__main__" else __name__
_logger = logging.getLogger(name = _logger_name)
# Add a NullHandler so that client apps aren't forced to see all log messages
_logger.addHandler(logging.NullHandler())

class LicenseIdentifier:
    def __init__(
            self,
            threshold=DEFAULT_THRESHOLD,
            input_path=None,
            output_format=None,
            output_path='',
            license_dir = None,
            context_length = 0,
            location_strategy=None,
            location_similarity=None,
            penalty_only_source=None,
            penalty_only_license=None,
            keep_fraction_of_best=DEFAULT_KEEP_FRACTION_OF_BEST,
            pickle_file_path=None,
            run_in_parellal=True,
            original_matched_text_flag=False):

        self.threshold = threshold
        self.context_length = context_length
        self.input_path = input_path
        self.output_format = output_format
        self.run_in_parellal = run_in_parellal
        self.location_strategy = location_strategy
        self.location_similarity = location_similarity
        self.penalty_only_source = penalty_only_source
        self.penalty_only_license = penalty_only_license
        self.keep_fraction_of_best = self._check_keep_fraction_of_best(keep_fraction_of_best)
        self.original_matched_text_flag = original_matched_text_flag

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

    def _check_keep_fraction_of_best(self, keep_fraction_of_best):
        assert keep_fraction_of_best >= 0.0
        assert keep_fraction_of_best <= 1.0
        return keep_fraction_of_best

    def analyze(self):
        if self.input_path is not None:
            return self.analyze_input_path(self.input_path)
        else:
            _logger.info("No input path; no analysis to perform")
            return None

    def output(self, result_obj):
        self.format_output(result_obj, self.output_format, output_path=self.output_path)

    def _init_pickled_library(self, pickle_file_path):
        global _license_library
        _logger.info("Loading license library from {}".format(pickle_file_path))
        _license_library = prep.LicenseLibrary.deserialize(pickle_file_path)

    def _init_using_lic_dir(self, license_dir):
        global _license_library
        _logger.info("Loading license library from {}".format(license_dir))
        _license_library = prep.LicenseLibrary.from_path(license_dir)

    def _create_pickled_library(self, pickle_file):
        _logger.info("Saving license library to {}".format(pickle_file))
        _license_library.serialize(pickle_file)

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
        field_names = match_summary.MatchSummary.field_names().values()
        if not self.original_matched_text_flag:
            field_names.remove("Matched license text without context")
        writer.writerow(field_names)
        for result_obj in result_obj_list:
            row = result_obj[1].to_csv_row()
            writer.writerow(row)
        f.close()

    def display_easy_read(self, result_obj_list):
        for result_obj in result_obj_list:
            print(result_obj[1].to_display_format())

    def analyze_file(self, input_fp):
        # Consider only the top matching licenses
        src = prep.Source.from_filename(input_fp)
        top_candidates = self.get_top_candidates(src)

        if len(top_candidates) == 0:
            lcs_match = license_match.LicenseMatch(
                file_name = input_fp,
                file_path = input_fp,
                license = '',
                start_byte = '',
                length = '')
            summary_obj = match_summary.MatchSummary(
                input_fp = input_fp,
                matched_license = '',
                score = '',
                start_line_ind = '',
                end_line_ind = '',
                start_offset = '',
                end_offset = '',
                region_score = '',
                original_region = '',
                found_region = '')
            return lcs_match, summary_obj

        # Search for best matching region for each of the top candidates
        region_results = []
        for lic_name, orig_score in top_candidates.items():
            lic = _license_library.licenses[lic_name]
            result = self.find_license_region(lic, src)
            region_results.append((lic_name, orig_score, result))

        matched_license, orig_score, best_region = max(region_results, key = lambda x: x[2].score)

        length = best_region.end_offset - best_region.start_offset + 1
        found_region_lines = src.lines[best_region.start_line : best_region.end_line]

        original_region_lines = found_region_lines[self.context_length : len(found_region_lines)- self.context_length]

        original_region = '\n'.join(original_region_lines) + '\n'
        found_region = '\n'.join(found_region_lines) + '\n'

        lcs_match = license_match.LicenseMatch(
            file_name = input_fp,
            file_path = input_fp,
            license = matched_license,
            start_byte = best_region.start_offset,
            length = length)
        summary_obj = match_summary.MatchSummary(
            input_fp = input_fp,
            matched_license = matched_license,
            score = orig_score,
            start_line_ind = best_region.start_line,
            end_line_ind = best_region.end_line,
            start_offset = best_region.start_offset,
            end_offset = best_region.end_offset,
            region_score = best_region.score,
            found_region = found_region,
            original_region = original_region)

        if not self.original_matched_text_flag:
            summary_obj.pop("original_region")

        return lcs_match, summary_obj

    def postprocess_strip_off_comments(self, result_obj):
        for res in result_obj:
            input_fp = res[1]["input_fp"]
            matched_license = res[1]["matched_license"]
            score = res[1]["score"]
            start_ind = res[1]["start_line_ind"]
            end_ind = res[1]["end_line_ind"]
            list_of_src_str = self.get_str_from_file(input_fp)
            if matched_license and score >= self.threshold:
                _, ext = splitext(input_fp)
                lang = language.extension_to_lang_map.get(ext, None)
                if lang:                    
                    stripped_file_lines = \
                        list(comment_parser.parse_file(lang, list_of_src_str))
                else:
                    stripped_file_lines = list_of_src_str
                stripped_region = ''.join(stripped_file_lines[start_ind:end_ind])
            else:
                stripped_region = '' 
            res[1]["stripped_region"] = stripped_region
        return result_obj

    def analyze_file_lcs_match_output(self, input_fp):
        lcs_match, summary_obj = self.analyze_file(input_fp)
        return lcs_match

    def analyze_input_path(self, input_path):
        if isdir(input_path):
            return self.apply_function_on_all_files(analyze, input_path)
        elif isfile(input_path):
            return [self.analyze_file(input_path)]
        else:  # pragma: no cover
            raise OSError('Neither file nor directory{}'.format(input_path))

    def analyze_input_path_lcs_match_output(self, input_path):
        if isdir(input_path):
            return self.apply_function_on_all_files(analyze_lcs_match, input_path)
        elif isfile(input_path):
            return [self.analyze_file_lcs_match_output(input_path)]
        else:  # pragma: no cover
            raise OSError('Neither file nor directory{}'.format(input_path))

    def apply_function_on_all_files(self, function_ptr, top_dir_name):
        list_of_result = []
        with closing(multiprocessing.Pool()) as pool:
            apply_func = self.run_in_parellal and pool.apply_async or apply_sync
            for f in util.files_from_path(top_dir_name):
                list_of_result.append(apply_func(function_ptr, [self, f]))
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

    def get_top_candidates(self, src):
        # First, compute n-grams for all lines in the source file
        src_ng = ng.n_grams()
        src_ng.parse_text_list_items(src.lines, universe_ng = _license_library.universe_n_grams)

        # Measure n-gram similarity relative to all licenses in the library
        similarity_dict = OrderedDict()
        for license_name, lic in _license_library.licenses.items():
            similarity_score = lic.n_grams.measure_similarity(src_ng)
            similarity_dict[license_name] = similarity_score

        # Filter out low-scoring licenses
        best_score = max(similarity_dict.values())
        current_threshold = max(self.threshold, best_score * self.keep_fraction_of_best)

        top_candidates = OrderedDict()
        for license_name, score in similarity_dict.items():
            if score >= current_threshold:
                top_candidates[license_name] = score
        return top_candidates

    def get_str_from_file(self, file_path):
        fp = codecs.open(file_path, encoding='ascii', errors='surrogateescape')
        list_of_str = fp.readlines()
        fp.close()
        return list_of_str

def main(argv = []):
    aparse = argparse.ArgumentParser(
        description="License text identification and license text region finder")
    aparse.add_argument(
        "-T", "--threshold",
        default=DEFAULT_THRESHOLD,
        help="threshold for similarity measure (ranging from 0 to 1)")
    aparse.add_argument(
        "-L", "--license_folder",
        help="Specify directory path where the license text files are")
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
    aparse.add_argument(
        "--keep_fraction_of_best",
        help="Look for the best-matching source region for any license with similarity score >= (this fraction) * (best score)",
        default=DEFAULT_KEEP_FRACTION_OF_BEST,
        type=float)
    aparse.add_argument("--log",
        help="Logging level (for example: DEBUG, INFO, WARNING)",
        default="INFO")
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
    aparse.add_argument("--matched_text_without_context",
        help="Show matched license text without context",
        action='store_true',
        default=False)
    args = aparse.parse_args(argv)

    if args.input_path is not None and args.output_format is None:
        # Use easy_read as the default output format, but only
        # if a source-code analysis will be run
        args.output_format = 'easy_read'

    numeric_logging_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_logging_level, int):  # pragma: no cover
        raise ValueError("Invalid log level: {}".format(args.log))
    logging.basicConfig(level = numeric_logging_level)

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
                               keep_fraction_of_best=args.keep_fraction_of_best,
                               run_in_parellal=not args.single_thread,
                               original_matched_text_flag=args.matched_text_without_context)

    results = li_obj.analyze()
    li_obj.output(results)

def analyze(lid_obj, input_path):
    return lid_obj.analyze_input_path(input_path)

def analyze_lcs_match(lid_obj, input_path):
    return lid_obj.analyze_input_path_lcs_match_output(input_path)

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
