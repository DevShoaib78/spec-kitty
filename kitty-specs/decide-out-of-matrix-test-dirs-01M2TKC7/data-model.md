# Data Model: out-of-matrix disposition

Entities are configuration records, not runtime objects. "State" = the disposition lifecycle of each entry.

## Out-of-matrix entry
- **Fields**: `dirs: list[path]` (one or more test-bearing directories sharing a justification), `reason: str`.
- **Invariants**: every `dir` exists and is test-bearing; `reason` is a real decision (not a placeholder word);
  no `dir` is simultaneously claimed by a module row.
- **States**: `recorded-snapshot` (reason is a deferral) → `decided` (reason names a covering gate) **or**
  `promoted` (moved into a row's `test_dirs`, removed from this list).

## Module row
- **Fields**: `module: str`, `roots: list[glob]` (path routing), `cov_targets: list[str]`, `tier`,
  `shard_count: int`, optional `test_dirs: list[path]`.
- **Invariants**: effective test dirs (`test_dirs` or fallback `tests/<module>`) are real and pairwise
  non-nested; `shard_count ≥ 1`; LPT skew over the module's measured durations ≤ 20%.
- **Transitions**: `add-test-dir` (append a promoted dir), `resize-shards` (new `shard_count` from a fresh
  measured run), `mint-row` (new row for a population-(b) family with a source root).

## Measured timing record (`ci-shard-timings.json`)
- **Fields**: `run_id`, `command`, `module_test_durations{module→[float]}`, `module_test_count{module→int}`,
  `module_duration_seconds`, `excluded[]`, `schema_version`.
- **Invariants**: for any promoted/expanded module `m`,
  `len(module_test_durations[m]) == module_test_count[m] == collected count`; `run_id` is fresh (minted this
  mission) for every row whose `shard_count` changed.

## Disposition (the decision unit)
- **Enum**: `promote-per-pr` (1a), `promote-nightly` (1b), `lift-invariant` (2), `sharpen-reason` (3).
- **Required evidence**: 1a/1b → a fresh `run_id` + LPT/skew/timeout check; 2 → the new architectural test;
  3 → the name of the covering primary mirror or always-on gate.

## Registry guard (`test_module_shard_registry.py`)
- **Role**: the acceptance oracle. Green ⇔ every test-bearing dir claimed once or recorded once, skew ≤20%,
  entries real, test_dirs non-nested.

## Population
- **(a)** secondary `tests/specify_cli/**` trees (dual-tree class).
- **(b)** no-per-PR-lane dirs (marker-reachability class).

## Scrub group (`tests/release/ci_retirement_scrub.json`) — module-identity SSOT
- **Fields**: `group` (== registry module name), `roots`, `cov_targets`, `census_evidence`.
- **Invariant** (guard-enforced): registry module names == scrub group names (bijection); a promoted row's
  `roots`/`cov_targets` are byte-verbatim from its scrub group. Minting a registry row requires a scrub group
  first.

## Special tier (`special_tiers.integration_tests_next`)
- **Fields**: `job`, `roots` (`tests/integration/**`, `tests/next/**`), `parallel_mode`, duration targets.
- **State**: DECLARED but its `job` is currently **unwired** in `.github/workflows/` — a pre-existing honesty
  gap the integration disposition must reconcile with (wire-up or nightly), not bypass.
