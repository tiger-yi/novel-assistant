from pathlib import Path
import hashlib
import re

import yaml

try:
    from scripts.payoff_contract import (
        expected_payoff_profile,
        payoff_plan_window_item,
        validate_payoff_plan,
        validate_payoff_plan_window,
        validate_payoff_policy,
    )
except ModuleNotFoundError:  # Direct execution through scripts/validate_outline.py.
    from payoff_contract import (
        expected_payoff_profile,
        payoff_plan_window_item,
        validate_payoff_plan,
        validate_payoff_plan_window,
        validate_payoff_policy,
    )


OUTLINE_SCHEMA = "novel-harness/outline/v2"
ARC_ID = re.compile(r"ARC-\d{3}")
GOAL_ID = re.compile(r"GOAL-ARC-\d{3}")
MILESTONE_ID = re.compile(r"MS-ARC-\d{3}-\d{2}")
CHAPTER_ID = re.compile(r"CH-\d{4}")
SHA256 = re.compile(r"sha256:[0-9a-f]{64}")
PLANNING_STATUSES = {"roadmap", "frozen", "complete"}
CHAPTER_STATUSES = {"planned", "published"}
GOLDEN_THREE_ROLES = ("inciting", "feedback", "goal-lock")
GOAL_FIELDS = (
    "id",
    "result",
    "completion_conditions",
    "required_causality",
    "forbidden_outcomes",
    "completion_evidence",
)
CHAPTER_FIELDS = (
    "id",
    "task",
    "preconditions",
    "conflict",
    "outcome",
    "arc_contribution",
    "closing_pull",
    "milestone",
    "status",
)


class OutlineContractError(ValueError):
    pass


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _canonical_hash(value: dict) -> str:
    serialized = yaml.safe_dump(
        value, allow_unicode=True, sort_keys=True
    ).encode("utf-8")
    return _sha256_bytes(serialized)


def _non_empty(value) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value) and all(_non_empty(item) for item in value)
    return value is not None


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _archived_chapters(
    contract: dict, outline_path: Path | None, errors: list[str]
) -> tuple[dict[int, dict], list[dict]]:
    ranges = contract.get("archived_ranges", [])
    if ranges is None:
        ranges = []
    if not isinstance(ranges, list):
        errors.append("archived_ranges must be a list")
        return {}, []
    if ranges and outline_path is None:
        errors.append("archived_ranges requires an outline path")
        return {}, []

    chapters = {}
    valid_ranges = []
    previous_end = 0
    for index, archived_range in enumerate(ranges):
        label = f"archived_ranges[{index}]"
        if not isinstance(archived_range, dict):
            errors.append(f"{label} must be a mapping")
            continue
        start = archived_range.get("start_chapter")
        end = archived_range.get("end_chapter")
        if not isinstance(start, int) or not isinstance(end, int) or start > end:
            errors.append(f"{label} requires a valid chapter range")
            continue
        if start <= previous_end:
            errors.append("archived ranges must not overlap")
        previous_end = max(previous_end, end)
        archive_file = archived_range.get("archive_file")
        anchor = archived_range.get("anchor")
        if not isinstance(archive_file, str) or not archive_file.strip():
            errors.append(f"{label}.archive_file is required")
            continue
        if not isinstance(anchor, str) or not anchor.strip():
            errors.append(f"{label}.anchor is required")
            continue
        if not _non_empty(archived_range.get("source_summary")):
            errors.append(f"{label}.source_summary is required")
        archive_path = (outline_path.parent / archive_file).resolve()
        archive_root = (outline_path.parent / "archive").resolve()
        if not _within(archive_path, archive_root):
            errors.append(f"{label}.archive_file must be below world/archive")
            continue
        try:
            archive_text = archive_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{label}.archive_file cannot be read: {exc}")
            continue
        anchor_match = re.search(
            rf"^#{{1,6}}\s+{re.escape(anchor.strip())}\s*$",
            archive_text,
            flags=re.MULTILINE,
        )
        if anchor_match is None:
            errors.append(f"{label}.anchor is missing from archive_file")
            continue
        section_text = archive_text[anchor_match.end() :]
        heading_level = len(anchor_match.group().split()[0])
        next_heading = re.search(
            rf"^#{{1,{heading_level}}}\s+", section_text, flags=re.MULTILINE
        )
        if next_heading is not None:
            section_text = section_text[: next_heading.start()]
        block_match = re.search(r"```ya?ml\s*\n(.*?)```", section_text, re.DOTALL)
        if block_match is None:
            errors.append(f"{label}.anchor requires a YAML chapter block")
            continue
        try:
            archived_data = yaml.safe_load(block_match.group(1))
        except yaml.YAMLError as exc:
            errors.append(f"{label}.anchor YAML is invalid: {exc}")
            continue
        archived_list = (
            archived_data.get("chapters") if isinstance(archived_data, dict) else None
        )
        if not isinstance(archived_list, list):
            errors.append(f"{label}.anchor YAML requires chapters")
            continue
        archive_numbers = []
        for chapter_index, chapter in enumerate(archived_list):
            chapter_label = f"{label}.chapters[{chapter_index}]"
            if not isinstance(chapter, dict):
                errors.append(f"{chapter_label} must be a mapping")
                continue
            chapter_id = chapter.get("id")
            if not isinstance(chapter_id, str) or CHAPTER_ID.fullmatch(chapter_id) is None:
                errors.append(f"{chapter_label}.id must match CH-NNNN")
                continue
            chapter_number = int(chapter_id.removeprefix("CH-"))
            archive_numbers.append(chapter_number)
            if chapter.get("status") != "published":
                errors.append(f"{chapter_label} must be published before archiving")
            if chapter_number in chapters:
                errors.append("archived ranges must not overlap")
            chapters[chapter_number] = chapter
        if sorted(archive_numbers) != list(range(start, end + 1)):
            errors.append(f"{label} must preserve every chapter in its range")

        proof = archived_range.get("published_proof")
        if not isinstance(proof, list):
            errors.append(f"{label}.published_proof must be a list")
            continue
        proof_ids = []
        chapter_root = (outline_path.parent.parent / "chapters").resolve()
        for proof_index, item in enumerate(proof):
            proof_label = f"{label}.published_proof[{proof_index}]"
            if not isinstance(item, dict):
                errors.append(f"{proof_label} must be a mapping")
                continue
            chapter_id = item.get("chapter_id")
            chapter_file = item.get("chapter_file")
            chapter_hash = item.get("chapter_hash")
            if not isinstance(chapter_id, str) or CHAPTER_ID.fullmatch(chapter_id) is None:
                errors.append(f"{proof_label}.chapter_id must match CH-NNNN")
                continue
            proof_ids.append(int(chapter_id.removeprefix("CH-")))
            if not isinstance(chapter_file, str) or not chapter_file.strip():
                errors.append(f"{proof_label}.chapter_file is required")
                continue
            if not isinstance(chapter_hash, str) or SHA256.fullmatch(chapter_hash) is None:
                errors.append(f"{proof_label}.chapter_hash must be a sha256 digest")
                continue
            published_path = (outline_path.parent / chapter_file).resolve()
            if not _within(published_path, chapter_root) or ".staging" in published_path.parts:
                errors.append(f"{proof_label}.chapter_file must be a formal chapter target")
                continue
            try:
                actual_hash = _sha256_bytes(published_path.read_bytes())
            except OSError as exc:
                errors.append(f"{proof_label}.chapter_file cannot be read: {exc}")
                continue
            if actual_hash != chapter_hash:
                errors.append(f"{proof_label}.chapter_hash does not match published chapter")
        if sorted(proof_ids) != list(range(start, end + 1)):
            errors.append(f"{label}.published_proof must cover every archived chapter")
        valid_ranges.append({"start": start, "end": end})
    return chapters, valid_ranges


def load_outline_contract(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise OutlineContractError(f"cannot read outline: {exc}") from exc
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise OutlineContractError("outline YAML frontmatter is required")
    try:
        end = next(
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        )
    except StopIteration as exc:
        raise OutlineContractError("outline YAML frontmatter is not closed") from exc
    try:
        contract = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as exc:
        raise OutlineContractError(f"invalid outline YAML: {exc}") from exc
    if not isinstance(contract, dict):
        raise OutlineContractError("outline contract root must be a mapping")
    return contract


def validate_outline_contract(
    contract: dict, outline_path: Path | None = None
) -> list[str]:
    if not isinstance(contract, dict):
        return ["outline contract root must be a mapping"]
    errors = []
    if contract.get("schema") != OUTLINE_SCHEMA:
        errors.append(f"schema must be {OUTLINE_SCHEMA}")
    if not isinstance(contract.get("revision"), int) or contract["revision"] < 1:
        errors.append("revision must be a positive integer")
    if contract.get("status") != "frozen":
        errors.append("outline status must be frozen")
    if not _non_empty(contract.get("novel_goal")):
        errors.append("novel_goal is required")

    archived_chapters, archived_ranges = _archived_chapters(
        contract, outline_path, errors
    )

    payoff_policy = contract.get("payoff_policy")
    if payoff_policy is not None:
        errors.extend(validate_payoff_policy(payoff_policy))
        policy_valid = not validate_payoff_policy(payoff_policy)
    else:
        policy_valid = False

    volumes = contract.get("volumes")
    if not isinstance(volumes, list) or not volumes:
        return [*errors, "volumes must be a non-empty list"]

    seen_arcs = set()
    seen_goals = set()
    previous_end = 0
    current_arc = contract.get("current_arc")
    current_found = False
    for index, volume in enumerate(volumes):
        label = f"volumes[{index}]"
        if not isinstance(volume, dict):
            errors.append(f"{label} must be a mapping")
            continue
        arc_id = volume.get("id")
        if not isinstance(arc_id, str) or ARC_ID.fullmatch(arc_id) is None:
            errors.append(f"{label}.id must match ARC-NNN")
        elif arc_id in seen_arcs:
            errors.append(f"duplicate volume id: {arc_id}")
        else:
            seen_arcs.add(arc_id)
        if not _non_empty(volume.get("title")):
            errors.append(f"{label}.title is required")
        start = volume.get("start_chapter")
        end = volume.get("end_chapter")
        if not isinstance(start, int) or not isinstance(end, int) or start > end:
            errors.append(f"{label} requires a valid fixed chapter range")
            continue
        if start != previous_end + 1:
            errors.append("volume chapter ranges must be contiguous")
        previous_end = end

        planning_status = volume.get("planning_status")
        if planning_status not in PLANNING_STATUSES:
            errors.append(f"{label}.planning_status is invalid")
        if not _non_empty(volume.get("entry_cause")):
            errors.append(f"{label}.entry_cause is required")

        goal = volume.get("goal")
        if not isinstance(goal, dict):
            errors.append(f"{label}.goal must be a mapping")
            goal = {}
        for field in GOAL_FIELDS:
            if not _non_empty(goal.get(field)):
                errors.append(f"{label}.goal.{field} is required")
        goal_id = goal.get("id")
        if isinstance(goal_id, str):
            if GOAL_ID.fullmatch(goal_id) is None:
                errors.append(f"{label}.goal.id must match GOAL-ARC-NNN")
            elif goal_id in seen_goals:
                errors.append(f"duplicate volume goal id: {goal_id}")
            else:
                seen_goals.add(goal_id)

        if arc_id == current_arc:
            current_found = True
            if planning_status != "frozen":
                errors.append("current_arc must be frozen")

        milestones = volume.get("milestones")
        chapters = volume.get("chapters")
        if not isinstance(milestones, list):
            errors.append(f"{label}.milestones must be a list")
            milestones = []
        if not isinstance(chapters, list):
            errors.append(f"{label}.chapters must be a list")
            chapters = []
        if planning_status != "frozen":
            continue

        if not 3 <= len(milestones) <= 5:
            errors.append(f"{label} frozen volume requires 3-5 milestones")
        milestone_ids = set()
        previous_due = start - 1
        for milestone_index, milestone in enumerate(milestones):
            milestone_label = f"{label}.milestones[{milestone_index}]"
            if not isinstance(milestone, dict):
                errors.append(f"{milestone_label} must be a mapping")
                continue
            milestone_id = milestone.get("id")
            if (
                not isinstance(milestone_id, str)
                or MILESTONE_ID.fullmatch(milestone_id) is None
                or milestone_id in milestone_ids
            ):
                errors.append(f"{milestone_label}.id is invalid or duplicate")
            else:
                milestone_ids.add(milestone_id)
            due = milestone.get("due_chapter")
            if not isinstance(due, int) or not start <= due <= end:
                errors.append(f"{milestone_label}.due_chapter is outside volume")
            elif due <= previous_due:
                errors.append("milestone due chapters must be strictly increasing")
            else:
                previous_due = due
            if not _non_empty(milestone.get("outcome")):
                errors.append(f"{milestone_label}.outcome is required")

        expected_numbers = list(range(start, end + 1))
        actual_numbers = []
        archived_numbers = [
            number for number in archived_chapters if start <= number <= end
        ]
        combined_chapters = [
            *[item for item in chapters if isinstance(item, dict)],
            *[archived_chapters[number] for number in archived_numbers],
        ]
        payoff_window = []
        for chapter_index, chapter in enumerate(
            sorted(combined_chapters, key=lambda item: item.get("id", ""))
        ):
            chapter_label = f"{label}.chapters[{chapter_index}]"
            if not isinstance(chapter, dict):
                errors.append(f"{chapter_label} must be a mapping")
                continue
            for field in CHAPTER_FIELDS:
                if not _non_empty(chapter.get(field)):
                    errors.append(f"{chapter_label}.{field} is required")
            chapter_id = chapter.get("id")
            if isinstance(chapter_id, str) and CHAPTER_ID.fullmatch(chapter_id):
                chapter_number = int(chapter_id.removeprefix("CH-"))
                actual_numbers.append(chapter_number)
            else:
                errors.append(f"{chapter_label}.id must match CH-NNNN")
                chapter_number = None
            if chapter.get("status") not in CHAPTER_STATUSES:
                errors.append(f"{chapter_label}.status is invalid")
            if chapter.get("milestone") not in milestone_ids:
                errors.append(f"{chapter_label}.milestone is not declared")
            offset = chapter_number - start if chapter_number is not None else chapter_index
            if offset < 3:
                expected_role = GOLDEN_THREE_ROLES[offset]
                if chapter.get("golden_three_role") != expected_role:
                    errors.append(
                        f"{chapter_label}.golden_three_role must be {expected_role}"
                    )
            if (
                policy_valid
                and chapter_number is not None
                and chapter_number >= payoff_policy["activation_chapter"]
            ):
                plan = chapter.get("payoff_contract")
                if plan is None:
                    errors.append(f"{chapter_label}.payoff_contract is required")
                    continue
                profile = expected_payoff_profile(
                    payoff_policy, chapter_number, start
                )
                for error in validate_payoff_plan(plan, chapter_id, profile):
                    errors.append(f"{chapter_label}.payoff_contract: {error}")
                window_item = payoff_plan_window_item(plan, chapter_id)
                if window_item is not None:
                    payoff_window.append(window_item)
                    for error in validate_payoff_plan_window(payoff_window, profile):
                        errors.append(f"{chapter_label}.payoff_window: {error}")
        if len(actual_numbers) != len(set(actual_numbers)):
            errors.append(f"{label} active and archived chapter contracts overlap")
        if sorted(actual_numbers) != expected_numbers:
            errors.append(f"{label} must define every chapter in its fixed range")

    for archived_range in archived_ranges:
        if not any(
            isinstance(volume, dict)
            and volume.get("planning_status") == "frozen"
            and volume.get("start_chapter") <= archived_range["start"]
            and archived_range["end"] <= volume.get("end_chapter")
            for volume in volumes
        ):
            errors.append("archived range must belong wholly to a frozen volume")

    if not current_found:
        errors.append("current_arc must reference a declared volume")
    return errors


def chapter_binding(path: Path, chapter_number: int) -> dict:
    contract = load_outline_contract(path)
    errors = validate_outline_contract(contract, outline_path=path)
    if errors:
        raise OutlineContractError("; ".join(errors))
    archived_chapters, _ = _archived_chapters(contract, path, [])
    for volume in contract["volumes"]:
        if volume["start_chapter"] <= chapter_number <= volume["end_chapter"]:
            if volume.get("planning_status") != "frozen":
                raise OutlineContractError(
                    f"chapter {chapter_number} belongs to an arc that is not frozen"
                )
            chapter_id = f"CH-{chapter_number:04d}"
            chapter = next(
                (
                    item
                    for item in volume["chapters"]
                    if item.get("id") == chapter_id
                ),
                archived_chapters.get(chapter_number),
            )
            return {
                "outline_revision": contract["revision"],
                "outline_hash": _sha256_bytes(path.read_bytes()),
                "arc_id": volume["id"],
                "arc_goal_id": volume["goal"]["id"],
                "chapter_id": chapter_id,
                "chapter_contract_hash": _canonical_hash(chapter),
            }
    raise OutlineContractError(f"chapter {chapter_number} is outside the roadmap")
