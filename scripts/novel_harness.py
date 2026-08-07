import argparse
import json
from pathlib import Path
import sys

import yaml

from harness_runtime import CommandResolutionError, HarnessManifest
from transaction_executor import (
    TransactionError,
    begin_transaction,
    commit_transaction,
    confirm_overwrite,
    load_transaction,
    validate_transaction,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Novel Harness commands")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=(
            Path(__file__).resolve().parents[1]
            / "novel-harness"
            / "context.manifest.yaml"
        ),
    )
    subparsers = parser.add_subparsers(dest="action", required=True)
    resolve_parser = subparsers.add_parser("resolve")
    resolve_parser.add_argument("text")
    begin_parser = subparsers.add_parser("begin")
    begin_parser.add_argument("text")
    begin_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    validate_parser = subparsers.add_parser("validate-transaction")
    validate_parser.add_argument("transaction", type=Path)
    commit_parser = subparsers.add_parser("commit")
    commit_parser.add_argument("transaction", type=Path)
    commit_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    confirm_parser = subparsers.add_parser("confirm-overwrite")
    confirm_parser.add_argument("transaction", type=Path)
    confirm_parser.add_argument("target")
    confirm_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("transaction", type=Path)
    return parser


def main(argv=None):
    args = _build_parser().parse_args(argv)
    try:
        if args.action == "resolve":
            manifest = HarnessManifest.load(args.manifest)
            match = manifest.resolve(args.text)
            pipeline_name = match.route.get("pipeline")
            pipeline = manifest.data.get("pipelines", {}).get(pipeline_name, {})
            print(
                json.dumps(
                    {
                        "command": match.name,
                        "mode": match.mode,
                        "arguments": match.arguments,
                        "pipeline": pipeline_name,
                        "stages": [
                            stage["name"] for stage in pipeline.get("stages", [])
                        ],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 0
        if args.action == "begin":
            transaction_path = begin_transaction(
                args.repo_root, args.manifest, args.text
            )
            print(f"[PASS] transaction created: {transaction_path}")
            return 0
        if args.action == "validate-transaction":
            transaction = load_transaction(args.transaction)
            errors = validate_transaction(transaction)
            if errors:
                for error in errors:
                    print(f"[FAIL] {error}")
                return 1
            print("[PASS] transaction is valid")
            return 0
        if args.action == "commit":
            transaction = commit_transaction(
                args.repo_root, args.manifest, args.transaction
            )
            print(f"[PASS] transaction committed: {transaction['transaction_id']}")
            return 0
        if args.action == "confirm-overwrite":
            expected = f"CONFIRM {Path(args.target).as_posix()}"
            confirmation_text = input(f'Type "{expected}" to authorize: ')
            confirmation = confirm_overwrite(
                args.repo_root,
                args.manifest,
                args.transaction,
                args.target,
                confirmation_text,
            )
            print(f"[PASS] overwrite confirmed: {confirmation['target']}")
            return 0
        transaction = load_transaction(args.transaction)
        print(yaml.safe_dump(transaction, allow_unicode=True, sort_keys=False), end="")
        return 0
    except (OSError, EOFError, CommandResolutionError, TransactionError) as exc:
        print(f"[FAIL] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
