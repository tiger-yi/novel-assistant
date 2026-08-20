import argparse
from pathlib import Path
import sys

try:
    from scripts.outline_contract import (
        OutlineContractError,
        load_outline_contract,
        validate_outline_contract,
    )
except ModuleNotFoundError:
    from outline_contract import (
        OutlineContractError,
        load_outline_contract,
        validate_outline_contract,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate frozen outline contract")
    parser.add_argument("outline_file", type=Path)
    args = parser.parse_args(argv)
    try:
        contract = load_outline_contract(args.outline_file)
    except OutlineContractError as exc:
        print(f"[FAIL] INV-PLOT-001: {exc}")
        return 1
    errors = validate_outline_contract(contract, outline_path=args.outline_file)
    if errors:
        for error in errors:
            print(f"[FAIL] INV-PLOT-001: {error}")
        return 1
    print("[PASS] INV-PLOT-001: outline contract is valid and frozen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
