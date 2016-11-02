import chardet
import codecs
import datetime
import getpass
import os
import os.path
import string


def detect_file_encoding(file_name):
    """
    Detect encoding by reading entire file in binary mode.

    Note: If the files are too large, we may want to consider using
          chardet.universaldetector to process it in smaller pieces.
    """
    with open(file_name, 'rb') as f:
        contents = f.read()
        encoding = chardet.detect(contents)["encoding"]

    return encoding

def read_lines_offsets(filename):
    encoding = detect_file_encoding(filename)

    try:
        return read_with_detected_encoding(filename, encoding)
    except:
        return read_with_default_encoder(filename)
    

def read_with_detected_encoding(filename, encoding):
    with codecs.open(filename, 'r', encoding=encoding, errors='replace') as fp:
        lines, line_offsets = get_lines_and_line_offsets(iter(fp))
    return lines, line_offsets


def read_with_default_encoder(filename):
    with codecs.open(filename, 'r', encoding='utf-8', errors='replace') as fp:
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
    # add username and datetime
    username = getpass.getuser()
    start_datetime = datetime.datetime.now()

    return '{user}_{year}_{month}_{day}_{hour}_{min_}'.format(
        user=username,
        year=start_datetime.year,
        month=start_datetime.month,
        day=start_datetime.day,
        hour=start_datetime.hour,
        min_=start_datetime.minute
    )


def files_from_path(path):
    if os.path.isfile(path):
        filepaths = [path]
    elif os.path.isdir(path):
        filepaths = _files_from_dir(path)
    else:  # pragma: no cover
        raise Exception("Not a file or a directory: {}".format(path))

    return filepaths


def _files_from_dir(path):
    """
    Recursive helper function for extracting a list of files within
    a directory, in a platform-independent order.
    """
    assert os.path.isdir(path), "Not a directory: {}".format(path)

    filepaths = []

    # Explicitly sort contents to get a platform-independent order
    contents = sorted(os.listdir(path))

    # First, add files in the given directory
    for filename in contents:
        filepath = os.path.join(path, filename)
        if os.path.isfile(filepath):
            filepaths.append(filepath)

    # Next, add subdirectories recursively
    for filename in contents:
        subdir = os.path.join(path, filename)
        if os.path.isdir(subdir):
            subdir_filepaths = _files_from_dir(subdir)
            filepaths.extend(subdir_filepaths)

    return filepaths
