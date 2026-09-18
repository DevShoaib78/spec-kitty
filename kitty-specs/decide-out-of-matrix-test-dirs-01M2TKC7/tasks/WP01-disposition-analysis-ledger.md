---
work_package_id: WP01
title: Disposition analysis & ledger
dependencies: []
requirement_refs:
- FR-001
- FR-002
- FR-003
- FR-008
- FR-011
planning_base_branch: chore/decide-out-of-matrix-test-dirs
merge_target_branch: chore/decide-out-of-matrix-test-dirs
branch_strategy: Planning artifacts for this mission were generated on chore/decide-out-of-matrix-test-dirs. During /spec-kitty.implement this WP may branch from a dependency-specific base, but completed changes must merge back into chore/decide-out-of-matrix-test-dirs unless the human explicitly redirects the landing branch.
subtasks:
- T001
- T002
- T003
- T004
- T005
- T006
phase: Phase 1 - Analysis
history:
- timestamp: '2026-09-18T16:48:24Z'
  agent: system
  action: Prompt generated for mission decide-out-of-matrix-test-dirs (#4374)
agent_profile: architect-alphonso
authoritative_surface: kitty-specs/decide-out-of-matrix-test-dirs-01M2TKC7/analysis/
create_intent:
- kitty-specs/decide-out-of-matrix-test-dirs-01M2TKC7/analysis/disposition-ledger.md
- kitty-specs/decide-out-of-matrix-test-dirs-01M2TKC7/analysis/evidence/README.md
- kitty-specs/decide-out-of-matrix-test-dirs-01M2TKC7/analysis/evidence/capture-floor.txt
execution_mode: planning_artifact
model: claude-sonnet-5
owned_files:
- kitty-specs/decide-out-of-matrix-test-dirs-01M2TKC7/analysis/**
role: analyst
tags: []
tracker_refs: []
---

## ⚡ Do This First: Load Agent Profile

Before reading anything else, load your assigned profile so your identity, boundaries, and governance scope are active:

```
/ad-hoc-profile-load architect-alphonso
```

(Or `spec-kitty charter context --action tasks --json` + `spec-kitty agent profile show architect-alphonso --json`.) Then read this mission's `spec.md`, `plan.md` (incl. the "Post-plan squad amendments" section), `research.md`, and both `contracts/*.md` — they are binding.

## Objective

Produce the **authoritative disposition ledger**: for every one of the 128 targeted directories, decide exactly
one disposition (promote-per-pr / promote-nightly / lift-invariant / sharpen-reason / deferred-promotion) with a
rationale and the evidence that makes it defensible. WP02–WP04 execute this ledger; they do not re-decide.

**Do not edit any config or source file in this WP.** Output is confined to
`kitty-specs/decide-out-of-matrix-test-dirs-01M2TKC7/analysis/`.

## Context (binding constraints from the squad)

- The registry guard `tests/architectural/test_module_shard_registry.py` is the acceptance oracle (currently
  green on `main`). Never propose a disposition that would red it.
- **Bounded promotion policy** (operator-confirmed): promote only pop-(a) trees with an existing owning row +
  clean nested-family check, plus at most the security-critical `auth` new-row via scrub. Everything else →
  verified sharpen / lift / recorded deferred-promotion. NO aggregate-folds.
- Minting a new module row is a census-gated `tests/release/ci_retirement_scrub.json` + registry verbatim edit.
- `special_tiers.integration_tests_next` already claims `tests/integration/**` + `tests/next/**` (job unwired).

## Subtasks

### T001 — Enumerate + nested-family classification (PC1)
Parse `.github/ci-module-registry.yml` `out_of_matrix_test_dirs`; extract the two target groups (60 pop-(a) +
68 pop-(b)); confirm exclusions (`tests/specify_cli/cli/commands` + 5 named-home). For each dir, compute its
recursive descendant set from disk and flag: descendants that are excluded entries or claimed by another row
(→ promotion-blocked, e.g. `tests/specify_cli/cli`, `tests/specify_cli/cli/commands/agent` under it). Record
which dirs are promotion-eligible vs promotion-blocked.

### T002 — Owning-row resolution + tie-break (PC2)
For each pop-(a) tree, map `tests/specify_cli/<x>` → the module row whose `cov_targets` most specifically names
`specify_cli.<x>` (leaf-specific, never an aggregate that merely carries the broad root). Flag rootless trees
(no owning row → would need a scrub-minted row) and shared-root ambiguities (e.g. `status` root in 4 rows) with
the chosen owner + rationale. Do the same family-level analysis for pop-(b) (auth, tracker, dossier, git_ops,
cross_cutting, integration, contract, singletons).

### T003 — Coverage-diff evidence for disposition-3 candidates [P]
For each tree you propose to KEEP out-of-matrix claiming an in-matrix mirror covers it: run
`pytest --cov=<module-src> --cov-branch --cov-report=json` over the tree and over the named mirror; assert
covered(line/branch) of the tree ⊆ mirror. Resolve DIRECTION (do not assume `tests/<leaf>` is primary — the
path-faithful mirror of `src/specify_cli/<x>` is `tests/specify_cli/<x>`). Store each JSON under
`analysis/evidence/` and cite it in the ledger. Where the tree asserts a distinct *property* over shared lines,
mark it promote/lift, NOT sharpen.

### T004 — Marker-presence grep for pop-(b) [P]
For each pop-(b) tree, `grep` for the pytest marker of any lane you'd name as its home (corpus/windows_ci/
performance/e2e/interpreter). If absent, the "runs via marker lane" reason is a disguised snapshot (#2979
class): mark the tree as needing a marker (honest-red/ticket) or a different disposition. Record the grep result
per tree.

### T005 — Write the disposition ledger + capture floor
Write `analysis/disposition-ledger.md`: a row per targeted dir with columns `dir | population | disposition |
owner/mirror | rationale | evidence-pointer | phase`. Order security-first (auth, dashboard-adjacent, merge,
status). Every disposition-3 row's `evidence-pointer` is a real committed path under `analysis/evidence/` that
WP03 embeds verbatim as `evidence: analysis/evidence/<file>.json` in the registry reason. Also write
`analysis/evidence/capture-floor.txt` — an ISO-8601 UTC timestamp (mission-start floor, e.g. the planning commit
time) that WP03's captures must post-date and WP04's freshness guard reads. This is the single source WP02–WP04 consume.

### T006 — Identify the lift-invariant set
For trees whose unique value is a single drift-prone invariant, specify: the invariant, the always-on test name
(`tests/architectural/test_lifted_<x>.py`), and the assertion shape. This feeds WP02.

## Branch Strategy

Planning/base branch: `chore/decide-out-of-matrix-test-dirs`. Final merge target: `chore/decide-out-of-matrix-test-dirs`.
Execution worktrees are allocated per computed lane from `lanes.json` during `/spec-kitty.implement`.

## Definition of Done

- `analysis/disposition-ledger.md` covers all 128 dirs; every row has a disposition + rationale.
- Every disposition-3 row cites a committed coverage-diff JSON under `analysis/evidence/`, and its pointer is the
  exact string WP03 will embed in the registry reason.
- `analysis/evidence/capture-floor.txt` exists with an ISO-8601 UTC mission-start floor.
- Every pop-(b) row that names a marker lane cites a passing marker grep (or is re-dispositioned).
- Promotion-blocked and rootless dirs are explicitly flagged; the capped promotion set is named.
- No config/source file changed by this WP.

## Risks & reviewer guidance

- **Direction inversion** (Renata F1): reviewer confirms disposition-3 kept the SUPERSET-coverage tree in-matrix.
- **Effort**: coverage captures cost time; run them only for genuine disposition-3 candidates, batch per module.
- Reviewer checks the ledger's promotion set respects the bounded cap (existing-row + auth only).
