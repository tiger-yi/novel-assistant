import tempfile
import textwrap
import unittest
from pathlib import Path

import yaml

from scripts.validate_harness import validate_repository


class HarnessValidationTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "novel-harness").mkdir()
        (self.root / "writespec" / "commands").mkdir(parents=True)
        (self.root / "templates").mkdir()

        (self.root / "writespec" / "commands" / "draft.md").write_text(
            '# 命令协议\n\n触发词: "创作章节"\n', encoding="utf-8"
        )
        (self.root / "writespec" / "chapter.md").write_text(
            "# 章节规范\n", encoding="utf-8"
        )
        (self.root / "templates" / "outline.md").write_text(
            "# 大纲模板\n", encoding="utf-8"
        )
        self.write_style_guide()
        (self.root / "AGENTS.md").write_text(
            "创作章节入口：`writespec/commands/draft.md`、`writespec/chapter.md`、"
            "`templates/outline.md`。\n",
            encoding="utf-8",
        )
        (self.root / "README.md").write_text(
            "创作章节，详见 writespec/commands/draft.md。\n", encoding="utf-8"
        )
        self.manifest = self.root / "novel-harness" / "context.manifest.yaml"
        self.write_manifest()

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_style_guide(self, *, status="ready", include_forbidden=True):
        forbidden = "## 11. 禁忌与避坑\n" if include_forbidden else ""
        (self.root / "writespec" / "style-guide.md").write_text(
            textwrap.dedent(
                f"""\
                ---
                schema: novel-harness/style/v1
                status: {status}
                ---
                # 风格
                ## 2. 核心调性
                ## 4. 排版规范
                ### 受限视角
                ## 7. 角色刻画重点
                {forbidden}### 黑名单词
                * 显然
                """
            ),
            encoding="utf-8",
        )

    def write_manifest(self, *, command_path="../writespec/commands/draft.md",
                       required="../world/outline.md", aliases=None,
                       patterns=None):
        command = {
            "name": "draft",
            "path": command_path,
            "trigger": "创作章节",
        }
        if aliases is not None:
            command["aliases"] = aliases
        if patterns is not None:
            command["patterns"] = patterns
        manifest = {
            "schema": "novel-harness/context/v1",
            "routes": {
                "commands": [command],
                "specs": [
                    {"name": "chapter", "path": "../writespec/chapter.md"},
                    {
                        "name": "style-guide",
                        "path": "../writespec/style-guide.md",
                    },
                ],
            },
            "templates": [
                {"name": "outline", "path": "../templates/outline.md"}
            ],
            "world_data": {
                "default_order": ["../world/outline.md"],
                "required": [required],
            },
        }
        self.manifest.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def test_accepts_consistent_repository(self):
        self.assertEqual([], validate_repository(self.root))

    def test_reports_missing_declared_file(self):
        self.write_manifest(command_path="../writespec/commands/missing.md")

        errors = validate_repository(self.root)

        self.assertTrue(any("missing.md" in error for error in errors))

    def test_reports_required_world_file_outside_default_order(self):
        self.write_manifest(required="../world/characters.md")

        errors = validate_repository(self.root)

        self.assertTrue(any("required" in error for error in errors))

    def test_reports_duplicate_trigger_aliases(self):
        self.write_manifest(aliases=["创作章节"])

        errors = validate_repository(self.root)

        self.assertTrue(any("duplicate command trigger" in error for error in errors))

    def test_accepts_repository_without_spec_map(self):
        self.assertEqual([], validate_repository(self.root))

    def test_reports_style_guide_without_ready_marker(self):
        self.write_style_guide(status="draft")

        errors = validate_repository(self.root)

        self.assertTrue(any("style guide is not ready" in error for error in errors))

    def test_reports_style_guide_without_required_section(self):
        self.write_style_guide(include_forbidden=False)

        errors = validate_repository(self.root)

        self.assertTrue(any("style guide section is missing" in error for error in errors))

    def test_reports_command_document_without_trigger(self):
        command = self.root / "writespec" / "commands" / "draft.md"
        command.write_text("# 命令协议\n", encoding="utf-8")

        errors = validate_repository(self.root)

        self.assertTrue(any("does not declare trigger" in error for error in errors))

    def test_reports_invalid_command_pattern(self):
        self.write_manifest(patterns=["[invalid"])

        errors = validate_repository(self.root)

        self.assertTrue(any("invalid command pattern" in error for error in errors))

    def test_reports_non_mapping_command_without_traceback(self):
        manifest = yaml.safe_load(self.manifest.read_text(encoding="utf-8"))
        manifest["routes"]["commands"].append("invalid")
        self.manifest.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        errors = validate_repository(self.root)

        self.assertTrue(any("must be mappings" in error for error in errors))

    def test_reports_route_path_that_escapes_repository(self):
        self.write_manifest(command_path="../../outside.md")

        errors = validate_repository(self.root)

        self.assertTrue(any("escapes repository" in error for error in errors))

    def test_reports_alias_missing_from_human_docs(self):
        self.write_manifest(aliases=["章节规划"])

        errors = validate_repository(self.root)

        self.assertTrue(any("not documented" in error for error in errors))

    def test_reports_agents_entry_missing_from_manifest(self):
        with (self.root / "AGENTS.md").open("a", encoding="utf-8") as handle:
            handle.write("`writespec/missing-spec.md`\n")

        errors = validate_repository(self.root)

        self.assertTrue(any("AGENTS.md target" in error for error in errors))

    def test_reports_readme_entry_missing_from_manifest(self):
        with (self.root / "README.md").open("a", encoding="utf-8") as handle:
            handle.write("[失效规范](writespec/missing-spec.md)\n")

        errors = validate_repository(self.root)

        self.assertTrue(any("README.md target" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
