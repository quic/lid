import nltk
import os.path
import six
from collections import namedtuple, OrderedDict

from . import util
from . import n_grams as ng

_nltk_tokenizer = nltk.tokenize.WordPunctTokenizer()

def _tokenize(text):
    if not isinstance(text, six.string_types):
        # Interpret text as a list of lines
        text = '\n'.join(text)
    return _nltk_tokenizer.tokenize(text)


class License(namedtuple("License",
        ["name",
         "filename",
         "lines",
         "offsets_by_line",
         "tokens",
         "n_grams"])):

    @staticmethod
    def from_filename(filename):
        name, ext = os.path.splitext(os.path.basename(filename))
        lines, offsets_by_line = util.read_lines_offsets(filename)
        tokens = _tokenize(lines)
        n_grams = ng.n_grams(lines)
        return License(
            name = name,
            filename = filename,
            lines = lines,
            offsets_by_line = offsets_by_line,
            tokens = tokens,
            n_grams = n_grams)

    @staticmethod
    def from_lines(lines, name = "<from_lines>"):
        lines, offsets_by_line = util.get_lines_and_line_offsets(lines)
        tokens = _tokenize(lines)
        n_grams = ng.n_grams(lines)
        return License(
            name = name,
            filename = None,
            lines = lines,
            offsets_by_line = offsets_by_line,
            tokens = tokens,
            n_grams = n_grams)


class Source(namedtuple("Source",
        ["filename",
         "lines",
         "original_line_offset",
         "offsets_by_line",
         "tokens_by_line"])):

    @staticmethod
    def from_filename(filename):
        lines, offsets_by_line = util.read_lines_offsets(filename)
        tokens_by_line = [_tokenize(line) for line in lines]

        return Source(
            filename = filename,
            lines = lines,
            original_line_offset = 0,
            offsets_by_line = offsets_by_line,
            tokens_by_line = tokens_by_line)

    @staticmethod
    def from_lines(lines):
        lines, offsets_by_line = util.get_lines_and_line_offsets(lines)
        tokens_by_line = [_tokenize(line) for line in lines]

        return Source(
            filename = None,
            lines = lines,
            original_line_offset = 0,
            offsets_by_line = offsets_by_line,
            tokens_by_line = tokens_by_line)

    def subset(self, start_ind, end_ind):
        return Source(
            filename = self.filename,
            lines = self.lines[start_ind : end_ind],
            original_line_offset = self.original_line_offset + start_ind,
            offsets_by_line = self.offsets_by_line[start_ind : end_ind],
            tokens_by_line = self.tokens_by_line[start_ind : end_ind])


class LicenseLibrary(namedtuple("LicenseLibrary",
        ["licenses",
         "universe_n_grams"])):
    @staticmethod
    def from_path(path):
        assert isinstance(path, six.string_types)
        filenames = util.files_from_path(path)
        result = OrderedDict([])
        universe_n_grams = ng.n_grams()
        for f in filenames:
            if f.endswith(".txt"):
                prepped_license = License.from_filename(f)
                result[prepped_license.name] = prepped_license
                universe_n_grams.parse_text_list_items(prepped_license.lines)

        return LicenseLibrary(licenses = result, universe_n_grams = universe_n_grams)
