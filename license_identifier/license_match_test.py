import pytest

import license_identifier


@pytest.fixture()
def match():
    return license_identifier.LicenseMatch(
        'file_name', 'path/to/file', 'license', 0, 10, True, True)


def test_equal_matches(match):
    eq_match = license_identifier.LicenseMatch(
        match.file_name,
        match.file_path,
        match.license,
        match.start_byte,
        match.length,
        full_text=match.full_text,
        scan_error=match.scan_error)

    assert match == eq_match


def test_diff_file_name(match):
    diff_match = license_identifier.LicenseMatch(
        '{}_diff'.format(match.file_name),
        match.file_path,
        match.license,
        match.start_byte,
        match.length,
        full_text=match.full_text,
        scan_error=match.scan_error)

    assert match != diff_match


def test_diff_file_path(match):
    diff_match = license_identifier.LicenseMatch(
        match.file_name,
        '{}_diff'.format(match.file_path),
        match.license,
        match.start_byte,
        match.length,
        full_text=match.full_text,
        scan_error=match.scan_error)

    assert match != diff_match


def test_diff_license(match):
    diff_match = license_identifier.LicenseMatch(
        match.file_name,
        match.file_path,
        '{}_diff'.format(match.license),
        match.start_byte,
        match.length,
        full_text=match.full_text,
        scan_error=match.scan_error)

    assert match != diff_match


def test_diff_start_byte(match):
    diff_match = license_identifier.LicenseMatch(
        match.file_name,
        match.file_path,
        match.license,
        match.start_byte + 10,
        match.length,
        full_text=match.full_text,
        scan_error=match.scan_error)

    assert match != diff_match


def test_diff_length(match):
    diff_match = license_identifier.LicenseMatch(
        match.file_name,
        match.file_path,
        match.license,
        match.start_byte,
        match.length + 10,
        full_text=match.full_text,
        scan_error=match.scan_error)

    assert match != diff_match


def test_diff_full_text(match):
    diff_match = license_identifier.LicenseMatch(
        match.file_name,
        match.file_path,
        match.license,
        match.start_byte,
        match.length,
        full_text=(not match.full_text),
        scan_error=True)

    assert match != diff_match


def test_diff_scan_error(match):
    diff_match = license_identifier.LicenseMatch(
        match.file_name,
        match.file_path,
        match.license,
        match.start_byte,
        match.length,
        full_text=match.full_text,
        scan_error=(not match.scan_error))

    assert match != diff_match


def test_has_snippet():
    match = license_identifier.LicenseMatch('name', 'path', 'lic', 0, 10)

    assert match.has_snippet


def test_has_no_snippet():
    match = license_identifier.LicenseMatch('name', 'path', 'lic', 10, 0)

    assert match.has_snippet == False


def test_full_text_defaults_to_false():
    match = license_identifier.LicenseMatch('name', 'path', 'lic', 10, 0)

    assert match.full_text == False


def test_scan_error_defaults_to_false():
    match = license_identifier.LicenseMatch('name', 'path', 'lic', 10, 0)

    assert match.scan_error == False