import argparse
import csv
import logging
import sys

from . import license_identifier
from . import match_summary
from . import util


def main():
    args = _parse_args(sys.argv[1:])

    if args.input_path is not None and args.output_format is None:
        # Use easy_read as the default output format, but only
        # if a source-code analysis will be run
        args.output_format = 'easy_read'

    numeric_logging_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_logging_level, int):  # pragma: no cover
        raise ValueError("Invalid log level: {}".format(args.log))
    logging.basicConfig(level=numeric_logging_level)

    lid = license_identifier.LicenseIdentifier(
        license_dir=args.license_folder,
        threshold=float(args.threshold),
        input_path=args.input_path,
        context_length=args.context,
        location_strategy=args.location_strategy,
        penalty_only_source=args.penalty_only_source,
        penalty_only_license=args.penalty_only_license,
        punct_weight=args.punct_weight,
        pickle_file_path=args.pickle_file_path,
        keep_fraction_of_best=args.keep_fraction_of_best,
        run_in_parallel=not args.single_thread,
        original_matched_text_flag=args.matched_text_without_context
    )

    results = lid.analyze()
    _output_results(results, args.output_format, args.output_file_path,
                    args.matched_text_without_context)


def _parse_args(args):
    aparse = argparse.ArgumentParser(
        description="License text identification and license text region "
                    "finder")
    aparse.add_argument(
        "-T", "--threshold", default=license_identifier.DEFAULT_THRESHOLD,
        help="threshold for similarity measure (ranging from 0 to 1)")
    aparse.add_argument(
        "-L", "--license_folder",
        help="Specify directory path where the license text files are")
    aparse.add_argument(
        "-C", "--context",
        help="Specify an amount of context to add to the license text output",
        default=0, type=int)
    aparse.add_argument(
        "-P", "--pickle_file_path",
        help="Specify the name of the pickle file where license template "
             "library will be saved.",
        default=None)
    aparse.add_argument(
        "-I", "--input_path",
        help="Specify directory or file path where the input source code "
             "files are",
        required=False)
    aparse.add_argument(
        "-F", "--output_format", help="Format the output accordingly",
        choices=["csv", "easy_read"])
    aparse.add_argument(
        "-O", "--output_file_path",
        help="Specify a output path with data info (user name, date, time and "
             ".csv info will be automatically added).",
        default=None)
    aparse.add_argument(
        "-S", "--single_thread", help="Run as a single thread",
        action='store_true', default=False)
    aparse.add_argument(
        "--keep_fraction_of_best",
        help="Look for the best-matching source region for any license with "
             "similarity score >= (this fraction) * (best score)",
        default=license_identifier.DEFAULT_KEEP_FRACTION_OF_BEST, type=float)
    aparse.add_argument(
        "--log", help="Logging level (for example: DEBUG, INFO, ""WARNING)",
        default="INFO")
    aparse.add_argument(
        "--location_strategy", help=argparse.SUPPRESS)
    aparse.add_argument(
        "--location_similarity", help=argparse.SUPPRESS)
    aparse.add_argument(
        "--penalty_only_source", help=argparse.SUPPRESS, type=float)
    aparse.add_argument(
        "--penalty_only_license", help=argparse.SUPPRESS, type=float)
    aparse.add_argument(
        "--punct_weight", help=argparse.SUPPRESS, type=float)
    aparse.add_argument(
        "--matched_text_without_context",
        help="Show matched license text without context", action='store_true',
        default=False)

    return aparse.parse_args(args)


def _output_results(results, format_, path, original_matched_text_flag):
    if format_ == 'csv':
        _write_csv_file(results, path, original_matched_text_flag)
    elif format_ == 'easy_read':
        _display_easy_read(results)
    elif format_ is None:
        pass
    else:  # pragma: no cover
        raise Exception("Unrecognized output format: {}".format(format_))


def _write_csv_file(results, path, original_matched_text_flag):
    path = '{}_{}.csv'.format(path, util.get_user_date_time_str())

    with _open_file(path) as f:
        writer = csv.writer(f)

        field_names = match_summary.MatchSummary.field_names().values()
        if not original_matched_text_flag:
            field_names.remove("Matched license text without context")
        writer.writerow(field_names)

        for filename, results_by_file in results.iteritems():
            for __, summary in results_by_file:
                row = summary.to_csv_row()
                writer.writerow(row)


def _open_file(path):
    if sys.version_info >= (3, 0, 0):  # pragma: no cover
        f = open(path, 'w', newline='')
    else:  # pragma: no cover
        f = open(path, 'wb')

    return f


def _display_easy_read(results):
    for filename, results_by_file in results.iteritems():
        print("=== Found {} results for '{}':".format(len(results_by_file),
                                                      filename))
        for __, summary in results_by_file:
            print(summary.to_display_format())


if __name__ == '__main__':
    main()
