import nltk
import os.path
import six
import pickle
from collections import namedtuple, OrderedDict

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


class TokenLocatorMixin(object):
    '''
    License and Source inherit from this class in order to share
    token-locating functionality.
    The subclass must provide the attribute `token_positions_by_line`.
    '''

    def _locate_token(self, token_index):
        if token_index < 0:
            raise ValueError("Token index is negative")
        current_token_index = 0
        for line_index, positions in enumerate(self.token_positions_by_line):
            if token_index - current_token_index >= len(positions):
                current_token_index += len(positions)
                continue
            start_in_line, end_in_line = \
                positions[token_index - current_token_index]
            return (line_index, start_in_line, end_in_line)
        raise ValueError("Token index is too large")

    def _get_ignored_text_before_token(self, token_index):
        '''
        Extracts the "ignored" text (generally whitespace) that appears
        before the given `token_index`.  If the index is 0, this will
        extract any initial whitespace, and if the index is equal to the
        total number of tokens, this will extract any final whitespace.
        Otherwise, this will extract the whitespace that appears after
        (token_index - 1) and before (token_index).
        '''
        total_num_tokens = sum(len(t_list) for t_list in self.token_positions_by_line)
        if token_index < 0:
            raise ValueError("Token index is negative")
        if token_index > total_num_tokens:
            raise ValueError("Token index is too large")

        if total_num_tokens == 0:
            # Return full text if there are no tokens
            return '\n'.join(self.lines) + '\n'

        # Locate the boundaries of the ignored text
        if token_index == 0:
            start_line_index = 0
            char_offset_within_start_line = 0
        else:
            line_index, start, end = self._locate_token(token_index - 1)
            start_line_index = line_index
            char_offset_within_start_line = end

        if token_index == total_num_tokens:
            end_line_index = len(self.lines) - 1
            char_offset_within_end_line = len(self.lines[end_line_index])
        else:
            line_index, start, end = self._locate_token(token_index)
            end_line_index = line_index
            char_offset_within_end_line = start

        # Extract the ignored text
        ignored_text = ''
        for line_index in range(start_line_index, end_line_index + 1):
            line = self.lines[line_index]

            if line_index == start_line_index:
                start_within_line = char_offset_within_start_line
            else:
                start_within_line = 0
                # Insert a newline for all but the first line
                ignored_text += '\n'

            if line_index == end_line_index:
                end_within_line = char_offset_within_end_line
            else:
                end_within_line = len(line)

            ignored_text += line[start_within_line : end_within_line]

        # Ignored text after final token should include a newline
        if token_index == total_num_tokens:
            ignored_text += '\n'

        return ignored_text


class License(namedtuple("License",
        ["name",
         "filename",
         "lines",
         "offsets_by_line",
         "tokens",
         "token_positions_by_line",
         "n_grams"]), TokenLocatorMixin):

    @staticmethod
    def from_filename(filename):
        name, ext = os.path.splitext(os.path.basename(filename))
        lines, offsets_by_line = util.read_lines_offsets(filename)
        tokens_by_line, token_positions_by_line = _tokens_and_positions_by_line(lines)
        tokens = []
        for token_list in tokens_by_line:
            tokens.extend(token_list)
        n_grams = ng.n_grams(lines)
        return License(
            name = name,
            filename = filename,
            lines = lines,
            offsets_by_line = offsets_by_line,
            tokens = tokens,
            token_positions_by_line = token_positions_by_line,
            n_grams = n_grams)

    @staticmethod
    def from_lines(lines, name = "<from_lines>"):
        lines, offsets_by_line = util.get_lines_and_line_offsets(lines)
        tokens_by_line, token_positions_by_line = _tokens_and_positions_by_line(lines)
        tokens = []
        for token_list in tokens_by_line:
            tokens.extend(token_list)
        n_grams = ng.n_grams(lines)
        return License(
            name = name,
            filename = None,
            lines = lines,
            offsets_by_line = offsets_by_line,
            tokens = tokens,
            token_positions_by_line = token_positions_by_line,
            n_grams = n_grams)


class Source(namedtuple("Source",
        ["filename",
         "lines",
         "original_line_offset",
         "offsets_by_line",
         "token_positions_by_line",
         "tokens_by_line"]), TokenLocatorMixin):

    @staticmethod
    def from_filename(filename):
        lines, offsets_by_line = util.read_lines_offsets(filename)
        tokens_by_line, token_positions_by_line = \
            _tokens_and_positions_by_line(lines)

        return Source(
            filename = filename,
            lines = lines,
            original_line_offset = 0,
            offsets_by_line = offsets_by_line,
            token_positions_by_line = token_positions_by_line,
            tokens_by_line = tokens_by_line)

    @staticmethod
    def from_lines(lines):
        lines, offsets_by_line = util.get_lines_and_line_offsets(lines)
        tokens_by_line, token_positions_by_line = \
            _tokens_and_positions_by_line(lines)

        return Source(
            filename = None,
            lines = lines,
            original_line_offset = 0,
            offsets_by_line = offsets_by_line,
            token_positions_by_line = token_positions_by_line,
            tokens_by_line = tokens_by_line)

    def subset(self, start_ind, end_ind):
        return Source(
            filename = self.filename,
            lines = self.lines[start_ind : end_ind],
            original_line_offset = self.original_line_offset + start_ind,
            offsets_by_line = self.offsets_by_line[start_ind : end_ind],
            token_positions_by_line = self.token_positions_by_line[start_ind : end_ind],
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

    @staticmethod
    def deserialize(filename):
        with open(filename, 'rb') as f:
            result = pickle.load(f)
        # Sanity check: make sure we're not opening an old pickle file
        assert isinstance(result, LicenseLibrary)
        return result

    def serialize(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self, f, protocol = DEFAULT_PICKLE_PROTOCOL_VERSION)
