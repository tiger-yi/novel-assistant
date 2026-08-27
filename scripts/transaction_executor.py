from pathlib import Path
from datetime import datetime, timezone
import hashlib
import os
import re
import secrets
import shlex
import subprocess
import sys
import tempfile
from urllib.parse import unquote

import yaml

try:
    from scripts.harness_runtime import CommandResolutionError, HarnessManifest
    from scripts.outline_contract import OutlineContractError, chapter_binding
    from scripts.reader_evaluation_contract import (
        ReaderEvaluationContractError,
        load_reader_evaluation_report,
    )
    from scripts.validate_chapter import (
        find_presentation_errors,
        find_quoted_lines,
    )
except ModuleNotFoundError:  # Direct execution through scripts/novel_harness.py.
    from harness_runtime import CommandResolutionError, HarnessManifest
    from outline_contract import OutlineContractError, chapter_binding
    from reader_evaluation_contract import (
        ReaderEvaluationContractError,
        load_reader_evaluation_report,
    )
    from validate_chapter import find_presentation_errors, find_quoted_lines


TRANSACTION_SCHEMA = "novel-harness/transaction/v1"
TRANSACTION_STATES = {
    "PREFLIGHT",
    "PREPARING",
    "PREPARED",
    "COMMITTING",
    "COMPLETE",
    "FAILED",
    "ABORTED",
}
ARCHIVE_STATES = {
    "NOT_CHECKED",
    "NOT_DUE",
    "COMPLETE",
    "ARCHIVE_PENDING",
}
GATE_STATUSES = {"PASS", "WARN", "FAIL", "NOT_APPLICABLE"}
GATE_KINDS = {"deterministic", "semantic"}
SPEECH_AUDIT_KEY = "reported_speech_audit"
DIALOGUE_CLARITY_AUDIT_KEY = "dialogue_clarity_audit"
DIALOGUE_CLARITY_SCAN_KEY = "dialogue_clarity_scan"
SPEECH_AUDIT_VERDICTS = {
    "legal_retention",
    "event_summary",
    "indirect_report",
    "nominalization",
    "quote_tag",
    "variant_quote",
    "impersonation",
}
DIALOGUE_RISK_CATEGORIES = {
    "character_decision",
    "action_causality",
    "fact_revelation",
    "resource_or_state",
    "relationship_commitment",
    "payoff_or_closing_pull",
}
DIALOGUE_CLARITY_VERDICTS = {"clear", "resolved_after_auto_fix"}
SHA256_VALUE = re.compile(r"sha256:[0-9a-f]{64}")
TRANSACTION_ID = re.compile(
    r"TX-(?:CH-\d{4}|CMD-[A-Z0-9-]+-\d{4})-R\d{2}"
)
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
MARKDOWN_REFERENCE_DEFINITION = re.compile(
    r"^\s*\[([^\]]+)\]:\s*(\S+)", re.MULTILINE
)
MARKDOWN_REFERENCE_USE = re.compile(r"\[[^\]]+\]\[([^\]]+)\]")
MARKDOWN_HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
HTML_ID = re.compile(r"\bid=[\"']([^\"']+)[\"']", re.IGNORECASE)
PUBLISHED_CHAPTER_FILE = re.compile(r"^CH-(?P<chapter>\d{4})(?:-.+)?\.txt$")
OUTLINE_BOOK_TITLE = re.compile(r"^\s*[*-]\s*\*\*书名\*\*\s*[:：]\s*(.+?)\s*$", re.MULTILINE)
STYLE_BASIS_FIELDS = (
    "title",
    "genre",
    "tone",
    "protagonist_identity",
    "cheat",
    "core_taboo",
)


class TransactionError(ValueError):
    pass


def load_transaction(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise TransactionError(f"invalid transaction YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise TransactionError("transaction root must be a mapping")
    return data


def _yaml_frontmatter(text: str) -> dict:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    try:
        end_index = next(
            index for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        )
    except StopIteration:
        return {}
    try:
        data = yaml.safe_load("\n".join(lines[1:end_index]))
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def validate_transaction(data: dict) -> list[str]:
    if not isinstance(data, dict):
        return ["transaction root must be a mapping"]

    errors = []
    if data.get("schema") != TRANSACTION_SCHEMA:
        errors.append(f"schema must be {TRANSACTION_SCHEMA}")
    transaction_id = data.get("transaction_id")
    if not isinstance(transaction_id, str) or not TRANSACTION_ID.fullmatch(
        transaction_id
    ):
        errors.append(f"invalid transaction ID: {transaction_id}")
    if data.get("state") not in TRANSACTION_STATES:
        errors.append(f"invalid transaction state: {data.get('state')}")
    if data.get("archive_state") not in ARCHIVE_STATES:
        errors.append(f"invalid archive state: {data.get('archive_state')}")
    staging_state = data.get("staging_state")
    if staging_state is not None and staging_state != "CLEANED":
        errors.append(f"invalid staging state: {staging_state}")
    completed_at = data.get("completed_at")
    if completed_at is not None:
        try:
            parsed_completed_at = datetime.fromisoformat(completed_at)
        except (TypeError, ValueError):
            parsed_completed_at = None
        if (
            parsed_completed_at is None
            or parsed_completed_at.tzinfo is None
            or parsed_completed_at.utcoffset()
            != timezone.utc.utcoffset(parsed_completed_at)
        ):
            errors.append(f"invalid completed_at: {completed_at}")

    gates = data.get("gates")
    if not isinstance(gates, list):
        errors.append("transaction gates must be a list")
        gates = []
    for gate in gates:
        if not isinstance(gate, dict):
            errors.append("transaction gates must be mappings")
            continue
        gate_name = gate.get("gate")
        if not gate_name:
            errors.append("gate name is required")
        kind = gate.get("kind")
        if kind not in GATE_KINDS:
            errors.append(f"invalid gate kind: {kind}")
        status = gate.get("status")
        if status not in GATE_STATUSES:
            errors.append(f"invalid gate status: {status}")
            continue
        if (
            gate.get("required")
            and status == "FAIL"
            and kind != "deterministic"
            and data.get("state") != "ABORTED"
        ):
            errors.append(f"required gate did not pass: {gate_name}")
        if status == "NOT_APPLICABLE" and not gate.get("reason"):
            errors.append(f"NOT_APPLICABLE gate requires reason: {gate_name}")
        if kind == "semantic" and status in {"PASS", "WARN"}:
            evidence = gate.get("evidence") or []
            if not evidence:
                errors.append(f"required semantic evidence is missing: {gate_name}")
            for item in evidence:
                if not isinstance(item, dict):
                    errors.append(f"semantic evidence must be mappings: {gate_name}")
                    continue
                if not item.get("claim") or not item.get("source"):
                    errors.append(
                        f"semantic evidence requires claim and source: {gate_name}"
                    )
                excerpt_hash = item.get("excerpt_hash")
                if excerpt_hash and (
                    not isinstance(excerpt_hash, str)
                    or not SHA256_VALUE.fullmatch(excerpt_hash)
                ):
                    errors.append(f"invalid excerpt_hash: {gate_name}")

    changes = data.get("changes")
    if not isinstance(changes, list):
        errors.append("transaction changes must be a list")
    applied_keys = data.get("applied_keys")
    if not isinstance(applied_keys, list):
        errors.append("transaction applied_keys must be a list")
    confirmations = data.get("confirmations", [])
    if not isinstance(confirmations, list):
        errors.append("transaction confirmations must be a list")
    else:
        for confirmation in confirmations:
            if not isinstance(confirmation, dict):
                errors.append("transaction confirmations must be mappings")
                continue
            if (
                confirmation.get("type") != "overwrite"
                or not confirmation.get("target")
                or confirmation.get("status") != "CONFIRMED"
                or confirmation.get("source") != "user"
                or confirmation.get("method") != "interactive-cli"
                or not isinstance(confirmation.get("proof"), str)
                or not SHA256_VALUE.fullmatch(confirmation["proof"])
            ):
                errors.append("invalid overwrite confirmation")
    recovery = data.get("recovery")
    if not isinstance(recovery, dict):
        errors.append("transaction recovery must be a mapping")
    events = data.get("events", [])
    if not isinstance(events, list) or any(
        not isinstance(event, str) or not event for event in events
    ):
        errors.append("transaction events must be a list of names")
    return errors


def validate_plan_binding(repo_root: Path, transaction: dict) -> None:
    recorded = transaction.get("plan_contract")
    if recorded is None:
        return
    chapter = (transaction.get("arguments") or {}).get("chapter")
    if not isinstance(chapter, str) or not chapter.isdigit():
        raise TransactionError("plan-bound transaction chapter is invalid")
    outline_path = repo_root / "world" / "outline.md"
    try:
        current = chapter_binding(outline_path, int(chapter))
    except OutlineContractError as exc:
        raise TransactionError(str(exc)) from exc
    recorded_binding = {
        field: recorded.get(field)
        for field in current
    }
    if current != recorded_binding:
        raise TransactionError("plan contract became stale after transaction begin")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _repository_path(repo_root: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        raise TransactionError(f"absolute transaction path is forbidden: {raw_path}")
    resolved = (repo_root / candidate).resolve()
    if not _within(resolved, repo_root):
        raise TransactionError(f"path escapes repository: {raw_path}")
    return resolved


def _transaction_path(
    repo_root: Path, record_directory: Path, transaction_path: Path
) -> Path:
    resolved = transaction_path.resolve()
    if not _within(resolved, repo_root):
        raise TransactionError(f"transaction path escapes repository: {transaction_path}")
    if resolved.parent != record_directory:
        raise TransactionError(
            f"transaction is outside Manifest record directory: {transaction_path}"
        )
    return resolved


def _record_directory(repo_root: Path, manifest: HarnessManifest) -> Path:
    raw_directory = (manifest.data.get("transaction") or {}).get(
        "record_directory", "../world/.transactions/"
    )
    directory = (manifest.path.parent / raw_directory).resolve()
    if not _within(directory, repo_root):
        raise TransactionError(
            f"Manifest record directory escapes repository: {raw_directory}"
        )
    return directory


def _scan_presentation_issues(repo_root: Path) -> dict[str, list[str]]:
    chapter_dir = repo_root / "chapters"
    if not chapter_dir.is_dir():
        return {}
    issues = {}
    for path in sorted(chapter_dir.glob("CH-*.txt")):
        match = PUBLISHED_CHAPTER_FILE.fullmatch(path.name)
        if match is None:
            continue
        errors = find_presentation_errors(path.read_text(encoding="utf-8"))
        if errors:
            issues[f"CH-{match.group('chapter')}"] = errors
    return issues


def _migration_parent_authorization(
    transaction_dir: Path, parent_command: str, chapter_id: str
) -> dict:
    authorized = []
    for path in transaction_dir.glob("TX-CMD-MIGRATE-PRESENTATION-*-R01.yaml"):
        try:
            record = load_transaction(path)
        except (OSError, UnicodeError, TransactionError):
            continue
        migration = record.get("migration") or {}
        if (
            record.get("command") == parent_command
            and record.get("state") == "COMPLETE"
            and chapter_id in (migration.get("chapters") or [])
            and chapter_id not in (migration.get("completed") or [])
        ):
            authorized.append(record)
    if not authorized:
        raise TransactionError(
            f"completed migration authorization is missing for {chapter_id}"
        )
    return sorted(authorized, key=lambda item: item["transaction_id"])[-1]


def record_migration_child_completion(
    transaction_dir: Path, child_transaction: dict
) -> None:
    parent_id = child_transaction.get("parent_transaction")
    if not parent_id:
        return
    parent_path = transaction_dir / f"{parent_id}.yaml"
    parent = load_transaction(parent_path)
    if parent.get("state") != "COMPLETE":
        raise TransactionError("migration parent authorization is not complete")
    migration = parent.get("migration")
    if not isinstance(migration, dict):
        raise TransactionError("migration parent record is invalid")
    chapter = (child_transaction.get("arguments") or {}).get("chapter")
    if not isinstance(chapter, str) or not chapter.isdigit():
        raise TransactionError("migration child chapter is invalid")
    chapter_id = f"CH-{int(chapter):04d}"
    if chapter_id not in (migration.get("chapters") or []):
        raise TransactionError(f"migration parent did not authorize {chapter_id}")

    completed = migration.setdefault("completed", [])
    if chapter_id not in completed:
        completed.append(chapter_id)
        completed.sort()
    child_transactions = migration.setdefault("child_transactions", {})
    child_transactions[chapter_id] = child_transaction["transaction_id"]
    migration["migration_state"] = (
        "COMPLETE"
        if set(completed) == set(migration.get("chapters") or [])
        else "PARTIAL"
    )
    _atomic_write_yaml(parent_path, parent)


def _allowed_target(target: Path, manifest: HarnessManifest, scopes: list[str]) -> bool:
    for raw_scope in scopes:
        scope = (manifest.path.parent / raw_scope).resolve()
        is_directory = raw_scope.endswith(("/", "\\")) or scope.is_dir()
        if (is_directory and _within(target, scope)) or target == scope:
            return True
    return False


def _confirmation_proof(
    transaction: dict, target: str, baseline_hash: str
) -> str:
    nonce = transaction.get("confirmation_nonce")
    if not isinstance(nonce, str) or not nonce:
        raise TransactionError("transaction confirmation nonce is missing")
    payload = "\0".join(
        (transaction["transaction_id"], target, baseline_hash, nonce)
    )
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _atomic_write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            yaml.safe_dump(data, handle, allow_unicode=True, sort_keys=False)
            handle.flush()
            os.fsync(handle.fileno())
            temp_path = Path(handle.name)
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def _atomic_create_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            yaml.safe_dump(data, handle, allow_unicode=True, sort_keys=False)
            handle.flush()
            os.fsync(handle.fileno())
            temp_path = Path(handle.name)
        try:
            os.link(temp_path, path)
        except FileExistsError as exc:
            raise TransactionError(
                f"transaction already exists; retry begin: {path.name}"
            ) from exc
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def _atomic_replace_from_stage(staged: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with staged.open("rb") as source, tempfile.NamedTemporaryFile(
            mode="wb",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as destination:
            for chunk in iter(lambda: source.read(65536), b""):
                destination.write(chunk)
            destination.flush()
            os.fsync(destination.fileno())
            temp_path = Path(destination.name)
        os.replace(temp_path, target)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def _commit_order(
    target: Path, repo_root: Path, manifest: HarnessManifest
) -> tuple[int, str]:
    raw_order = (manifest.data.get("transaction") or {}).get("commit_order") or []
    for index, raw_scope in enumerate(raw_order):
        scope = (manifest.path.parent / raw_scope).resolve()
        is_directory = raw_scope.endswith(("/", "\\")) or scope.is_dir()
        if (is_directory and _within(target, scope)) or target == scope:
            return index, str(target.relative_to(repo_root))
    return len(raw_order), str(target.relative_to(repo_root))


def _preflight_changes(
    repo_root: Path,
    manifest: HarnessManifest,
    match,
    transaction: dict,
) -> list[dict]:
    prepared = []
    seen_keys = set()
    applied_keys = set(transaction.get("applied_keys") or [])
    confirmations = transaction.get("confirmations") or []
    scopes = match.write_scopes()
    chapter_targets = 0
    for change in transaction.get("changes") or []:
        if not isinstance(change, dict):
            raise TransactionError("transaction changes must be mappings")
        target_raw = change.get("target")
        staged_raw = change.get("staged")
        if not target_raw or not staged_raw:
            raise TransactionError("change requires target and staged paths")
        target = _repository_path(repo_root, target_raw)
        staged = _repository_path(repo_root, staged_raw)
        staged_parts = staged.relative_to(repo_root).parts
        if (
            ".staging" not in staged_parts
            or transaction.get("transaction_id") not in staged_parts
        ):
            raise TransactionError(
                f"staged file is outside transaction staging: {staged_raw}"
            )
        txid = transaction.get("transaction_id")
        expected_staged = target.parent / ".staging" / txid / target.name
        if staged != expected_staged:
            raise TransactionError(
                f"staged file does not mirror target: {staged_raw}"
            )
        if not _allowed_target(target, manifest, scopes):
            raise TransactionError(
                f"target is outside command write scope: {target_raw}"
            )
        normalized_target = target.relative_to(repo_root).as_posix()
        if match.route.get("chapter_target_only") and _within(
            target, repo_root / "chapters"
        ):
            chapter = (transaction.get("arguments") or {}).get("chapter")
            expected_prefix = f"CH-{int(chapter):04d}"
            if target.parent != repo_root / "chapters" or not target.name.startswith(
                expected_prefix
            ):
                raise TransactionError(
                    f"target does not match authorized chapter: {normalized_target}"
                )
            chapter_targets += 1
        if (
            match.route.get("requires_confirmation") == "when_overwriting"
            and change.get("baseline_hash") != "absent"
        ):
            expected_proof = _confirmation_proof(
                transaction, normalized_target, change.get("baseline_hash")
            )
            confirmed = any(
                isinstance(confirmation, dict)
                and confirmation.get("type") == "overwrite"
                and confirmation.get("target") == normalized_target
                and confirmation.get("status") == "CONFIRMED"
                and confirmation.get("source") == "user"
                and confirmation.get("method") == "interactive-cli"
                and confirmation.get("proof") == expected_proof
                for confirmation in confirmations
            )
            if not confirmed:
                raise TransactionError(
                    f"overwrite confirmation is required: {normalized_target}"
                )
        key = change.get("idempotency_key")
        if not key or key in seen_keys:
            raise TransactionError(f"invalid or duplicate idempotency key: {key}")
        seen_keys.add(key)
        staged_hash = change.get("staged_hash")
        if not isinstance(staged_hash, str) or not SHA256_VALUE.fullmatch(
            staged_hash
        ):
            raise TransactionError(f"invalid staged hash: {staged_raw}")
        if not staged.is_file() or sha256_file(staged) != staged_hash:
            raise TransactionError(f"staged hash mismatch: {staged_raw}")

        if key in applied_keys:
            if not target.is_file() or sha256_file(target) != staged_hash:
                raise TransactionError(f"applied target hash mismatch: {target_raw}")
            prepared.append(
                {
                    "change": change,
                    "target": target,
                    "staged": staged,
                    "skip": True,
                    "recover": False,
                }
            )
            continue

        baseline_hash = change.get("baseline_hash")
        if baseline_hash == "absent":
            if target.exists():
                if target.is_file() and sha256_file(target) == staged_hash:
                    prepared.append(
                        {
                            "change": change,
                            "target": target,
                            "staged": staged,
                            "skip": True,
                            "recover": True,
                        }
                    )
                    continue
                raise TransactionError(f"baseline expected absent target: {target_raw}")
        elif not isinstance(baseline_hash, str) or not SHA256_VALUE.fullmatch(
            baseline_hash
        ):
            raise TransactionError(f"invalid baseline hash: {target_raw}")
        elif not target.is_file() or sha256_file(target) != baseline_hash:
            if target.is_file() and sha256_file(target) == staged_hash:
                prepared.append(
                    {
                        "change": change,
                        "target": target,
                        "staged": staged,
                        "skip": True,
                        "recover": True,
                    }
                )
                continue
            raise TransactionError(f"baseline hash mismatch: {target_raw}")
        prepared.append(
            {
                "change": change,
                "target": target,
                "staged": staged,
                "skip": False,
                "recover": False,
            }
        )
    if match.route.get("chapter_target_only") and chapter_targets != 1:
        raise TransactionError("command requires exactly one authorized chapter target")
    prepared.sort(
        key=lambda item: _commit_order(item["target"], repo_root, manifest)
    )
    return prepared


def _validate_pipeline_completion(
    manifest: HarnessManifest,
    route: dict,
    transaction: dict,
    expected_quoted_lines: list[dict] | None = None,
    chapter_context: dict | None = None,
) -> None:
    pipeline_name = route.get("pipeline")
    if not pipeline_name:
        return
    if transaction.get("pipeline") != pipeline_name:
        raise TransactionError(
            f"transaction pipeline does not match command pipeline: {pipeline_name}"
        )
    pipeline = (manifest.data.get("pipelines") or {}).get(pipeline_name)
    if not isinstance(pipeline, dict):
        raise TransactionError(f"command pipeline is not defined: {pipeline_name}")

    gates = {
        gate.get("gate"): gate
        for gate in transaction.get("gates") or []
        if isinstance(gate, dict) and gate.get("gate")
    }
    stages = {
        stage.get("name"): stage
        for stage in transaction.get("stages") or []
        if isinstance(stage, dict) and stage.get("name")
    }
    for required_stage in pipeline.get("stages") or []:
        if not isinstance(required_stage, dict) or not required_stage.get("required"):
            continue
        handler = required_stage.get("handler")
        if handler == "transaction-commit":
            continue
        if handler == "transaction-archive":
            if transaction.get("archive_state") not in {"COMPLETE", "NOT_DUE"}:
                raise TransactionError(
                    f"required archive state is incomplete: "
                    f"{transaction.get('archive_state')}"
                )
            continue
        stage_name = required_stage.get("name")
        if handler in {"deterministic-gate", "semantic-gate", "transaction-gate"}:
            gate = gates.get(stage_name)
            if gate is None:
                raise TransactionError(f"required gate is missing: {stage_name}")
            allowed_statuses = set(
                required_stage.get("allowed_statuses")
                or {"PASS", "WARN", "NOT_APPLICABLE"}
            )
            if gate.get("status") not in allowed_statuses:
                raise TransactionError(f"required gate did not pass: {stage_name}")
            required_evidence = set(required_stage.get("required_evidence") or [])
            if handler == "semantic-gate" and required_evidence:
                evidence_items = [
                    item
                    for item in (gate.get("evidence") or [])
                    if isinstance(item, dict) and item.get("key")
                ]
                evidence_keys = {
                    item.get("key") for item in evidence_items
                }
                missing_evidence = sorted(required_evidence - evidence_keys)
                if missing_evidence:
                    raise TransactionError(
                        "required semantic evidence key is missing: "
                        f"{stage_name} ({', '.join(missing_evidence)})"
                    )
                if SPEECH_AUDIT_KEY in required_evidence:
                    audit_item = next(
                        (
                            item
                            for item in evidence_items
                            if item.get("key") == SPEECH_AUDIT_KEY
                        ),
                        None,
                    )
                    audited_lines = (audit_item or {}).get("audited_lines") or []
                    if not isinstance(audited_lines, list):
                        raise TransactionError(
                            f"{stage_name} evidence {SPEECH_AUDIT_KEY} requires "
                            "an audited_lines list"
                        )
                    for audit_entry in audited_lines:
                        if not isinstance(audit_entry, dict):
                            raise TransactionError(
                                f"{stage_name} audited_lines entries must be mappings"
                            )
                        line_no = audit_entry.get("line")
                        verdict = audit_entry.get("verdict")
                        rationale = audit_entry.get("rationale")
                        if not isinstance(line_no, int) or line_no < 1:
                            raise TransactionError(
                                f"{stage_name} audited_lines entry requires a "
                                "positive integer line"
                            )
                        if verdict not in SPEECH_AUDIT_VERDICTS:
                            raise TransactionError(
                                f"{stage_name} audited line {line_no} has invalid "
                                f"verdict: {verdict}"
                            )
                        if not isinstance(rationale, str) or not rationale.strip():
                            raise TransactionError(
                                f"{stage_name} audited line {line_no} requires "
                                "a non-empty rationale"
                            )
                    audited_line_numbers = {
                        entry.get("line")
                        for entry in audited_lines
                        if isinstance(entry, dict)
                    }
                    expected_line_numbers = {
                        entry.get("line")
                        for entry in (expected_quoted_lines or [])
                        if isinstance(entry, dict) and entry.get("line")
                    }
                    uncovered = sorted(expected_line_numbers - audited_line_numbers)
                    if uncovered:
                        raise TransactionError(
                            f"{stage_name} speech transcript is missing lines: "
                            f"{', '.join(str(line) for line in uncovered)}"
                        )
                if DIALOGUE_CLARITY_AUDIT_KEY in required_evidence:
                    audit_item = next(
                        (
                            item
                            for item in evidence_items
                            if item.get("key") == DIALOGUE_CLARITY_AUDIT_KEY
                        ),
                        None,
                    )
                    _validate_dialogue_clarity_audit(
                        stage_name, audit_item, chapter_context
                    )
        else:
            stage = stages.get(stage_name)
            if stage is None:
                raise TransactionError(f"required stage is missing: {stage_name}")
            if stage.get("status") not in {"PASS", "WARN", "NOT_APPLICABLE"}:
                raise TransactionError(f"required stage did not pass: {stage_name}")
            if (
                stage.get("status") == "NOT_APPLICABLE"
                and not stage.get("reason")
            ):
                raise TransactionError(
                    f"NOT_APPLICABLE stage requires reason: {stage_name}"
                )


def _verification_command(manifest: HarnessManifest, gate_name: str) -> str:
    verification = manifest.data.get("verification") or {}
    for entries in verification.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if (
                isinstance(entry, dict)
                and entry.get("name") == gate_name
                and entry.get("command")
            ):
                return entry["command"]
    raise TransactionError(
        f"required deterministic gate has no command: {gate_name}"
    )


def _staged_artifact(
    repo_root: Path, prepared: list[dict], artifact: str
) -> Path:
    candidates = []
    for item in prepared:
        relative_target = item["target"].relative_to(repo_root).as_posix()
        if artifact == "chapter" and relative_target.startswith("chapters/"):
            candidates.append(item["staged"])
        if artifact == "style" and relative_target == "writespec/style-guide.md":
            candidates.append(item["staged"])
        if artifact == "outline" and relative_target == "world/outline.md":
            candidates.append(item["staged"])
    if len(candidates) != 1:
        raise TransactionError(
            f"deterministic gate requires exactly one staged {artifact} file"
        )
    return candidates[0]


def _expected_quoted_lines(
    repo_root: Path, prepared: list[dict]
) -> list[dict] | None:
    """Enumerate all quoted lines in the staged chapter for speech-audit gates.
    Returns None when no chapter artifact is present (read-only pipelines)."""
    try:
        chapter_path = _staged_artifact(repo_root, prepared, "chapter")
    except TransactionError:
        return None
    try:
        text = chapter_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise TransactionError(f"cannot read staged chapter: {exc}") from exc
    return find_quoted_lines(text)


def _staged_chapter_context(
    repo_root: Path, prepared: list[dict]
) -> dict | None:
    try:
        chapter_path = _staged_artifact(repo_root, prepared, "chapter")
    except TransactionError:
        return None
    try:
        text = chapter_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise TransactionError(f"cannot read staged chapter: {exc}") from exc
    return {
        "source": chapter_path.relative_to(repo_root).as_posix(),
        "source_hash": sha256_file(chapter_path),
        "lines": text.splitlines(),
    }


def _non_empty_string(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _non_empty_string_list(value) -> bool:
    return isinstance(value, list) and bool(value) and all(
        _non_empty_string(item) for item in value
    )


def _validate_dialogue_clarity_audit(
    stage_name: str, audit_item: dict | None, chapter_context: dict | None
) -> None:
    label = f"{stage_name} evidence {DIALOGUE_CLARITY_AUDIT_KEY}"
    if not isinstance(audit_item, dict):
        raise TransactionError(f"{label} must be a mapping")
    if chapter_context is None:
        raise TransactionError(f"{label} requires a staged chapter")
    if audit_item.get("source") != chapter_context["source"]:
        raise TransactionError(f"{label} source does not match staged chapter")
    source_hash = audit_item.get("source_hash")
    if (
        not isinstance(source_hash, str)
        or SHA256_VALUE.fullmatch(source_hash) is None
        or source_hash != chapter_context["source_hash"]
    ):
        raise TransactionError(f"{label} source_hash does not match staged chapter")

    lines = chapter_context["lines"]
    scan_scope = audit_item.get("scan_scope")
    if not isinstance(scan_scope, dict):
        raise TransactionError(f"{label} scan_scope must be a mapping")
    if scan_scope.get("start_line") != 1 or scan_scope.get("end_line") != len(lines):
        raise TransactionError(f"{label} scan_scope must cover the complete chapter")

    counts = audit_item.get("risk_category_counts")
    if not isinstance(counts, dict) or set(counts) != DIALOGUE_RISK_CATEGORIES:
        raise TransactionError(
            f"{label} risk_category_counts must cover all risk categories"
        )
    if any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in counts.values()
    ):
        raise TransactionError(
            f"{label} risk_category_counts values must be non-negative integers"
        )

    key_dialogues = audit_item.get("key_dialogues")
    if not isinstance(key_dialogues, list):
        raise TransactionError(f"{label} key_dialogues must be a list")
    unresolved = audit_item.get("unresolved_items")
    if not isinstance(unresolved, list):
        raise TransactionError(f"{label} unresolved_items must be a list")
    if unresolved:
        raise TransactionError(f"{label} unresolved_items must be empty for PASS")

    observed_counts = {category: 0 for category in DIALOGUE_RISK_CATEGORIES}
    for index, dialogue in enumerate(key_dialogues):
        item_label = f"{label} key_dialogues[{index}]"
        if not isinstance(dialogue, dict):
            raise TransactionError(f"{item_label} must be a mapping")
        start_line = dialogue.get("start_line")
        end_line = dialogue.get("end_line")
        if (
            not isinstance(start_line, int)
            or isinstance(start_line, bool)
            or not isinstance(end_line, int)
            or isinstance(end_line, bool)
            or start_line < 1
            or end_line < start_line
            or end_line > len(lines)
        ):
            raise TransactionError(f"{item_label} has invalid line range")
        excerpt = dialogue.get("excerpt")
        if not _non_empty_string(excerpt):
            raise TransactionError(f"{item_label} requires a non-empty excerpt")
        declared_text = "\n".join(lines[start_line - 1 : end_line])
        if excerpt not in declared_text:
            raise TransactionError(
                f"{item_label} excerpt is not present in the declared lines"
            )
        categories = dialogue.get("risk_categories")
        if (
            not isinstance(categories, list)
            or not categories
            or len(categories) != len(set(categories))
            or any(category not in DIALOGUE_RISK_CATEGORIES for category in categories)
        ):
            raise TransactionError(f"{item_label} has invalid risk_categories")
        for category in categories:
            observed_counts[category] += 1
        for field in ("core_referent", "character_stance", "causal_role"):
            if not _non_empty_string(dialogue.get(field)):
                raise TransactionError(f"{item_label} requires {field}")
        if not _non_empty_string_list(dialogue.get("context_anchors")):
            raise TransactionError(f"{item_label} requires context_anchors")
        verdict = dialogue.get("verdict")
        if verdict not in DIALOGUE_CLARITY_VERDICTS:
            raise TransactionError(f"{item_label} has invalid verdict: {verdict}")
        if verdict == "resolved_after_auto_fix":
            trace = dialogue.get("repair_trace")
            if not isinstance(trace, dict):
                raise TransactionError(f"{item_label} requires repair_trace")
            for field in (
                "original_excerpt",
                "ambiguity_reason",
                "anchor_strategy",
                "equivalence_basis",
            ):
                if not _non_empty_string(trace.get(field)):
                    raise TransactionError(
                        f"{item_label} repair_trace requires {field}"
                    )
    if counts != observed_counts:
        raise TransactionError(
            f"{label} risk_category_counts do not match key_dialogues"
        )

    no_match_reason = audit_item.get("no_match_reason")
    if not key_dialogues and not _non_empty_string(no_match_reason):
        raise TransactionError(f"{label} requires no_match_reason when no key dialogue matches")
    if key_dialogues and no_match_reason not in {None, ""}:
        raise TransactionError(f"{label} no_match_reason is only valid for zero matches")


def _apply_dialogue_clarity_migration_scan(
    repo_root: Path, transaction: dict
) -> None:
    gate = next(
        (
            item
            for item in (transaction.get("gates") or [])
            if isinstance(item, dict) and item.get("gate") == "presentation-scan"
        ),
        None,
    )
    if gate is None:
        gate = next(
            (
                item
                for item in (transaction.get("gates") or [])
                if isinstance(item, dict) and item.get("gate") == "scan"
            ),
            None,
        )
    evidence = next(
        (
            item
            for item in ((gate or {}).get("evidence") or [])
            if isinstance(item, dict) and item.get("key") == DIALOGUE_CLARITY_SCAN_KEY
        ),
        None,
    )
    if not isinstance(evidence, dict):
        return
    unresolved = evidence.get("unresolved_items")
    if not isinstance(unresolved, list) or unresolved:
        raise TransactionError(
            f"{DIALOGUE_CLARITY_SCAN_KEY}.unresolved_items must be an empty list"
        )

    formal_chapters = {}
    for path in sorted((repo_root / "chapters").glob("CH-*.txt")):
        match = re.match(r"^(CH-\d{4})(?:-|\.)", path.name)
        if match is None:
            continue
        chapter = match.group(1)
        if chapter in formal_chapters:
            raise TransactionError(f"duplicate formal chapter target: {chapter}")
        formal_chapters[chapter] = path

    scanned = evidence.get("scanned_chapters")
    if not isinstance(scanned, list):
        raise TransactionError(
            f"{DIALOGUE_CLARITY_SCAN_KEY}.scanned_chapters must be a list"
        )
    scanned_by_chapter = {}
    for index, item in enumerate(scanned):
        label = f"{DIALOGUE_CLARITY_SCAN_KEY}.scanned_chapters[{index}]"
        if not isinstance(item, dict):
            raise TransactionError(f"{label} must be a mapping")
        chapter = item.get("chapter")
        if chapter not in formal_chapters or chapter in scanned_by_chapter:
            raise TransactionError(f"{label} has invalid or duplicate chapter")
        path = formal_chapters[chapter]
        source = path.relative_to(repo_root).as_posix()
        if item.get("source") != source:
            raise TransactionError(f"{label}.source does not match formal chapter")
        if item.get("source_hash") != sha256_file(path):
            raise TransactionError(f"{label}.source_hash does not match formal chapter")
        scanned_by_chapter[chapter] = item
    if set(scanned_by_chapter) != set(formal_chapters):
        missing = sorted(set(formal_chapters) - set(scanned_by_chapter))
        raise TransactionError(
            f"{DIALOGUE_CLARITY_SCAN_KEY} did not scan all formal chapters: "
            + ", ".join(missing)
        )

    issues = evidence.get("issues")
    if not isinstance(issues, list):
        raise TransactionError(f"{DIALOGUE_CLARITY_SCAN_KEY}.issues must be a list")
    clarity_issues = {}
    for index, item in enumerate(issues):
        label = f"{DIALOGUE_CLARITY_SCAN_KEY}.issues[{index}]"
        if not isinstance(item, dict):
            raise TransactionError(f"{label} must be a mapping")
        chapter = item.get("chapter")
        path = formal_chapters.get(chapter)
        if path is None:
            raise TransactionError(f"{label}.chapter was not scanned")
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            raise TransactionError(f"cannot read formal chapter: {exc}") from exc
        start_line = item.get("start_line")
        end_line = item.get("end_line")
        if (
            not isinstance(start_line, int)
            or isinstance(start_line, bool)
            or not isinstance(end_line, int)
            or isinstance(end_line, bool)
            or start_line < 1
            or end_line < start_line
            or end_line > len(lines)
        ):
            raise TransactionError(f"{label} has invalid line range")
        excerpt = item.get("excerpt")
        if not _non_empty_string(excerpt) or excerpt not in "\n".join(
            lines[start_line - 1 : end_line]
        ):
            raise TransactionError(f"{label}.excerpt is not present in formal chapter")
        categories = item.get("risk_categories")
        if (
            not isinstance(categories, list)
            or not categories
            or len(categories) != len(set(categories))
            or any(category not in DIALOGUE_RISK_CATEGORIES for category in categories)
        ):
            raise TransactionError(f"{label} has invalid risk_categories")
        if not _non_empty_string(item.get("reason")):
            raise TransactionError(f"{label}.reason must be a non-empty string")
        clarity_issues.setdefault(chapter, []).append(item)

    migration = transaction.setdefault("migration", {})
    presentation_issues = migration.get("presentation_issues")
    if not isinstance(presentation_issues, dict):
        presentation_issues = migration.get("issues") or {}
    combined_issues = {
        chapter: list(items) for chapter, items in presentation_issues.items()
    }
    for chapter, items in clarity_issues.items():
        combined_issues.setdefault(chapter, []).extend(
            f"dialogue clarity lines {item['start_line']}-{item['end_line']}: "
            f"{item['reason']}"
            for item in items
        )
    migration["presentation_issues"] = presentation_issues
    migration["dialogue_clarity_issues"] = clarity_issues
    migration["issues"] = combined_issues
    migration["chapters"] = sorted(combined_issues)


def _validate_reader_dialogue_cross_check(
    repo_root: Path, transaction: dict
) -> None:
    if not isinstance(transaction.get("reader_evaluation"), dict):
        return
    audit_item = None
    for gate in transaction.get("gates") or []:
        if not isinstance(gate, dict) or gate.get("gate") != "narrative-integrity":
            continue
        audit_item = next(
            (
                item
                for item in (gate.get("evidence") or [])
                if isinstance(item, dict)
                and item.get("key") == DIALOGUE_CLARITY_AUDIT_KEY
            ),
            None,
        )
        break
    if not isinstance(audit_item, dict):
        return
    report_path = _reader_evaluation_file(repo_root, transaction)
    try:
        report = load_reader_evaluation_report(report_path)
    except ReaderEvaluationContractError as exc:
        raise TransactionError(str(exc)) from exc
    cross_check = report.get("dialogue_clarity_cross_check") or {}
    reviewed = cross_check.get("reviewed_dialogues") or []
    reviewed_refs = {
        (item.get("line"), item.get("excerpt"))
        for item in reviewed
        if isinstance(item, dict)
    }
    audited_refs = {
        (item.get("start_line"), item.get("excerpt"))
        for item in (audit_item.get("key_dialogues") or [])
        if isinstance(item, dict)
    }
    if reviewed_refs != audited_refs:
        raise TransactionError(
            "reader dialogue_clarity_cross_check does not cover the audited "
            "key dialogues"
        )


def _payoff_evidence_file(repo_root: Path, transaction: dict) -> Path:
    payoff = (transaction.get("plan_contract") or {}).get("payoff")
    if not isinstance(payoff, dict):
        raise TransactionError(
            "payoff-contract gate requires plan_contract.payoff in transaction record"
        )
    raw_path = payoff.get("evidence_path")
    if not isinstance(raw_path, str) or not raw_path:
        raise TransactionError(
            "payoff-contract gate requires plan_contract.payoff.evidence_path"
        )
    resolved = _repository_path(repo_root, raw_path)
    if not resolved.is_file():
        raise TransactionError(
            f"payoff evidence file does not exist: {raw_path}"
        )
    return resolved


def _reader_evaluation_file(
    repo_root: Path, transaction: dict, chapter_context: dict | None = None
) -> Path:
    evaluation = transaction.get("reader_evaluation")
    if not isinstance(evaluation, dict):
        raise TransactionError(
            "reader-evaluation-contract gate requires reader_evaluation in transaction record"
        )
    raw_path = evaluation.get("artifact_path")
    if not isinstance(raw_path, str) or not raw_path:
        raise TransactionError(
            "reader-evaluation-contract gate requires reader_evaluation.artifact_path"
        )
    artifact_hash = evaluation.get("artifact_hash")
    if not isinstance(artifact_hash, str) or SHA256_VALUE.fullmatch(artifact_hash) is None:
        raise TransactionError(
            "reader-evaluation-contract gate requires a valid reader_evaluation.artifact_hash"
        )
    resolved = _repository_path(repo_root, raw_path)
    if not resolved.is_file():
        raise TransactionError(
            f"reader evaluation report does not exist: {raw_path}"
        )
    if sha256_file(resolved) != artifact_hash:
        raise TransactionError(
            "reader-evaluation-contract gate reader_evaluation.artifact_hash "
            "does not match the report file"
        )
    if chapter_context is not None:
        try:
            report = load_reader_evaluation_report(resolved)
        except ReaderEvaluationContractError as exc:
            raise TransactionError(str(exc)) from exc
        cross_check = report.get("dialogue_clarity_cross_check")
        if not isinstance(cross_check, dict):
            raise TransactionError(
                "reader evaluation dialogue_clarity_cross_check is missing"
            )
        if cross_check.get("source_hash") != chapter_context["source_hash"]:
            raise TransactionError(
                "reader evaluation dialogue_clarity_cross_check.source_hash "
                "does not match staged chapter"
            )
    return resolved


def _execute_deterministic_gates(
    repo_root: Path,
    manifest: HarnessManifest,
    route: dict,
    transaction_path: Path,
    transaction: dict,
    prepared: list[dict],
) -> None:
    pipeline = (manifest.data.get("pipelines") or {}).get(
        route.get("pipeline"), {}
    )
    gates = transaction.setdefault("gates", [])
    chapter_context = _staged_chapter_context(repo_root, prepared)
    for stage in pipeline.get("stages") or []:
        if (
            not isinstance(stage, dict)
            or stage.get("handler") != "deterministic-gate"
            or not stage.get("required")
        ):
            continue
        gate_name = stage.get("name")
        command = _verification_command(manifest, gate_name)
        arguments = shlex.split(command, posix=os.name != "nt")
        resolved_arguments = []
        for argument in arguments:
            if argument == "<chapter_file>":
                argument = str(_staged_artifact(repo_root, prepared, "chapter"))
            elif argument == "<style_file>":
                argument = str(_staged_artifact(repo_root, prepared, "style"))
            elif argument == "<outline_file>":
                argument = str(_staged_artifact(repo_root, prepared, "outline"))
            elif argument == "<payoff_evidence_file>":
                argument = str(_payoff_evidence_file(repo_root, transaction))
            elif argument == "<reader_evaluation_file>":
                argument = str(
                    _reader_evaluation_file(
                        repo_root, transaction, chapter_context=chapter_context
                    )
                )
            resolved_arguments.append(argument)
        if resolved_arguments and resolved_arguments[0].lower() in {
            "python",
            "python3",
        }:
            resolved_arguments[0] = sys.executable
        result = subprocess.run(
            resolved_arguments,
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        output = "\n".join(
            value.strip() for value in (result.stdout, result.stderr) if value.strip()
        )
        gate = next(
            (
                item
                for item in gates
                if isinstance(item, dict) and item.get("gate") == gate_name
            ),
            None,
        )
        if gate is None:
            gate = {"gate": gate_name}
            gates.append(gate)
        gate.update(
            {
                "kind": "deterministic",
                "required": True,
                "status": "PASS" if result.returncode == 0 else "FAIL",
                "summary": output[:2000] or f"exit code {result.returncode}",
                "evidence": [
                    {
                        "command": command,
                        "exit_code": result.returncode,
                        "output_hash": "sha256:"
                        + hashlib.sha256(output.encode("utf-8")).hexdigest(),
                    }
                ],
            }
        )
        _atomic_write_yaml(transaction_path, transaction)
        if result.returncode != 0:
            raise TransactionError(
                f"deterministic gate failed: {gate_name} ({result.returncode})"
            )


def _record_executor_gate(
    manifest: HarnessManifest,
    transaction: dict,
    gate_name: str,
    *,
    status: str,
    summary: str,
    evidence: list[dict],
    reason: str | None = None,
) -> None:
    configured = {
        entry.get("name")
        for entry in (manifest.data.get("verification") or {}).get(
            "transaction_gates", []
        )
        if isinstance(entry, dict)
    }
    if gate_name not in configured:
        return
    gates = transaction.setdefault("gates", [])
    gate = next(
        (
            item
            for item in gates
            if isinstance(item, dict) and item.get("gate") == gate_name
        ),
        None,
    )
    if gate is None:
        gate = {"gate": gate_name}
        gates.append(gate)
    gate.update(
        {
            "kind": "deterministic",
            "required": True,
            "status": status,
            "summary": summary,
            "evidence": evidence,
        }
    )
    if reason is not None:
        gate["reason"] = reason
    else:
        gate.pop("reason", None)


def _validate_archive_changes(
    repo_root: Path,
    manifest: HarnessManifest,
    route: dict,
    transaction: dict,
    prepared: list[dict],
) -> None:
    pipeline = (manifest.data.get("pipelines") or {}).get(
        route.get("pipeline"), {}
    )
    archive_stages = [
        stage
        for stage in pipeline.get("stages") or []
        if isinstance(stage, dict)
        and stage.get("handler") == "transaction-archive"
    ]
    if not archive_stages:
        return
    archive_state = transaction.get("archive_state")
    if archive_state == "NOT_DUE" and any(
        stage.get("required") for stage in archive_stages
    ):
        if prepared:
            raise TransactionError("NOT_DUE archive change set must be empty")
        return
    if archive_state != "COMPLETE":
        return

    archive_targets = {
        (manifest.path.parent / entry.get("path", "")).resolve()
        for entry in manifest.data.get("archive") or []
        if isinstance(entry, dict) and entry.get("path")
    }
    world_root = (manifest.path.parent / "../world/").resolve()
    targets = {item["target"] for item in prepared}
    has_archive_target = any(target in archive_targets for target in targets)
    has_active_target = any(
        _within(target, world_root) and target not in archive_targets
        for target in targets
    )
    if not has_archive_target or not has_active_target:
        raise TransactionError(
            "archive change set requires an archive target and an active index target"
        )
    archive_gate = next(
        (
            gate
            for gate in transaction.get("gates") or []
            if isinstance(gate, dict) and gate.get("gate") == "archive-integrity"
        ),
        None,
    )
    if (
        archive_gate is None
        or archive_gate.get("status") not in {"PASS", "WARN"}
        or not archive_gate.get("evidence")
    ):
        raise TransactionError(
            "COMPLETE archive requires archive-integrity PASS/WARN evidence"
        )


def _validate_local_links(
    repo_root: Path, prepared: list[dict], *, staged: bool
) -> None:
    future_targets = {item["target"] for item in prepared}
    content_sources = {
        item["target"]: item["staged"] if staged else item["target"]
        for item in prepared
    }

    def validate_destination(source_target: Path, raw_destination: str) -> None:
        raw_destination = raw_destination.strip()
        if raw_destination.startswith("<") and ">" in raw_destination:
            raw_destination = raw_destination[1 : raw_destination.index(">")]
        else:
            raw_destination = raw_destination.split(maxsplit=1)[0]
        if "://" in raw_destination or raw_destination.startswith(
            ("mailto:", "data:")
        ):
            return
        raw_path, separator, raw_fragment = raw_destination.partition("#")
        destination = unquote(raw_path.split("?", 1)[0])
        resolved = (
            source_target
            if not destination
            else (source_target.parent / destination).resolve()
        )
        if not _within(resolved, repo_root):
            raise TransactionError(
                f"local link escapes repository: {source_target} -> {raw_destination}"
            )
        if resolved not in future_targets and not resolved.is_file():
            raise TransactionError(
                f"local link target is missing: {source_target} -> {raw_destination}"
            )
        if not separator or not raw_fragment:
            return
        linked_source = content_sources.get(resolved, resolved)
        try:
            linked_text = linked_source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise TransactionError(
                f"cannot validate anchor in {linked_source}: {exc}"
            ) from exc
        anchors = {unquote(value) for value in HTML_ID.findall(linked_text)}
        for heading in MARKDOWN_HEADING.findall(linked_text):
            slug = heading.strip().lower().replace(" ", "-")
            slug = re.sub(r"[^\w\u4e00-\u9fff-]", "", slug)
            anchors.add(slug)
        fragment = unquote(raw_fragment).lower()
        if fragment not in {anchor.lower() for anchor in anchors}:
            raise TransactionError(
                f"local link anchor is missing: {source_target} -> {raw_destination}"
            )

    for item in prepared:
        target = item["target"]
        if target.suffix.lower() != ".md":
            continue
        source = item["staged"] if staged else target
        try:
            text = source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise TransactionError(f"cannot validate links in {source}: {exc}") from exc
        for raw_destination in MARKDOWN_LINK.findall(text):
            validate_destination(target, raw_destination)
        definitions = {
            label.lower(): destination
            for label, destination in MARKDOWN_REFERENCE_DEFINITION.findall(text)
        }
        for label in MARKDOWN_REFERENCE_USE.findall(text):
            destination = definitions.get(label.lower())
            if destination is None:
                raise TransactionError(
                    f"Markdown reference definition is missing: {target} -> {label}"
                )
            validate_destination(target, destination)


def _transaction_number(
    transaction_dir: Path, pattern: re.Pattern, number_group: str
) -> tuple[int, list[dict]]:
    highest = 0
    matched_records = []
    if not transaction_dir.is_dir():
        return highest, matched_records
    for path in transaction_dir.glob("*.yaml"):
        match = pattern.fullmatch(path.name)
        if not match:
            continue
        highest = max(highest, int(match.group(number_group)))
        matched_records.append(load_transaction(path))
    return highest, matched_records


def _transaction_records(transaction_dir: Path) -> list[dict]:
    if not transaction_dir.is_dir():
        return []
    return [load_transaction(path) for path in transaction_dir.glob("*.yaml")]


def _highest_completed_chapter(transaction_dir: Path) -> int:
    highest = 0
    for record in _transaction_records(transaction_dir):
        if record.get("command") != "create-chapter" or record.get("state") != "COMPLETE":
            continue
        chapter = (record.get("arguments") or {}).get("chapter")
        if isinstance(chapter, str) and chapter.isdigit():
            highest = max(highest, int(chapter))
    return highest


def _periodic_trigger_names(manifest: HarnessManifest) -> set[str]:
    return {
        trigger
        for gate in (manifest.data.get("verification") or {}).get(
            "periodic_gates", []
        )
        if isinstance(gate, dict)
        for trigger in gate.get("triggers") or []
        if isinstance(trigger, str)
    }


def _completed_trigger_events(
    transaction_dir: Path, manifest: HarnessManifest
) -> dict[str, set[str]]:
    trigger_names = _periodic_trigger_names(manifest)
    completed = {}
    for record in _transaction_records(transaction_dir):
        if record.get("state") != "COMPLETE":
            continue
        events = set(record.get("events") or []) & trigger_names
        transaction_id = record.get("transaction_id")
        if events and isinstance(transaction_id, str):
            completed[transaction_id] = events
    return completed


def _enforce_periodic_gates(
    transaction_dir: Path,
    manifest: HarnessManifest,
    match,
) -> None:
    if match.name != "create-chapter" or match.mode != "full":
        return
    chapter = int(match.arguments["chapter"])
    periodic_gates = (manifest.data.get("verification") or {}).get(
        "periodic_gates", []
    )
    records = _transaction_records(transaction_dir)
    for gate in periodic_gates:
        if not isinstance(gate, dict) or not gate.get("blocks_next_cycle"):
            continue
        interval = gate.get("interval_chapters")
        pipeline = gate.get("pipeline")
        pipeline_route = next(
            (
                route
                for route in manifest.data.get("routes", {}).get("commands", [])
                if isinstance(route, dict) and route.get("pipeline") == pipeline
            ),
            None,
        )
        valid_audits = []
        for record in records:
            if (
                validate_transaction(record)
                or record.get("state") != "COMPLETE"
                or record.get("command") != "audit-originality"
                or record.get("pipeline") != pipeline
                or not isinstance(record.get("coverage"), dict)
                or pipeline_route is None
            ):
                continue
            try:
                _validate_pipeline_completion(manifest, pipeline_route, record)
            except TransactionError:
                continue
            audit_gate = next(
                (
                    item
                    for item in record.get("gates") or []
                    if isinstance(item, dict) and item.get("gate") == "audit"
                ),
                None,
            )
            if (
                audit_gate is None
                or audit_gate.get("status") not in {"PASS", "WARN"}
                or not audit_gate.get("evidence")
            ):
                continue
            valid_audits.append(record)
        trigger_names = set(gate.get("triggers") or [])
        event_records = {
            transaction_id
            for transaction_id, events in _completed_trigger_events(
                transaction_dir, manifest
            ).items()
            if events & trigger_names
        }
        covered_events = {
            event_id
            for record in valid_audits
            for event_id in record["coverage"].get("events", [])
        }
        uncovered_events = event_records - covered_events
        if uncovered_events:
            raise TransactionError(
                "periodic event gate is required before chapter "
                f"{chapter}: {', '.join(sorted(uncovered_events))}"
            )
        if not isinstance(interval, int) or interval <= 0 or chapter <= interval:
            continue
        checkpoint = ((chapter - 1) // interval) * interval
        satisfied = any(
            isinstance(record["coverage"].get("through_chapter"), int)
            and record["coverage"].get("through_chapter", -1) >= checkpoint
            for record in valid_audits
        )
        if not satisfied:
            raise TransactionError(
                f"periodic gate is required before chapter {chapter}: "
                f"{gate.get('name')} through chapter {checkpoint}"
            )


def _style_guide_path(repo_root: Path, manifest: HarnessManifest) -> Path:
    routes = manifest.data.get("routes") or {}
    for entries in routes.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict) and entry.get("name") == "style-guide":
                raw_path = entry.get("path")
                if isinstance(raw_path, str) and raw_path:
                    return (manifest.path.parent / raw_path).resolve()
    return repo_root / "writespec" / "style-guide.md"


def _outline_title(outline_path: Path) -> str:
    try:
        text = outline_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise TransactionError(f"cannot read world/outline.md: {exc}") from exc
    frontmatter = _yaml_frontmatter(text)
    for key in ("book_title", "novel_title"):
        value = frontmatter.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    match = OUTLINE_BOOK_TITLE.search(text)
    if match and match.group(1).strip():
        return match.group(1).strip()
    raise TransactionError("cannot find book title in world/outline.md")


def _basis_value_is_present(value) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(isinstance(item, str) and item.strip() for item in value)
    return False


def _normalized_label(value: str) -> str:
    return re.sub(r"\s+", "", value)


def _enforce_chapter_style_basis(
    repo_root: Path, manifest: HarnessManifest, match
) -> None:
    if match.name != "create-chapter" or match.mode != "full":
        return
    outline_title = _outline_title(repo_root / "world" / "outline.md")
    style_path = _style_guide_path(repo_root, manifest)
    try:
        style_text = style_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise TransactionError(f"cannot read style guide: {exc}") from exc
    frontmatter = _yaml_frontmatter(style_text)
    basis = frontmatter.get("style_basis")
    if not isinstance(basis, dict):
        raise TransactionError(
            "INV-STYLE-001: style_basis is required for chapter creation"
        )
    missing = [
        field for field in STYLE_BASIS_FIELDS
        if not _basis_value_is_present(basis.get(field))
    ]
    if missing:
        raise TransactionError(
            "INV-STYLE-001: style_basis field is missing: "
            + ", ".join(missing)
        )
    if _normalized_label(str(basis["title"])) != _normalized_label(outline_title):
        raise TransactionError(
            "INV-STYLE-001: style_basis.title does not match world/outline.md"
        )


def begin_transaction(
    repo_root: Path, manifest_path: Path, raw_text: str
) -> Path:
    repo_root = repo_root.resolve()
    try:
        manifest = HarnessManifest.load(manifest_path)
        match = manifest.resolve(raw_text)
    except (OSError, CommandResolutionError) as exc:
        raise TransactionError(str(exc)) from exc
    is_read_only_record = (
        match.route.get("side_effect") == "read_only"
        and bool(match.route.get("pipeline"))
    )
    if not match.write_scopes() and not is_read_only_record:
        raise TransactionError(
            f"command does not authorize writes: {match.name}"
        )

    transaction_dir = _record_directory(repo_root, manifest)
    _enforce_periodic_gates(transaction_dir, manifest, match)
    _enforce_chapter_style_basis(repo_root, manifest, match)
    chapter = match.arguments.get("chapter")
    migration = None
    parent_transaction = None
    if match.name == "migrate-presentation":
        issues = _scan_presentation_issues(repo_root)
        migration = {
            "migration_state": "SCANNED",
            "chapters": sorted(issues),
            "issues": issues,
            "presentation_issues": issues,
            "dialogue_clarity_issues": {},
            "completed": [],
            "failed": [],
        }
    parent_command = match.route.get("requires_parent_authorization")
    if parent_command:
        if chapter is None:
            raise TransactionError("migration child requires a chapter argument")
        parent = _migration_parent_authorization(
            transaction_dir, parent_command, f"CH-{int(chapter):04d}"
        )
        parent_transaction = parent["transaction_id"]
    plan_contract = None
    if match.route.get("plan_contract") == "required":
        if chapter is None:
            raise TransactionError("plan-bound command requires a chapter argument")
        try:
            plan_contract = chapter_binding(
                repo_root / "world" / "outline.md", int(chapter)
            )
        except (OutlineContractError, ValueError) as exc:
            raise TransactionError(str(exc)) from exc
    if match.name in {
        "create-chapter",
        "migrate-presentation-chapter",
        "polish-chapter",
    } and chapter is not None:
        chapter_number = int(chapter)
        prefix = f"TX-CH-{chapter_number:04d}"
        pattern = re.compile(
            rf"{re.escape(prefix)}-R(?P<revision>\d{{2}})\.yaml"
        )
        highest, records = _transaction_number(
            transaction_dir, pattern, "revision"
        )
        active = [
            record
            for record in records
            if record.get("state")
            in {"PREFLIGHT", "PREPARING", "PREPARED", "COMMITTING"}
        ]
        if active:
            raise TransactionError(f"active transaction exists: {prefix}")
        revision = highest + 1
        if revision > 99:
            raise TransactionError(f"chapter revision limit exceeded: {prefix}")
        transaction_id = f"{prefix}-R{revision:02d}"
    else:
        command_slug = match.name.upper()
        prefix = f"TX-CMD-{command_slug}"
        pattern = re.compile(
            rf"{re.escape(prefix)}-(?P<run>\d{{4}})-R01\.yaml"
        )
        highest, records = _transaction_number(transaction_dir, pattern, "run")
        active = [
            record
            for record in records
            if record.get("state")
            in {"PREFLIGHT", "PREPARING", "PREPARED", "COMMITTING"}
        ]
        if active:
            raise TransactionError(f"active transaction exists: {prefix}")
        run_number = highest + 1
        if run_number > 9999:
            raise TransactionError(f"command run limit exceeded: {prefix}")
        transaction_id = f"{prefix}-{run_number:04d}-R01"

    transaction = {
        "schema": TRANSACTION_SCHEMA,
        "transaction_id": transaction_id,
        "source_command": raw_text,
        "command": match.name,
        "mode": match.mode,
        "pipeline": match.route.get("pipeline"),
        "arguments": match.arguments,
        "state": "PREFLIGHT",
        "archive_state": "NOT_CHECKED",
        "stages": [],
        "gates": [],
        "changes": [],
        "applied_keys": [],
        "confirmations": [],
        "confirmation_nonce": secrets.token_hex(16),
        "events": [],
        "recovery": {
            "last_successful_stage": None,
            "failed_stage": None,
            "message": None,
        },
    }
    if plan_contract is not None:
        transaction["plan_contract"] = plan_contract
    if migration is not None:
        transaction["migration"] = migration
    if parent_transaction is not None:
        transaction["parent_transaction"] = parent_transaction
    if match.name == "audit-originality":
        transaction["coverage"] = {
            "through_chapter": _highest_completed_chapter(transaction_dir),
            "events": sorted(
                _completed_trigger_events(transaction_dir, manifest)
            ),
        }
    transaction_path = transaction_dir / f"{transaction_id}.yaml"
    _atomic_create_yaml(transaction_path, transaction)
    return transaction_path


def confirm_overwrite(
    repo_root: Path,
    manifest_path: Path,
    transaction_path: Path,
    target: str,
    confirmation_text: str,
) -> dict:
    repo_root = repo_root.resolve()
    try:
        manifest = HarnessManifest.load(manifest_path)
    except (OSError, CommandResolutionError) as exc:
        raise TransactionError(str(exc)) from exc
    transaction_path = _transaction_path(
        repo_root,
        _record_directory(repo_root, manifest),
        transaction_path,
    )
    transaction = load_transaction(transaction_path)
    if transaction_path.name != f"{transaction.get('transaction_id')}.yaml":
        raise TransactionError("transaction filename does not match transaction ID")
    if transaction.get("state") not in {"PREFLIGHT", "PREPARING", "PREPARED"}:
        raise TransactionError(
            f"cannot confirm overwrite from state: {transaction.get('state')}"
        )
    try:
        match = manifest.resolve(transaction.get("source_command", ""))
    except (OSError, CommandResolutionError) as exc:
        raise TransactionError(str(exc)) from exc
    if match.route.get("requires_confirmation") != "when_overwriting":
        raise TransactionError("command does not require overwrite confirmation")
    normalized_target = _repository_path(repo_root, target).relative_to(
        repo_root
    ).as_posix()
    if confirmation_text != f"CONFIRM {normalized_target}":
        raise TransactionError("interactive overwrite confirmation text did not match")
    change = next(
        (
            item
            for item in transaction.get("changes") or []
            if isinstance(item, dict)
            and item.get("target")
            and _repository_path(repo_root, item["target"])
            .relative_to(repo_root)
            .as_posix()
            == normalized_target
        ),
        None,
    )
    if change is None or change.get("baseline_hash") == "absent":
        raise TransactionError(
            f"target is not an overwrite in this transaction: {normalized_target}"
        )
    confirmation = {
        "type": "overwrite",
        "target": normalized_target,
        "status": "CONFIRMED",
        "source": "user",
        "method": "interactive-cli",
        "proof": _confirmation_proof(
            transaction, normalized_target, change["baseline_hash"]
        ),
    }
    confirmations = transaction.setdefault("confirmations", [])
    confirmations[:] = [
        item
        for item in confirmations
        if not (
            isinstance(item, dict)
            and item.get("type") == "overwrite"
            and item.get("target") == normalized_target
        )
    ]
    confirmations.append(confirmation)
    _atomic_write_yaml(transaction_path, transaction)
    return confirmation


def commit_transaction(
    repo_root: Path, manifest_path: Path, transaction_path: Path
) -> dict:
    repo_root = repo_root.resolve()
    try:
        manifest = HarnessManifest.load(manifest_path)
    except (OSError, CommandResolutionError) as exc:
        raise TransactionError(str(exc)) from exc
    record_directory = _record_directory(repo_root, manifest)
    transaction_path = _transaction_path(
        repo_root, record_directory, transaction_path
    )
    transaction = load_transaction(transaction_path)
    expected_name = f"{transaction.get('transaction_id')}.yaml"
    if transaction_path.name != expected_name:
        raise TransactionError(
            f"transaction filename does not match transaction ID: {expected_name}"
        )
    errors = validate_transaction(transaction)
    if errors:
        raise TransactionError("; ".join(errors))
    if transaction.get("state") not in {"PREPARED", "COMMITTING"}:
        raise TransactionError(
            f"cannot commit from state: {transaction.get('state')}"
        )

    try:
        match = manifest.resolve(transaction.get("source_command", ""))
    except (OSError, CommandResolutionError) as exc:
        raise TransactionError(str(exc)) from exc
    if match.name != transaction.get("command"):
        raise TransactionError("resolved command does not match transaction command")
    if match.mode != transaction.get("mode"):
        raise TransactionError("resolved mode does not match transaction mode")
    if match.arguments != (transaction.get("arguments") or {}):
        raise TransactionError("resolved arguments do not match transaction arguments")
    if match.name == "migrate-presentation":
        current_issues = _scan_presentation_issues(repo_root)
        migration = transaction.get("migration") or {}
        recorded_issues = migration.get("presentation_issues", migration.get("issues"))
        if current_issues != recorded_issues:
            raise TransactionError("migration scan became stale before commit")
    if match.route.get("plan_contract") == "required":
        if transaction.get("plan_contract") is None:
            raise TransactionError("required plan contract binding is missing")
        validate_plan_binding(repo_root, transaction)
    if match.name == "audit-originality":
        expected_coverage = _highest_completed_chapter(record_directory)
        expected_events = sorted(
            _completed_trigger_events(record_directory, manifest)
        )
        coverage = transaction.get("coverage") or {}
        recorded_coverage = coverage.get("through_chapter")
        if (
            recorded_coverage != expected_coverage
            or coverage.get("events", []) != expected_events
        ):
            raise TransactionError(
                "audit coverage was modified or became stale: "
                f"expected chapter {expected_coverage} and events "
                f"{expected_events}"
            )
    unknown_events = set(transaction.get("events") or []) - (
        _periodic_trigger_names(manifest)
    )
    if unknown_events:
        raise TransactionError(
            f"transaction declares unknown periodic events: "
            f"{', '.join(sorted(unknown_events))}"
        )

    if not transaction.get("changes"):
        pipeline = (manifest.data.get("pipelines") or {}).get(
            match.route.get("pipeline"), {}
        )
        required_archive = any(
            isinstance(stage, dict)
            and stage.get("required")
            and stage.get("handler") == "transaction-archive"
            for stage in pipeline.get("stages") or []
        )
        read_only_record = match.route.get("side_effect") == "read_only"
        if not (
            read_only_record
            or (required_archive and transaction.get("archive_state") == "NOT_DUE")
        ):
            raise TransactionError("transaction change set is empty")
    prepared = _preflight_changes(repo_root, manifest, match, transaction)
    _execute_deterministic_gates(
        repo_root,
        manifest,
        match.route,
        transaction_path,
        transaction,
        prepared,
    )
    _validate_local_links(repo_root, prepared, staged=True)
    if prepared:
        _record_executor_gate(
            manifest,
            transaction,
            "prepared-change-set",
            status="PASS",
            summary=f"validated {len(prepared)} prepared change(s)",
            evidence=[
                {
                    "target": item["change"]["target"],
                    "staged_hash": item["change"]["staged_hash"],
                }
                for item in prepared
            ],
        )
    else:
        no_change_reason = (
            "read-only pipeline has no formal changes"
            if match.route.get("side_effect") == "read_only"
            else "archive_state is NOT_DUE"
        )
        _record_executor_gate(
            manifest,
            transaction,
            "prepared-change-set",
            status="NOT_APPLICABLE",
            summary=no_change_reason,
            evidence=[],
            reason=no_change_reason,
        )
    _atomic_write_yaml(transaction_path, transaction)
    _validate_pipeline_completion(
        manifest,
        match.route,
        transaction,
        expected_quoted_lines=_expected_quoted_lines(repo_root, prepared),
        chapter_context=_staged_chapter_context(repo_root, prepared),
    )
    _validate_reader_dialogue_cross_check(repo_root, transaction)
    if match.name == "migrate-presentation":
        _apply_dialogue_clarity_migration_scan(repo_root, transaction)
    if match.name == "init-world":
        events = transaction.setdefault("events", [])
        if "outline_initialized" not in events:
            events.append("outline_initialized")
    _validate_archive_changes(
        repo_root, manifest, match.route, transaction, prepared
    )
    if match.name == "create-chapter" and transaction.get("archive_state") == "NOT_CHECKED":
        raise TransactionError("conditional archive state was not checked")
    transaction["state"] = "COMMITTING"
    _atomic_write_yaml(transaction_path, transaction)
    try:
        for item in prepared:
            if item["skip"]:
                if item["recover"]:
                    change = item["change"]
                    transaction["applied_keys"].append(
                        change["idempotency_key"]
                    )
                    transaction["recovery"] = {
                        "last_successful_stage": (
                            f"recover:{change['idempotency_key']}"
                        ),
                        "failed_stage": None,
                        "message": None,
                    }
                    _atomic_write_yaml(transaction_path, transaction)
                continue
            _atomic_replace_from_stage(item["staged"], item["target"])
            change = item["change"]
            if sha256_file(item["target"]) != change["staged_hash"]:
                raise TransactionError(
                    f"published target hash mismatch: {change['target']}"
                )
            transaction["applied_keys"].append(change["idempotency_key"])
            transaction["recovery"] = {
                "last_successful_stage": f"commit:{change['idempotency_key']}",
                "failed_stage": None,
                "message": None,
            }
            _atomic_write_yaml(transaction_path, transaction)
        applied_keys = set(transaction.get("applied_keys") or [])
        for item in prepared:
            change = item["change"]
            if change["idempotency_key"] not in applied_keys:
                raise TransactionError(
                    f"postflight idempotency key is missing: "
                    f"{change['idempotency_key']}"
                )
            if sha256_file(item["target"]) != change["staged_hash"]:
                raise TransactionError(
                    f"postflight target hash mismatch: {change['target']}"
                )
        _validate_local_links(repo_root, prepared, staged=False)
        _record_executor_gate(
            manifest,
            transaction,
            "postflight-consistency",
            status="PASS",
            summary=f"verified {len(prepared)} published target(s)",
            evidence=[
                {
                    "target": item["change"]["target"],
                    "published_hash": item["change"]["staged_hash"],
                }
                for item in prepared
            ],
        )
        _atomic_write_yaml(transaction_path, transaction)
    except (OSError, TransactionError) as exc:
        transaction["recovery"] = {
            "last_successful_stage": transaction.get("recovery", {}).get(
                "last_successful_stage"
            ),
            "failed_stage": "commit",
            "message": str(exc),
        }
        _atomic_write_yaml(transaction_path, transaction)
        if isinstance(exc, TransactionError):
            raise
        raise TransactionError(f"commit failed: {exc}") from exc

    if match.name == "migrate-presentation":
        migration = transaction["migration"]
        migration["migration_state"] = (
            "AUTHORIZED" if migration.get("chapters") else "COMPLETE"
        )
    if match.name == "migrate-presentation-chapter":
        record_migration_child_completion(record_directory, transaction)
    transaction["state"] = "COMPLETE"
    transaction["completed_at"] = datetime.now(timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
    transaction["recovery"] = {
        "last_successful_stage": "commit",
        "failed_stage": None,
        "message": None,
    }
    _atomic_write_yaml(transaction_path, transaction)
    return transaction
