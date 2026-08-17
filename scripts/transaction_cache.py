from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import shutil
import tempfile

import yaml


STAGING_ROOTS = (
    Path("chapters/.staging"),
    Path("world/.staging"),
    Path("analysis/.staging"),
    Path("metadata/.staging"),
)
TRANSACTION_DIRECTORY = Path("world/.transactions")
OBSERVATION_FILE = Path(".local/transaction-cache-observations.yaml")
RETENTION = timedelta(days=10)
ACTIVE_STATES = {"PREFLIGHT", "PREPARING", "PREPARED", "COMMITTING"}


class CacheError(ValueError):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_timestamp(value) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _load_observations(repo_root: Path) -> dict[str, str]:
    path = repo_root / OBSERVATION_FILE
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise CacheError(f"cannot read cache observation state: {exc}") from exc
    observations = data.get("observations") if isinstance(data, dict) else None
    if not isinstance(observations, dict) or any(
        not isinstance(key, str) or _parse_timestamp(value) is None
        for key, value in observations.items()
    ):
        raise CacheError("cache observation state is invalid")
    return dict(observations)


def _write_observations(repo_root: Path, observations: dict[str, str]) -> None:
    path = repo_root / OBSERVATION_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_yaml(path, {"observations": observations})


def _atomic_write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temp_path = Path(handle.name)
    try:
        with handle:
            yaml.safe_dump(
                data,
                handle,
                allow_unicode=True,
                sort_keys=True,
            )
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _directory_measure(paths: list[Path]) -> tuple[int, int]:
    files = [
        path
        for directory in paths
        for path in directory.rglob("*")
        if path.is_file()
    ]
    return len(files), sum(path.stat().st_size for path in files)


def _load_transaction_records(repo_root: Path) -> dict[str, dict | None]:
    transaction_dir = repo_root / TRANSACTION_DIRECTORY
    records = {}
    if not transaction_dir.is_dir():
        return records
    for path in transaction_dir.glob("*.yaml"):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError):
            data = None
        if not isinstance(data, dict) or data.get("transaction_id") != path.stem:
            records[path.stem] = None
        else:
            records[path.stem] = data
    return records


def _staging_groups(repo_root: Path) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = {}
    for relative_root in STAGING_ROOTS:
        staging_root = repo_root / relative_root
        if not staging_root.is_dir():
            continue
        for path in staging_root.iterdir():
            if path.is_dir():
                groups.setdefault(path.name, []).append(path)
    return groups


def _orphan_reference_status(repo_root: Path, paths: list[Path]) -> str:
    candidate_paths = {path.resolve() for path in paths}
    references = {path.relative_to(repo_root).as_posix() for path in paths}
    references.update(path.name for path in paths)
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        resolved = path.resolve()
        if any(
            resolved == candidate or candidate in resolved.parents
            for candidate in candidate_paths
        ):
            continue
        relative_parts = path.relative_to(repo_root).parts
        if relative_parts and relative_parts[0] in {".git", ".local"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return "UNKNOWN"
        if any(reference in text for reference in references):
            return "REFERENCED"
    return "CLEAR"


def _retention_result(
    observation_key: str,
    reference_time: datetime | None,
    observations: dict[str, str],
    now: datetime,
    *,
    unobserved_reason: str,
    expired_reason: str,
) -> tuple[bool, str]:
    if reference_time is None:
        reference_time = _parse_timestamp(observations.get(observation_key))
        if reference_time is None:
            return False, unobserved_reason
    if now - reference_time >= RETENTION:
        return True, expired_reason
    return False, "RETENTION_ACTIVE"


def inspect_cache(
    repo_root: Path,
    *,
    now: datetime | None = None,
    record_observations: bool = False,
) -> dict:
    repo_root = repo_root.resolve()
    now = now or _utc_now()
    if now.tzinfo is None:
        raise CacheError("cache inspection time must include a timezone")
    now = now.astimezone(timezone.utc)
    observations = _load_observations(repo_root)
    records = _load_transaction_records(repo_root)
    groups = _staging_groups(repo_root)
    observation_changed = False
    items = []

    for item_id, paths in sorted(groups.items()):
        file_count, byte_count = _directory_measure(paths)
        relative_paths = sorted(path.relative_to(repo_root).as_posix() for path in paths)
        record = records.get(item_id)
        if item_id in records:
            kind = "transaction"
            state = record.get("state") if record else "INVALID"
            if record is None:
                eligible, reason = False, "TRANSACTION_INVALID"
            elif record.get("staging_state") == "CLEANED":
                eligible, reason = False, "ALREADY_CLEANED"
            elif state in ACTIVE_STATES:
                eligible, reason = False, "TRANSACTION_ACTIVE"
            elif state == "COMPLETE":
                completed_at = record.get("completed_at")
                reference_time = _parse_timestamp(completed_at)
                if completed_at is not None and reference_time is None:
                    eligible, reason = False, "INVALID_COMPLETED_AT"
                else:
                    key = f"transaction:{item_id}"
                    if reference_time is None and key not in observations and record_observations:
                        observations[key] = now.isoformat()
                        observation_changed = True
                    eligible, reason = _retention_result(
                        key,
                        reference_time,
                        observations,
                        now,
                        unobserved_reason="LEGACY_UNOBSERVED",
                        expired_reason="RETENTION_EXPIRED",
                    )
            elif state == "ABORTED":
                eligible, reason = True, "ABORTED"
            else:
                eligible, reason = False, "TRANSACTION_NOT_COMPLETE"
        else:
            kind = "orphan"
            state = None
            key = f"orphan:{item_id}"
            if key not in observations and record_observations:
                observations[key] = now.isoformat()
                observation_changed = True
            reference_status = _orphan_reference_status(repo_root, paths)
            if reference_status == "REFERENCED":
                eligible, reason = False, "ORPHAN_REFERENCED"
            elif reference_status == "UNKNOWN":
                eligible, reason = False, "ORPHAN_REFERENCE_UNKNOWN"
            else:
                eligible, reason = _retention_result(
                    key,
                    None,
                    observations,
                    now,
                    unobserved_reason="ORPHAN_UNOBSERVED",
                    expired_reason="ORPHAN_EXPIRED",
                )

        items.append(
            {
                "id": item_id,
                "kind": kind,
                "state": state,
                "paths": relative_paths,
                "file_count": file_count,
                "bytes": byte_count,
                "eligible": eligible,
                "reason": reason,
            }
        )

    if record_observations and observation_changed:
        _write_observations(repo_root, observations)

    return {
        "retention_days": RETENTION.days,
        "total_bytes": sum(item["bytes"] for item in items),
        "eligible_count": sum(1 for item in items if item["eligible"]),
        "eligible_bytes": sum(item["bytes"] for item in items if item["eligible"]),
        "active_transactions": sum(
            1 for item in items if item["reason"] == "TRANSACTION_ACTIVE"
        ),
        "orphan_count": sum(1 for item in items if item["kind"] == "orphan"),
        "items": items,
    }


def _item_by_id(inventory: dict, item_id: str) -> dict | None:
    return next(
        (item for item in inventory["items"] if item["id"] == item_id), None
    )


def _safe_staging_path(repo_root: Path, relative_path: str, item_id: str) -> Path:
    path = (repo_root / relative_path).resolve()
    allowed_parents = {(repo_root / root).resolve() for root in STAGING_ROOTS}
    if path.parent not in allowed_parents or path.name != item_id:
        raise CacheError(f"unsafe staging path: {relative_path}")
    return path


def _update_transaction_state(
    repo_root: Path,
    transaction_id: str,
    *,
    abort: bool = False,
    cleaned: bool = False,
) -> None:
    path = repo_root / TRANSACTION_DIRECTORY / f"{transaction_id}.yaml"
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise CacheError(f"cannot read transaction {transaction_id}: {exc}") from exc
    if not isinstance(data, dict) or data.get("transaction_id") != transaction_id:
        raise CacheError(f"transaction record is invalid: {transaction_id}")
    if abort:
        if data.get("state") not in ACTIVE_STATES | {"FAILED"}:
            raise CacheError(f"transaction is no longer abortable: {transaction_id}")
        data["state"] = "ABORTED"
    if cleaned:
        if data.get("state") not in {"COMPLETE", "ABORTED"}:
            raise CacheError(f"transaction is not terminal: {transaction_id}")
        data["staging_state"] = "CLEANED"
    _atomic_write_yaml(path, data)


def _remove_observation(repo_root: Path, item: dict) -> None:
    observations = _load_observations(repo_root)
    key = f"{item['kind']}:{item['id']}"
    if key in observations:
        del observations[key]
        _write_observations(repo_root, observations)


def cleanup_cache(
    repo_root: Path,
    selected_ids: list[str],
    *,
    confirmed: bool,
    now: datetime | None = None,
) -> dict:
    if not confirmed:
        raise CacheError("cleanup confirmation is required")
    if len(selected_ids) != len(set(selected_ids)):
        raise CacheError("duplicate cache item selection")
    repo_root = repo_root.resolve()
    cleaned = []

    # The preview records first observation only in local transient state.
    initial_inventory = inspect_cache(
        repo_root, now=now, record_observations=True
    )
    known_ids = {item["id"] for item in initial_inventory["items"]}
    missing = [item_id for item_id in selected_ids if item_id not in known_ids]
    if missing:
        raise CacheError(f"cache item does not exist: {missing[0]}")
    for item_id in selected_ids:
        try:
            inventory = inspect_cache(repo_root, now=now)
            item = _item_by_id(inventory, item_id)
            if item is None:
                raise CacheError("cache item does not exist")
            abort = item["kind"] == "transaction" and item["state"] in (
                ACTIVE_STATES | {"FAILED"}
            )
            if not item["eligible"] and not abort:
                raise CacheError(f"cache item is not eligible: {item['reason']}")
            paths = [
                _safe_staging_path(repo_root, relative_path, item_id)
                for relative_path in item["paths"]
            ]
            if abort:
                _update_transaction_state(repo_root, item_id, abort=True)
            for path in paths:
                shutil.rmtree(path)
            if item["kind"] == "transaction":
                _update_transaction_state(repo_root, item_id, cleaned=True)
            _remove_observation(repo_root, item)
            cleaned.append(item_id)
        except (CacheError, OSError) as exc:
            return {
                "cleaned": cleaned,
                "failed": {"id": item_id, "error": str(exc)},
            }
    return {"cleaned": cleaned, "failed": None}
