import argparse
from pathlib import Path
import sys

from reader_evaluation_contract import (
    ReaderEvaluationContractError,
    load_reader_evaluation_report,
    validate_reader_evaluation_report,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate reader evaluation evidence")
    parser.add_argument("report_file", type=Path)
    args = parser.parse_args(argv)
    try:
        report = load_reader_evaluation_report(args.report_file)
    except ReaderEvaluationContractError as exc:
        print(f"[FAIL] {exc}")
        return 1
    errors = validate_reader_evaluation_report(report)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print("[PASS] Reader evaluation evidence validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
