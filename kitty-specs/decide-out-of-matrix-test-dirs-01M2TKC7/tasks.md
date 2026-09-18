# Tasks: Decide the fate of out-of-matrix test directories

**Mission**: decide-out-of-matrix-test-dirs-01M2TKC7 · **Issue**: #4374 · **Branch**: `chore/decide-out-of-matrix-test-dirs`
**Promotion policy**: BOUNDED (operator-confirmed) — decide all 128 entries; promote only existing-row pop-(a)
trees + at most the security-critical `auth` new-row via scrub; defer the rest as recorded decisions.

## Why the WP shape is serial-ish

Most of this mission edits a small set of **shared** config files (`.github/ci-module-registry.yml`,
`.github/ci-shard-timings.json`, `tests/release/ci_retirement_scrub.json`). Two WPs cannot both own the same
file, so the registry/timings/scrub edits are consolidated into one execution WP (WP03), fed by an analysis WP
(WP01), with two disjoint-file code WPs for lifted invariants (WP02) and permanent evidence guards (WP04).

## Subtask Index

| ID | Description | WP | Parallel |
|----|-------------|----|----------|
| T001 | Enumerate all 128 targeted dirs; classify recursive descendants (nested-family pre-check PC1) | WP01 |  |
| T002 | Resolve owning row per pop-(a) tree (ownership tie-break PC2); flag rootless + promotion-blocked | WP01 |  |
| T003 | Coverage-diff evidence for every disposition-3 candidate (demoted ⊆ in-matrix mirror) | WP01 | [P] |
| T004 | Marker-presence grep per pop-(b) tree; classify honest marker home vs #2979 gap | WP01 | [P] |
| T005 | Write the disposition ledger (dir → disposition → owner → rationale → evidence pointer) | WP01 |  |
| T006 | Identify the lift-invariant set; specify each invariant + its always-on test | WP01 |  |
| T007 | Author `tests/architectural/test_lifted_*.py` for each disposition-2 invariant | WP02 |  |
| T008 | Sharpen the pop-(a) 60-dir mega-group into decision-grouped reasons naming in-matrix targets | WP03 |  |
| T009 | Promote the capped existing-row pop-(a) set (parent-only, de-record descendants, non-nesting) | WP03 |  |
| T010 | Capture timings for every promoted/expanded module; assert provenance parity; size shards (LPT) | WP03 |  |
| T011 | Mint the `auth` row via scrub+registry verbatim edit; capture; size shards | WP03 |  |
| T012 | Sharpen the pop-(b) 68-dir mega-group; reconcile integration with special-tier; nightly split if too-slow | WP03 |  |
| T013 | Fold #4426 (decide `tests/performance`, `tests/specify_cli/live_work`); keep exclusions untouched | WP03 |  |
| T014 | Run the full acceptance-checks contract; guard green; injected-red proof via gate_selection.py | WP03 |  |
| T015 | Add permanent evidence guard: provenance parity + freshness (module_capture_provenance) | WP04 |  |
| T016 | Add permanent marker-presence honesty guard for out-of-matrix marker-named reasons | WP04 |  |
| T017 | Permanent guard: no out-of-matrix reason uses a deferral phrase / must name a covering surface | WP04 |  |
| T018 | Permanent guard: each disposition-3 reason resolves to a committed coverage-diff JSON (subset) | WP04 |  |
| T019 | Permanent guard: gate_selection selects the owning module for each expanded test_dir (per-PR proof) | WP04 |  |

## Work Packages

### WP01 — Disposition analysis & ledger (planning_artifact)
- **Goal**: Produce the authoritative per-dir disposition ledger with evidence, so WP02–WP04 execute a decided
  plan rather than re-deciding per tree. Security-first ordering (FR-008).
- **Priority**: P1 (MVP brain). **Independent test**: ledger covers all 128 dirs, each with a disposition +
  rationale + (where disposition-3) a coverage-diff pointer, and (where pop-(b) marker) a marker-grep result.
- **Subtasks**: T001, T002, T003, T004, T005, T006
- **Depends on**: none. **Est.**: ~420 lines.

### WP02 — Lift repo-invariants into the always-on battery (code_change)
- **Goal**: For each disposition-2 tree, add an always-on `tests/architectural/test_lifted_<x>.py` asserting its
  one drift-prone invariant (the #4715 pattern), so the tree can stay out-of-matrix with an honest reason.
- **Priority**: P2. **Independent test**: each new test is `pytest.mark.architectural`, passes on green code,
  and fails when the invariant is violated.
- **Subtasks**: T007
- **Depends on**: WP01 (ledger names the lift set). Runs PARALLEL to WP03. **Est.**: ~260 lines.

### WP03 — Config-surface dispositions: sharpen + promote + auth-row + fold (code_change)
- **Goal**: Execute every registry/timings/scrub decision: sharpen reasons (in-matrix-target + marker-checked),
  promote the capped set with measured evidence, mint the `auth` row via scrub, reconcile integration with the
  special tier (nightly split if too-slow), fold #4426. Guard stays green throughout.
- **Priority**: P1 (the execution). **Independent test**: `test_module_shard_registry.py` green; zero snapshot
  reasons among targeted dirs; every shard_count change has fresh parity-checked evidence; injected-red proof
  passes through `gate_selection.py`.
- **Subtasks**: T008, T009, T010, T011, T012, T013, T014
- **Depends on**: WP01 only (parallel to WP02). One commit per subtask; guard green at each. **Est.**: ~560 lines (heaviest; the coupled-config core).

### WP04 — Permanent evidence & marker-honesty guards + acceptance dossier (code_change)
- **Goal**: Lift the mission's load-bearing acceptance checks into always-on guards so future drift is caught:
  promotion evidence parity/freshness and marker-presence honesty. Record the mission-acceptance summary.
- **Priority**: P2. **Independent test**: new guards pass post-WP03, and fail on a synthetic parity/marker
  violation.
- **Subtasks**: T015, T016, T017, T018, T019
- **Depends on**: WP02 AND WP03. **Est.**: ~360 lines.

## Dependencies

```
WP01 ─┬─► WP02 ─┐
      └─► WP03 ─┴─► WP04
```

WP02 (lifts, owns `tests/architectural/test_lifted_*.py`) runs in PARALLEL with WP03 (owns the config files) —
disjoint ownership, and the lifted-test NAMES are fixed in the WP01 ledger, so WP03's reasons reference decided
strings, not WP02's code. WP04 asserts the post-WP03 + post-WP02 state, so it depends on both. WP01→{WP02∥WP03}→WP04.

## MVP

WP01 (the ledger) + WP03 (execution) are the mission MVP — they alone satisfy #4374's acceptance (every entry a
decision, guard green). WP02/WP04 harden it (lifts + permanent guards).
