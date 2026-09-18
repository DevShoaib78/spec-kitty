---
work_package_id: WP03
title: Config-surface dispositions — sharpen, promote, auth-row, fold
dependencies:
- WP01
requirement_refs:
- FR-002
- FR-003
- FR-004
- FR-006
- FR-007
- FR-009
- FR-010
planning_base_branch: chore/decide-out-of-matrix-test-dirs
merge_target_branch: chore/decide-out-of-matrix-test-dirs
branch_strategy: Planning artifacts for this mission were generated on chore/decide-out-of-matrix-test-dirs. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into chore/decide-out-of-matrix-test-dirs unless the human explicitly redirects the landing branch.
subtasks:
- T008
- T009
- T010
- T011
- T012
- T013
- T014
phase: Phase 3 - Execute
history:
- timestamp: '2026-09-18T16:48:24Z'
  agent: system
  action: Prompt generated for mission decide-out-of-matrix-test-dirs (#4374)
agent_profile: python-pedro
authoritative_surface: .github/ci-module-registry.yml
create_intent: []
execution_mode: code_change
model: claude-sonnet-5
owned_files:
- .github/ci-module-registry.yml
- .github/ci-shard-timings.json
- tests/release/ci_retirement_scrub.json
- .github/workflows/ci-nightly.yml
role: implementer
tags: []
tracker_refs: []
---

## ⚡ Do This First: Load Agent Profile

```
/ad-hoc-profile-load python-pedro
```

Then read `analysis/disposition-ledger.md` (WP01 — your work order), `contracts/disposition-decision-procedure.md`
and `contracts/acceptance-checks.md`. Execute the ledger exactly; do not re-decide dispositions here.

## Objective

Apply every config-surface decision from the WP01 ledger, keeping the registry guard green at every commit:
sharpen out-of-matrix reasons (in-matrix-target + marker-checked), promote the bounded capped set with measured
evidence, mint the security-critical `auth` row via scrub, reconcile integration with the special tier (nightly
split if too-slow), and fold #4426. **You own exactly four files** (registry, timings, scrub, ci-nightly) — do
not edit test contents or any other file.

## Subtasks

### T008 — Sharpen the pop-(a) mega-group
Split the single 60-dir `Secondary tests/specify_cli/** tree` block into decision-grouped entries per the ledger:
each entry's reason names the specific in-matrix mirror/gate that covers it (never another out-of-matrix entry —
no circular coverage), and for disposition-3 embeds the structured pointer `evidence: analysis/evidence/<f>.json`
verbatim from the WP01 ledger (WP04 resolves it; a reason with no resolvable pointer fails acceptance). Keep `tests/specify_cli/cli/commands` (#4715) and named-home entries byte-untouched. Run
the guard after.

### T009 — Promote the capped existing-row pop-(a) set
For each promotion in the ledger (existing owning row, PC1-clean): add the tree PARENT-ONLY to the row's
`test_dirs` (materialize the fallback mirror as an explicit entry if the row had none), and remove the tree AND
all its nested descendants from `out_of_matrix` in the SAME edit (recursion covers descendants). Never add a
parent and its child both to `test_dirs` (non-nesting guard). Respect the bounded cap — do not promote beyond
the ledger's named set; deferred-promotion trees get a recorded reason, not a promotion.

### T010 — Measure + size the promoted modules
For every expanded module M: `python scripts/ci/capture_shard_timings.py --module M --write`. Assert
`module_capture_provenance[M].unique_tests_measured == len(module_test_durations[M]) == module_test_count[M]`
(parity). Choose `shard_count` by greedy-LPT so within-module skew ≤20% and projected serial wall ≤30-min budget;
record the choice + run_id in a YAML comment. If a real test red surfaces during capture: classify (baseline-red
gotcha), file its own ticket (honest-red), and continue — do NOT fix in-tree here.

### T011 — Mint the `auth` row via scrub (security-critical)
Only if the ledger promotes auth per-PR: add a census-authorized `auth` group to
`tests/release/ci_retirement_scrub.json` (with `census_evidence`), then mirror its `roots`
(`src/specify_cli/<auth-source>/**`) and `cov_targets` VERBATIM into a new `auth` registry row; add
`tests/auth` (+ descendants handling) to its `test_dirs`; capture + size as T010. Confirm the scrub-bijection and
verbatim guards pass. If the ledger defers auth, record the deferred-promotion decision instead.

### T012 — Sharpen the pop-(b) mega-group + integration/nightly
Split the 68-dir block into decision-grouped entries: each names the ACTUAL marker lane its tests carry (verified
by WP01's grep) or a deferred-promotion decision. For `tests/integration/**` + `tests/next`: reconcile with
`special_tiers.integration_tests_next`. Its job is currently UNWIRED — produce ONE concrete outcome: an inline
registry annotation naming the gap AND a filed follow-up issue number recorded in the ledger (not a vague
"annotate/ticket"). If a promoted tree is too slow for per-PR, author the deliberate nightly marker split in
`.github/workflows/ci-nightly.yml`.

### T013 — Fold #4426; verify exclusions
Give `tests/performance` and `tests/specify_cli/live_work` (the #4426 dirs, already present in the inventory)
their decision reasons. Confirm via `git diff main` that the `tests/specify_cli/cli/commands` entry and the 5
named-home entries are byte-unchanged.

### T014 — Full acceptance run
Run every check in `contracts/acceptance-checks.md`: guard green; snapshot-elimination + names-a-surface script;
evidence parity/freshness script; injected-red proof THROUGH `python scripts/ci/gate_selection.py` with a SOURCE
injection (assert owning module selected, shard reds, THEN REVERT to zero net diff — do not leave the synthetic
break); paste the live transcript into the PR body. The DURABLE, re-runnable form of this proof is WP04's
permanent per-PR-selection guard (§5) — this transcript is corroboration. Also run marker-presence and
`make test-fast`. Record commands + pass counts for the PR.

## Branch Strategy

Planning/base + merge target: `chore/decide-out-of-matrix-test-dirs`. Worktree per lane from `lanes.json`.

## Definition of Done

- **One commit per subtask (T008–T013)**; `test_module_shard_registry.py` green at EACH commit (shown in
  `git log`) — the checkpoint discipline that makes this heavy WP safe.
- `tests/architectural/test_module_shard_registry.py` green after every subtask.
- Zero snapshot reasons among targeted dirs; every reason names an in-matrix surface / marker lane / deferral.
- Every `shard_count` change carries a fresh, parity-checked `run_id`.
- Injected-red proof passes through `gate_selection.py` (source injection).
- Exclusions byte-unchanged; #4426 dirs decided.
- `make test-fast` green (or only pre-existing baseline reds, classified honestly in the PR).
- Injected-red transcript pasted in the PR body; T014 synthetic break reverted (zero net source diff).
- PR body carries `Fixes #4426` and `Fixes #4374` and links #4708/#2979 (auto-close footgun guard).

## Risks & reviewer guidance

- **Heaviest WP** — coupled edits to four shared files. Commit per subtask so the guard-green invariant is
  checkable at each step.
- **Claimed-AND-recorded red**: a promotion that forgets to de-record a descendant. Reviewer greps the promoted
  tree's descendants against `out_of_matrix`.
- **False aggregate-fold**: reviewer rejects any promotion that adds a family to an aggregate `test_dirs` whose
  `roots` don't cover the family's source.
- **Scrub verbatim**: reviewer diffs the new `auth` row's roots/cov_targets against the scrub group byte-for-byte.
