---
work_package_id: WP04
title: Permanent evidence & marker-honesty guards
dependencies:
- WP02
- WP03
requirement_refs:
- FR-004
- FR-006
- FR-011
planning_base_branch: chore/decide-out-of-matrix-test-dirs
merge_target_branch: chore/decide-out-of-matrix-test-dirs
branch_strategy: Planning artifacts for this mission were generated on chore/decide-out-of-matrix-test-dirs. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into chore/decide-out-of-matrix-test-dirs unless the human explicitly redirects the landing branch.
subtasks:
- T015
- T016
- T017
- T018
- T019
phase: Phase 4 - Guard
history:
- timestamp: '2026-09-18T16:48:24Z'
  agent: system
  action: Prompt generated for mission decide-out-of-matrix-test-dirs (#4374)
agent_profile: python-pedro
authoritative_surface: tests/architectural/test_out_of_matrix_evidence.py
create_intent:
- tests/architectural/test_out_of_matrix_evidence.py
execution_mode: code_change
model: claude-sonnet-5
owned_files:
- tests/architectural/test_out_of_matrix_evidence.py
role: implementer
tags: []
tracker_refs: []
---

## ⚡ Do This First: Load Agent Profile

```
/ad-hoc-profile-load python-pedro
```

Then read `contracts/acceptance-checks.md` — this WP lifts its load-bearing checks into an always-on guard so the
mission's outcome cannot silently rot on `main`.

## Objective

Add ONE new always-on architectural test file, `tests/architectural/test_out_of_matrix_evidence.py`
(`pytestmark = [pytest.mark.architectural]`), encoding the mission's load-bearing invariants (evidence parity/freshness, marker honesty, no-deferral reasons, coverage-pointer resolution, per-PR selection). It may import helpers from
`tests/architectural/test_module_shard_registry.py` but must NOT edit that file.

## Subtasks

### T015 — Evidence parity + freshness guard
Assert: for every module row whose `shard_count` differs from `git show main:.github/ci-module-registry.yml`,
`module_capture_provenance[m]` exists and `unique_tests_measured == len(module_test_durations[m]) ==
module_test_count[m]` (positional-pairing parity, closing the uniform-weight degradation). Read the floor from
`kitty-specs/decide-out-of-matrix-test-dirs-01M2TKC7/analysis/evidence/capture-floor.txt` and assert
`captured_at >= floor` UNCONDITIONALLY for every changed module (freshness is computed, not optional). Keep the
check inert (auto-pass) only when there are zero shard_count changes vs main, so it never reds unrelated PRs.

### T016 — Marker-presence honesty guard
Assert: any `out_of_matrix_test_dirs` reason that names a marker lane (corpus/windows_ci/performance/e2e/
interpreter) is backed by at least one test in that tree actually carrying the marker (`git grep`/AST). A reason
naming a lane the tree cannot reach fails — the #2979 disguised-snapshot class.

### T017 — No-deferral-reason guard
Assert: no `out_of_matrix_test_dirs` reason contains a deferral phrase ("recorded deliberately", "measured-
durations decision, never a silent default", or the placeholder words already banned) AND every reason references
a concrete covering surface (matches `tests/`, `module`, a marker lane, `architectural`, or an issue `#NNNN`).
This makes "reasons are decisions, not snapshots" a permanent invariant (the #4369/#4374 philosophy).

### T018 — Coverage-equivalence pointer guard (Renata F1, permanent)
Assert: every `out_of_matrix_test_dirs` disposition-3 reason that claims an in-matrix mirror carries a structured
pointer `evidence: analysis/evidence/<f>.json`; the file exists and is committed; and the stored JSON records
`covered(line/branch)` of the demoted tree ⊆ the retained in-matrix tree. Resolve the pointer and re-assert the
stored subset (READ the JSON — do not re-run coverage). A reason with no resolvable pointer fails.

### T019 — Per-PR selection guard (Renata F3 / Paula F3, permanent)
Assert: for each module row whose `test_dirs` was expanded this mission (vs `git show main:`), calling
`scripts/ci/gate_selection.select_modules` with (a) a synthetic path `<added_test_dir>/synthetic_test.py` and
(b) a synthetic path under the module's `roots` both include the owning module. This proves per-PR de-silencing
durably and re-runnably (zero net diff), replacing the transient injected-red.

## Branch Strategy

Planning/base + merge target: `chore/decide-out-of-matrix-test-dirs`. Worktree per lane from `lanes.json`.

## Definition of Done

- `tests/architectural/test_out_of_matrix_evidence.py` exists with all guards (T015–T019), all green post-WP03:
  `PYTHONPATH=src .venv/bin/python -m pytest tests/architectural/test_out_of_matrix_evidence.py -q`.
- Each guard demonstrably reds on a synthetic violation (recorded in PR notes), then reverted.
- `tests/architectural/test_module_shard_registry.py` is unchanged.
- The new file passes `ruff check` and `ruff format --check`.

## Risks & reviewer guidance

- **Over-strict guard**: T015 must be inert when no shard_count changed, and T017's surface-reference regex must
  not reject the legitimate named-home reasons. Reviewer runs the guard on a clean `main` checkout to confirm it
  would pass there too (no false global red).
- Reviewer confirms the file imports, not copies, the existing guard's constants where practical (DRY, S1192).
