import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.check_count import count_words


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "check_count.py"


class CheckCountCliTest(unittest.TestCase):
    def run_check(self, text, *args):
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        ) as handle:
            handle.write(text)
            chapter_path = Path(handle.name)

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        try:
            return subprocess.run(
                [sys.executable, str(SCRIPT), str(chapter_path), *args],
                cwd=REPO_ROOT,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
        finally:
            chapter_path.unlink(missing_ok=True)

    def test_returns_nonzero_when_below_target(self):
        result = self.run_check("短章", "--target", "10")

        self.assertEqual(1, result.returncode)
        self.assertIn("Status: INCOMPLETE", result.stdout)

    def test_accepts_text_at_target(self):
        result = self.run_check("甲" * 10, "--target", "10")

        self.assertEqual(0, result.returncode)
        self.assertIn("Status: COMPLETE", result.stdout)

    def test_has_no_implicit_maximum(self):
        result = self.run_check("甲" * 2401, "--target", "10")

        self.assertEqual(0, result.returncode)
        self.assertIn("Status: COMPLETE", result.stdout)

    def test_returns_nonzero_when_explicit_maximum_is_exceeded(self):
        result = self.run_check(
            "甲" * 20, "--target", "10", "--max", "15"
        )

        self.assertEqual(1, result.returncode)
        self.assertIn("Status: TOO_LONG", result.stdout)

    def test_status_markers_are_ascii(self):
        result = self.run_check("短章", "--target", "10")

        result.stdout.encode("ascii")

    def test_ignores_all_whitespace_and_punctuation(self):
        text = "甲\t乙\u3000丙，。！？——……【】"

        self.assertEqual(3, count_words(text))

    def test_punctuation_only_chapter_is_incomplete(self):
        result = self.run_check("，。！？——……" * 1000, "--target", "10")

        self.assertEqual(1, result.returncode)
        self.assertIn("Total Word Count: 0", result.stdout)


if __name__ == "__main__":
    unittest.main()
