import codecs
import getpass
import datetime
import os, os.path
import string
import chardet


def detect_file_encoding(file_name):
    # Detect encoding by reading entire file in binary mode.
    # Note: if the files are too large, we may want to consider using
    #       chardet.universaldetector to process it in smaller pieces.
    with open(file_name, 'rb') as f:
        contents = f.read()
        encoding = chardet.detect(contents)["encoding"]
    return encoding


def read_lines_offsets(file_name):
    encoding = detect_file_encoding(file_name)
    with codecs.open(file_name, 'r', encoding=encoding, errors='replace') as fp:
        lines, line_offsets = get_lines_and_line_offsets(iter(fp))
    return lines, line_offsets


def get_lines_and_line_offsets(lines):
    lines_stripped = []
    line_offsets = [0]
    for line in lines:
        line_offsets.append(line_offsets[-1] + len(line))
        lines_stripped.append(line.rstrip('\r\n'))
    return lines_stripped, line_offsets


def is_punctuation(input_value):
    return all(c in string.punctuation for c in input_value)


def get_user_date_time_str():
    # add user name and date_time
    user_name = getpass.getuser()
    start_date_time = datetime.datetime.now()
    start_dt_str = '{user}_{year}_{month}_{day}_{hour}_{min}'.format(
        user = user_name,
        year = start_date_time.year,
        month = start_date_time.month,
        day = start_date_time.day,
        hour = start_date_time.hour,
        min = start_date_time.minute
    )
    return start_dt_str


def files_from_path(path):
    if os.path.isfile(path):
        return [path]
    elif os.path.isdir(path):
        return _files_from_dir(path)
    else:  # pragma: no cover
        raise Exception("Not a file or a directory: {}".format(path))

def _files_from_dir(path):
    """
    Recursive helper function for extracting a list of files within
    a directory, in a platform-independent order.
    """
    assert os.path.isdir(path), "Not a directory: {}".format(path)
    result = []
    # Explicitly sort contents to get a platform-independent order
    contents = sorted(os.listdir(path))
    # First, add files in the given directory
    for f in contents:
        filepath = os.path.join(path, f)
        if os.path.isfile(filepath):
            result.append(filepath)
    # Next, add subdirectories recursively
    for f in contents:
        subdir = os.path.join(path, f)
        if os.path.isdir(subdir):
            subresult = _files_from_dir(subdir)
            result.extend(subresult)
    return result
