import argparse
import json
from pathlib import Path
import sys

import yaml

from harness_runtime import CommandResolutionError, HarnessManifest
from transaction_cache import CacheError, cleanup_cache, inspect_cache
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
    _add_command_text_arguments(resolve_parser)
    begin_parser = subparsers.add_parser("begin")
    _add_command_text_arguments(begin_parser)
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
    cache_status_parser = subparsers.add_parser("cache-status")
    cache_status_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    cleanup_parser = subparsers.add_parser("cleanup-cache")
    cleanup_parser.add_argument("items", nargs="+")
    cleanup_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    subparsers.add_parser("invariants")
    return parser


def _add_command_text_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("text", nargs="?")
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--text-file",
        type=Path,
        help="Read the raw command text from a UTF-8 file.",
    )
    source.add_argument(
        "--text-stdin",
        action="store_true",
        help="Read the raw command text from stdin as UTF-8.",
    )


def _read_command_text(args) -> str:
    sources = [
        args.text is not None,
        getattr(args, "text_file", None) is not None,
        bool(getattr(args, "text_stdin", False)),
    ]
    if sum(sources) != 1:
        raise CommandResolutionError(
            "provide exactly one command text source: text, --text-file, or --text-stdin"
        )
    if getattr(args, "text_file", None) is not None:
        return args.text_file.read_text(encoding="utf-8-sig").strip()
    if getattr(args, "text_stdin", False):
        return sys.stdin.buffer.read().decode("utf-8-sig").strip()
    return args.text


def _invariant_index(manifest: HarnessManifest) -> list[dict]:
    owners = {}
    routes = manifest.data.get("routes") or {}
    for entries in routes.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for invariant in entry.get("invariants") or []:
                owners[invariant] = entry.get("path")

    gates = {invariant: [] for invariant in owners}
    for entries in (manifest.data.get("verification") or {}).values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            invariant = entry.get("invariant")
            if invariant in gates and entry.get("name"):
                gates[invariant].append(entry["name"])
    return [
        {
            "id": invariant,
            "owner": owners[invariant],
            "gates": sorted(set(gates[invariant])),
        }
        for invariant in sorted(owners)
    ]


def main(argv=None):
    args = _build_parser().parse_args(argv)
    try:
        if args.action == "invariants":
            manifest = HarnessManifest.load(args.manifest)
            print(
                json.dumps(
                    _invariant_index(manifest),
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 0
        if args.action == "cache-status":
            print(
                json.dumps(
                    inspect_cache(args.repo_root),
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 0
        if args.action == "cleanup-cache":
            manifest = HarnessManifest.load(args.manifest)
            cleanup_match = manifest.resolve("清理事务缓存")
            if cleanup_match.name != "cleanup-transactions":
                raise CommandResolutionError(
                    "cleanup route does not resolve to cleanup-transactions"
                )
            inventory = inspect_cache(
                args.repo_root, record_observations=True
            )
            if len(args.items) != len(set(args.items)):
                raise CacheError("duplicate cache item selection")
            items_by_id = {item["id"]: item for item in inventory["items"]}
            missing = [item_id for item_id in args.items if item_id not in items_by_id]
            if missing:
                raise CacheError(f"cache item does not exist: {missing[0]}")
            selected = [items_by_id[item_id] for item_id in args.items]
            print(
                json.dumps(
                    {"selected": selected},
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            expected = f"CONFIRM CLEANUP {','.join(args.items)}"
            confirmation = input(f'Type "{expected}" to authorize: ')
            if confirmation != expected:
                raise CacheError("cleanup confirmation did not match")
            result = cleanup_cache(
                args.repo_root,
                args.items,
                confirmed=True,
            )
            if result["failed"] is not None:
                failure = result["failed"]
                print(
                    f"[FAIL] cache cleanup stopped at {failure['id']}: "
                    f"{failure['error']}"
                )
                return 1
            print(f"[PASS] cache cleanup complete: {','.join(result['cleaned'])}")
            return 0
        if args.action == "resolve":
            manifest = HarnessManifest.load(args.manifest)
            command_text = _read_command_text(args)
            match = manifest.resolve(command_text)
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
            command_text = _read_command_text(args)
            transaction_path = begin_transaction(
                args.repo_root, args.manifest, command_text
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
    except (
        OSError,
        EOFError,
        CacheError,
        CommandResolutionError,
        TransactionError,
    ) as exc:
        print(f"[FAIL] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
