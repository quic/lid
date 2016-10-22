import os.path
import pickle
from collections import namedtuple, OrderedDict

import nltk
import six

from . import util
from . import n_grams as ng


DEFAULT_PICKLE_PROTOCOL_VERSION = 2

_nltk_tokenizer = nltk.tokenize.WordPunctTokenizer()


def _span_tokenize(text):
    if not isinstance(text, six.string_types):
        # Interpret text as a list of lines
        text = '\n'.join(text)

    return list(_nltk_tokenizer.span_tokenize(text))


def _tokens_and_positions_by_line(lines):
    tokens_by_line, token_positions_by_line = [], []

    for line in lines:
        token_positions = _span_tokenize(line)
        line_tokens = [line[start:end] for start, end in token_positions]

        tokens_by_line.append(line_tokens)
        token_positions_by_line.append(token_positions)

    return tokens_by_line, token_positions_by_line


def _get_ignored_strings(lines, token_positions_by_line):
    """
    Extracts the "ignored" text (generally whitespace) that appears between
    (or before/after) tokens.

    If there are n tokens, then this generator will yield n+1 strings. The
    first string will be the initial whitespace (before any tokens), and the
    final string will be the trailing whitespace after the final token.
    """
    ignored_text = ''

    for line, token_positions in zip(lines, token_positions_by_line):
        char_index = 0

        for start, end in token_positions:
            ignored_text += line[char_index:start]
            yield ignored_text

            ignored_text = ''
            char_index = end

        ignored_text += line[char_index:] + '\n'

    # Produce any trailing ignored text
    yield ignored_text


LicenseBase = namedtuple('License', ['name',
                                     'filepath',
                                     'lines',
                                     'offsets_by_line',
                                     'tokens',
                                     'token_positions_by_line',
                                     'n_grams'])


class License(LicenseBase):

    # memory-saving hack
    __slots__ = ()

    @classmethod
    def from_filepath(cls, filepath):
        name, ext = os.path.splitext(os.path.basename(filepath))
        lines, offsets_by_line = util.read_lines_offsets(filepath)
        tokens_by_line, token_positions_by_line = \
            _tokens_and_positions_by_line(lines)
        tokens = [token for tokens in tokens_by_line for token in tokens]
        n_grams = ng.n_grams(lines)

        return cls(name=name,
                   filepath=filepath,
                   lines=lines,
                   offsets_by_line=offsets_by_line,
                   tokens=tokens,
                   token_positions_by_line=token_positions_by_line,
                   n_grams=n_grams)

    @classmethod
    def from_lines(cls, lines, name="<from_lines>"):
        lines, offsets_by_line = util.get_lines_and_line_offsets(lines)
        tokens_by_line, token_positions_by_line = \
            _tokens_and_positions_by_line(lines)
        tokens = [token for tokens in tokens_by_line for token in tokens]
        n_grams = ng.n_grams(lines)

        return cls(name=name,
                   filepath=None,
                   lines=lines,
                   offsets_by_line=offsets_by_line,
                   tokens=tokens,
                   token_positions_by_line=token_positions_by_line,
                   n_grams=n_grams)

    def get_ignored_strings(self):
        return _get_ignored_strings(self.lines, self.token_positions_by_line)


SourceBase = namedtuple('Source', ['filepath',
                                   'lines',
                                   'original_line_offset',
                                   'offsets_by_line',
                                   'token_positions_by_line',
                                   'tokens_by_line'])


class Source(SourceBase):

    # memory-saving hack
    __slots__ = ()

    @classmethod
    def from_filepath(cls, filepath):
        lines, offsets_by_line = util.read_lines_offsets(filepath)
        tokens_by_line, token_positions_by_line = \
            _tokens_and_positions_by_line(lines)

        return cls(filepath=filepath,
                   lines=lines,
                   original_line_offset=0,
                   offsets_by_line=offsets_by_line,
                   token_positions_by_line=token_positions_by_line,
                   tokens_by_line=tokens_by_line)

    @classmethod
    def from_lines(cls, lines):
        lines, offsets_by_line = util.get_lines_and_line_offsets(lines)
        tokens_by_line, token_positions_by_line = \
            _tokens_and_positions_by_line(lines)

        return cls(filepath=None,
                   lines=lines,
                   original_line_offset=0,
                   offsets_by_line=offsets_by_line,
                   token_positions_by_line=token_positions_by_line,
                   tokens_by_line=tokens_by_line)

    def subset(self, start, end):
        lines = self.lines[start:end]
        original_line_offset = self.original_line_offset + start
        offsets_by_line = self.offsets_by_line[start:end]
        token_positions_by_line = self.token_positions_by_line[start:end]
        tokens_by_line = self.tokens_by_line[start: end]

        return Source(filepath=self.filepath,
                      lines=lines,
                      original_line_offset=original_line_offset,
                      offsets_by_line=offsets_by_line,
                      token_positions_by_line=token_positions_by_line,
                      tokens_by_line=tokens_by_line)

    def get_ignored_strings(self):
        return _get_ignored_strings(self.lines, self.token_positions_by_line)

    def relative_line_index(self, ind):
        return ind - self.original_line_offset

    def get_lines_original_indexing(self, start, end):
        return self.lines[
            self.relative_line_index(start):self.relative_line_index(end)]


LicenseLibraryBase = namedtuple('LicenseLibrary',
                                ['licenses', 'universe_n_grams'])


class LicenseLibrary(LicenseLibraryBase):

    # memory-saving hack
    __slots__ = ()

    @classmethod
    def from_path(cls, path):
        assert isinstance(path, six.string_types)

        filenames = util.files_from_path(path)
        universe_n_grams = ng.n_grams()

        licenses = OrderedDict([])
        for filename in filenames:
            if filename.endswith('.txt'):
                prepped_license = License.from_filepath(filename)
                licenses[prepped_license.name] = prepped_license
                universe_n_grams.parse_text_list_items(prepped_license.lines)

        return cls(licenses=licenses, universe_n_grams=universe_n_grams)

    @classmethod
    def from_licenses(cls, licenses):
        licenses_by_name = OrderedDict([])

        universe_n_grams = ng.n_grams()
        for license in licenses:
            licenses_by_name[license.name] = license
            universe_n_grams.parse_text_list_items(license.lines)

        return cls(licenses=licenses_by_name,
                   universe_n_grams=universe_n_grams)

    @classmethod
    def deserialize(cls, filename):
        with open(filename, 'rb') as f:
            result = pickle.load(f)

        # Sanity check: make sure we're not opening an old pickle file
        assert isinstance(result, cls)

        return result

    def serialize(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self, f, protocol=DEFAULT_PICKLE_PROTOCOL_VERSION)
