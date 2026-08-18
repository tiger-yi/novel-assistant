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


def validate_outline_contract(contract: dict) -> list[str]:
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
        payoff_window = []
        for chapter_index, chapter in enumerate(chapters):
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
            offset = chapter_index
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
        if actual_numbers != expected_numbers:
            errors.append(f"{label} must define every chapter in its fixed range")

    if not current_found:
        errors.append("current_arc must reference a declared volume")
    return errors


def chapter_binding(path: Path, chapter_number: int) -> dict:
    contract = load_outline_contract(path)
    errors = validate_outline_contract(contract)
    if errors:
        raise OutlineContractError("; ".join(errors))
    for volume in contract["volumes"]:
        if volume["start_chapter"] <= chapter_number <= volume["end_chapter"]:
            if volume.get("planning_status") != "frozen":
                raise OutlineContractError(
                    f"chapter {chapter_number} belongs to an arc that is not frozen"
                )
            chapter_id = f"CH-{chapter_number:04d}"
            chapter = next(
                item for item in volume["chapters"] if item.get("id") == chapter_id
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
