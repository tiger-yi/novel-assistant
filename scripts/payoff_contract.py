from pathlib import Path
import re

import yaml


PAYOFF_SCHEMA = "novel-harness/payoff-evidence/v1"
PAYOFF_POLICY_SCHEMA = "novel-harness/payoff-policy/v1"
CHAPTER_ID = re.compile(r"CH-\d{4}")
PAYOFF_ID = re.compile(r"PAY-CH-\d{4}-\d{2}")
SHA256 = re.compile(r"sha256:[0-9a-f]{64}")
PAYOFF_TYPES = {
    "POWER",
    "RESOURCE",
    "STATUS",
    "REVERSAL",
    "INFORMATION",
    "RELATIONSHIP",
    "AUTONOMY",
    "COMPETENCE",
}
PROFILES = {
    "standard": {"minimum_payoffs": 2, "major_window": 12},
    "high": {"minimum_payoffs": 3, "major_window": 8},
}
PERSISTENCE = {"scene", "next-chapter", "short-cycle", "stage"}
CLIMAX_LEVELS = {"none", "small", "major"}
ESCALATION_LEVELS = {"routine", "cross-chapter", "stage"}
MODES = {"new", "published-revision"}
PAYOFF_PLAN_FIELDS = (
    "id",
    "type",
    "event_key",
    "promise",
    "action",
    "state_delta",
    "recognition",
    "cost",
    "persistence",
)
PAYOFF_EVIDENCE_FIELDS = (*PAYOFF_PLAN_FIELDS, "evidence_refs")


class PayoffContractError(ValueError):
    pass


def _non_empty(value) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value) and all(_non_empty(item) for item in value)
    return value is not None


def load_payoff_evidence(path: Path) -> dict:
    try:
        evidence = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise PayoffContractError(f"cannot load payoff evidence: {exc}") from exc
    if not isinstance(evidence, dict):
        raise PayoffContractError("payoff evidence root must be a mapping")
    return evidence


def _validate_payoff_items(payoffs, chapter_id, profile, *, require_evidence):
    errors = []
    if not isinstance(payoffs, list):
        return ["payoffs must be a list"]
    minimum = PROFILES[profile]["minimum_payoffs"]
    if len(payoffs) < minimum:
        errors.append(f"{profile} profile requires at least {minimum} payoffs")

    seen_ids = set()
    seen_events = set()
    payoff_types = set()
    expected_prefix = f"PAY-{chapter_id}-"
    for index, payoff in enumerate(payoffs):
        label = f"payoffs[{index}]"
        if not isinstance(payoff, dict):
            errors.append(f"{label} must be a mapping")
            continue
        fields = PAYOFF_EVIDENCE_FIELDS if require_evidence else PAYOFF_PLAN_FIELDS
        for field in fields:
            if not _non_empty(payoff.get(field)):
                errors.append(f"{label}.{field} is required")
        payoff_id = payoff.get("id")
        if (
            not isinstance(payoff_id, str)
            or PAYOFF_ID.fullmatch(payoff_id) is None
            or not payoff_id.startswith(expected_prefix)
        ):
            errors.append(f"{label}.id must belong to {chapter_id}")
        elif payoff_id in seen_ids:
            errors.append(f"duplicate payoff id: {payoff_id}")
        else:
            seen_ids.add(payoff_id)

        event_key = payoff.get("event_key")
        if isinstance(event_key, str) and event_key:
            if event_key in seen_events:
                errors.append(f"duplicate event_key: {event_key}")
            seen_events.add(event_key)

        payoff_type = payoff.get("type")
        if payoff_type not in PAYOFF_TYPES:
            errors.append(f"{label}.type is invalid")
        else:
            payoff_types.add(payoff_type)
        if payoff.get("persistence") not in PERSISTENCE:
            errors.append(f"{label}.persistence is invalid")

    if len(payoff_types) < 2:
        errors.append("chapter requires at least 2 payoff types")
    return errors


def validate_payoff_policy(policy: dict) -> list[str]:
    if not isinstance(policy, dict):
        return ["payoff_policy must be a mapping"]
    errors = []
    if policy.get("schema") != PAYOFF_POLICY_SCHEMA:
        errors.append(f"payoff_policy.schema must be {PAYOFF_POLICY_SCHEMA}")
    activation = policy.get("activation_chapter")
    if not isinstance(activation, int) or activation < 1:
        errors.append("payoff_policy.activation_chapter must be a positive integer")
    if policy.get("default_profile") not in PROFILES:
        errors.append("payoff_policy.default_profile must be standard or high")
    book_high = policy.get("book_opening_high_through")
    if not isinstance(book_high, int) or book_high < 0:
        errors.append("payoff_policy.book_opening_high_through must be non-negative")
    volume_high = policy.get("volume_opening_high_count")
    if not isinstance(volume_high, int) or volume_high < 0:
        errors.append("payoff_policy.volume_opening_high_count must be non-negative")
    return errors


def expected_payoff_profile(
    policy: dict, chapter_number: int, volume_start: int
) -> str:
    if chapter_number <= policy["book_opening_high_through"]:
        return "high"
    if chapter_number - volume_start < policy["volume_opening_high_count"]:
        return "high"
    return policy["default_profile"]


def validate_payoff_plan(
    plan: dict, chapter_id: str, expected_profile: str
) -> list[str]:
    if not isinstance(plan, dict):
        return ["payoff_contract must be a mapping"]
    errors = []
    profile = plan.get("profile")
    if profile != expected_profile:
        errors.append(f"profile must be {expected_profile}")
        profile = expected_profile
    payoffs = plan.get("payoffs")
    errors.extend(
        _validate_payoff_items(
            payoffs, chapter_id, profile, require_evidence=False
        )
    )
    payoff_by_id = {
        item.get("id"): item
        for item in payoffs or []
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    primary = payoff_by_id.get(plan.get("primary_payoff_id"))
    if primary is None:
        errors.append("primary_payoff_id must reference a declared payoff")
    elif primary.get("persistence") == "scene":
        errors.append("primary payoff state delta must persist beyond the scene")
    if plan.get("climax") not in CLIMAX_LEVELS:
        errors.append("climax must be none, small, or major")
    if plan.get("escalation") not in ESCALATION_LEVELS:
        errors.append("escalation must be routine, cross-chapter, or stage")
    if not _non_empty(plan.get("escalation_from")):
        errors.append("escalation_from is required")
    return errors


def payoff_plan_window_item(plan: dict, chapter_id: str) -> dict | None:
    if not isinstance(plan, dict):
        return None
    payoffs = plan.get("payoffs")
    if not isinstance(payoffs, list):
        return None
    primary_id = plan.get("primary_payoff_id")
    primary = next(
        (
            item
            for item in payoffs
            if isinstance(item, dict) and item.get("id") == primary_id
        ),
        None,
    )
    if primary is None:
        return None
    return {
        "chapter_id": chapter_id,
        "primary_type": primary.get("type"),
        "climax": plan.get("climax"),
        "escalation": plan.get("escalation"),
    }


def validate_payoff_plan_window(window: list[dict], profile: str) -> list[str]:
    if not window:
        return []
    return _validate_rolling_window(window, profile, window[-1]["chapter_id"])


def _validate_rolling_window(window, profile, chapter_id):
    errors = []
    if not isinstance(window, list) or not window:
        return ["rolling_window must be a non-empty list"]
    seen_chapters = set()
    chapter_numbers = []
    for index, item in enumerate(window):
        label = f"rolling_window[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be a mapping")
            continue
        item_chapter = item.get("chapter_id")
        if not isinstance(item_chapter, str) or CHAPTER_ID.fullmatch(item_chapter) is None:
            errors.append(f"{label}.chapter_id must match CH-NNNN")
        elif item_chapter in seen_chapters:
            errors.append(f"duplicate rolling chapter: {item_chapter}")
        else:
            seen_chapters.add(item_chapter)
            chapter_numbers.append(int(item_chapter.removeprefix("CH-")))
        if item.get("primary_type") not in PAYOFF_TYPES:
            errors.append(f"{label}.primary_type is invalid")
        if item.get("climax") not in CLIMAX_LEVELS:
            errors.append(f"{label}.climax is invalid")
        if item.get("escalation") not in ESCALATION_LEVELS:
            errors.append(f"{label}.escalation is invalid")

    if chapter_numbers != sorted(chapter_numbers):
        errors.append("rolling_window chapters must be ordered")
    if window[-1].get("chapter_id") != chapter_id:
        errors.append("rolling_window must end at the current chapter")
    if len(window) >= 2:
        if window[-1].get("primary_type") == window[-2].get("primary_type"):
            errors.append("adjacent primary payoff types must differ")
        if profile == "high" and not any(
            item.get("escalation") in {"cross-chapter", "stage"}
            for item in window[-2:]
        ):
            errors.append(
                "high profile requires cross-chapter escalation within two chapters"
            )
    if len(window) >= 3:
        recent = window[-3:]
        if len({item.get("primary_type") for item in recent}) < 3:
            errors.append("each three-chapter window requires three payoff types")
        if not any(item.get("climax") in {"small", "major"} for item in recent):
            errors.append("each three-chapter window requires a small climax")

    major_window = PROFILES[profile]["major_window"]
    if len(window) >= major_window:
        recent = window[-major_window:]
        if not any(item.get("climax") == "major" for item in recent):
            errors.append(
                f"{profile} profile requires a major payoff within {major_window} chapters"
            )
    return errors


def validate_payoff_evidence(evidence: dict) -> list[str]:
    if not isinstance(evidence, dict):
        return ["payoff evidence root must be a mapping"]
    errors = []
    if evidence.get("schema") != PAYOFF_SCHEMA:
        errors.append(f"schema must be {PAYOFF_SCHEMA}")
    chapter_id = evidence.get("chapter_id")
    if not isinstance(chapter_id, str) or CHAPTER_ID.fullmatch(chapter_id) is None:
        errors.append("chapter_id must match CH-NNNN")
        chapter_id = "CH-0000"
    profile = evidence.get("profile")
    if profile not in PROFILES:
        errors.append("profile must be standard or high")
        profile = "standard"
    mode = evidence.get("mode")
    if mode not in MODES:
        errors.append("mode must be new or published-revision")

    activation = evidence.get("activation")
    if not isinstance(activation, dict):
        errors.append("activation must be a mapping")
    else:
        if activation.get("non_retroactive") is not True:
            errors.append("activation.non_retroactive must be true")
        starts_at = activation.get("starts_at")
        if not isinstance(starts_at, str) or CHAPTER_ID.fullmatch(starts_at) is None:
            errors.append("activation.starts_at must match CH-NNNN")

    payoffs = evidence.get("payoffs")
    errors.extend(
        _validate_payoff_items(
            payoffs, chapter_id, profile, require_evidence=True
        )
    )
    primary_id = evidence.get("primary_payoff_id")
    payoff_by_id = {
        item.get("id"): item
        for item in payoffs or []
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    primary = payoff_by_id.get(primary_id)
    if primary is None:
        errors.append("primary_payoff_id must reference a declared payoff")
    elif primary.get("persistence") == "scene":
        errors.append("primary payoff state delta must persist beyond the scene")

    errors.extend(
        _validate_rolling_window(evidence.get("rolling_window"), profile, chapter_id)
    )

    if mode == "published-revision":
        revision = evidence.get("published_revision")
        if not isinstance(revision, dict):
            errors.append("published_revision must be a mapping")
        else:
            source_hash = revision.get("source_hash")
            if not isinstance(source_hash, str) or SHA256.fullmatch(source_hash) is None:
                errors.append("published_revision.source_hash must be sha256")
            if not _non_empty(revision.get("downstream_impact")):
                errors.append("published_revision.downstream_impact is required")
            if revision.get("approval_status") != "approved":
                errors.append("published_revision.approval_status must be approved")
    return errors
