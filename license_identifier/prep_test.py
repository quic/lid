from . import prep

import os


BASE_DIR = os.path.join(os.path.dirname(__file__), "..")

def test_tokenize():
    result = prep._tokenize(["Testing, test-ing: 1 - 2 - 3."])
    assert result == ["Testing", ",", "test", "-", "ing", ":", "1", "-", "2", "-", "3", "."]

    result = prep._tokenize("Testing, again.")
    assert result == ["Testing", ",", "again", "."]

def test_prep_license():
    path = os.path.join(BASE_DIR, "data", "test", "license", "test_license.txt")
    lic = prep.License.from_filename(path)
    assert len(lic.lines) == 1

def test_prep_source():
    path = os.path.join(BASE_DIR, "data", "test", "data", "test1.py")
    src = prep.Source.from_filename(path)
    assert src.lines == ["zero", "one two three four", "five", "six", "seven"]

    src_subset_1 = src.subset(0, 2)
    assert src_subset_1.lines == ["zero", "one two three four"]
    assert src_subset_1.original_line_offset == 0

    src_subset_2 = src.subset(3, 5)
    assert src_subset_2.lines == ["six", "seven"]
    assert src_subset_2.original_line_offset == 3

    src_subset_3 = src_subset_2.subset(1, 2)
    assert src_subset_3.lines == ["seven"]
    assert src_subset_3.original_line_offset == 4

def test_license_library():
    license_dir = os.path.join(BASE_DIR, "data", "test", "license")
    license_library = prep.LicenseLibrary.from_path(license_dir)
    assert set(["test_license", "custom_license"]) == set(license_library.licenses.keys())
