import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import yaml

from scripts.transaction_cache import CacheError, cleanup_cache, inspect_cache


UTC = timezone.utc


class TransactionCacheInspectionTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "world/.transactions").mkdir(parents=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_transaction(self, transaction_id, state, *, completed_at=None):
        data = {
            "schema": "novel-harness/transaction/v1",
            "transaction_id": transaction_id,
            "state": state,
        }
        if completed_at is not None:
            data["completed_at"] = completed_at.isoformat()
        path = self.root / "world/.transactions" / f"{transaction_id}.yaml"
        path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return path

    def stage(self, root, name, filename="artifact.txt", text="cache"):
        path = self.root / root / name / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def item(self, inventory, item_id):
        return next(item for item in inventory["items"] if item["id"] == item_id)

    def test_groups_four_staging_roots_and_marks_old_complete_eligible(self):
        now = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
        transaction_id = "TX-CH-0001-R01"
        self.write_transaction(
            transaction_id, "COMPLETE", completed_at=now - timedelta(days=11)
        )
        for staging_root in (
            "chapters/.staging",
            "world/.staging",
            "analysis/.staging",
            "metadata/.staging",
        ):
            self.stage(staging_root, transaction_id)

        inventory = inspect_cache(self.root, now=now)
        item = self.item(inventory, transaction_id)

        self.assertEqual("transaction", item["kind"])
        self.assertEqual(4, item["file_count"])
        self.assertEqual(20, item["bytes"])
        self.assertTrue(item["eligible"])
        self.assertEqual("RETENTION_EXPIRED", item["reason"])

    def test_recent_complete_and_active_transaction_are_not_eligible(self):
        now = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
        recent = "TX-CH-0001-R01"
        active = "TX-CH-0002-R01"
        self.write_transaction(recent, "COMPLETE", completed_at=now - timedelta(days=9))
        self.write_transaction(active, "PREFLIGHT")
        self.stage("chapters/.staging", recent)
        self.stage("chapters/.staging", active)

        inventory = inspect_cache(self.root, now=now)

        self.assertFalse(self.item(inventory, recent)["eligible"])
        self.assertEqual("RETENTION_ACTIVE", self.item(inventory, recent)["reason"])
        self.assertFalse(self.item(inventory, active)["eligible"])
        self.assertEqual("TRANSACTION_ACTIVE", self.item(inventory, active)["reason"])

    def test_legacy_complete_uses_transient_first_observation(self):
        first_seen = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)
        transaction_id = "TX-CH-0001-R01"
        self.write_transaction(transaction_id, "COMPLETE")
        self.stage("chapters/.staging", transaction_id)

        read_only = inspect_cache(self.root, now=first_seen)
        self.assertEqual("LEGACY_UNOBSERVED", self.item(read_only, transaction_id)["reason"])
        self.assertFalse(
            (self.root / ".local/transaction-cache-observations.yaml").exists()
        )

        observed = inspect_cache(
            self.root, now=first_seen, record_observations=True
        )
        self.assertEqual("RETENTION_ACTIVE", self.item(observed, transaction_id)["reason"])

        expired = inspect_cache(self.root, now=first_seen + timedelta(days=11))
        self.assertTrue(self.item(expired, transaction_id)["eligible"])

    def test_orphan_requires_ten_days_and_no_repository_reference(self):
        first_seen = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)
        orphan = "unbound-cache"
        self.stage("world/.staging", orphan)

        inspect_cache(self.root, now=first_seen, record_observations=True)
        expired = inspect_cache(self.root, now=first_seen + timedelta(days=11))
        self.assertTrue(self.item(expired, orphan)["eligible"])
        self.assertEqual("ORPHAN_EXPIRED", self.item(expired, orphan)["reason"])

        (self.root / "notes.md").write_text(
            "保留 world/.staging/unbound-cache 中的证据。", encoding="utf-8"
        )
        referenced = inspect_cache(self.root, now=first_seen + timedelta(days=11))
        self.assertFalse(self.item(referenced, orphan)["eligible"])
        self.assertEqual("ORPHAN_REFERENCED", self.item(referenced, orphan)["reason"])

    def test_orphan_remains_blocked_when_reference_scan_cannot_read_file(self):
        first_seen = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)
        orphan = "unbound-cache"
        self.stage("world/.staging", orphan)
        inspect_cache(self.root, now=first_seen, record_observations=True)
        unreadable = self.root / "unreadable.md"
        unreadable.write_text("unknown", encoding="utf-8")
        original_read_text = Path.read_text

        def guarded_read(path, *args, **kwargs):
            if path == unreadable:
                raise OSError("access denied")
            return original_read_text(path, *args, **kwargs)

        with mock.patch.object(Path, "read_text", guarded_read):
            inventory = inspect_cache(
                self.root, now=first_seen + timedelta(days=11)
            )

        self.assertFalse(self.item(inventory, orphan)["eligible"])
        self.assertEqual(
            "ORPHAN_REFERENCE_UNKNOWN", self.item(inventory, orphan)["reason"]
        )


class TransactionCacheCleanupTest(TransactionCacheInspectionTest):
    def test_deletes_old_complete_staging_and_marks_yaml_cleaned(self):
        now = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
        transaction_id = "TX-CH-0001-R01"
        transaction_path = self.write_transaction(
            transaction_id, "COMPLETE", completed_at=now - timedelta(days=11)
        )
        staged = self.stage("chapters/.staging", transaction_id)

        result = cleanup_cache(
            self.root, [transaction_id], confirmed=True, now=now
        )

        self.assertEqual([transaction_id], result["cleaned"])
        self.assertIsNone(result["failed"])
        self.assertFalse(staged.parent.exists())
        transaction = yaml.safe_load(transaction_path.read_text(encoding="utf-8"))
        self.assertEqual("COMPLETE", transaction["state"])
        self.assertEqual("CLEANED", transaction["staging_state"])

    def test_selected_active_transaction_is_aborted_then_deleted(self):
        now = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
        transaction_id = "TX-CH-0001-R01"
        transaction_path = self.write_transaction(transaction_id, "PREPARED")
        staged = self.stage("world/.staging", transaction_id)

        result = cleanup_cache(
            self.root, [transaction_id], confirmed=True, now=now
        )

        self.assertEqual([transaction_id], result["cleaned"])
        self.assertFalse(staged.parent.exists())
        transaction = yaml.safe_load(transaction_path.read_text(encoding="utf-8"))
        self.assertEqual("ABORTED", transaction["state"])
        self.assertEqual("CLEANED", transaction["staging_state"])

    def test_deletes_expired_unreferenced_orphan_without_permanent_record(self):
        first_seen = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)
        orphan = "unbound-cache"
        staged = self.stage("metadata/.staging", orphan)
        inspect_cache(self.root, now=first_seen, record_observations=True)

        result = cleanup_cache(
            self.root,
            [orphan],
            confirmed=True,
            now=first_seen + timedelta(days=11),
        )

        self.assertEqual([orphan], result["cleaned"])
        self.assertFalse(staged.parent.exists())
        observations = yaml.safe_load(
            (self.root / ".local/transaction-cache-observations.yaml").read_text(
                encoding="utf-8"
            )
        )["observations"]
        self.assertNotIn(f"orphan:{orphan}", observations)

    def test_stops_at_first_ineligible_item(self):
        now = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
        recent = "TX-CH-0001-R01"
        old = "TX-CH-0002-R01"
        self.write_transaction(recent, "COMPLETE", completed_at=now - timedelta(days=1))
        self.write_transaction(old, "COMPLETE", completed_at=now - timedelta(days=11))
        recent_stage = self.stage("chapters/.staging", recent)
        old_stage = self.stage("chapters/.staging", old)

        result = cleanup_cache(
            self.root, [recent, old], confirmed=True, now=now
        )

        self.assertEqual([], result["cleaned"])
        self.assertEqual(recent, result["failed"]["id"])
        self.assertTrue(recent_stage.exists())
        self.assertTrue(old_stage.exists())

    def test_requires_confirmation(self):
        with self.assertRaisesRegex(CacheError, "confirmation is required"):
            cleanup_cache(self.root, [], confirmed=False)

    def test_rejects_duplicate_selection_before_deleting(self):
        now = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
        transaction_id = "TX-CH-0001-R01"
        self.write_transaction(
            transaction_id, "COMPLETE", completed_at=now - timedelta(days=11)
        )
        staged = self.stage("chapters/.staging", transaction_id)

        with self.assertRaisesRegex(CacheError, "duplicate cache item"):
            cleanup_cache(
                self.root,
                [transaction_id, transaction_id],
                confirmed=True,
                now=now,
            )

        self.assertTrue(staged.exists())


if __name__ == "__main__":
    unittest.main()
