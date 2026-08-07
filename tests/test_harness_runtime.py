import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.harness_runtime import CommandResolutionError, HarnessManifest


class HarnessRuntimeTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.manifest_path = Path(self.temp_dir.name) / "manifest.yaml"
        self.write_manifest()

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_manifest(self, commands=None):
        if commands is None:
            commands = [
                {
                    "name": "check-status",
                    "path": "status.md",
                    "activation": "command",
                    "matches": [{"literal": "查看世界状态"}],
                },
                {
                    "name": "create-chapter",
                    "path": "draft.md",
                    "activation": "command",
                    "matches": [
                        {
                            "pattern": r"^创作第\s*(?P<chapter>\d+)\s*章$",
                            "display": "创作第 N 章",
                            "mode": "full",
                        },
                        {
                            "pattern": r"^构思第\s*(?P<chapter>\d+)\s*章$",
                            "display": "构思第 N 章",
                            "mode": "preview",
                        },
                    ],
                    "modes": {
                        "full": {"writes": ["../chapters/", "../world/"]},
                        "preview": {"writes": []},
                    },
                },
            ]
        self.manifest_path.write_text(
            yaml.safe_dump(
                {
                    "schema": "novel-harness/context/v2",
                    "routes": {"commands": commands},
                },
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

    def test_resolves_exact_literal(self):
        match = HarnessManifest.load(self.manifest_path).resolve("查看世界状态")

        self.assertEqual("check-status", match.name)
        self.assertEqual({}, match.arguments)
        self.assertIsNone(match.mode)

    def test_resolves_full_pattern_and_captures_chapter(self):
        match = HarnessManifest.load(self.manifest_path).resolve("创作第 12 章")

        self.assertEqual("create-chapter", match.name)
        self.assertEqual({"chapter": "12"}, match.arguments)
        self.assertEqual("full", match.mode)

    def test_preview_pattern_does_not_gain_full_mode(self):
        match = HarnessManifest.load(self.manifest_path).resolve("构思第 12 章")

        self.assertEqual("preview", match.mode)
        self.assertEqual([], match.write_scopes())

    def test_rejects_unregistered_natural_language(self):
        with self.assertRaisesRegex(CommandResolutionError, "no command matched"):
            HarnessManifest.load(self.manifest_path).resolve("帮我写一下第十二章")

    def test_rejects_ambiguous_match(self):
        duplicate = {
            "name": "duplicate-status",
            "path": "duplicate.md",
            "activation": "command",
            "matches": [{"literal": "查看世界状态"}],
        }
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest["routes"]["commands"].append(duplicate)
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(CommandResolutionError, "ambiguous command"):
            HarnessManifest.load(self.manifest_path).resolve("查看世界状态")

    def test_reports_invalid_yaml_as_resolution_error(self):
        self.manifest_path.write_text("routes: [", encoding="utf-8")

        with self.assertRaisesRegex(CommandResolutionError, "invalid manifest YAML"):
            HarnessManifest.load(self.manifest_path)


class HarnessRepositoryRoutesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = HarnessManifest.load(
            Path(__file__).resolve().parents[1]
            / "novel-harness"
            / "context.manifest.yaml"
        )

    def test_resolves_explicit_originality_audit(self):
        match = self.manifest.resolve("审计原创性")

        self.assertEqual("audit-originality", match.name)

    def test_resolves_explicit_metadata_generation(self):
        match = self.manifest.resolve("生成小说元数据")

        self.assertEqual("generate-metadata", match.name)

    def test_resolves_controlled_arc_revision(self):
        match = self.manifest.resolve("修订卷规划 ARC-001")

        self.assertEqual("revise-arc", match.name)
        self.assertEqual({"arc": "ARC-001"}, match.arguments)

    def test_chapter_creation_requires_frozen_plan_contract(self):
        route = self.manifest.command("create-chapter")

        self.assertEqual("required", route.get("plan_contract"))

    def test_outline_contract_gate_has_registered_command(self):
        commands = {
            gate.get("name"): gate.get("command")
            for gates in (self.manifest.data.get("verification") or {}).values()
            if isinstance(gates, list)
            for gate in gates
            if isinstance(gate, dict)
        }

        self.assertEqual(
            "python scripts/validate_outline.py <outline_file>",
            commands.get("outline-contract"),
        )

    def test_resolves_presentation_migration_parent_and_child(self):
        parent = self.manifest.resolve("迁移正文呈现")
        child = self.manifest.resolve("迁移正文呈现 CH-0007")

        self.assertEqual("migrate-presentation", parent.name)
        self.assertEqual("migrate-presentation-chapter", child.name)
        self.assertEqual({"chapter": "0007"}, child.arguments)

    def test_resolves_polish_chapter_commands(self):
        published = self.manifest.resolve("润色章节 CH-0007")
        current = self.manifest.resolve("润色当前章节")

        self.assertEqual("polish-chapter", published.name)
        self.assertEqual("published", published.mode)
        self.assertEqual({"chapter": "0007"}, published.arguments)
        self.assertEqual("polish-current-chapter", current.name)
        self.assertEqual("current-staging", current.mode)


if __name__ == "__main__":
    unittest.main()
