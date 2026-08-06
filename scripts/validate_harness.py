import argparse
import re
import sys
from pathlib import Path

import yaml


BACKTICK_LITERAL = re.compile(r"`([^`]+)`")
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
STYLE_SCHEMA = "novel-harness/style/v1"
STYLE_REQUIRED_SECTIONS = (
    "## 2. 核心调性",
    "## 4. 排版规范",
    "### 受限视角",
    "## 7. 角色刻画重点",
    "## 11. 禁忌与避坑",
    "### 黑名单词",
)


def _manifest_entries(manifest):
    routes = manifest.get("routes", {})
    if not isinstance(routes, dict):
        return []
    return [
        *(routes.get("commands") or []),
        *(routes.get("specs") or []),
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
        errors.append(f"style guide schema must be {STYLE_SCHEMA}")
    if frontmatter.get("status") != "ready":
        errors.append("style guide is not ready: status must be ready")
    for section in STYLE_REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"style guide section is missing: {section}")
    return errors


def validate_repository(repo_root):
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

    seen_triggers = set()
    seen_patterns = set()
    routes = manifest.get("routes", {})
    commands = routes.get("commands", []) if isinstance(routes, dict) else []
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
        trigger = command.get("trigger")
        aliases = command.get("aliases") or []
        display_patterns = command.get("display_patterns") or []
        for value in [trigger, *aliases, *display_patterns]:
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

        patterns = command.get("patterns") or []
        if patterns and len(patterns) != len(display_patterns):
            errors.append(
                f"command {command.get('name')} patterns require matching "
                f"display_patterns"
            )
        for index, pattern in enumerate(patterns):
            if pattern in seen_patterns:
                errors.append(f"duplicate command pattern: {pattern}")
            seen_patterns.add(pattern)
            try:
                compiled = re.compile(pattern)
                if index < len(display_patterns):
                    example = display_patterns[index].replace("N", "12")
                    if compiled.fullmatch(example) is None:
                        errors.append(
                            f"command pattern does not match display example: {pattern}"
                        )
            except re.error as exc:
                errors.append(
                    f"invalid command pattern for {command.get('name')}: {exc}"
                )

        raw_path = command.get("path")
        if not trigger or not raw_path:
            continue
        command_path = _resolve(manifest_dir, raw_path)
        if command_path.is_file():
            command_text = command_path.read_text(encoding="utf-8")
            for value in [trigger, *aliases, *display_patterns]:
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
        style_path = _resolve(manifest_dir, style_entries[0].get("path", ""))
        if style_path.is_file():
            errors.extend(_validate_style_guide(style_path))

    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate Novel Harness routing")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (default: inferred from script location)",
    )
    args = parser.parse_args(argv)

    errors = validate_repository(args.repo_root)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1

    print("[PASS] Harness validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
