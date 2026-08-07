from dataclasses import dataclass
from pathlib import Path
import re

import yaml


class CommandResolutionError(ValueError):
    pass


@dataclass(frozen=True)
class CommandMatch:
    name: str
    arguments: dict[str, str]
    mode: str | None
    route: dict
    raw_text: str

    def write_scopes(self) -> list[str]:
        if self.mode is None:
            return list(self.route.get("writes") or [])
        modes = self.route.get("modes") or {}
        mode = modes.get(self.mode) or {}
        return list(mode.get("writes") or [])


class HarnessManifest:
    def __init__(self, path: Path, data: dict):
        self.path = path.resolve()
        self.data = data

    @classmethod
    def load(cls, path: Path):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise CommandResolutionError(f"invalid manifest YAML: {exc}") from exc
        if not isinstance(data, dict):
            raise CommandResolutionError("manifest root must be a mapping")
        return cls(path, data)

    def command(self, name: str) -> dict:
        commands = self.data.get("routes", {}).get("commands", [])
        for route in commands:
            if isinstance(route, dict) and route.get("name") == name:
                return route
        raise CommandResolutionError(f"unknown command: {name}")

    def resolve(self, raw_text: str) -> CommandMatch:
        matches = []
        commands = self.data.get("routes", {}).get("commands", [])
        for route in commands:
            if not isinstance(route, dict):
                continue
            for matcher in route.get("matches") or []:
                if not isinstance(matcher, dict):
                    continue
                if matcher.get("literal") == raw_text:
                    matches.append(
                        CommandMatch(
                            route["name"],
                            {},
                            matcher.get("mode"),
                            route,
                            raw_text,
                        )
                    )
                pattern = matcher.get("pattern")
                pattern_match = re.fullmatch(pattern, raw_text) if pattern else None
                if pattern_match:
                    matches.append(
                        CommandMatch(
                            route["name"],
                            pattern_match.groupdict(),
                            matcher.get("mode"),
                            route,
                            raw_text,
                        )
                    )
        if not matches:
            raise CommandResolutionError(f"no command matched: {raw_text}")
        unique = {
            (match.name, match.mode, tuple(sorted(match.arguments.items())))
            for match in matches
        }
        if len(unique) != 1:
            raise CommandResolutionError(f"ambiguous command: {raw_text}")
        return matches[0]
