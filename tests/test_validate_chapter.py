import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.validate_chapter import load_blacklist, validate_chapter


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "validate_chapter.py"


class ChapterValidationTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.style = self.root / "style-guide.md"
        self.style.write_text(
            "# 风格\n\n### 黑名单词\n\n* 显然\n* 命运齿轮\n\n### 下一节\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_chapter(self, text):
        chapter = self.root / "chapter.txt"
        chapter.write_text(text, encoding="utf-8")
        return chapter

    def test_loads_blacklist_section_only(self):
        self.assertEqual(["显然", "命运齿轮"], load_blacklist(self.style))

    def test_rejects_style_guide_without_blacklist_section(self):
        self.style.write_text("# 风格\n\n没有黑名单。\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "blacklist"):
            load_blacklist(self.style)

    def test_blacklist_stops_at_higher_level_heading(self):
        self.style.write_text(
            "# 风格\n\n### 黑名单词\n\n* 显然\n\n## 新章节\n\n* 可用词\n",
            encoding="utf-8",
        )

        self.assertEqual(["显然"], load_blacklist(self.style))

    def test_accepts_clean_chapter_at_target(self):
        chapter = self.write_chapter("风从门缝钻进来。")

        self.assertEqual([], validate_chapter(chapter, self.style, target=7))

    def test_reports_forbidden_symbols(self):
        chapter = self.write_chapter("他看见【任务】浮在眼前。")

        errors = validate_chapter(chapter, self.style, target=1)

        self.assertTrue(any("forbidden symbol" in error for error in errors))
        self.assertTrue(any("INV-CHAPTER-001" in error for error in errors))

    def test_reports_book_title_marks_as_forbidden_symbols(self):
        chapter = self.write_chapter("他翻开《玄经》，找到炼气篇。")

        errors = validate_chapter(chapter, self.style, target=1)

        self.assertTrue(
            any(
                "forbidden symbol found at line 1: 《" in error
                for error in errors
            )
        )
        self.assertTrue(
            any(
                "forbidden symbol found at line 1: 》" in error
                for error in errors
            )
        )

    def test_reports_known_harness_identifier_with_line_number(self):
        chapter = self.write_chapter("风停了。\nCH-0007站在门外。")

        errors = validate_chapter(chapter, self.style, target=1)

        self.assertTrue(
            any(
                "narrative-layer identifier" in error
                and "CH-0007" in error
                and "line 2" in error
                for error in errors
            )
        )

    def test_reports_bare_alphanumeric_codes_case_insensitively(self):
        chapter = self.write_chapter("R16守在门外，c-12已经失踪，room12仍然封闭。")

        errors = validate_chapter(chapter, self.style, target=1)

        for code in ("R16", "c-12", "room12"):
            self.assertTrue(any(code in error for error in errors))

    def test_reports_chapter_structure_references(self):
        chapter = self.write_chapter(
            "上一章留下的伤还在。前文已经说明。第十二章再揭晓。第X章不能出现。"
        )

        errors = validate_chapter(chapter, self.style, target=1)

        for reference in ("上一章", "前文", "第十二章", "第X章"):
            self.assertTrue(any(reference in error for error in errors))

    def test_accepts_natural_chinese_identifiers_and_event_transitions(self):
        chapter = self.write_chapter(
            "此前，他在七号矿井见过这道刻痕。甲字三号牢房仍锁着。"
        )

        self.assertEqual([], validate_chapter(chapter, self.style, target=1))

    def test_reports_markdown_blocks(self):
        chapter = self.write_chapter("第一幕。\n- 这是列表\n| 列 | 表 |")

        errors = validate_chapter(chapter, self.style, target=1)

        self.assertEqual(2, sum("Markdown" in error for error in errors))
        self.assertTrue(
            all("INV-CHAPTER-001" in error for error in errors if "Markdown" in error)
        )

    def test_reports_blacklisted_terms(self):
        chapter = self.write_chapter("显然，命运齿轮已经转动。")

        errors = validate_chapter(chapter, self.style, target=1)

        self.assertEqual(2, sum("blacklisted term" in error for error in errors))

    def test_reports_word_count_failure(self):
        chapter = self.write_chapter("太短")

        errors = validate_chapter(chapter, self.style, target=10)

        self.assertTrue(any("word count" in error for error in errors))

    def test_reports_word_count_above_maximum(self):
        chapter = self.write_chapter("甲" * 21)

        errors = validate_chapter(chapter, self.style, target=10, max_words=20)

        self.assertTrue(any("above maximum 20" in error for error in errors))

    def test_cli_returns_nonzero_for_invalid_chapter(self):
        chapter = self.write_chapter("显然【太短】")
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(chapter),
                "--style",
                str(self.style),
                "--target",
                "10",
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        self.assertEqual(1, result.returncode)
        self.assertIn("[FAIL]", result.stdout)
        self.assertIn("[FAIL] INV-CHAPTER-001:", result.stdout)


if __name__ == "__main__":
    unittest.main()
