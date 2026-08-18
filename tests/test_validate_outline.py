import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.outline_contract import (
    OutlineContractError,
    chapter_binding,
    load_outline_contract,
    validate_outline_contract,
)


def chapter(number, milestone, role=None):
    data = {
        "id": f"CH-{number:04d}",
        "task": f"完成第{number}章任务",
        "preconditions": ["承接上一章状态"],
        "conflict": "主角必须支付代价才能推进",
        "outcome": f"形成第{number}章可验证结果",
        "arc_contribution": "推进卷目标的必要条件",
        "closing_pull": "以新危机牵引下一章",
        "milestone": milestone,
        "status": "planned",
    }
    if role is not None:
        data["golden_three_role"] = role
    return data


def valid_contract():
    return {
        "schema": "novel-harness/outline/v2",
        "revision": 1,
        "status": "frozen",
        "current_arc": "ARC-001",
        "novel_goal": "主角完成最终抉择并建立新秩序",
        "volumes": [
            {
                "id": "ARC-001",
                "title": "第一卷",
                "start_chapter": 1,
                "end_chapter": 3,
                "planning_status": "frozen",
                "entry_cause": "故事开端",
                "goal": {
                    "id": "GOAL-ARC-001",
                    "result": "主角取得入门资格",
                    "completion_conditions": ["资格由公开考核取得"],
                    "required_causality": ["主角先发现规则再利用规则"],
                    "forbidden_outcomes": ["不得依靠临时关系直接取得"],
                    "completion_evidence": "卷终正文与章节摘要",
                },
                "milestones": [
                    {
                        "id": "MS-ARC-001-01",
                        "due_chapter": 1,
                        "outcome": "建立卷冲突",
                    },
                    {
                        "id": "MS-ARC-001-02",
                        "due_chapter": 2,
                        "outcome": "取得关键条件",
                    },
                    {
                        "id": "MS-ARC-001-03",
                        "due_chapter": 3,
                        "outcome": "完成卷目标",
                    },
                ],
                "chapters": [
                    chapter(1, "MS-ARC-001-01", "inciting"),
                    chapter(2, "MS-ARC-001-02", "feedback"),
                    chapter(3, "MS-ARC-001-03", "goal-lock"),
                ],
            },
            {
                "id": "ARC-002",
                "title": "第二卷",
                "start_chapter": 4,
                "end_chapter": 8,
                "planning_status": "roadmap",
                "entry_cause": "第一卷资格使主角进入宗门",
                "goal": {
                    "id": "GOAL-ARC-002",
                    "result": "主角在宗门站稳脚跟",
                    "completion_conditions": ["获得独立修炼资格"],
                    "required_causality": ["沿用第一卷取得的资格"],
                    "forbidden_outcomes": ["不得跳过宗门规则"],
                    "completion_evidence": "卷终正文与章节摘要",
                },
                "milestones": [],
                "chapters": [],
            },
        ],
    }


def payoff_plan(number, payoff_types, primary_type, climax):
    payoffs = []
    for index, payoff_type in enumerate(payoff_types, start=1):
        payoffs.append(
            {
                "id": f"PAY-CH-{number:04d}-{index:02d}",
                "type": payoff_type,
                "event_key": f"EVT-CH-{number:04d}-{index:02d}",
                "promise": f"第{number}章第{index}项读者期待",
                "action": f"主角完成第{number}章第{index}项行动",
                "state_delta": f"形成第{number}章第{index}项有利变化",
                "recognition": f"环境确认第{number}章第{index}项结果",
                "cost": f"承担第{number}章第{index}项代价",
                "persistence": "next-chapter" if payoff_type == primary_type else "scene",
            }
        )
    primary = next(item for item in payoffs if item["type"] == primary_type)
    return {
        "profile": "high",
        "payoffs": payoffs,
        "primary_payoff_id": primary["id"],
        "climax": climax,
        "escalation_from": "相较前章改变了收益类型或影响范围",
        "escalation": "cross-chapter" if number % 2 == 0 else "routine",
    }


class OutlineContractTest(unittest.TestCase):
    def test_direct_script_entrypoint_accepts_valid_outline(self):
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "outline.md"
            path.write_text(
                "---\n"
                + yaml.safe_dump(
                    valid_contract(), allow_unicode=True, sort_keys=False
                )
                + "---\n# 小说大纲\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, "scripts/validate_outline.py", str(path)],
                cwd=repo_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_accepts_frozen_current_arc_and_roadmap_future_arc(self):
        self.assertEqual([], validate_outline_contract(valid_contract()))

    def test_non_retroactive_outline_without_payoff_policy_remains_valid(self):
        contract = valid_contract()

        self.assertEqual([], validate_outline_contract(contract))

    def test_activated_outline_requires_payoff_contracts(self):
        contract = valid_contract()
        contract["payoff_policy"] = {
            "schema": "novel-harness/payoff-policy/v1",
            "activation_chapter": 1,
            "default_profile": "standard",
            "book_opening_high_through": 10,
            "volume_opening_high_count": 3,
        }

        errors = validate_outline_contract(contract)

        self.assertTrue(any("payoff_contract is required" in error for error in errors))

    def test_accepts_activated_outline_with_high_density_plans(self):
        contract = valid_contract()
        contract["payoff_policy"] = {
            "schema": "novel-harness/payoff-policy/v1",
            "activation_chapter": 1,
            "default_profile": "standard",
            "book_opening_high_through": 10,
            "volume_opening_high_count": 3,
        }
        plans = (
            payoff_plan(1, ("POWER", "RESOURCE", "AUTONOMY"), "POWER", "none"),
            payoff_plan(2, ("STATUS", "RELATIONSHIP", "COMPETENCE"), "STATUS", "none"),
            payoff_plan(3, ("REVERSAL", "INFORMATION", "RESOURCE"), "REVERSAL", "small"),
        )
        for chapter_contract, plan in zip(
            contract["volumes"][0]["chapters"], plans
        ):
            chapter_contract["payoff_contract"] = plan

        self.assertEqual([], validate_outline_contract(contract))

    def test_activated_outline_rejects_underfilled_high_density_plan(self):
        contract = valid_contract()
        contract["payoff_policy"] = {
            "schema": "novel-harness/payoff-policy/v1",
            "activation_chapter": 1,
            "default_profile": "standard",
            "book_opening_high_through": 10,
            "volume_opening_high_count": 3,
        }
        for number, chapter_contract in enumerate(
            contract["volumes"][0]["chapters"], start=1
        ):
            plan = payoff_plan(
                number,
                ("POWER", "RESOURCE", "AUTONOMY"),
                "POWER",
                "small" if number == 3 else "none",
            )
            chapter_contract["payoff_contract"] = plan
        contract["volumes"][0]["chapters"][0]["payoff_contract"]["payoffs"].pop()

        errors = validate_outline_contract(contract)

        self.assertTrue(any("at least 3" in error for error in errors), errors)

    def test_activated_outline_rejects_adjacent_repeated_primary_type(self):
        contract = valid_contract()
        contract["payoff_policy"] = {
            "schema": "novel-harness/payoff-policy/v1",
            "activation_chapter": 1,
            "default_profile": "standard",
            "book_opening_high_through": 10,
            "volume_opening_high_count": 3,
        }
        for number, chapter_contract in enumerate(
            contract["volumes"][0]["chapters"], start=1
        ):
            chapter_contract["payoff_contract"] = payoff_plan(
                number,
                ("POWER", "RESOURCE", "AUTONOMY"),
                "POWER",
                "small" if number == 3 else "none",
            )

        errors = validate_outline_contract(contract)

        self.assertTrue(any("adjacent primary payoff types" in error for error in errors))

    def test_rejects_gap_between_volume_ranges(self):
        contract = valid_contract()
        contract["volumes"][1]["start_chapter"] = 5

        errors = validate_outline_contract(contract)

        self.assertTrue(any("contiguous" in error for error in errors))

    def test_rejects_missing_chapter_execution_contract_field(self):
        contract = valid_contract()
        del contract["volumes"][0]["chapters"][1]["closing_pull"]

        errors = validate_outline_contract(contract)

        self.assertTrue(any("closing_pull" in error for error in errors))

    def test_rejects_incomplete_frozen_arc(self):
        contract = valid_contract()
        contract["volumes"][0]["chapters"].pop()

        errors = validate_outline_contract(contract)

        self.assertTrue(any("every chapter" in error for error in errors))

    def test_rejects_missing_volume_golden_three_role(self):
        contract = valid_contract()
        del contract["volumes"][0]["chapters"][0]["golden_three_role"]

        errors = validate_outline_contract(contract)

        self.assertTrue(any("golden_three_role" in error for error in errors))

    def test_rejects_milestones_outside_arc_or_out_of_order(self):
        contract = valid_contract()
        contract["volumes"][0]["milestones"][1]["due_chapter"] = 1

        errors = validate_outline_contract(contract)

        self.assertTrue(any("strictly increasing" in error for error in errors))

    def test_loads_yaml_frontmatter_and_builds_stable_chapter_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "outline.md"
            path.write_text(
                "---\n"
                + yaml.safe_dump(
                    valid_contract(), allow_unicode=True, sort_keys=False
                )
                + "---\n# 小说大纲\n",
                encoding="utf-8",
            )

            loaded = load_outline_contract(path)
            binding = chapter_binding(path, 2)

        self.assertEqual("novel-harness/outline/v2", loaded["schema"])
        self.assertEqual("ARC-001", binding["arc_id"])
        self.assertEqual("GOAL-ARC-001", binding["arc_goal_id"])
        self.assertEqual("CH-0002", binding["chapter_id"])
        self.assertRegex(binding["outline_hash"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(
            binding["chapter_contract_hash"], r"^sha256:[0-9a-f]{64}$"
        )

    def test_binding_rejects_chapter_in_unfrozen_future_arc(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "outline.md"
            path.write_text(
                "---\n"
                + yaml.safe_dump(
                    valid_contract(), allow_unicode=True, sort_keys=False
                )
                + "---\n# 小说大纲\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(OutlineContractError, "not frozen"):
                chapter_binding(path, 4)


if __name__ == "__main__":
    unittest.main()
