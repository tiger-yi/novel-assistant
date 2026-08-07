import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.transaction_executor import (
    TransactionError,
    begin_transaction,
    commit_transaction,
    confirm_overwrite,
    load_transaction,
    sha256_file,
    validate_plan_binding,
    validate_transaction,
)
from tests.test_validate_outline import valid_contract


class TransactionContractTest(unittest.TestCase):
    def valid_transaction(self):
        return {
            "schema": "novel-harness/transaction/v1",
            "transaction_id": "TX-CH-0001-R01",
            "source_command": "创作第 1 章",
            "command": "create-chapter",
            "mode": "full",
            "arguments": {"chapter": "1"},
            "state": "PREPARED",
            "archive_state": "NOT_CHECKED",
            "stages": [
                {"name": "preflight", "status": "PASS"},
                {"name": "final-gates", "status": "PASS"},
            ],
            "gates": [
                {
                    "gate": "world-audit",
                    "kind": "semantic",
                    "required": True,
                    "status": "PASS",
                    "summary": "六维审计通过",
                    "evidence": [
                        {
                            "claim": "战力差距在允许范围内",
                            "source": "world/power.md",
                            "entity": "CHAR-LINCHEN",
                            "chapter": "CH-0001",
                            "excerpt_hash": "sha256:" + "a" * 64,
                        }
                    ],
                }
            ],
            "changes": [],
            "applied_keys": [],
            "recovery": {"last_successful_stage": "final-gates"},
        }

    def test_accepts_complete_semantic_evidence(self):
        self.assertEqual([], validate_transaction(self.valid_transaction()))

    def test_fails_closed_when_required_gate_is_missing_evidence(self):
        transaction = self.valid_transaction()
        transaction["gates"][0]["evidence"] = []

        errors = validate_transaction(transaction)

        self.assertTrue(any("required semantic evidence" in error for error in errors))

    def test_rejects_pending_as_gate_status(self):
        transaction = self.valid_transaction()
        transaction["gates"][0]["status"] = "PENDING"

        errors = validate_transaction(transaction)

        self.assertTrue(any("invalid gate status" in error for error in errors))

    def test_requires_reason_for_not_applicable(self):
        transaction = self.valid_transaction()
        transaction["gates"][0]["status"] = "NOT_APPLICABLE"
        transaction["gates"][0]["evidence"] = []

        errors = validate_transaction(transaction)

        self.assertTrue(any("requires reason" in error for error in errors))

    def test_accepts_not_applicable_with_reason(self):
        transaction = self.valid_transaction()
        transaction["gates"][0]["status"] = "NOT_APPLICABLE"
        transaction["gates"][0]["reason"] = "本章没有战斗场景"
        transaction["gates"][0]["evidence"] = []

        self.assertEqual([], validate_transaction(transaction))

    def test_required_fail_blocks_transaction(self):
        transaction = self.valid_transaction()
        transaction["gates"][0]["status"] = "FAIL"

        errors = validate_transaction(transaction)

        self.assertTrue(any("required gate did not pass" in error for error in errors))

    def test_semantic_evidence_requires_claim_and_source(self):
        transaction = self.valid_transaction()
        transaction["gates"][0]["evidence"] = [{"claim": "缺少来源"}]

        errors = validate_transaction(transaction)

        self.assertTrue(any("requires claim and source" in error for error in errors))

    def test_rejects_invalid_excerpt_hash(self):
        transaction = self.valid_transaction()
        transaction["gates"][0]["evidence"][0]["excerpt_hash"] = "sha256:short"

        errors = validate_transaction(transaction)

        self.assertTrue(any("invalid excerpt_hash" in error for error in errors))

    def test_rejects_unknown_transaction_state(self):
        transaction = self.valid_transaction()
        transaction["state"] = "DONE"

        errors = validate_transaction(transaction)

        self.assertTrue(any("invalid transaction state" in error for error in errors))


class TransactionCommitTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "novel-harness").mkdir()
        (self.root / "world" / ".transactions").mkdir(parents=True)
        (self.root / "world" / "outline.md").write_text(
            "旧大纲\n", encoding="utf-8"
        )
        self.manifest_path = self.root / "novel-harness" / "context.manifest.yaml"
        self.write_manifest()

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_manifest(self, *, writes=None, preview=False):
        if writes is None:
            writes = ["../world/"]
        route = {
            "name": "update-world",
            "path": "../writespec/commands/update-world.md",
            "activation": "command",
            "matches": [{"literal": "更新世界"}],
            "writes": writes,
            "pipeline": "update-world",
        }
        if preview:
            route = {
                "name": "create-chapter",
                "path": "../writespec/commands/draft-chapter.md",
                "activation": "command",
                "matches": [
                    {
                        "pattern": r"^构思第\s*(?P<chapter>\d+)\s*章$",
                        "display": "构思第 N 章",
                        "mode": "preview",
                    }
                ],
                "modes": {"preview": {"writes": []}},
            }
        self.manifest_path.write_text(
            yaml.safe_dump(
                {
                    "schema": "novel-harness/context/v2",
                    "routes": {"commands": [route]},
                    "pipelines": {
                        "update-world": {
                            "stages": [
                                {
                                    "name": "preflight",
                                    "uses": "update-world",
                                    "handler": "preflight",
                                    "required": True,
                                },
                                {
                                    "name": "commit",
                                    "uses": "update-world",
                                    "handler": "transaction-commit",
                                    "required": True,
                                },
                            ]
                        }
                    },
                    "transaction": {"commit_order": ["../world/"]},
                    "verification": {
                        "transaction_gates": [
                            {"name": "prepared-change-set"},
                            {"name": "postflight-consistency"},
                        ]
                    },
                },
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

    def stage_file(self, relative_path, text):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def write_prepared_transaction(
        self,
        *,
        target="world/outline.md",
        staged="world/.staging/TX-CMD-UPDATE-WORLD-0001-R01/world/outline.md",
        baseline_hash=None,
        state="PREPARED",
        applied=False,
        source_command="更新世界",
        command="update-world",
        mode=None,
        arguments=None,
    ):
        target_path = self.root / target
        if baseline_hash is None:
            baseline_hash = sha256_file(target_path)
        staged_path = self.stage_file(staged, "新大纲\n")
        key = "CH-0001:outline"
        data = {
            "schema": "novel-harness/transaction/v1",
            "transaction_id": "TX-CMD-UPDATE-WORLD-0001-R01",
            "source_command": source_command,
            "command": command,
            "mode": mode,
            "pipeline": "update-world",
            "arguments": arguments or {},
            "state": state,
            "archive_state": "NOT_CHECKED",
            "stages": [{"name": "preflight", "status": "PASS"}],
            "gates": [],
            "changes": [
                {
                    "target": target,
                    "staged": staged,
                    "baseline_hash": baseline_hash,
                    "staged_hash": sha256_file(staged_path),
                    "idempotency_key": key,
                }
            ],
            "applied_keys": [key] if applied else [],
            "confirmation_nonce": "test-confirmation-nonce",
            "recovery": {"last_successful_stage": "final-gates"},
        }
        if applied:
            target_path.write_text("新大纲\n", encoding="utf-8")
        transaction_path = (
            self.root
            / "world/.transactions/TX-CMD-UPDATE-WORLD-0001-R01.yaml"
        )
        transaction_path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return transaction_path

    def test_commit_replaces_target_when_hashes_match(self):
        transaction_path = self.write_prepared_transaction()

        result = commit_transaction(
            self.root, self.manifest_path, transaction_path
        )

        self.assertEqual(
            "新大纲\n",
            (self.root / "world/outline.md").read_text(encoding="utf-8"),
        )
        self.assertEqual("COMPLETE", result["state"])
        self.assertEqual(["CH-0001:outline"], result["applied_keys"])
        self.assertEqual(
            {"prepared-change-set", "postflight-consistency"},
            {gate["gate"] for gate in result["gates"]},
        )

    def test_commit_stops_before_write_when_baseline_changed(self):
        transaction_path = self.write_prepared_transaction()
        (self.root / "world/outline.md").write_text(
            "用户新修改\n", encoding="utf-8"
        )

        with self.assertRaisesRegex(TransactionError, "baseline hash mismatch"):
            commit_transaction(self.root, self.manifest_path, transaction_path)

        self.assertEqual(
            "用户新修改\n",
            (self.root / "world/outline.md").read_text(encoding="utf-8"),
        )

    def test_preflight_checks_all_changes_before_first_write(self):
        transaction_path = self.write_prepared_transaction()
        data = yaml.safe_load(transaction_path.read_text(encoding="utf-8"))
        second_target = self.root / "world/characters.md"
        second_target.write_text("用户角色\n", encoding="utf-8")
        second_stage = self.stage_file(
            "world/.staging/TX-CMD-UPDATE-WORLD-0001-R01/world/characters.md",
            "新角色\n",
        )
        data["changes"].append(
            {
                "target": "world/characters.md",
                "staged": str(second_stage.relative_to(self.root)),
                "baseline_hash": "sha256:" + "0" * 64,
                "staged_hash": sha256_file(second_stage),
                "idempotency_key": "CH-0001:characters",
            }
        )
        transaction_path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(TransactionError, "baseline hash mismatch"):
            commit_transaction(self.root, self.manifest_path, transaction_path)

        self.assertEqual(
            "旧大纲\n",
            (self.root / "world/outline.md").read_text(encoding="utf-8"),
        )

    def test_missing_local_link_is_rejected_before_first_write(self):
        transaction_path = self.write_prepared_transaction()
        transaction = yaml.safe_load(transaction_path.read_text(encoding="utf-8"))
        staged_path = self.root / transaction["changes"][0]["staged"]
        staged_path.write_text(
            "[缺失索引](missing.md)\n", encoding="utf-8"
        )
        transaction["changes"][0]["staged_hash"] = sha256_file(staged_path)
        transaction_path.write_text(
            yaml.safe_dump(transaction, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(TransactionError, "link target is missing"):
            commit_transaction(self.root, self.manifest_path, transaction_path)

        self.assertEqual(
            "旧大纲\n",
            (self.root / "world/outline.md").read_text(encoding="utf-8"),
        )

    def test_missing_local_link_anchor_is_rejected_before_first_write(self):
        transaction_path = self.write_prepared_transaction()
        (self.root / "world/archive.md").write_text(
            "# Existing\n", encoding="utf-8"
        )
        transaction = yaml.safe_load(transaction_path.read_text(encoding="utf-8"))
        staged_path = self.root / transaction["changes"][0]["staged"]
        staged_path.write_text(
            "[缺失锚点](archive.md#missing)\n", encoding="utf-8"
        )
        transaction["changes"][0]["staged_hash"] = sha256_file(staged_path)
        transaction_path.write_text(
            yaml.safe_dump(transaction, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(TransactionError, "link anchor is missing"):
            commit_transaction(self.root, self.manifest_path, transaction_path)

        self.assertEqual(
            "旧大纲\n",
            (self.root / "world/outline.md").read_text(encoding="utf-8"),
        )

    def test_missing_markdown_reference_definition_is_rejected(self):
        transaction_path = self.write_prepared_transaction()
        transaction = yaml.safe_load(transaction_path.read_text(encoding="utf-8"))
        staged_path = self.root / transaction["changes"][0]["staged"]
        staged_path.write_text("[缺失引用][missing]\n", encoding="utf-8")
        transaction["changes"][0]["staged_hash"] = sha256_file(staged_path)
        transaction_path.write_text(
            yaml.safe_dump(transaction, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(TransactionError, "reference definition"):
            commit_transaction(self.root, self.manifest_path, transaction_path)

    def test_resume_skips_an_existing_idempotency_key(self):
        transaction_path = self.write_prepared_transaction(
            state="COMMITTING", applied=True
        )

        result = commit_transaction(
            self.root, self.manifest_path, transaction_path
        )

        self.assertEqual(["CH-0001:outline"], result["applied_keys"])
        self.assertEqual("COMPLETE", result["state"])

    def test_resume_recovers_when_target_was_replaced_before_key_was_recorded(self):
        transaction_path = self.write_prepared_transaction(state="COMMITTING")
        (self.root / "world/outline.md").write_text("新大纲\n", encoding="utf-8")

        result = commit_transaction(
            self.root, self.manifest_path, transaction_path
        )

        self.assertEqual(["CH-0001:outline"], result["applied_keys"])
        self.assertEqual("COMPLETE", result["state"])

    def test_resume_recovers_new_target_created_before_key_was_recorded(self):
        transaction_path = self.write_prepared_transaction(
            target="world/new.md",
            baseline_hash="absent",
            state="COMMITTING",
        )
        (self.root / "world/new.md").write_text("新大纲\n", encoding="utf-8")

        result = commit_transaction(
            self.root, self.manifest_path, transaction_path
        )

        self.assertEqual(["CH-0001:outline"], result["applied_keys"])
        self.assertEqual("COMPLETE", result["state"])

    def test_overwrite_policy_requires_target_confirmation(self):
        transaction_path = self.write_prepared_transaction()
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest["routes"]["commands"][0]["requires_confirmation"] = (
            "when_overwriting"
        )
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(TransactionError, "overwrite confirmation"):
            commit_transaction(self.root, self.manifest_path, transaction_path)

    def test_overwrite_policy_accepts_exact_user_confirmation(self):
        transaction_path = self.write_prepared_transaction()
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest["routes"]["commands"][0]["requires_confirmation"] = (
            "when_overwriting"
        )
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        confirm_overwrite(
            self.root,
            self.manifest_path,
            transaction_path,
            "world/outline.md",
            "CONFIRM world/outline.md",
        )

        result = commit_transaction(
            self.root, self.manifest_path, transaction_path
        )

        self.assertEqual("COMPLETE", result["state"])

    def test_rejects_empty_change_set_for_normal_write_command(self):
        transaction_path = self.write_prepared_transaction()
        transaction = yaml.safe_load(transaction_path.read_text(encoding="utf-8"))
        transaction["changes"] = []
        transaction_path.write_text(
            yaml.safe_dump(transaction, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(TransactionError, "change set is empty"):
            commit_transaction(self.root, self.manifest_path, transaction_path)

    def test_read_only_audit_completes_with_semantic_evidence_and_no_changes(self):
        original_path = self.write_prepared_transaction()
        transaction = yaml.safe_load(original_path.read_text(encoding="utf-8"))
        transaction.update(
            {
                "transaction_id": "TX-CMD-AUDIT-ORIGINALITY-0001-R01",
                "source_command": "审计原创性",
                "command": "audit-originality",
                "pipeline": "audit-originality",
                "coverage": {"through_chapter": 0, "events": []},
                "changes": [],
                "stages": [],
                "gates": [
                    {
                        "gate": "audit",
                        "kind": "semantic",
                        "required": True,
                        "status": "PASS",
                        "summary": "审计通过",
                        "evidence": [
                            {
                                "claim": "主线差异化成立",
                                "source": "world/outline.md",
                            }
                        ],
                    }
                ],
            }
        )
        transaction_path = (
            self.root
            / "world/.transactions/TX-CMD-AUDIT-ORIGINALITY-0001-R01.yaml"
        )
        transaction_path.write_text(
            yaml.safe_dump(transaction, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest["routes"]["commands"][0].update(
            {
                "name": "audit-originality",
                "matches": [{"literal": "审计原创性"}],
                "pipeline": "audit-originality",
                "side_effect": "read_only",
                "writes": [],
            }
        )
        manifest["pipelines"] = {
            "audit-originality": {
                "stages": [
                    {
                        "name": "audit",
                        "uses": "audit-originality",
                        "handler": "semantic-gate",
                        "required": True,
                    }
                ]
            }
        }
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        result = commit_transaction(
            self.root, self.manifest_path, transaction_path
        )

        self.assertEqual("COMPLETE", result["state"])

    def test_read_only_audit_rejects_tampered_chapter_coverage(self):
        original_path = self.write_prepared_transaction()
        transaction = yaml.safe_load(original_path.read_text(encoding="utf-8"))
        transaction.update(
            {
                "transaction_id": "TX-CMD-AUDIT-ORIGINALITY-0001-R01",
                "source_command": "审计原创性",
                "command": "audit-originality",
                "pipeline": "audit-originality",
                "coverage": {"through_chapter": 999, "events": []},
                "changes": [],
                "stages": [],
                "gates": [
                    {
                        "gate": "audit",
                        "kind": "semantic",
                        "required": True,
                        "status": "PASS",
                        "summary": "审计通过",
                        "evidence": [
                            {
                                "claim": "主线差异化成立",
                                "source": "world/outline.md",
                            }
                        ],
                    }
                ],
            }
        )
        transaction_path = (
            self.root
            / "world/.transactions/TX-CMD-AUDIT-ORIGINALITY-0001-R01.yaml"
        )
        transaction_path.write_text(
            yaml.safe_dump(transaction, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest["routes"]["commands"][0].update(
            {
                "name": "audit-originality",
                "matches": [{"literal": "审计原创性"}],
                "pipeline": "audit-originality",
                "side_effect": "read_only",
                "writes": [],
            }
        )
        manifest["pipelines"] = {
            "audit-originality": {
                "stages": [
                    {
                        "name": "audit",
                        "uses": "audit-originality",
                        "handler": "semantic-gate",
                        "required": True,
                    }
                ]
            }
        }
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(TransactionError, "coverage was modified"):
            commit_transaction(self.root, self.manifest_path, transaction_path)

    def test_rejects_transaction_outside_manifest_record_directory(self):
        transaction_path = self.write_prepared_transaction()
        rogue_path = self.root / transaction_path.name
        rogue_path.write_text(
            transaction_path.read_text(encoding="utf-8"), encoding="utf-8"
        )

        with self.assertRaisesRegex(TransactionError, "record directory"):
            commit_transaction(self.root, self.manifest_path, rogue_path)

    def test_rejects_target_outside_manifest_write_scope(self):
        transaction_path = self.write_prepared_transaction(
            target="chapters/CH-0001.txt",
            baseline_hash="absent",
        )

        with self.assertRaisesRegex(TransactionError, "outside command write scope"):
            commit_transaction(self.root, self.manifest_path, transaction_path)

    def test_migration_child_cannot_replace_another_chapter(self):
        self.write_manifest(writes=["../chapters/", "../world/"])
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        route = manifest["routes"]["commands"][0]
        route.update(
            {
                "name": "migrate-presentation-chapter",
                "matches": [
                    {
                        "pattern": r"^迁移正文呈现\s+CH-(?P<chapter>\d{4})$",
                        "display": "迁移正文呈现 CH-0001",
                    }
                ],
                "chapter_target_only": True,
            }
        )
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        transaction_path = self.write_prepared_transaction(
            target="chapters/CH-0002-他章.txt",
            staged=(
                "world/.staging/TX-CMD-UPDATE-WORLD-0001-R01/"
                "chapters/CH-0002-他章.txt"
            ),
            baseline_hash="absent",
            source_command="迁移正文呈现 CH-0001",
            command="migrate-presentation-chapter",
            arguments={"chapter": "0001"},
        )

        with self.assertRaisesRegex(TransactionError, "authorized chapter"):
            commit_transaction(self.root, self.manifest_path, transaction_path)

    def test_rejects_parent_traversal(self):
        transaction_path = self.write_prepared_transaction(
            target="../outside.md",
            baseline_hash="absent",
        )

        with self.assertRaisesRegex(TransactionError, "path escapes repository"):
            commit_transaction(self.root, self.manifest_path, transaction_path)

    def test_rejects_file_outside_transaction_staging_directory(self):
        transaction_path = self.write_prepared_transaction(
            staged="world/untrusted.md"
        )

        with self.assertRaisesRegex(TransactionError, "outside transaction staging"):
            commit_transaction(self.root, self.manifest_path, transaction_path)

    def test_preview_mode_has_no_write_scope(self):
        self.write_manifest(preview=True)
        transaction_path = self.write_prepared_transaction(
            source_command="构思第 1 章",
            command="create-chapter",
            mode="preview",
            arguments={"chapter": "1"},
        )

        with self.assertRaisesRegex(TransactionError, "outside command write scope"):
            commit_transaction(self.root, self.manifest_path, transaction_path)

    def test_requires_prepared_or_committing_state(self):
        transaction_path = self.write_prepared_transaction(state="PREPARING")

        with self.assertRaisesRegex(TransactionError, "cannot commit from state"):
            commit_transaction(self.root, self.manifest_path, transaction_path)

    def test_rejects_missing_required_pipeline_gate(self):
        transaction_path = self.write_prepared_transaction()
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest["pipelines"]["update-world"]["stages"].insert(
            1,
            {
                "name": "world-audit",
                "uses": "update-world",
                "handler": "semantic-gate",
                "required": True,
            },
        )
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(TransactionError, "required gate is missing"):
            commit_transaction(self.root, self.manifest_path, transaction_path)

    def test_required_semantic_gate_can_disallow_warn(self):
        transaction_path = self.write_prepared_transaction()
        transaction = load_transaction(transaction_path)
        transaction["gates"] = [
            {
                "gate": "plot-alignment",
                "kind": "semantic",
                "required": True,
                "status": "WARN",
                "summary": "存在剧情偏离风险",
                "evidence": [
                    {
                        "claim": "本章没有完成绑定结果",
                        "source": "world/outline.md",
                    }
                ],
            }
        ]
        transaction_path.write_text(
            yaml.safe_dump(transaction, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest["pipelines"]["update-world"]["stages"].insert(
            1,
            {
                "name": "plot-alignment",
                "uses": "update-world",
                "handler": "semantic-gate",
                "required": True,
                "allowed_statuses": ["PASS"],
            },
        )
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(TransactionError, "required gate did not pass"):
            commit_transaction(self.root, self.manifest_path, transaction_path)

    def test_rejects_missing_required_agent_stage(self):
        transaction_path = self.write_prepared_transaction()
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest["pipelines"]["update-world"]["stages"].insert(
            1,
            {
                "name": "prepare-changes",
                "uses": "update-world",
                "handler": "agent",
                "required": True,
            },
        )
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(TransactionError, "required stage is missing"):
            commit_transaction(self.root, self.manifest_path, transaction_path)

    def test_executor_runs_deterministic_gate_instead_of_trusting_pass(self):
        transaction_path = self.write_prepared_transaction()
        transaction = yaml.safe_load(transaction_path.read_text(encoding="utf-8"))
        transaction["gates"] = [
            {
                "gate": "script-check",
                "kind": "deterministic",
                "required": True,
                "status": "PASS",
                "summary": "untrusted self report",
                "evidence": [],
            }
        ]
        transaction_path.write_text(
            yaml.safe_dump(transaction, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        (self.root / "fail_gate.py").write_text(
            "raise SystemExit(7)\n", encoding="utf-8"
        )
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest["pipelines"]["update-world"]["stages"].insert(
            1,
            {
                "name": "script-check",
                "uses": "update-world",
                "handler": "deterministic-gate",
                "required": True,
            },
        )
        manifest["verification"] = {
            "commands": [
                {
                    "name": "script-check",
                    "command": "python fail_gate.py",
                }
            ]
        }
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(TransactionError, "deterministic gate failed"):
            commit_transaction(self.root, self.manifest_path, transaction_path)

        recorded = load_transaction(transaction_path)
        self.assertEqual("FAIL", recorded["gates"][0]["status"])
        self.assertEqual(7, recorded["gates"][0]["evidence"][0]["exit_code"])

        (self.root / "fail_gate.py").write_text(
            "print('fixed')\n", encoding="utf-8"
        )
        result = commit_transaction(
            self.root, self.manifest_path, transaction_path
        )

        self.assertEqual("COMPLETE", result["state"])
        script_gate = next(
            gate for gate in result["gates"] if gate["gate"] == "script-check"
        )
        self.assertEqual("PASS", script_gate["status"])

    def test_executor_resolves_staged_outline_for_deterministic_gate(self):
        transaction_path = self.write_prepared_transaction()
        (self.root / "check_outline.py").write_text(
            "from pathlib import Path\n"
            "import sys\n"
            "path = Path(sys.argv[1])\n"
            "raise SystemExit(0 if path.is_file() and '.staging' in path.parts else 9)\n",
            encoding="utf-8",
        )
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest["pipelines"]["update-world"]["stages"].insert(
            1,
            {
                "name": "outline-contract",
                "uses": "update-world",
                "handler": "deterministic-gate",
                "required": True,
            },
        )
        manifest["verification"] = {
            "commands": [
                {
                    "name": "outline-contract",
                    "command": "python check_outline.py <outline_file>",
                }
            ]
        }
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        result = commit_transaction(self.root, self.manifest_path, transaction_path)

        gate = next(
            item for item in result["gates"] if item["gate"] == "outline-contract"
        )
        self.assertEqual("PASS", gate["status"])

    def test_required_archive_stage_rejects_unresolved_archive_state(self):
        transaction_path = self.write_prepared_transaction(
            source_command="归档世界",
            command="archive-world",
        )
        transaction = yaml.safe_load(transaction_path.read_text(encoding="utf-8"))
        transaction["pipeline"] = "archive-world"
        transaction_path.write_text(
            yaml.safe_dump(transaction, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest["routes"]["commands"][0].update(
            {
                "name": "archive-world",
                "matches": [{"literal": "归档世界"}],
                "pipeline": "archive-world",
            }
        )
        manifest["pipelines"] = {
            "archive-world": {
                "stages": [
                    {
                        "name": "preflight",
                        "uses": "archive-world",
                        "handler": "preflight",
                        "required": True,
                    },
                    {
                        "name": "commit",
                        "uses": "archive-world",
                        "handler": "transaction-archive",
                        "required": True,
                    },
                ]
            }
        }
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(TransactionError, "archive state is incomplete"):
            commit_transaction(self.root, self.manifest_path, transaction_path)

    def test_required_archive_stage_accepts_not_due(self):
        transaction_path = self.write_prepared_transaction(
            source_command="归档世界",
            command="archive-world",
        )
        transaction = yaml.safe_load(transaction_path.read_text(encoding="utf-8"))
        transaction["pipeline"] = "archive-world"
        transaction["archive_state"] = "NOT_DUE"
        transaction["changes"] = []
        transaction_path.write_text(
            yaml.safe_dump(transaction, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest["routes"]["commands"][0].update(
            {
                "name": "archive-world",
                "matches": [{"literal": "归档世界"}],
                "pipeline": "archive-world",
            }
        )
        manifest["pipelines"] = {
            "archive-world": {
                "stages": [
                    {
                        "name": "preflight",
                        "uses": "archive-world",
                        "handler": "preflight",
                        "required": True,
                    },
                    {
                        "name": "commit",
                        "uses": "archive-world",
                        "handler": "transaction-archive",
                        "required": True,
                    },
                ]
            }
        }
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        result = commit_transaction(self.root, self.manifest_path, transaction_path)

        self.assertEqual("COMPLETE", result["state"])

    def test_completed_archive_requires_archive_and_active_targets(self):
        transaction_path = self.write_prepared_transaction(
            source_command="归档世界",
            command="archive-world",
        )
        transaction = yaml.safe_load(transaction_path.read_text(encoding="utf-8"))
        transaction["pipeline"] = "archive-world"
        transaction["archive_state"] = "COMPLETE"
        transaction_path.write_text(
            yaml.safe_dump(transaction, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest["routes"]["commands"][0].update(
            {
                "name": "archive-world",
                "matches": [{"literal": "归档世界"}],
                "pipeline": "archive-world",
            }
        )
        manifest["pipelines"] = {
            "archive-world": {
                "stages": [
                    {
                        "name": "commit",
                        "uses": "archive-world",
                        "handler": "transaction-archive",
                        "required": True,
                    }
                ]
            }
        }
        manifest["archive"] = [
            {
                "name": "outline-history",
                "path": "../world/archive/outline_history.md",
            }
        ]
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(TransactionError, "archive change set"):
            commit_transaction(self.root, self.manifest_path, transaction_path)


class TransactionBeginTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "novel-harness").mkdir()
        self.manifest_path = self.root / "novel-harness/context.manifest.yaml"
        self.manifest_path.write_text(
            yaml.safe_dump(
                {
                    "schema": "novel-harness/context/v2",
                    "routes": {
                        "commands": [
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
                                    "full": {
                                        "writes": ["../chapters/", "../world/"]
                                    },
                                    "preview": {"writes": []},
                                },
                            },
                            {
                                "name": "create-style",
                                "path": "create-style.md",
                                "activation": "command",
                                "matches": [{"literal": "创建写作风格"}],
                                "writes": ["../writespec/style-guide.md"],
                            },
                            {
                                "name": "check-status",
                                "path": "status.md",
                                "activation": "command",
                                "matches": [{"literal": "查看世界状态"}],
                            },
                            {
                                "name": "audit-originality",
                                "path": "audit.md",
                                "activation": "command",
                                "matches": [{"literal": "审计原创性"}],
                                "pipeline": "audit-originality",
                                "side_effect": "read_only",
                            },
                        ]
                    },
                    "pipelines": {
                        "audit-originality": {
                            "stages": [
                                {
                                    "name": "audit",
                                    "uses": "audit-originality",
                                    "handler": "semantic-gate",
                                    "required": True,
                                }
                            ]
                        }
                    },
                },
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def enable_plan_contract(self):
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest["routes"]["commands"][0]["plan_contract"] = "required"
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def write_outline(self, contract=None):
        if contract is None:
            contract = valid_contract()
        outline = self.root / "world/outline.md"
        outline.parent.mkdir(parents=True, exist_ok=True)
        outline.write_text(
            "---\n"
            + yaml.safe_dump(contract, allow_unicode=True, sort_keys=False)
            + "---\n# 小说大纲\n",
            encoding="utf-8",
        )
        return outline

    def test_plan_bound_route_rejects_missing_outline(self):
        self.enable_plan_contract()

        with self.assertRaisesRegex(TransactionError, "cannot read outline"):
            begin_transaction(self.root, self.manifest_path, "创作第 1 章")

    def add_presentation_migration_routes(self):
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest["routes"]["commands"].extend(
            [
                {
                    "name": "migrate-presentation",
                    "path": "migrate.md",
                    "activation": "command",
                    "matches": [{"literal": "迁移正文呈现"}],
                    "pipeline": "migration-scan",
                    "side_effect": "read_only",
                },
                {
                    "name": "migrate-presentation-chapter",
                    "path": "migrate.md",
                    "activation": "command",
                    "matches": [
                        {
                            "pattern": r"^迁移正文呈现\s+CH-(?P<chapter>\d{4})$",
                            "display": "迁移正文呈现 CH-0001",
                        }
                    ],
                    "pipeline": "migration-chapter",
                    "side_effect": "write",
                    "writes": ["../chapters/", "../world/"],
                    "requires_parent_authorization": "migrate-presentation",
                },
            ]
        )
        manifest["pipelines"].update(
            {
                "migration-scan": {
                    "stages": [
                        {
                            "name": "scan",
                            "uses": "migrate-presentation",
                            "handler": "semantic-gate",
                            "required": True,
                        }
                    ]
                },
                "migration-chapter": {
                    "stages": [
                        {
                            "name": "prepare-rewrite",
                            "uses": "migrate-presentation-chapter",
                            "handler": "agent",
                            "required": True,
                        }
                    ]
                },
            }
        )
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def write_published_chapter(self, number, text):
        path = self.root / "chapters" / f"CH-{number:04d}-旧章.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_migration_parent_scans_only_chapters_with_presentation_issues(self):
        self.add_presentation_migration_routes()
        self.write_published_chapter(1, "上一章留下的伤仍在。")
        self.write_published_chapter(2, "此前留下的伤仍在。")

        path = begin_transaction(self.root, self.manifest_path, "迁移正文呈现")

        migration = load_transaction(path)["migration"]
        self.assertEqual(["CH-0001"], migration["chapters"])
        self.assertIn("chapter structure reference", migration["issues"]["CH-0001"][0])

    def test_migration_child_requires_completed_parent_authorization(self):
        self.add_presentation_migration_routes()
        self.write_published_chapter(1, "上一章留下的伤仍在。")

        with self.assertRaisesRegex(TransactionError, "migration authorization"):
            begin_transaction(
                self.root, self.manifest_path, "迁移正文呈现 CH-0001"
            )

    def test_migration_child_uses_next_chapter_revision_and_parent_id(self):
        self.add_presentation_migration_routes()
        self.write_published_chapter(1, "上一章留下的伤仍在。")
        parent_path = begin_transaction(
            self.root, self.manifest_path, "迁移正文呈现"
        )
        parent = load_transaction(parent_path)
        parent["state"] = "COMPLETE"
        parent_path.write_text(
            yaml.safe_dump(parent, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        prior = parent_path.parent / "TX-CH-0001-R01.yaml"
        prior.write_text(
            yaml.safe_dump(
                {"transaction_id": "TX-CH-0001-R01", "state": "COMPLETE"},
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        child_path = begin_transaction(
            self.root, self.manifest_path, "迁移正文呈现 CH-0001"
        )

        child = load_transaction(child_path)
        self.assertEqual("TX-CH-0001-R02.yaml", child_path.name)
        self.assertEqual(parent["transaction_id"], child["parent_transaction"])

    def test_migration_parent_commit_rejects_stale_scan(self):
        self.add_presentation_migration_routes()
        chapter = self.write_published_chapter(1, "上一章留下的伤仍在。")
        parent_path = begin_transaction(
            self.root, self.manifest_path, "迁移正文呈现"
        )
        parent = load_transaction(parent_path)
        parent["state"] = "PREPARED"
        parent["gates"] = [
            {
                "gate": "scan",
                "kind": "semantic",
                "required": True,
                "status": "PASS",
                "summary": "扫描完成",
                "evidence": [
                    {"claim": "已扫描正式章节", "source": "chapters/"}
                ],
            }
        ]
        parent_path.write_text(
            yaml.safe_dump(parent, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        chapter.write_text("此前留下的伤仍在。", encoding="utf-8")

        with self.assertRaisesRegex(TransactionError, "migration scan became stale"):
            commit_transaction(self.root, self.manifest_path, parent_path)

    def test_migration_parent_commit_authorizes_scanned_chapters(self):
        self.add_presentation_migration_routes()
        self.write_published_chapter(1, "上一章留下的伤仍在。")
        parent_path = begin_transaction(
            self.root, self.manifest_path, "迁移正文呈现"
        )
        parent = load_transaction(parent_path)
        parent["state"] = "PREPARED"
        parent["gates"] = [
            {
                "gate": "scan",
                "kind": "semantic",
                "required": True,
                "status": "PASS",
                "summary": "扫描完成",
                "evidence": [
                    {"claim": "已扫描正式章节", "source": "chapters/"}
                ],
            }
        ]
        parent_path.write_text(
            yaml.safe_dump(parent, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        committed = commit_transaction(self.root, self.manifest_path, parent_path)

        self.assertEqual("AUTHORIZED", committed["migration"]["migration_state"])

    def test_completed_migration_chapter_cannot_reuse_parent_authorization(self):
        self.add_presentation_migration_routes()
        self.write_published_chapter(1, "上一章留下的伤仍在。")
        parent_path = begin_transaction(
            self.root, self.manifest_path, "迁移正文呈现"
        )
        parent = load_transaction(parent_path)
        parent["state"] = "COMPLETE"
        parent["migration"]["completed"] = ["CH-0001"]
        parent_path.write_text(
            yaml.safe_dump(parent, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(TransactionError, "migration authorization"):
            begin_transaction(
                self.root, self.manifest_path, "迁移正文呈现 CH-0001"
            )

    def test_migration_child_completion_updates_parent_progress(self):
        from scripts.transaction_executor import record_migration_child_completion

        self.add_presentation_migration_routes()
        self.write_published_chapter(1, "上一章留下的伤仍在。")
        self.write_published_chapter(2, "前文留下的伤仍在。")
        parent_path = begin_transaction(
            self.root, self.manifest_path, "迁移正文呈现"
        )
        parent = load_transaction(parent_path)
        parent["state"] = "COMPLETE"
        parent_path.write_text(
            yaml.safe_dump(parent, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        record_migration_child_completion(
            parent_path.parent,
            {
                "transaction_id": "TX-CH-0001-R02",
                "parent_transaction": parent["transaction_id"],
                "arguments": {"chapter": "0001"},
            },
        )

        updated = load_transaction(parent_path)["migration"]
        self.assertEqual("PARTIAL", updated["migration_state"])
        self.assertEqual(["CH-0001"], updated["completed"])
        self.assertEqual(
            "TX-CH-0001-R02", updated["child_transactions"]["CH-0001"]
        )

    def test_begin_records_frozen_chapter_plan_binding(self):
        self.enable_plan_contract()
        self.write_outline()

        path = begin_transaction(self.root, self.manifest_path, "创作第 1 章")

        binding = load_transaction(path)["plan_contract"]
        self.assertEqual("ARC-001", binding["arc_id"])
        self.assertEqual("GOAL-ARC-001", binding["arc_goal_id"])
        self.assertEqual("CH-0001", binding["chapter_id"])

    def test_plan_binding_rejects_outline_changed_after_begin(self):
        self.enable_plan_contract()
        outline = self.write_outline()
        path = begin_transaction(self.root, self.manifest_path, "创作第 1 章")
        transaction = load_transaction(path)
        contract = valid_contract()
        contract["revision"] = 2
        outline.write_text(
            "---\n"
            + yaml.safe_dump(contract, allow_unicode=True, sort_keys=False)
            + "---\n# 小说大纲\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(TransactionError, "plan contract became stale"):
            validate_plan_binding(self.root, transaction)

    def test_begin_creates_chapter_transaction_with_resolved_mode(self):
        path = begin_transaction(
            self.root, self.manifest_path, "创作第 1 章"
        )

        self.assertEqual("TX-CH-0001-R01.yaml", path.name)
        transaction = load_transaction(path)
        self.assertEqual("create-chapter", transaction["command"])
        self.assertEqual("full", transaction["mode"])
        self.assertEqual({"chapter": "1"}, transaction["arguments"])
        self.assertEqual("PREFLIGHT", transaction["state"])

    def test_begin_increments_revision_after_complete_transaction(self):
        first = begin_transaction(self.root, self.manifest_path, "创作第 1 章")
        data = load_transaction(first)
        data["state"] = "COMPLETE"
        first.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        second = begin_transaction(self.root, self.manifest_path, "创作第 1 章")

        self.assertEqual("TX-CH-0001-R02.yaml", second.name)

    def test_begin_refuses_when_chapter_transaction_is_active(self):
        begin_transaction(self.root, self.manifest_path, "创作第 1 章")

        with self.assertRaisesRegex(TransactionError, "active transaction exists"):
            begin_transaction(self.root, self.manifest_path, "创作第 1 章")

    def test_begin_creates_sequential_non_chapter_runs(self):
        first = begin_transaction(self.root, self.manifest_path, "创建写作风格")
        first_data = load_transaction(first)
        first_data["state"] = "COMPLETE"
        first.write_text(
            yaml.safe_dump(first_data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        second = begin_transaction(self.root, self.manifest_path, "创建写作风格")

        self.assertEqual("TX-CMD-CREATE-STYLE-0001-R01.yaml", first.name)
        self.assertEqual("TX-CMD-CREATE-STYLE-0002-R01.yaml", second.name)

    def test_begin_rejects_preview_mode(self):
        with self.assertRaisesRegex(TransactionError, "does not authorize writes"):
            begin_transaction(self.root, self.manifest_path, "构思第 1 章")

        self.assertFalse((self.root / "world").exists())

    def test_begin_rejects_read_only_command(self):
        with self.assertRaisesRegex(TransactionError, "does not authorize writes"):
            begin_transaction(self.root, self.manifest_path, "查看世界状态")

    def test_begin_rejects_unregistered_phrase(self):
        with self.assertRaisesRegex(TransactionError, "no command matched"):
            begin_transaction(self.root, self.manifest_path, "帮我写第一章")

    def test_begin_uses_manifest_record_directory(self):
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest["transaction"] = {"record_directory": "../records/"}
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        path = begin_transaction(
            self.root, self.manifest_path, "创建写作风格"
        )

        self.assertEqual(self.root / "records", path.parent)

    def test_begin_allows_read_only_audit_record(self):
        path = begin_transaction(
            self.root, self.manifest_path, "审计原创性"
        )

        transaction = load_transaction(path)
        self.assertEqual("audit-originality", transaction["command"])
        self.assertEqual(
            {"through_chapter": 0, "events": []}, transaction["coverage"]
        )

    def test_periodic_gate_blocks_next_cycle_without_completed_audit(self):
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest["verification"] = {
            "periodic_gates": [
                {
                    "name": "originality-cycle",
                    "pipeline": "audit-originality",
                    "interval_chapters": 10,
                    "blocks_next_cycle": True,
                }
            ]
        }
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(TransactionError, "periodic gate is required"):
            begin_transaction(self.root, self.manifest_path, "创作第 11 章")

    def test_periodic_gate_accepts_audit_covering_checkpoint(self):
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest["verification"] = {
            "periodic_gates": [
                {
                    "name": "originality-cycle",
                    "pipeline": "audit-originality",
                    "interval_chapters": 10,
                    "blocks_next_cycle": True,
                }
            ]
        }
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        transaction_dir = self.root / "world/.transactions"
        transaction_dir.mkdir(parents=True)
        audit_path = (
            transaction_dir
            / "TX-CMD-AUDIT-ORIGINALITY-0001-R01.yaml"
        )
        audit_path.write_text(
            yaml.safe_dump(
                {
                    "schema": "novel-harness/transaction/v1",
                    "transaction_id": "TX-CMD-AUDIT-ORIGINALITY-0001-R01",
                    "source_command": "审计原创性",
                    "command": "audit-originality",
                    "mode": None,
                    "pipeline": "audit-originality",
                    "arguments": {},
                    "state": "COMPLETE",
                    "archive_state": "NOT_CHECKED",
                    "coverage": {"through_chapter": 10, "events": []},
                    "stages": [],
                    "gates": [
                        {
                            "gate": "audit",
                            "kind": "semantic",
                            "required": True,
                            "status": "PASS",
                            "summary": "审计通过",
                            "evidence": [
                                {
                                    "claim": "已审计前十章",
                                    "source": "world/chapter-summary.md",
                                }
                            ],
                        }
                    ],
                    "changes": [],
                    "applied_keys": [],
                    "confirmations": [],
                    "recovery": {"last_successful_stage": "commit"},
                },
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        audit = load_transaction(audit_path)
        audit["gates"][0].update(
            {
                "status": "NOT_APPLICABLE",
                "reason": "错误地跳过审计",
                "evidence": [],
            }
        )
        audit_path.write_text(
            yaml.safe_dump(audit, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(TransactionError, "periodic gate is required"):
            begin_transaction(self.root, self.manifest_path, "创作第 11 章")

        audit["gates"][0].update(
            {
                "status": "PASS",
                "evidence": [
                    {
                        "claim": "已审计前十章",
                        "source": "world/chapter-summary.md",
                    }
                ],
            }
        )
        audit["gates"][0].pop("reason", None)
        audit_path.write_text(
            yaml.safe_dump(audit, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        path = begin_transaction(
            self.root, self.manifest_path, "创作第 11 章"
        )

        self.assertEqual("TX-CH-0011-R01.yaml", path.name)

    def test_periodic_event_blocks_chapter_until_audit_record_covers_it(self):
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest["verification"] = {
            "periodic_gates": [
                {
                    "name": "originality-cycle",
                    "pipeline": "audit-originality",
                    "interval_chapters": 10,
                    "triggers": ["outline_initialized"],
                    "blocks_next_cycle": True,
                }
            ]
        }
        self.manifest_path.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        transaction_dir = self.root / "world/.transactions"
        transaction_dir.mkdir(parents=True)
        (transaction_dir / "TX-CMD-INIT-WORLD-0001-R01.yaml").write_text(
            yaml.safe_dump(
                {
                    "transaction_id": "TX-CMD-INIT-WORLD-0001-R01",
                    "state": "COMPLETE",
                    "events": ["outline_initialized"],
                },
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(TransactionError, "periodic event gate"):
            begin_transaction(self.root, self.manifest_path, "创作第 1 章")

        audit_path = begin_transaction(
            self.root, self.manifest_path, "审计原创性"
        )
        audit = load_transaction(audit_path)
        self.assertEqual(
            ["TX-CMD-INIT-WORLD-0001-R01"], audit["coverage"]["events"]
        )


if __name__ == "__main__":
    unittest.main()
