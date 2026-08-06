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

    def test_reports_markdown_blocks(self):
        chapter = self.write_chapter("第一幕。\n- 这是列表\n| 列 | 表 |")

        errors = validate_chapter(chapter, self.style, target=1)

        self.assertEqual(2, sum("Markdown" in error for error in errors))

    def test_reports_blacklisted_terms(self):
        chapter = self.write_chapter("显然，命运齿轮已经转动。")

        errors = validate_chapter(chapter, self.style, target=1)

        self.assertEqual(2, sum("blacklisted term" in error for error in errors))

    def test_reports_word_count_failure(self):
        chapter = self.write_chapter("太短")

        errors = validate_chapter(chapter, self.style, target=10)

        self.assertTrue(any("word count" in error for error in errors))

    def test_cli_returns_nonzero_for_invalid_chapter(self):
        chapter = self.write_chapter("显然太短")
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


if __name__ == "__main__":
    unittest.main()
