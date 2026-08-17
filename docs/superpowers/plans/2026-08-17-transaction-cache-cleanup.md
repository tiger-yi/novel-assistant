# Transaction Cache Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a confirmed, retention-aware cleanup workflow for transaction staging without deleting transaction YAML or gate evidence.

**Architecture:** A focused `transaction_cache.py` module discovers transaction-bound and orphan staging directories, computes cache status, applies the 10-day eligibility policy, and deletes one item at a time after one confirmation. The transaction executor records durable transaction lifecycle fields (`completed_at`, `ABORTED`, `staging_state`) while legacy/orphan first-observation timestamps live only in local transient state under `.local/`.

**Tech Stack:** Python 3 standard library, PyYAML, unittest, Manifest v2 YAML.

---

### Task 1: Transaction lifecycle fields

**Files:**
- Modify: `scripts/transaction_executor.py`
- Modify: `templates/transaction-record-template.yaml`
- Test: `tests/test_transaction_executor.py`

- [x] Write failing tests proving `completed_at` is written on commit and `ABORTED` plus `staging_state` validate.
- [x] Run the focused tests and confirm they fail because the fields and state are unsupported.
- [x] Add UTC timestamp generation, lifecycle validation, and template fields.
- [x] Run the focused tests and confirm they pass.

### Task 2: Cache discovery and eligibility

**Files:**
- Create: `scripts/transaction_cache.py`
- Create: `tests/test_transaction_cache.py`

- [x] Write failing tests for four staging roots, 10-day completed retention, legacy first observation, active exclusion, and orphan reference checks.
- [x] Run the focused tests and confirm the module is missing.
- [x] Implement structured discovery, local observation state, byte totals, and eligibility reasons.
- [x] Run the focused tests and confirm they pass.

### Task 3: Confirmed cleanup and abort transition

**Files:**
- Modify: `scripts/transaction_cache.py`
- Modify: `tests/test_transaction_cache.py`

- [x] Write failing tests for direct deletion, minimal `staging_state: CLEANED`, selected active transaction abort, orphan deletion, and stop-on-first-failure behavior.
- [x] Run the focused tests and confirm the cleanup API is absent.
- [x] Implement one-confirmation cleanup with per-item preflight, atomic YAML state update, direct deletion, and fail-stop reporting.
- [x] Run the focused tests and confirm they pass.

### Task 4: CLI and status surface

**Files:**
- Modify: `scripts/novel_harness.py`
- Modify: `tests/test_novel_harness_cli.py`

- [x] Write failing CLI tests for `cache-status` and interactive `cleanup-cache`.
- [x] Run the focused tests and confirm the subcommands are unknown.
- [x] Add JSON status output and a single exact confirmation prompt for selected cleanup items.
- [x] Run the focused tests and confirm they pass.

### Task 5: Manifest and specifications

**Files:**
- Create: `writespec/commands/cleanup-transactions.md`
- Modify: `novel-harness/context.manifest.yaml`
- Modify: `writespec/state-management.md`
- Modify: `writespec/commands/check-status.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `tests/test_validate_harness.py`

- [x] Write failing routing/integrity assertions for `清理事务缓存` and the cache policy references.
- [x] Run the focused tests and confirm routing or documentation checks fail.
- [x] Register the destructive-local-cache command and document the agreed retention, orphan, confirmation, and evidence boundaries.
- [x] Run routing and Harness validation tests and confirm they pass.

### Task 6: Completion verification

**Files:**
- Verify only; no planned production edits.

- [x] Run `python -m unittest tests.test_transaction_cache tests.test_transaction_executor tests.test_novel_harness_cli tests.test_harness_runtime tests.test_validate_harness -v`.
- [x] Run `python scripts/validate_harness.py`.
- [x] Run `python -m unittest discover -s tests -v`.
- [x] Inspect `git diff --check`, `git status --short`, and the final diff for scope and unrelated changes.
