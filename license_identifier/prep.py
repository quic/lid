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
    token_positions_by_line = [_span_tokenize(line) for line in lines]
    tokens_by_line = []
    for i in xrange(len(lines)):
        current_tokens = []
        for start, end in token_positions_by_line[i]:
            current_tokens.append(lines[i][start:end])
        tokens_by_line.append(current_tokens)
    return tokens_by_line, token_positions_by_line


def _get_ignored_strings(lines, token_positions_by_line):
    '''
    Extracts the "ignored" text (generally whitespace) that appears
    between (or before/after) tokens.  If there are N tokens, then this
    generator will yield N+1 strings.  The first string will be the initial
    whitespace (before any tokens), and the final string will be the
    trailing whitespace after the final token.
    '''
    ignored_text = ''
    for line_index in range(len(lines)):
        char_index = 0
        for start, end in token_positions_by_line[line_index]:
            ignored_text += lines[line_index][char_index:start]
            yield ignored_text
            ignored_text = ''
            char_index = end
        ignored_text += lines[line_index][char_index:] + '\n'

    # Produce any trailing ignored text
    yield ignored_text


class License(namedtuple("License",
                         ["name",
                          "filepath",
                          "lines",
                          "offsets_by_line",
                          "tokens",
                          "token_positions_by_line",
                          "n_grams"])):
    @classmethod
    def from_filepath(cls, filenpath):
        name, ext = os.path.splitext(os.path.basename(filenpath))
        lines, offsets_by_line = util.read_lines_offsets(filenpath)
        tokens_by_line, token_positions_by_line = _tokens_and_positions_by_line(lines)
        tokens = []
        for token_list in tokens_by_line:
            tokens.extend(token_list)
        n_grams = ng.n_grams(lines)
        return cls(
            name=name,
            filepath=filenpath,
            lines=lines,
            offsets_by_line=offsets_by_line,
            tokens=tokens,
            token_positions_by_line=token_positions_by_line,
            n_grams=n_grams)

    @classmethod
    def from_lines(cls, lines, name="<from_lines>"):
        lines, offsets_by_line = util.get_lines_and_line_offsets(lines)
        tokens_by_line, token_positions_by_line = _tokens_and_positions_by_line(lines)
        tokens = []
        for token_list in tokens_by_line:
            tokens.extend(token_list)
        n_grams = ng.n_grams(lines)
        return cls(
            name=name,
            filepath=None,
            lines=lines,
            offsets_by_line=offsets_by_line,
            tokens=tokens,
            token_positions_by_line=token_positions_by_line,
            n_grams=n_grams)

    def get_ignored_strings(self):
        return _get_ignored_strings(self.lines, self.token_positions_by_line)


class Source(namedtuple("Source",
                        ["filepath",
                         "lines",
                         "original_line_offset",
                         "offsets_by_line",
                         "token_positions_by_line",
                         "tokens_by_line"])):
    @classmethod
    def from_filepath(cls, filepath):
        lines, offsets_by_line = util.read_lines_offsets(filepath)
        tokens_by_line, token_positions_by_line = \
            _tokens_and_positions_by_line(lines)

        return cls(
            filepath=filepath,
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

        return cls(
            filepath=None,
            lines=lines,
            original_line_offset=0,
            offsets_by_line=offsets_by_line,
            token_positions_by_line=token_positions_by_line,
            tokens_by_line=tokens_by_line)

    def subset(self, start_ind, end_ind):
        return Source(
            filepath=self.filepath,
            lines=self.lines[start_ind: end_ind],
            original_line_offset=self.original_line_offset + start_ind,
            offsets_by_line=self.offsets_by_line[start_ind: end_ind],
            token_positions_by_line=self.token_positions_by_line[start_ind: end_ind],
            tokens_by_line=self.tokens_by_line[start_ind: end_ind])

    def get_ignored_strings(self):
        return _get_ignored_strings(self.lines, self.token_positions_by_line)

    def relative_line_index(self, ind):
        return ind - self.original_line_offset

    def get_lines_original_indexing(self, start_ind, end_ind):
        return self.lines[self.relative_line_index(start_ind): self.relative_line_index(end_ind)]


class LicenseLibrary(namedtuple("LicenseLibrary",
                                ["licenses",
                                 "universe_n_grams"])):
    @classmethod
    def from_path(cls, path):
        assert isinstance(path, six.string_types)
        filenames = util.files_from_path(path)
        result = OrderedDict([])
        universe_n_grams = ng.n_grams()
        for f in filenames:
            if f.endswith(".txt"):
                prepped_license = License.from_filepath(f)
                result[prepped_license.name] = prepped_license
                universe_n_grams.parse_text_list_items(prepped_license.lines)

        return cls(licenses=result, universe_n_grams=universe_n_grams)

    @classmethod
    def from_licenses(cls, licenses):
        license_dict = OrderedDict([])
        universe_n_grams = ng.n_grams()
        for lic in licenses:
            license_dict[lic.name] = lic
            universe_n_grams.parse_text_list_items(lic.lines)
        return cls(licenses=license_dict, universe_n_grams=universe_n_grams)

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
