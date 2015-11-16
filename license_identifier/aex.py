import argparse
# aparser = argparse.ArgumentParser()
# aparser.parse_args()
DEFAULT_THRESH_HOLD=0.02
aparse= argparse.ArgumentParser(
    description="License text identification and license text region finder")
aparse.add_argument("-T", "--threshold",
                    default=DEFAULT_THRESH_HOLD,
                    help="threshold hold for similarity measure (ranging from 0 to 1)")
aparse.add_argument("-L", "--license",
                    help="Specify directory path where the license text files are",
                    required=True)
aparse.add_argument("-I", "--input_path",
                    help="Specify directory or file path where the input source code files are",
                    required=True)
aparse.add_argument("-o", "--flag_state",
                    help="Flag states to annotate over", action="append",
                    choices=["analyze", "escalate", "disregard", "hold", "verify", "new"])
aparse.parse_args()
