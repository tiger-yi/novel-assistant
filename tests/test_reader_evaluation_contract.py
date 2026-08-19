import tempfile
import unittest
from pathlib import Path

from scripts.reader_evaluation_contract import (
    load_reader_evaluation_report,
    validate_reader_evaluation_report,
)


def dimension(score, *, negative_refs, comparison_refs=None, hint="补足具体动作"):
    return {
        "name": "翻页欲",
        "score": score,
        "weight": 1.0,
        "evidence_refs": ["段落 1"],
        "negative_evidence_refs": negative_refs,
        "comparative_evidence_refs": comparison_refs or [],
        "score_ceiling_reason": "有明确推进，但仍有可定位缺口",
        "improvement_hint": hint,
        "suggestion_type": "PACING_FIX",
    }


def report_with(item):
    return {
        "target_genre_reader": {
            "weighted_score": item["score"],
            "dimensions": [item],
        }
    }


class ReaderEvaluationContractTest(unittest.TestCase):
    def test_accepts_very_high_score_with_two_counterexamples_and_comparison(self):
        report = report_with(
            dimension(
                8.5,
                negative_refs=["段落 2", "段落 8"],
                comparison_refs=["同类强章在场景转换处无解释停顿"],
            )
        )

        self.assertEqual([], validate_reader_evaluation_report(report))

    def test_rejects_score_above_eight_without_negative_evidence(self):
        report = report_with(dimension(8.1, negative_refs=[]))

        errors = validate_reader_evaluation_report(report)

        self.assertTrue(any("negative_evidence_refs" in error for error in errors), errors)

    def test_rejects_very_high_score_without_two_counterexamples(self):
        report = report_with(
            dimension(
                8.5,
                negative_refs=["段落 2"],
                comparison_refs=["同类强章在场景转换处无解释停顿"],
            )
        )

        errors = validate_reader_evaluation_report(report)

        self.assertTrue(any("two negative_evidence_refs" in error for error in errors), errors)

    def test_rejects_very_high_score_without_comparative_evidence(self):
        report = report_with(dimension(8.5, negative_refs=["段落 2", "段落 8"]))

        errors = validate_reader_evaluation_report(report)

        self.assertTrue(any("comparative_evidence_refs" in error for error in errors), errors)

    def test_rejects_high_score_with_no_change_hint(self):
        report = report_with(
            dimension(8.1, negative_refs=["段落 2"], hint="保持现状，无需改动")
        )

        errors = validate_reader_evaluation_report(report)

        self.assertTrue(any("improvement_hint" in error for error in errors), errors)

    def test_loads_markdown_report_with_yaml_blocks(self):
        content = "```yaml\n" + __import__("yaml").safe_dump(
            report_with(dimension(8.0, negative_refs=[])),
            allow_unicode=True,
            sort_keys=False,
        ) + "```\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reader-evaluation-R1.md"
            path.write_text(content, encoding="utf-8")

            report = load_reader_evaluation_report(path)

        self.assertEqual([], validate_reader_evaluation_report(report))


if __name__ == "__main__":
    unittest.main()
