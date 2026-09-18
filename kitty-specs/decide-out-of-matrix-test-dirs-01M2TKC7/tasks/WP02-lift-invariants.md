---
work_package_id: WP02
title: Lift repo-invariants into the always-on battery
dependencies:
- WP01
requirement_refs:
- FR-005
planning_base_branch: chore/decide-out-of-matrix-test-dirs
merge_target_branch: chore/decide-out-of-matrix-test-dirs
branch_strategy: Planning artifacts for this mission were generated on chore/decide-out-of-matrix-test-dirs. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into chore/decide-out-of-matrix-test-dirs unless the human explicitly redirects the landing branch.
subtasks:
- T007
phase: Phase 2 - Lift
history:
- timestamp: '2026-09-18T16:48:24Z'
  agent: system
  action: Prompt generated for mission decide-out-of-matrix-test-dirs (#4374)
agent_profile: python-pedro
authoritative_surface: tests/architectural/
create_intent:
- tests/architectural/test_lifted_placeholder.py
execution_mode: code_change
model: claude-sonnet-5
owned_files:
- tests/architectural/test_lifted_*.py
role: implementer
tags: []
tracker_refs: []
---

## ⚡ Do This First: Load Agent Profile

```
/ad-hoc-profile-load python-pedro
```

Then read `spec.md`, `plan.md` (Post-plan squad amendments), `contracts/disposition-decision-procedure.md`, and
this mission's `analysis/disposition-ledger.md` (from WP01) — it names exactly which invariants to lift.

## Objective

For each disposition-2 tree in the WP01 ledger, add an always-on `tests/architectural/test_lifted_<x>.py` that
asserts the tree's single drift-prone invariant — the #4715 pattern
(`tests/architectural/test_completion_manifest_freshness.py`). This lets the behavioral tree stay out-of-matrix
with an honest reason (WP03 writes that reason).

## Context

The precedent to mirror: `tests/architectural/test_completion_manifest_freshness.py` lifts help-text freshness
(the one invariant unique to the out-of-matrix `tests/specify_cli/cli/commands` tree) into the always-on battery
with `pytestmark = [pytest.mark.architectural]`. Study it before writing.

## Subtasks

### T007 — Author the lifted-invariant tests
For each lift named in the ledger:
- Create `tests/architectural/test_lifted_<slug>.py` with `pytestmark = [pytest.mark.architectural]`.
- Assert exactly the invariant the ledger specifies (recompute the live value, compare to the committed/expected
  value), with a docstring citing the source tree and #4374/#4479.
- Keep each test narrow and deterministic; no network, no browser.
- Verify each passes on current green code AND fails when the invariant is violated (demonstrate the red locally,
  then revert the synthetic break).
- Name each file from the ledger's lift slug; create no `placeholder` file.

## Branch Strategy

Planning/base + merge target: `chore/decide-out-of-matrix-test-dirs`. Worktree per lane from `lanes.json`.

## Definition of Done

- One `tests/architectural/test_lifted_<x>.py` per ledger-named lift; all pass:
  `PYTHONPATH=src .venv/bin/python -m pytest tests/architectural/ -q -k lifted`.
- Each new test carries `pytest.mark.architectural` and a red-on-violation demonstration recorded in the PR notes.
- No behavioral test contents elsewhere are modified.
- If the ledger names ZERO lifts, this WP is a recorded no-op lane: create no file and note "no disposition-2 trees" — an empty lane here is expected, not an implementation miss.

## Risks & reviewer guidance

- Reviewer confirms each lifted assertion is the SAME invariant the out-of-matrix tree uniquely provided (not a
  weaker restatement) — otherwise the sharpened reason WP03 writes would over-claim coverage.
- Do not lift a behavioral suite wholesale; a lift is ONE invariant. If the tree has broad unique behavior, it is
  a promote/deferred-promotion in the ledger, not a lift.
