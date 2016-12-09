import logging
import multiprocessing
from collections import OrderedDict
from contextlib import closing
from os.path import dirname, join, splitext

import ntpath
from future.utils.surrogateescape import register_surrogateescape
from future.utils import iteritems

import comment_parser
from comment_parser import language

from . import location_identifier
from . import match_summary
from . import n_grams
from . import prep
from . import util


register_surrogateescape()

base_dir = dirname(__file__)

DEFAULT_THRESHOLD = 0.04
DEFAULT_PICKLED_LIBRARY_FILE = join(base_dir, 'data',
                                    'license_n_gram_lib.pickle')
DEFAULT_KEEP_FRACTION_OF_BEST = 0.9

# Use a global "registry" of license libraries, as a workaround to improve
# multiprocessing performance.

# TODO: Find a better way to share the license library between workers
# (ideally avoiding global objects).
# For ideas, see:
# https://docs.python.org/2/library/multiprocessing.html#sharing-state-between-processes

_license_library_registry = dict()

# Set up a logger for this module
_logger = logging.getLogger(name=__name__)

# Add a NullHandler so that client apps aren't forced to see all log messages
_logger.addHandler(logging.NullHandler())


class LicenseIdentifier:

    def __init__(self,
                 threshold=DEFAULT_THRESHOLD,
                 input_path=None,
                 license_library=None,
                 license_dir=None,
                 context_length=0,
                 cpu_count=multiprocessing.cpu_count(),
                 location_strategy=None,
                 location_similarity=None,
                 penalty_only_source=None,
                 penalty_only_license=None,
                 punct_weight=None,
                 keep_fraction_of_best=DEFAULT_KEEP_FRACTION_OF_BEST,
                 pickle_file_path=None,
                 run_in_parallel=True,
                 original_matched_text_flag=False):

        self.threshold = threshold
        self.context_length = context_length
        self.input_path = input_path
        self.run_in_parallel = run_in_parallel
        self.cpu_count=cpu_count
        self.location_strategy = location_strategy
        self.location_similarity = location_similarity
        self.penalty_only_source = penalty_only_source
        self.penalty_only_license = penalty_only_license
        self.punct_weight = punct_weight
        self.keep_fraction_of_best = \
            self._check_keep_fraction_of_best(keep_fraction_of_best)
        self.original_matched_text_flag = original_matched_text_flag

        if license_library is not None:
            self._init_using_library_object(license_library)
        elif license_dir is None:
            # Use pickled library
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

    def _set_license_library(self, license_library):
        global _license_library_registry

        ref = id(license_library)
        self.license_library_ref = ref

        if ref not in _license_library_registry:
            _license_library_registry[ref] = license_library

    def _init_using_library_object(self, license_library):
        _logger.info("Using given license library")
        self._set_license_library(license_library)

    def _init_pickled_library(self, pickle_file_path):
        _logger.info("Loading license library from {}".
                     format(pickle_file_path))
        license_library = prep.LicenseLibrary.deserialize(pickle_file_path)
        self._set_license_library(license_library)

    def _init_using_lic_dir(self, license_dir):
        _logger.info("Loading license library from {}".format(license_dir))
        license_library = prep.LicenseLibrary.from_path(license_dir)
        self._set_license_library(license_library)

    def _create_pickled_library(self, pickle_file):
        _logger.info("Saving license library to {}".format(pickle_file))
        self.license_library.serialize(pickle_file)

    def _get_license_library(self):
        """Deprecated - remove once Andrew's app no longer depends on it."""
        return self.license_library

    @property
    def license_library(self):
        return _license_library_registry[self.license_library_ref]

    def analyze(self):
        if self.input_path is not None:
            results = self.analyze_input_path(self.input_path)
        else:
            _logger.info("No input path; no analysis to perform")
            results = None

        return results

    def analyze_input_path(self, input_path):
        return self.apply_function_on_all_files(_analyze_file, input_path)

    def apply_function_on_all_files(self, function_ptr, top_dir_name):
        with closing(multiprocessing.Pool(processes=self.cpu_count)) as pool:
            apply_func = self.run_in_parallel and \
                pool.apply_async or apply_sync

            filenames = util.files_from_path(top_dir_name)
            results = [(x, apply_func(function_ptr, [self, x]))
                       for x in filenames]

            output = OrderedDict()
            for filename, result in results:
                output[filename] = result.get()

        return output

    def analyze_files(self, filepaths):
        """
        Find licenses within each source file for the passed-in filepaths.
        """
        return [self.analyze_file(x) for x in filepaths]

    def analyze_file(self, filepath):
        """
        Find licenses within a source file (or within a subset of a file).
        """
        source_file = prep.Source.from_filepath(filepath)

        return self.analyze_source(source_file)

    def analyze_source(self, source):
        if len(source.lines) == 0:
            return []

        # Consider only the top matching licenses
        top_candidates = self.get_top_candidates(source)
        if len(top_candidates) == 0:
            return []

        # Search for best matching region for each of the top candidates
        region_results = []
        for license_name, original_score in iteritems(top_candidates):
            license = self.license_library.licenses[license_name]
            result = self.find_license_region(license, source)
            region_results.append((license_name, original_score, result))

        matched_license, orig_score, best_region = \
            max(region_results, key=lambda x: x[2].score)

        found_region_lines = \
            source.get_lines_original_indexing(best_region.start_line,
                                               best_region.end_line)
        found_region = '\r\n'.join(found_region_lines) + '\r\n'

        original_region_lines = \
            source.get_lines_original_indexing(best_region.start_line_orig,
                                               best_region.end_line_orig)
        original_region = '\r\n'.join(original_region_lines) + '\r\n'

        summary = match_summary.MatchSummary(
            input_fp=source.filepath,
            matched_license=matched_license,
            score=orig_score,
            start_line_ind=best_region.start_line,
            end_line_ind=best_region.end_line,
            start_offset=best_region.start_offset,
            end_offset=best_region.end_offset,
            region_score=best_region.score,
            found_region=found_region,
            original_region=original_region
        )

        if not self.original_matched_text_flag:
            summary.pop('original_region')

        results = [summary]

        source_above = source.subset(
            0, source.relative_line_index(best_region.start_line))
        source_below = source.subset(
            source.relative_line_index(best_region.end_line),
            len(source.lines))

        results_above = self.analyze_source(source_above)
        results_below = self.analyze_source(source_below)

        results.extend(results_above)
        results.extend(results_below)
        results.sort(key=lambda x: -x['region_score'])

        return results

    def get_top_candidates(self, source):
        # First, compute n-grams for all lines in the source file
        src_ng = n_grams.NGrams()
        src_ng.parse_text_list_items(
            source.lines,
            universe_ng=self.license_library.universe_n_grams)

        # Measure n-gram similarity relative to all licenses in the library
        similarities = OrderedDict()
        for license_name, lic in iteritems(self.license_library.licenses):
            similarity_score = lic.n_grams.measure_similarity(src_ng)
            similarities[license_name] = similarity_score

        # Filter out low-scoring licenses
        best_score = max(similarities.values())
        current_threshold = max(self.threshold,
                                best_score * self.keep_fraction_of_best)

        top_candidates = OrderedDict()
        for license_name, score in iteritems(similarities):
            if score >= current_threshold:
                top_candidates[license_name] = score

        return top_candidates

    def find_license_region(self, lic, src):
        # Pass along only the location args that were explicitly specified
        loc_args_raw = dict(context_lines=self.context_length,
                            strategy=self.location_strategy,
                            similarity=self.location_similarity,
                            penalty_only_source=self.penalty_only_source,
                            penalty_only_license=self.penalty_only_license,
                            punct_weight=self.punct_weight)

        loc_args = {k: v for k, v in iteritems(loc_args_raw) if v is not None}
        loc_finder = location_identifier.Location_Finder(**loc_args)

        return loc_finder.main_process(lic, src)

    def postprocess_strip_off_code(self, results):
        return PostProcessor(self.threshold).strip_off_code(results)


class PostProcessor(object):

    def __init__(self, threshold):
        self._threshold = threshold

    def strip_off_code(self, results):
        for file_results in results.values():
            for summary in file_results:
                summary['stripped_region'] = self._strip_region(summary)

        return results

    def _strip_region(self, summary):
        if summary['matched_license'] and summary['score'] >= self._threshold:
            stripped_file_lines = self._strip_file_lines(summary)
            start, end = summary['start_line_ind'], summary['end_line_ind']

            stripped_region = ''.join(stripped_file_lines[start:end])
        else:
            stripped_region = ''

        return stripped_region

    def _strip_file_lines(self, summary):
        lang = self._get_language(summary['input_fp'])
        src_lines_crlf = self._src_lines_crlf(summary['input_fp'])

        if lang:
            stripped_file_lines = list(
                comment_parser.parse_file(lang, src_lines_crlf))
        else:
            stripped_file_lines = src_lines_crlf

        return stripped_file_lines

    def _get_language(self, input_filepath):
        __, ext = splitext(input_filepath)

        return comment_parser.language.extension_to_lang_map.get(ext, None)

    def _src_lines_crlf(self, input_filepath):
        src = prep.Source.from_filepath(input_filepath)

        return [line + '\r\n' for line in src.lines]


def _analyze_file(lid, input_path):
    return lid.analyze_file(input_path)


class SyncResult(object):
    """Mimic the interface of multiprocessing.pool.AsyncResult"""

    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


def apply_sync(f, args):
    """Behave like multiprocessing.pool.apply_async, but run synchronously"""
    return SyncResult(f(*args))
