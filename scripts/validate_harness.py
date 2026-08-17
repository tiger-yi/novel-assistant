import argparse
import re
import sys
from pathlib import Path

import yaml


BACKTICK_LITERAL = re.compile(r"`([^`]+)`")
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
STYLE_SCHEMA = "novel-harness/style/v1"
STYLE_READY_INV = "INV-STYLE-001"
INVARIANT_ID = re.compile(r"INV-[A-Z]+-\d{3}")
MANIFEST_V2 = "novel-harness/context/v2"
ACTIVATION_TYPES = {
    "command",
    "pipeline",
    "event",
    "periodic",
    "profile",
    "reference",
}
PIPELINE_HANDLERS = {
    "preflight",
    "agent",
    "deterministic-gate",
    "semantic-gate",
    "transaction-gate",
    "transaction-commit",
    "transaction-archive",
    "local-cache-cleanup",
    "render",
}
STYLE_REQUIRED_SECTIONS = (
    "## 2. 核心调性",
    "## 4. 排版规范",
    "### 受限视角",
    "## 7. 角色刻画重点",
    "## 11. 禁忌与避坑",
    "### 黑名单词",
)
DELEGATION_REQUIRED_OUTPUT_FIELDS = {
    "task",
    "status",
    "artifact_path",
    "artifact_hash",
    "evidence_refs",
    "blocking_risks",
    "summary",
}


def _manifest_entries(manifest):
    routes = manifest.get("routes", {})
    if not isinstance(routes, dict):
        return []
    return [
        *(routes.get("commands") or []),
        *(routes.get("specs") or []),
        *(routes.get("records") or []),
        *(manifest.get("templates") or []),
    ]


def _resolve(base, raw_path):
    return (base / raw_path).resolve()


def _is_within(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _display_path(path, repo_root):
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def _invariant_reference_files(repo_root):
    files = [repo_root / "AGENTS.md", repo_root / "README.md"]
    for directory, patterns in (
        (repo_root / "novel-harness", ("*.md", "*.yaml")),
        (repo_root / "writespec", ("*.md",)),
        (repo_root / "templates", ("*.md",)),
        (repo_root / "scripts", ("*.py",)),
        (repo_root / "tests", ("*.py",)),
    ):
        if not directory.is_dir():
            continue
        for pattern in patterns:
            files.extend(directory.rglob(pattern))
    return {path.resolve() for path in files if path.is_file()}


def _agent_markdown_targets(repo_root):
    agents_path = repo_root / "AGENTS.md"
    text = agents_path.read_text(encoding="utf-8")
    targets = set()
    for match in BACKTICK_LITERAL.finditer(text):
        raw_target = match.group(1).strip()
        if "*" in raw_target or not raw_target.endswith(".md"):
            continue
        if raw_target.startswith(("writespec/", "templates/")):
            targets.add(_resolve(repo_root, raw_target))
        elif "/" not in raw_target:
            candidate = _resolve(repo_root / "writespec", raw_target)
            if candidate.is_file():
                targets.add(candidate)
    return targets


def _document_route_targets(doc_path, repo_root):
    text = doc_path.read_text(encoding="utf-8")
    route_roots = (repo_root / "writespec", repo_root / "templates")
    targets = set()
    for match in MARKDOWN_LINK.finditer(text):
        raw_target = match.group(1).split("#", 1)[0].strip()
        if not raw_target or "://" in raw_target or not raw_target.endswith(".md"):
            continue
        target = _resolve(doc_path.parent, raw_target)
        if any(_is_within(target, route_root) for route_root in route_roots):
            targets.add(target)
    return targets


def _style_frontmatter(text):
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
        frontmatter = yaml.safe_load("\n".join(lines[1:end_index]))
    except yaml.YAMLError:
        return {}
    return frontmatter if isinstance(frontmatter, dict) else {}


def _validate_style_guide(style_path):
    try:
        text = style_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"cannot read style guide: {exc}"]

    errors = []
    frontmatter = _style_frontmatter(text)
    if frontmatter.get("schema") != STYLE_SCHEMA:
        errors.append(
            f"{STYLE_READY_INV}: style guide schema must be {STYLE_SCHEMA}"
        )
    if frontmatter.get("status") != "ready":
        errors.append(
            f"{STYLE_READY_INV}: style guide is not ready: status must be ready"
        )
    for section in STYLE_REQUIRED_SECTIONS:
        if section not in text:
            errors.append(
                f"{STYLE_READY_INV}: style guide section is missing: {section}"
            )
    return errors


def validate_repository(repo_root, style_override=None):
    repo_root = Path(repo_root).resolve()
    manifest_path = repo_root / "novel-harness" / "context.manifest.yaml"
    errors = []

    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return [f"cannot load manifest: {exc}"]

    if not isinstance(manifest, dict):
        return ["manifest root must be a mapping"]

    manifest_dir = manifest_path.parent
    entries = _manifest_entries(manifest)
    declared_paths = set()
    names = set()
    invariant_owners = {}

    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("manifest route entries must be mappings")
            continue
        name = entry.get("name")
        raw_path = entry.get("path")
        if not name or not raw_path:
            errors.append("manifest route entry requires name and path")
            continue
        if name in names:
            errors.append(f"duplicate route name: {name}")
        names.add(name)

        resolved = _resolve(manifest_dir, raw_path)
        declared_paths.add(resolved)
        if not _is_within(resolved, repo_root):
            errors.append(f"declared route path escapes repository: {raw_path}")
            continue
        if not resolved.is_file():
            errors.append(f"declared route file does not exist: {raw_path}")

        invariants = entry.get("invariants") or []
        if not isinstance(invariants, list):
            errors.append(f"route {name} invariants must be a list")
            continue
        for invariant in invariants:
            if (
                not isinstance(invariant, str)
                or INVARIANT_ID.fullmatch(invariant) is None
            ):
                errors.append(f"invalid invariant ID on route {name}: {invariant}")
                continue
            previous_owner = invariant_owners.get(invariant)
            if previous_owner is not None:
                errors.append(
                    f"duplicate invariant owner: {invariant} in "
                    f"{_display_path(previous_owner, repo_root)} and "
                    f"{_display_path(resolved, repo_root)}"
                )
                continue
            invariant_owners[invariant] = resolved
            if resolved.is_file():
                owner_text = resolved.read_text(encoding="utf-8")
                if invariant not in owner_text:
                    errors.append(
                        f"invariant owner does not define {invariant}: "
                        f"{_display_path(resolved, repo_root)}"
                    )

    routes = manifest.get("routes", {})
    commands = routes.get("commands", []) if isinstance(routes, dict) else []
    specs = routes.get("specs", []) if isinstance(routes, dict) else []
    is_v2 = manifest.get("schema") == MANIFEST_V2

    if is_v2:
        delegation = manifest.get("delegation")
        delegation_workers = set()
        if delegation is not None:
            if not isinstance(delegation, dict):
                errors.append("manifest delegation must be a mapping")
            else:
                output_contract = delegation.get("output_contract") or {}
                must_include = set(output_contract.get("must_include") or [])
                missing = DELEGATION_REQUIRED_OUTPUT_FIELDS - must_include
                if missing:
                    errors.append(
                        "delegation output_contract is missing required fields: "
                        + ", ".join(sorted(missing))
                    )
                workers = delegation.get("workers") or []
                if not isinstance(workers, list):
                    errors.append("delegation workers must be a list")
                    workers = []
                for worker in workers:
                    if not isinstance(worker, dict):
                        errors.append("delegation workers must be mappings")
                        continue
                    name = worker.get("name")
                    if not name:
                        errors.append("delegation worker requires name")
                        continue
                    if name in delegation_workers:
                        errors.append(f"duplicate delegation worker: {name}")
                    delegation_workers.add(name)
                    if worker.get("may_return") != "evidence_artifact_pointer":
                        errors.append(
                            f"delegation worker {name} must return "
                            "evidence_artifact_pointer"
                        )
        for entry in [*(commands or []), *(specs or [])]:
            if not isinstance(entry, dict):
                continue
            activation = entry.get("activation")
            if activation is None:
                errors.append(f"route {entry.get('name')} activation is required")
            elif activation not in ACTIVATION_TYPES:
                errors.append(
                    f"route {entry.get('name')} has invalid activation: {activation}"
                )
        for command in commands or []:
            if not isinstance(command, dict):
                continue
            if command.get("activation") != "command":
                errors.append(
                    f"command {command.get('name')} activation must be command"
                )
            matchers = command.get("matches") or []
            if not matchers:
                errors.append(f"command {command.get('name')} requires a matcher")
            for matcher in matchers:
                if not isinstance(matcher, dict):
                    errors.append(
                        f"command {command.get('name')} matchers must be mappings"
                    )
                    continue
                keys = {
                    key for key in ("literal", "pattern") if matcher.get(key)
                }
                if len(keys) != 1:
                    errors.append(
                        f"command {command.get('name')} matcher requires exactly "
                        "one of literal or pattern"
                    )
                mode = matcher.get("mode")
                modes = command.get("modes") or {}
                if mode and mode not in modes:
                    errors.append(
                        f"command {command.get('name')} matcher uses unknown mode: "
                        f"{mode}"
                    )

        known_routes = {
            entry.get("name")
            for entry in [*(commands or []), *(specs or [])]
            if isinstance(entry, dict) and entry.get("name")
        }
        verification = manifest.get("verification") or {}
        verification_commands = {
            entry.get("name")
            for entries in verification.values()
            if isinstance(entries, list)
            for entry in entries
            if isinstance(entry, dict) and entry.get("command")
        }
        pipelines = manifest.get("pipelines") or {}
        if not isinstance(pipelines, dict):
            errors.append("manifest pipelines must be a mapping")
        else:
            for command in commands or []:
                if not isinstance(command, dict):
                    continue
                pipeline_name = command.get("pipeline")
                if pipeline_name and pipeline_name not in pipelines:
                    errors.append(
                        f"command {command.get('name')} uses unknown pipeline "
                        f"{pipeline_name}"
                    )
            for pipeline_name, pipeline in pipelines.items():
                if not isinstance(pipeline, dict):
                    errors.append(f"pipeline {pipeline_name} must be a mapping")
                    continue
                stage_names = set()
                stages = pipeline.get("stages") or []
                if not isinstance(stages, list):
                    errors.append(f"pipeline {pipeline_name} stages must be a list")
                    continue
                for stage in stages:
                    if not isinstance(stage, dict):
                        errors.append(
                            f"pipeline {pipeline_name} stages must be mappings"
                        )
                        continue
                    stage_name = stage.get("name")
                    if not stage_name:
                        errors.append(f"pipeline {pipeline_name} stage requires name")
                    elif stage_name in stage_names:
                        errors.append(
                            f"pipeline {pipeline_name} has duplicate stage: "
                            f"{stage_name}"
                        )
                    stage_names.add(stage_name)
                    route_name = stage.get("uses")
                    if route_name not in known_routes:
                        errors.append(
                            f"pipeline {pipeline_name} uses unknown route "
                            f"{route_name}"
                        )
                    handler = stage.get("handler")
                    if handler not in PIPELINE_HANDLERS:
                        errors.append(
                            f"pipeline {pipeline_name} stage {stage_name} has "
                            f"invalid handler: {handler}"
                        )
                    if (
                        handler == "deterministic-gate"
                        and stage.get("required")
                        and stage_name not in verification_commands
                    ):
                        errors.append(
                            f"pipeline {pipeline_name} deterministic gate "
                            f"{stage_name} has no verification command"
                        )
                    if (
                        stage.get("delegable")
                        and stage.get("worker") not in delegation_workers
                    ):
                        errors.append(
                            f"pipeline {pipeline_name} stage {stage_name} uses "
                            f"unknown delegation worker: {stage.get('worker')}"
                        )
                    required_evidence = stage.get("required_evidence")
                    if required_evidence is not None:
                        if handler != "semantic-gate":
                            errors.append(
                                f"pipeline {pipeline_name} stage {stage_name} "
                                "required_evidence requires semantic-gate"
                            )
                        if (
                            not isinstance(required_evidence, list)
                            or not required_evidence
                            or any(
                                not isinstance(item, str) or not item.strip()
                                for item in required_evidence
                            )
                        ):
                            errors.append(
                                f"pipeline {pipeline_name} stage {stage_name} "
                                "required_evidence must be a non-empty string list"
                            )
                        elif len(required_evidence) != len(set(required_evidence)):
                            errors.append(
                                f"pipeline {pipeline_name} stage {stage_name} "
                                "required_evidence contains duplicates"
                            )

    seen_triggers = set()
    seen_patterns = set()
    human_doc_paths = [
        repo_root / "AGENTS.md",
        repo_root / "README.md",
    ]
    human_docs = {}
    for doc_path in human_doc_paths:
        if doc_path.is_file():
            try:
                human_docs[doc_path] = doc_path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                errors.append(f"cannot read {_display_path(doc_path, repo_root)}: {exc}")

    for command in commands or []:
        if not isinstance(command, dict):
            continue
        if is_v2:
            matchers = command.get("matches") or []
            documented_values = [
                matcher.get("literal") or matcher.get("display")
                for matcher in matchers
                if isinstance(matcher, dict)
            ]
            pattern_definitions = [
                (matcher.get("pattern"), matcher.get("display"))
                for matcher in matchers
                if isinstance(matcher, dict) and matcher.get("pattern")
            ]
        else:
            trigger = command.get("trigger")
            aliases = command.get("aliases") or []
            display_patterns = command.get("display_patterns") or []
            documented_values = [trigger, *aliases, *display_patterns]
            patterns = command.get("patterns") or []
            pattern_definitions = [
                (
                    pattern,
                    display_patterns[index]
                    if index < len(display_patterns)
                    else None,
                )
                for index, pattern in enumerate(patterns)
            ]
            if patterns and len(patterns) != len(display_patterns):
                errors.append(
                    f"command {command.get('name')} patterns require matching "
                    f"display_patterns"
                )

        for value in documented_values:
            if not value:
                continue
            if value in seen_triggers:
                errors.append(f"duplicate command trigger or alias: {value}")
            seen_triggers.add(value)
            for doc_path, doc_text in human_docs.items():
                if value not in doc_text:
                    errors.append(
                        f"command token is not documented in "
                        f"{_display_path(doc_path, repo_root)}: {value}"
                    )

        for pattern, display in pattern_definitions:
            if pattern in seen_patterns:
                errors.append(f"duplicate command pattern: {pattern}")
            seen_patterns.add(pattern)
            try:
                compiled = re.compile(pattern)
                if display:
                    example = display.replace("N", "12")
                    if compiled.fullmatch(example) is None:
                        errors.append(
                            f"command pattern does not match display example: {pattern}"
                        )
            except re.error as exc:
                errors.append(
                    f"invalid command pattern for {command.get('name')}: {exc}"
                )

        raw_path = command.get("path")
        if not raw_path:
            continue
        command_path = _resolve(manifest_dir, raw_path)
        if command_path.is_file():
            command_text = command_path.read_text(encoding="utf-8")
            if (
                is_v2
                and command.get("side_effect") in {"write", "destructive_move"}
                and "事务执行器" not in command_text
            ):
                errors.append(
                    f"write command {command.get('name')} must require transaction "
                    "executor"
                )
            for value in documented_values:
                if value and value not in command_text:
                    errors.append(
                        f"command {command.get('name')} does not declare trigger: "
                        f"{value}"
                    )

    world_data = manifest.get("world_data", {})
    if not isinstance(world_data, dict):
        errors.append("world_data must be a mapping")
        world_data = {}
    default_order = set(world_data.get("default_order") or [])
    for required in world_data.get("required") or []:
        if required not in default_order:
            errors.append(f"required world file is not in default_order: {required}")

    agents_path = repo_root / "AGENTS.md"
    if not agents_path.is_file():
        errors.append("AGENTS.md does not exist")
    else:
        agent_targets = _agent_markdown_targets(repo_root)
        for target in sorted(agent_targets - declared_paths):
            errors.append(
                f"AGENTS.md target is not declared in manifest: "
                f"{_display_path(target, repo_root)}"
            )

    readme_path = repo_root / "README.md"
    if readme_path.is_file():
        try:
            readme_targets = _document_route_targets(readme_path, repo_root)
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read README.md routes: {exc}")
        else:
            for target in sorted(readme_targets - declared_paths):
                errors.append(
                    f"README.md target is not declared in manifest: "
                    f"{_display_path(target, repo_root)}"
                )

    style_entries = [
        entry for entry in entries
        if isinstance(entry, dict) and entry.get("name") == "style-guide"
    ]
    if len(style_entries) != 1:
        errors.append("manifest requires exactly one style-guide route")
    else:
        style_path = (
            Path(style_override).resolve()
            if style_override is not None
            else _resolve(manifest_dir, style_entries[0].get("path", ""))
        )
        if style_path.is_file():
            errors.extend(_validate_style_guide(style_path))
        elif style_override is not None:
            errors.append(f"cannot read style guide: {style_path}")

    verification = manifest.get("verification", {})
    if isinstance(verification, dict):
        for gates in verification.values():
            if not isinstance(gates, list):
                continue
            for gate in gates:
                if not isinstance(gate, dict):
                    continue
                invariant = gate.get("invariant")
                raw_spec = gate.get("spec")
                owner = invariant_owners.get(invariant)
                if invariant and raw_spec and owner is not None:
                    gate_spec = _resolve(manifest_dir, raw_spec)
                    if gate_spec != owner:
                        errors.append(
                            f"verification gate {gate.get('name')} spec does not own "
                            f"{invariant}: {_display_path(gate_spec, repo_root)}"
                        )

    referenced_invariants = set()
    for source_path in _invariant_reference_files(repo_root):
        try:
            source_text = source_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(
                f"cannot read invariant references from "
                f"{_display_path(source_path, repo_root)}: {exc}"
            )
            continue
        referenced_invariants.update(INVARIANT_ID.findall(source_text))
    for invariant in sorted(referenced_invariants - set(invariant_owners)):
        errors.append(f"invariant reference has no manifest owner: {invariant}")

    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate Novel Harness routing")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (default: inferred from script location)",
    )
    parser.add_argument(
        "--style-guide",
        type=Path,
        help="Validate this staged style guide instead of the formal target",
    )
    args = parser.parse_args(argv)

    if args.style_guide is not None:
        errors = _validate_style_guide(args.style_guide)
    else:
        errors = validate_repository(args.repo_root)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1

    print("[PASS] Harness validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
