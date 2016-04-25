class LicenseMatch(object):
    """
    A python object to package the data from the scanner lib to
    return to calling functions.
    """

    def __init__(self, file_name, file_path, license, start_byte, length,
                 full_text=False, scan_error=False):
        self.file_name = file_name
        self.file_path = file_path
        self.license = license
        self.start_byte = start_byte
        self.length = length
        self.full_text = full_text
        self.scan_error = scan_error

    def __eq__(self, other):
        return \
            self.file_name == other.file_name and \
            self.file_path == other.file_path and \
            self.license == other.license and \
            self.start_byte == other.start_byte and \
            self.length == other.length and \
            self.full_text == other.full_text and \
            self.scan_error == other.scan_error

    @property
    def has_snippet(self):
        return self.length > 0