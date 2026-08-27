from pathlib import Path
import re

import yaml


class ReaderEvaluationContractError(ValueError):
    pass


YAML_BLOCK = re.compile(r"```ya?ml\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
NO_CHANGE_HINT = re.compile(r"(?:保持现状|无需改动|无需修改|不需要改)")
SHA256_VALUE = re.compile(r"sha256:[0-9a-f]{64}")


def _non_empty_strings(value) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and item.strip() for item in value
    )


def load_reader_evaluation_report(path: Path) -> dict:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ReaderEvaluationContractError(
            f"cannot load reader evaluation report: {exc}"
        ) from exc

    report = {}
    try:
        for block in YAML_BLOCK.findall(content):
            value = yaml.safe_load(block)
            if isinstance(value, dict):
                report.update(value)
    except yaml.YAMLError as exc:
        raise ReaderEvaluationContractError(
            f"reader evaluation report has invalid YAML evidence: {exc}"
        ) from exc
    if not report:
        raise ReaderEvaluationContractError(
            "reader evaluation report requires at least one YAML evidence mapping"
        )
    return report


def _dimension_sets(value, path="report"):
    if not isinstance(value, dict):
        return
    dimensions = value.get("dimensions")
    if isinstance(dimensions, list):
        yield path, dimensions
    for key, child in value.items():
        if key != "dimensions":
            yield from _dimension_sets(child, f"{path}.{key}")


def validate_reader_evaluation_report(report: dict) -> list[str]:
    if not isinstance(report, dict):
        return ["reader evaluation report must be a mapping"]

    errors = []
    cross_check = report.get("dialogue_clarity_cross_check")
    if not isinstance(cross_check, dict):
        errors.append("dialogue_clarity_cross_check must be a mapping")
    else:
        source_hash = cross_check.get("source_hash")
        if not isinstance(source_hash, str) or SHA256_VALUE.fullmatch(source_hash) is None:
            errors.append(
                "dialogue_clarity_cross_check.source_hash must be a SHA-256 value"
            )
        reviewed = cross_check.get("reviewed_dialogues")
        if not isinstance(reviewed, list):
            errors.append(
                "dialogue_clarity_cross_check.reviewed_dialogues must be a list"
            )
            reviewed = []
        for index, item in enumerate(reviewed):
            label = f"dialogue_clarity_cross_check.reviewed_dialogues[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label} must be a mapping")
                continue
            line = item.get("line")
            if not isinstance(line, int) or isinstance(line, bool) or line < 1:
                errors.append(f"{label}.line must be a positive integer")
            for field in ("excerpt", "finding"):
                value = item.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{label}.{field} must be a non-empty string")
            if item.get("external_explanation_dependency") is not False:
                errors.append(
                    f"{label}.external_explanation_dependency must be false"
                )
        dependencies = cross_check.get("external_explanation_dependencies")
        if not isinstance(dependencies, list):
            errors.append(
                "dialogue_clarity_cross_check.external_explanation_dependencies must be a list"
            )
        elif dependencies:
            errors.append(
                "dialogue_clarity_cross_check.external_explanation_dependencies must be empty"
            )
        conflicts = cross_check.get("audit_conflicts")
        if not isinstance(conflicts, list):
            errors.append(
                "dialogue_clarity_cross_check.audit_conflicts must be a list"
            )
        elif conflicts:
            errors.append("dialogue_clarity_cross_check.audit_conflicts must be empty")
        no_match_reason = cross_check.get("no_match_reason")
        if not reviewed and (
            not isinstance(no_match_reason, str) or not no_match_reason.strip()
        ):
            errors.append(
                "dialogue_clarity_cross_check.no_match_reason is required when no dialogue is reviewed"
            )
        if reviewed and no_match_reason not in {None, ""}:
            errors.append(
                "dialogue_clarity_cross_check.no_match_reason is only valid for zero matches"
            )
    found_dimensions = False
    for persona_path, dimensions in _dimension_sets(report):
        found_dimensions = True
        for index, item in enumerate(dimensions):
            label = f"{persona_path}.dimensions[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label} must be a mapping")
                continue
            score = item.get("score")
            if not isinstance(score, (int, float)) or isinstance(score, bool):
                errors.append(f"{label}.score must be numeric")
                continue
            if score < 0 or score > 10:
                errors.append(f"{label}.score must be between 0 and 10")
                continue
            negative_refs = item.get("negative_evidence_refs")
            if score > 8.0 and not _non_empty_strings(negative_refs):
                errors.append(
                    f"{label}.negative_evidence_refs is required when score exceeds 8.0"
                )
            if score >= 8.5:
                if not _non_empty_strings(negative_refs) or len(set(negative_refs)) < 2:
                    errors.append(
                        f"{label} requires two negative_evidence_refs when score is at least 8.5"
                    )
                if not _non_empty_strings(item.get("comparative_evidence_refs")):
                    errors.append(
                        f"{label}.comparative_evidence_refs is required when score is at least 8.5"
                    )
            hint = item.get("improvement_hint")
            if score > 8.0 and (
                not isinstance(hint, str)
                or not hint.strip()
                or NO_CHANGE_HINT.search(hint)
            ):
                errors.append(
                    f"{label}.improvement_hint must name a concrete direction for scores above 8.0"
                )
    if not found_dimensions:
        errors.append("reader evaluation report requires persona dimensions")
    return errors
