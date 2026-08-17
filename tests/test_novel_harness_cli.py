import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "novel_harness.py"


class NovelHarnessCliTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "novel-harness").mkdir()
        self.manifest = self.root / "novel-harness/context.manifest.yaml"
        self.manifest.write_text(
            yaml.safe_dump(
                {
                    "schema": "novel-harness/context/v2",
                    "routes": {
                        "commands": [
                            {
                                "name": "create-style",
                                "path": "create-style.md",
                                "activation": "command",
                                "matches": [{"literal": "创建写作风格"}],
                                "pipeline": "create-style",
                                "writes": ["../writespec/style-guide.md"],
                            },
                            {
                                "name": "cleanup-transactions",
                                "path": "cleanup-transactions.md",
                                "activation": "command",
                                "matches": [{"literal": "清理事务缓存"}],
                                "pipeline": "cleanup-transactions",
                                "side_effect": "destructive_local_cache",
                            },
                        ]
                    },
                    "pipelines": {
                        "create-style": {
                            "stages": [
                                {
                                    "name": "generate-style",
                                    "uses": "create-style",
                                    "handler": "agent",
                                    "required": True,
                                }
                            ]
                        },
                        "cleanup-transactions": {
                            "stages": [
                                {
                                    "name": "preview",
                                    "uses": "cleanup-transactions",
                                    "handler": "render",
                                    "required": True,
                                }
                            ]
                        },
                    },
                },
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        self.transaction = self.root / "transaction.yaml"
        self.transaction.write_text(
            yaml.safe_dump(
                {
                    "schema": "novel-harness/transaction/v1",
                    "transaction_id": "TX-CMD-CREATE-STYLE-0001-R01",
                    "source_command": "创建写作风格",
                    "command": "create-style",
                    "mode": None,
                    "arguments": {},
                    "state": "PREFLIGHT",
                    "archive_state": "NOT_CHECKED",
                    "stages": [],
                    "gates": [],
                    "changes": [],
                    "applied_keys": [],
                    "recovery": {"last_successful_stage": None},
                },
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_cli(self, *args, input_text=None):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--manifest",
                str(self.manifest),
                *args,
            ],
            cwd=REPO_ROOT,
            env=env,
            input=input_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def test_validate_transaction_reports_pass(self):
        result = self.run_cli("validate-transaction", str(self.transaction))

        self.assertEqual(0, result.returncode)
        self.assertIn("[PASS] transaction is valid", result.stdout)

    def test_validate_transaction_reports_contract_errors(self):
        self.transaction.write_text("schema: wrong\n", encoding="utf-8")

        result = self.run_cli("validate-transaction", str(self.transaction))

        self.assertEqual(1, result.returncode)
        self.assertIn("[FAIL]", result.stdout)

    def test_status_renders_yaml_record(self):
        result = self.run_cli("status", str(self.transaction))

        self.assertEqual(0, result.returncode)
        self.assertIn("state: PREFLIGHT", result.stdout)
        self.assertIn("transaction_id: TX-CMD-CREATE-STYLE-0001-R01", result.stdout)

    def test_begin_creates_transaction_through_resolver(self):
        result = self.run_cli(
            "begin", "创建写作风格", "--repo-root", str(self.root)
        )

        self.assertEqual(0, result.returncode)
        self.assertIn("TX-CMD-CREATE-STYLE-0001-R01.yaml", result.stdout)
        self.assertTrue(
            (
                self.root
                / "world/.transactions/TX-CMD-CREATE-STYLE-0001-R01.yaml"
            ).is_file()
        )

    def test_begin_reads_command_text_from_utf8_file(self):
        command_file = self.root / "command.txt"
        command_file.write_text("创建写作风格\n", encoding="utf-8")

        result = self.run_cli(
            "begin",
            "--text-file",
            str(command_file),
            "--repo-root",
            str(self.root),
        )

        self.assertEqual(0, result.returncode)
        self.assertIn("TX-CMD-CREATE-STYLE-0001-R01.yaml", result.stdout)

    def test_resolve_returns_pipeline_and_ordered_stages(self):
        result = self.run_cli("resolve", "创建写作风格")

        self.assertEqual(0, result.returncode)
        payload = yaml.safe_load(result.stdout)
        self.assertEqual("create-style", payload["pipeline"])
        self.assertEqual(["generate-style"], payload["stages"])

    def test_resolve_reads_command_text_from_utf8_stdin(self):
        result = self.run_cli("resolve", "--text-stdin", input_text="创建写作风格\n")

        self.assertEqual(0, result.returncode)
        payload = yaml.safe_load(result.stdout)
        self.assertEqual("create-style", payload["command"])

    def test_invariants_renders_manifest_owner_and_related_gates(self):
        manifest = yaml.safe_load(self.manifest.read_text(encoding="utf-8"))
        manifest["routes"]["specs"] = [
            {
                "name": "chapter",
                "path": "../writespec/chapter.md",
                "activation": "pipeline",
                "invariants": ["INV-CHAPTER-001"],
            }
        ]
        manifest["verification"] = {
            "commands": [
                {
                    "name": "chapter-format",
                    "command": "python validate.py <chapter_file>",
                    "invariant": "INV-CHAPTER-001",
                }
            ],
            "semantic_gates": [
                {
                    "name": "narrative-integrity",
                    "spec": "../writespec/chapter.md",
                    "invariant": "INV-CHAPTER-001",
                }
            ],
        }
        self.manifest.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        result = self.run_cli("invariants")

        self.assertEqual(0, result.returncode)
        payload = yaml.safe_load(result.stdout)
        self.assertEqual("INV-CHAPTER-001", payload[0]["id"])
        self.assertEqual("../writespec/chapter.md", payload[0]["owner"])
        self.assertEqual(
            ["chapter-format", "narrative-integrity"], payload[0]["gates"]
        )

    def write_cache_transaction(self, transaction_id="TX-CH-0001-R01"):
        transaction_dir = self.root / "world/.transactions"
        transaction_dir.mkdir(parents=True, exist_ok=True)
        transaction = transaction_dir / f"{transaction_id}.yaml"
        transaction.write_text(
            yaml.safe_dump(
                {
                    "schema": "novel-harness/transaction/v1",
                    "transaction_id": transaction_id,
                    "state": "COMPLETE",
                    "completed_at": "2000-01-01T00:00:00+00:00",
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        staged = self.root / "chapters/.staging" / transaction_id / "chapter.txt"
        staged.parent.mkdir(parents=True, exist_ok=True)
        staged.write_text("cache", encoding="utf-8")
        return transaction, staged

    def test_cache_status_reports_current_cache_metrics(self):
        self.write_cache_transaction()

        result = self.run_cli("cache-status", "--repo-root", str(self.root))

        self.assertEqual(0, result.returncode)
        payload = yaml.safe_load(result.stdout)
        self.assertEqual(10, payload["retention_days"])
        self.assertEqual(1, payload["eligible_count"])
        self.assertEqual(5, payload["eligible_bytes"])
        self.assertEqual(0, payload["active_transactions"])

    def test_cleanup_cache_previews_and_confirms_once(self):
        transaction_id = "TX-CH-0001-R01"
        transaction, staged = self.write_cache_transaction(transaction_id)

        result = self.run_cli(
            "cleanup-cache",
            transaction_id,
            "--repo-root",
            str(self.root),
            input_text=f"CONFIRM CLEANUP {transaction_id}\n",
        )

        self.assertEqual(0, result.returncode)
        self.assertEqual(1, result.stdout.count("Type \"CONFIRM CLEANUP"))
        self.assertIn("[PASS] cache cleanup complete", result.stdout)
        self.assertFalse(staged.parent.exists())
        record = yaml.safe_load(transaction.read_text(encoding="utf-8"))
        self.assertEqual("CLEANED", record["staging_state"])

    def test_cleanup_cache_rejects_wrong_confirmation_without_deleting(self):
        transaction_id = "TX-CH-0001-R01"
        _, staged = self.write_cache_transaction(transaction_id)

        result = self.run_cli(
            "cleanup-cache",
            transaction_id,
            "--repo-root",
            str(self.root),
            input_text="NO\n",
        )

        self.assertEqual(1, result.returncode)
        self.assertIn("[FAIL] cleanup confirmation did not match", result.stdout)
        self.assertTrue(staged.exists())

    def test_cleanup_cache_requires_registered_manifest_route(self):
        transaction_id = "TX-CH-0001-R01"
        _, staged = self.write_cache_transaction(transaction_id)
        manifest = yaml.safe_load(self.manifest.read_text(encoding="utf-8"))
        manifest["routes"]["commands"] = [manifest["routes"]["commands"][0]]
        manifest["pipelines"].pop("cleanup-transactions")
        self.manifest.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        result = self.run_cli(
            "cleanup-cache",
            transaction_id,
            "--repo-root",
            str(self.root),
            input_text=f"CONFIRM CLEANUP {transaction_id}\n",
        )

        self.assertEqual(1, result.returncode)
        self.assertIn("[FAIL] no command matched", result.stdout)
        self.assertTrue(staged.exists())

    def test_cleanup_cache_rejects_unknown_selection_before_prompt(self):
        _, staged = self.write_cache_transaction()

        result = self.run_cli(
            "cleanup-cache",
            "missing-cache",
            "--repo-root",
            str(self.root),
        )

        self.assertEqual(1, result.returncode)
        self.assertIn("[FAIL] cache item does not exist", result.stdout)
        self.assertNotIn("Type \"CONFIRM CLEANUP", result.stdout)
        self.assertTrue(staged.exists())


if __name__ == "__main__":
    unittest.main()
