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
                            }
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
                        }
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

    def run_cli(self, *args):
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

    def test_resolve_returns_pipeline_and_ordered_stages(self):
        result = self.run_cli("resolve", "创建写作风格")

        self.assertEqual(0, result.returncode)
        payload = yaml.safe_load(result.stdout)
        self.assertEqual("create-style", payload["pipeline"])
        self.assertEqual(["generate-style"], payload["stages"])

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


if __name__ == "__main__":
    unittest.main()
