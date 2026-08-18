import argparse
from pathlib import Path
import sys

from payoff_contract import (
    PayoffContractError,
    load_payoff_evidence,
    validate_payoff_evidence,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate chapter payoff evidence")
    parser.add_argument("evidence_file", type=Path)
    args = parser.parse_args(argv)
    try:
        evidence = load_payoff_evidence(args.evidence_file)
    except PayoffContractError as exc:
        print(f"[FAIL] {exc}")
        return 1
    errors = validate_payoff_evidence(evidence)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print("[PASS] Payoff evidence validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
