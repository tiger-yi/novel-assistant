import copy
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.payoff_contract import (
    PayoffContractError,
    load_payoff_evidence,
    validate_payoff_evidence,
)


def payoff(index, payoff_type, *, event_key=None, persistence="scene"):
    return {
        "id": f"PAY-CH-0011-{index:02d}",
        "type": payoff_type,
        "event_key": event_key or f"EVT-PAY-{index:02d}",
        "promise": f"读者期待第{index}项回报",
        "action": f"主角主动完成第{index}项行动",
        "state_delta": f"第{index}项有利状态变化",
        "recognition": f"对手或环境确认第{index}项结果",
        "cost": f"主角承担第{index}项代价",
        "persistence": persistence,
        "evidence_refs": [f"scene-{index}"],
    }


def valid_evidence():
    return {
        "schema": "novel-harness/payoff-evidence/v1",
        "chapter_id": "CH-0011",
        "profile": "high",
        "mode": "new",
        "activation": {
            "non_retroactive": True,
            "starts_at": "CH-0011",
        },
        "payoffs": [
            payoff(1, "COMPETENCE"),
            payoff(2, "RESOURCE"),
            payoff(3, "REVERSAL", persistence="next-chapter"),
        ],
        "primary_payoff_id": "PAY-CH-0011-03",
        "rolling_window": [
            {
                "chapter_id": "CH-0009",
                "primary_type": "STATUS",
                "climax": "none",
                "escalation": "routine",
            },
            {
                "chapter_id": "CH-0010",
                "primary_type": "POWER",
                "climax": "none",
                "escalation": "cross-chapter",
            },
            {
                "chapter_id": "CH-0011",
                "primary_type": "REVERSAL",
                "climax": "small",
                "escalation": "routine",
            },
        ],
    }


class PayoffEvidenceTest(unittest.TestCase):
    def test_repository_payoff_evidence_template_is_valid(self):
        template = (
            Path(__file__).resolve().parents[1]
            / "templates"
            / "payoff-evidence-template.yaml"
        )

        evidence = load_payoff_evidence(template)

        self.assertEqual([], validate_payoff_evidence(evidence))

    def test_accepts_high_density_evidence(self):
        self.assertEqual([], validate_payoff_evidence(valid_evidence()))

    def test_rejects_high_profile_with_fewer_than_three_micro_payoffs(self):
        evidence = valid_evidence()
        evidence["payoffs"].pop()
        evidence["primary_payoff_id"] = "PAY-CH-0011-02"

        errors = validate_payoff_evidence(evidence)

        self.assertTrue(any("at least 3" in error for error in errors), errors)

    def test_rejects_chapter_with_fewer_than_two_payoff_types(self):
        evidence = valid_evidence()
        for item in evidence["payoffs"]:
            item["type"] = "POWER"

        errors = validate_payoff_evidence(evidence)

        self.assertTrue(any("at least 2 payoff types" in error for error in errors))

    def test_rejects_one_event_split_into_multiple_payoffs(self):
        evidence = valid_evidence()
        evidence["payoffs"][1]["event_key"] = evidence["payoffs"][0]["event_key"]

        errors = validate_payoff_evidence(evidence)

        self.assertTrue(any("duplicate event_key" in error for error in errors))

    def test_rejects_primary_payoff_without_persistent_state_delta(self):
        evidence = valid_evidence()
        evidence["payoffs"][2]["persistence"] = "scene"

        errors = validate_payoff_evidence(evidence)

        self.assertTrue(any("persist beyond the scene" in error for error in errors))

    def test_rejects_adjacent_repeated_primary_type(self):
        evidence = valid_evidence()
        evidence["rolling_window"][-2]["primary_type"] = "REVERSAL"

        errors = validate_payoff_evidence(evidence)

        self.assertTrue(any("adjacent primary payoff types" in error for error in errors))

    def test_rejects_three_chapter_window_without_small_climax(self):
        evidence = valid_evidence()
        evidence["rolling_window"][-1]["climax"] = "none"

        errors = validate_payoff_evidence(evidence)

        self.assertTrue(any("small climax" in error for error in errors))

    def test_rejects_three_chapter_window_with_fewer_than_three_types(self):
        evidence = valid_evidence()
        evidence["rolling_window"][0]["primary_type"] = "POWER"

        errors = validate_payoff_evidence(evidence)

        self.assertTrue(any("three payoff types" in error for error in errors))

    def test_rejects_high_two_chapter_window_without_cross_chapter_escalation(self):
        evidence = valid_evidence()
        evidence["rolling_window"][-2]["escalation"] = "routine"

        errors = validate_payoff_evidence(evidence)

        self.assertTrue(any("cross-chapter escalation" in error for error in errors))

    def test_rejects_high_profile_eight_chapter_window_without_major_payoff(self):
        evidence = valid_evidence()
        evidence["rolling_window"] = [
            {
                "chapter_id": f"CH-{number:04d}",
                "primary_type": ("POWER", "RESOURCE", "STATUS")[number % 3],
                "climax": "small" if number % 3 == 2 else "none",
                "escalation": "cross-chapter" if number % 2 == 0 else "routine",
            }
            for number in range(4, 12)
        ]

        errors = validate_payoff_evidence(evidence)

        self.assertTrue(any("major payoff" in error for error in errors))

    def test_requires_approval_for_published_revision(self):
        evidence = valid_evidence()
        evidence["mode"] = "published-revision"
        evidence["published_revision"] = {
            "source_hash": "sha256:" + "a" * 64,
            "downstream_impact": "none",
            "approval_status": "pending",
        }

        errors = validate_payoff_evidence(evidence)

        self.assertTrue(any("approval_status must be approved" in error for error in errors))

    def test_loads_yaml_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "payoff-evidence.yaml"
            path.write_text(
                yaml.safe_dump(valid_evidence(), allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

            loaded = load_payoff_evidence(path)

        self.assertEqual("CH-0011", loaded["chapter_id"])

    def test_reports_non_mapping_yaml(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "payoff-evidence.yaml"
            path.write_text("- invalid\n", encoding="utf-8")

            with self.assertRaisesRegex(PayoffContractError, "must be a mapping"):
                load_payoff_evidence(path)


if __name__ == "__main__":
    unittest.main()
