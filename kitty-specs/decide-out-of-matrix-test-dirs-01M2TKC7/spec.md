# Mission Specification: Decide the fate of out-of-matrix test directories

**Mission Branch**: `chore/decide-out-of-matrix-test-dirs`  
**Created**: 2026-09-18  
**Status**: Draft  
**Input**: GitHub issue spec-kitty/spec-kitty#4374 (P3 `type:chore`, milestone 4.0.0) — "decide the fate of the test directories recorded out-of-matrix in #4369."

## Overview

Issue #4369 added the `out_of_matrix_test_dirs` inventory to `.github/ci-module-registry.yml` and a guard
(`tests/architectural/test_module_shard_registry.py`) requiring every test-bearing `tests/` directory to be
either claimed by exactly one module row **or** recorded out-of-matrix with a reason. That made the un-lane'd
directories *visible* but deliberately deferred *deciding what to do about them*. Today those recorded entries
carry **snapshot reasons** ("recorded deliberately… promoting is a measured-durations decision") rather than
**decisions**. A red in an un-lane'd tree therefore persists silently on `main` and surfaces only under the
local/external `make test-full` — the exact defect class #4369 fixed for `tests/test_dashboard/`.

This mission converts every targeted out-of-matrix entry into a deliberate, evidence-backed decision.

### Disposition framework (each targeted entry gets exactly one)

1. **Promote** the tree into its owning module row's `test_dirs` — the `core_misc`/`execution_context`
   precedent. Allowed **only** with a fresh measured run recorded in `.github/ci-shard-timings.json`;
   `shard_count` re-sized by greedy LPT bin-packing of the **measured per-test durations** (never guessed,
   never from file counts), respecting the 30-minute shard timeout and the ≤20% inter-shard skew (registry
   NFR-005). A tree too slow for the per-PR matrix is promoted instead to a **nightly lane with a deliberate
   marker split** (authored in this mission).
2. **Lift a repo-invariant** into the always-on `tests/architectural` battery — the #4715 pattern
   (`tests/specify_cli/cli/commands` → `test_completion_manifest_freshness.py`). Used when the tree's unique
   value is an invariant/freshness check rather than behavioral module coverage; no shard re-measurement
   needed. The tree's registry reason is then sharpened to name that gate.
3. **Keep out-of-matrix with a sharpened reason** that names *why* the primary mirror (`tests/<module>`) or
   another always-on gate already covers the tree's behavior. The reason must be a decision, not a snapshot.

### Scope populations (both in scope — confirmed in discovery)

- **Population (a)** — the ~59 secondary `tests/specify_cli/**` trees (second test trees for modules whose
  primary `tests/<module>` mirror is already in the matrix), currently sharing one snapshot reason.
- **Population (b)** — the ~68 directories with no per-PR path-based lane at all (`tests/auth/**`,
  `tests/dossier`, `tests/git_ops`, `tests/cross_cutting/**`, `tests/integration/**`, `tests/mission`,
  `tests/tracker`, and siblings), reached by CI only through marker-selected lanes (corpus / windows_ci /
  nightly) when individually marked.

### Explicitly excluded / untouched

- `tests/specify_cli/cli/commands` — already resolved in #4715 (#4479); do **not** reopen.
- Entries that already name a per-PR or nightly home: `tests` (root modules), `tests/docs`, `tests/e2e`,
  `tests/architectural`, `tests/ui`. These are already decisions.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Resolve the secondary `specify_cli` trees, security-first (Priority: P1)

As a CI-registry owner, I decide the disposition of each of the ~59 secondary `tests/specify_cli/**` trees —
starting with the security- and regression-relevant ones (auth-adjacent, dashboard, merge, status) — so that
each carries a decision instead of a shared snapshot, and behavioral coverage that was silently unrun on
`main` is either lane-selected or provably redundant.

**Why this priority**: This is the population the #4374 acceptance text is written against, and it contains
the highest-risk silent gaps (a broken `tests/specify_cli/merge` or `tests/specify_cli/status` tree would go
unseen on `main`). Resolving it alone is a viable, shippable MVP.

**Independent Test**: Reviewable by inspecting `out_of_matrix_test_dirs`: every population-(a) directory is
either moved into a module row's `test_dirs` (with a matching `ci-shard-timings.json` entry) or carries a
sharpened, per-tree/per-group decision reason. The registry guard passes.

**Acceptance Scenarios**:

1. **Given** a security-relevant secondary tree with behavioral coverage (e.g. `tests/specify_cli/merge`),
   **When** its disposition is decided as *promote*, **Then** the directory appears in the `merge` module
   row's `test_dirs`, its `shard_count` is re-derived from a measured run present in `ci-shard-timings.json`,
   and the tree no longer appears under `out_of_matrix_test_dirs`.
2. **Given** a secondary tree whose behavior is genuinely a subset of its primary mirror, **When** its
   disposition is decided as *keep-out-of-matrix*, **Then** its registry reason names the specific primary
   mirror (or always-on gate) that covers it, worded as a decision rather than "recorded deliberately".
3. **Given** all population-(a) trees have a disposition, **When** the registry guard runs, **Then** it
   passes with every directory claimed or recorded exactly once.

---

### User Story 2 - Resolve the no-per-PR-lane directories (Priority: P2)

As a CI-registry owner, I decide the disposition of each of the ~68 population-(b) directories, so that
marker-only-reachable trees are either given a real per-PR/nightly lane or carry a decision reason explaining
why marker/nightly reachability is the deliberate, sufficient home.

**Why this priority**: These are a distinct problem class (marker-reachability, not dual-tree) and lower
individual risk than the security-relevant secondary trees, but leaving them as snapshots keeps the inventory
half-decided. In scope per discovery.

**Independent Test**: Every population-(b) directory in `out_of_matrix_test_dirs` carries a decision reason
or has been promoted into a lane; no targeted entry retains the "recorded deliberately (#4369)" snapshot
wording. Guard passes.

**Acceptance Scenarios**:

1. **Given** a population-(b) tree that warrants per-PR coverage (e.g. `tests/auth/**`), **When** its
   disposition is decided as *promote*, **Then** it is claimed by a module row (or a dedicated row) with
   measured-duration evidence and a lane selects it per PR.
2. **Given** a population-(b) tree whose value is deliberately nightly/marker-scoped, **When** its
   disposition is decided as *keep-out-of-matrix*, **Then** its reason names the specific marker lane
   (corpus / windows_ci / nightly e2e/performance/interpreter) that is its intended home and why per-PR
   selection is not warranted.

---

### User Story 3 - Measured-evidence and guard integrity discipline (Priority: P1)

As a CI maintainer, I require that every promotion is backed by a fresh measured run and that the registry
guard stays green throughout, so the registry remains self-consistent, reproducible, and never regresses to
an unclaimed-or-double-claimed state.

**Why this priority**: This invariant is what separates a real decision from a guessed one; it is the
binding rule in both the issue and the registry description. It gates every promotion in US1 and US2.

**Independent Test**: For each shard_count change, a corresponding measured entry exists in
`ci-shard-timings.json`; projected shard durations respect the 30-min timeout and ≤20% skew; the guard exits
0 with zero orphaned or double-claimed directories.

**Acceptance Scenarios**:

1. **Given** a proposed promotion, **When** no fresh measured run for that tree exists in
   `ci-shard-timings.json`, **Then** the promotion is not landed (the tree stays out-of-matrix or a
   measurement is taken first).
2. **Given** a promoted module row, **When** its shards are projected from measured durations, **Then** the
   within-module inter-shard skew is ≤20% and no shard's projected wall-time exceeds 30 minutes.
3. **Given** a newly lane-selected tree, **When** a failing assertion is introduced into it, **Then** the
   corresponding per-PR (or nightly) lane selects and reds on it — proving the coverage is no longer silent.

### Edge Cases

- **A tree too slow for per-PR**: measured duration cannot fit the per-PR budget → promote to a nightly lane
  with a deliberate marker split (authored here), not a silent drop.
- **A tree whose only unique value is an invariant/freshness check** (not behavioral coverage) → lift the
  invariant into `tests/architectural` (disposition 2) rather than sharding the whole tree.
- **A tree that collects zero tests** (empty/placeholder) → recorded with a reason stating it is not
  test-bearing; must not be counted as covered behavior.
- **A real red discovered while measuring** a tree → filed as its own ticket (honest-red) and does not block
  the disposition decision (non-goal: this mission does not fix in-tree reds).
- **A directory already claimed by a per-PR/nightly home** (the exclusions) → left untouched; re-deciding it
  would double-run it.
- **A group of trees that share one honest justification** → may share a single decision reason as a coherent
  group, provided the reason is a decision that applies to each listed directory.

## Requirements *(mandatory)*

### Functional Requirements

| ID | Title | User Story | Priority | Status |
|----|-------|------------|----------|--------|
| FR-001 | Single disposition per entry | As a CI-registry owner, I assign every targeted out-of-matrix entry exactly one disposition — promote, invariant-lift, or sharpened-reason — so no entry stays a snapshot. | High | Open |
| FR-002 | Resolve population (a) | As a CI-registry owner, I resolve all ~59 secondary `tests/specify_cli/**` trees so each is a decision. | High | Open |
| FR-003 | Resolve population (b) | As a CI-registry owner, I resolve all ~68 no-per-PR-lane directories so each is a decision. | Medium | Open |
| FR-004 | Evidence-backed promotion | As a CI maintainer, promoting a tree adds it to the owning module row's `test_dirs` and re-sizes `shard_count` from measured per-test durations recorded in `ci-shard-timings.json`. | High | Open |
| FR-005 | Invariant lift | As a CI maintainer, when a tree's unique value is a repo-invariant/freshness check, I lift that invariant into the always-on `tests/architectural` battery (the #4715 pattern) and sharpen the tree's reason. | Medium | Open |
| FR-006 | Sharpened reason | As a CI-registry owner, a kept-out-of-matrix tree's reason names the specific primary mirror or always-on gate that already covers its behavior, worded as a decision. | High | Open |
| FR-007 | Too-slow → nightly marker split | As a CI maintainer, a promoted tree that cannot meet the per-PR budget is routed to a nightly lane with a deliberate marker split authored in this mission. | Medium | Open |
| FR-008 | Security-first sequencing | As a CI-registry owner, I resolve security/regression-relevant trees first (auth, dashboard-adjacent, merge, status). | Medium | Open |
| FR-009 | Honest-red routing | As a maintainer, a genuine failure discovered while measuring a tree is filed as its own ticket and does not block the disposition decision. | Medium | Open |
| FR-010 | Preserve exclusions | As a CI-registry owner, I do not modify `tests/specify_cli/cli/commands` (#4715) or entries already naming a per-PR/nightly home (`tests`, `tests/docs`, `tests/e2e`, `tests/architectural`, `tests/ui`). | High | Open |
| FR-011 | Traceable decisions | As a reviewer, each disposition records its rationale and (for promotions) its measured-evidence pointer, traceable to #4374. | Medium | Open |

### Non-Functional Requirements

| ID | Title | Requirement | Category | Priority | Status |
|----|-------|-------------|----------|----------|--------|
| NFR-001 | Inter-shard skew | Every promoted module row's `shard_count` is derived by greedy LPT bin-packing of measured per-test durations; within-module inter-shard skew ≤ 20% (registry NFR-005). | Correctness | High | Open |
| NFR-002 | Shard timeout headroom | No shard's projected wall-time exceeds the 30-minute CI shard timeout for any promoted row. | Reliability | High | Open |
| NFR-003 | Fresh measured evidence | 100% of `shard_count` changes reference a measured run recorded in `.github/ci-shard-timings.json` produced within this mission; 0 promotions reuse stale or absent numbers. | Correctness | High | Open |
| NFR-004 | Guard green, zero orphans | `tests/architectural/test_module_shard_registry.py` passes with 0 unclaimed and 0 double-claimed test-bearing `tests/` directories. | Reliability | High | Open |
| NFR-005 | Snapshot elimination | 0 of the targeted entries (populations a + b) retain a snapshot reason at mission end; 100% are decisions or promotions. | Completeness | High | Open |

### Constraints

| ID | Title | Constraint | Category | Priority | Status |
|----|-------|------------|----------|----------|--------|
| C-001 | Registry is SSOT | `.github/ci-module-registry.yml` `out_of_matrix_test_dirs` is the single source of truth; each test-bearing dir is claimed by one row OR recorded out-of-matrix exactly once. | Technical | High | Open |
| C-002 | No guessed shards | `shard_count` is never guessed and never derived from file counts — measured durations only. | Technical | High | Open |
| C-003 | No test-content changes | Do not change test contents or fix reds inside these trees; route any real red to its own ticket (honest-red). | Technical | High | Open |
| C-004 | No version assignment | Do not assign a release/version number; the PO owns versioning. | Business | Medium | Open |
| C-005 | Canonical sources only | Use the registry's own rule and the `core_misc`/`execution_context` precedents; never improvise a substitute lane or hand-rolled shard sizing. | Technical | High | Open |
| C-006 | PR-bound, operator merges | Changes land via the mission's topic branch and a PR targeting `main`; the operator performs the merge. | Process | Medium | Open |

### Key Entities

- **Out-of-matrix entry**: a `{dirs, reason}` record under `out_of_matrix_test_dirs`; the unit of decision.
- **Module row**: a `{module, roots, cov_targets, tier, shard_count, [test_dirs]}` record; a promotion adds
  a directory to its `test_dirs` and may change `shard_count`.
- **Measured timing record**: per-test duration data in `.github/ci-shard-timings.json`; the only admissible
  evidence for a `shard_count`.
- **Disposition**: one of {promote-to-module-row, promote-to-nightly-marker-lane, lift-invariant,
  sharpened-reason} assigned to each targeted entry.
- **Registry guard**: `tests/architectural/test_module_shard_registry.py`; enforces claim/record-exactly-once.
- **Population**: (a) secondary `tests/specify_cli/**` trees; (b) no-per-PR-lane directories.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 0 of the targeted out-of-matrix entries (populations a + b, excluding the named exclusions)
  retain a snapshot reason — every one is a promotion or a decision reason.
- **SC-002**: 100% of promoted trees have a matching measured-duration entry in
  `.github/ci-shard-timings.json` created during this mission; 0 promotions land without one.
- **SC-003**: The registry guard passes with 0 unclaimed and 0 double-claimed test-bearing directories.
- **SC-004**: Every promoted module row's projected shards respect the 30-minute timeout and hold ≤20%
  inter-shard skew.
- **SC-005**: For each newly lane-selected tree, injecting a failing assertion causes the corresponding
  per-PR or nightly lane to red — demonstrating the coverage is no longer silent on `main`.
- **SC-006**: The two named exclusions (`tests/specify_cli/cli/commands` and the already-decided per-PR/
  nightly homes) are unchanged by the mission diff. Note `tests/specify_cli/cli/commands/charter` and
  `.../review` are subdirectories of the excluded dir but are themselves IN scope.
- **SC-007**: Every disposition-3 reason names an **in-matrix** covering target (row or `tests/architectural`),
  and — for pop-(b) — the tree actually carries the marker of any lane its reason names (no #2979-class
  disguised snapshot).
- **SC-008**: #4426 is resolved (its two dirs decided) and closed on merge; #4708/#2979 linked as related.

## Assumptions

- The registry's greedy-LPT shard-sizing method and the `ci-shard-timings.json` schema are the canonical
  sizing mechanism and are reused as-is (no new sizing algorithm is introduced).
- "Security/regression-relevant first" orders the work but does not change any disposition's admissibility.
- A coherent group of directories may share one decision reason when that reason honestly applies to each
  listed directory (matching the existing registry grouping style).
- Measured runs are produced in the mission's own environment; a real red encountered during measurement is
  categorized per the project's baseline-red gotcha (pre-existing vs. introduced) before any ticket is filed.

- Promotion removes silent-on-`main` coverage **only for diffs that select the owning module** (the tree's own
  files, or the module's `roots` source); it does not make the tree run on unrelated PRs (CI is diff-scoped by
  design). This is the intended, bounded guarantee — not universal execution.
- Minting a new module row is a census-gated change to `tests/release/ci_retirement_scrub.json` mirrored
  verbatim into the registry; it is heavier than adding to an existing row and is capped per PR.
- "Fold into an existing aggregate row" is NOT a valid promotion: CI selection is `roots`-based, so it would not
  de-silence source-triggered diffs.

