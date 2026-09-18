# Research: out-of-matrix test-directory disposition

**Mission**: decide-out-of-matrix-test-dirs-01M2TKC7 · **Issue**: #4374 · **Date**: 2026-09-18

Phase 0 resolves how the CI module-shard machinery works so dispositions are evidence-driven, not guessed.

## Decision 1 — The claim/record guard is the acceptance oracle
- **Decision**: Treat `tests/architectural/test_module_shard_registry.py` as the binding gate. A `tests/`
  directory is *test-bearing* iff it directly holds a file matching pytest `python_files`
  (`test_*.py` / `*_test.py`). Every test-bearing dir must be claimed by exactly one row
  (`test_dirs` if present, else fallback `tests/<module>`, descendants count as claimed) **or** listed once
  under `out_of_matrix_test_dirs` with a real reason.
- **Rationale**: This is the #4369 invariant the mission must keep green while changing dispositions.
- **Companion guards** (also binding): out-of-matrix entries must be real, test-bearing dirs with reasons that
  are not placeholders (`n/a/none/tbd/todo/pending`); `test_dirs` must be real, pairwise non-nested dirs; the
  `ci` row is pinned. Re-run `tests/architectural/test_module_shard_registry.py` after every edit.

## Decision 2 — Measured runs come only from `capture_shard_timings.py`
- **Decision**: Produce a fresh `run_id` with `python scripts/ci/capture_shard_timings.py --module <m> --write`
  after adding a directory to module `<m>`'s effective test dirs. The tool runs pytest serially with the
  consumer's own selection and records one `call`-phase duration per collected test into
  `module_test_durations[<m>]`.
- **Rationale**: The registry's own rule — `shard_count` from measured per-test durations, never file counts.
- **Constraint**: Positional pairing in `module-tests.yml` requires
  `len(module_test_durations[m]) == collected count`; a mismatch silently degrades to uniform weights. Assert
  count parity after `--write`.

## Decision 3 — `shard_count` is an offline greedy-LPT choice; the guard enforces skew
- **Decision**: Choose `shard_count` by greedy longest-processing-time-first bin-packing of the measured
  durations, recorded in a per-row YAML comment; the guard's `test_inter_shard_skew_within_twenty_percent`
  re-derives skew and fails >20%. `reconcile_shards.py` only validates a positive int.
- **Rationale**: No script writes `shard_count`; sizing is a human decision bounded by the guard (NFR-005) and
  the 30-min design budget (CI hard ceiling `timeout-minutes: 40`, #4429).

## Decision 4 — Promotion wiring is three coupled edits
- **Decision**: Promoting `D` into module `M` means, atomically: (a) add `D` to `M.test_dirs`
  (materializing the fallback `tests/<M>` mirror as an explicit entry when the row had none), (b) remove `D`
  from `out_of_matrix_test_dirs`, (c) refresh `M`'s durations + `shard_count`. `ci-modules.yml` →
  `module-tests.yml` then executes `D` per PR, and `gate_selection.py::_modules_for_test_paths` selects `M`
  for tests-only diffs under `D`.
- **Rationale**: Missing (b) trips the "claimed AND recorded" red; missing (c) leaves shard sizing unevidenced.

## Decision 5 — Single-invariant trees use the #4715 lift, not a shard
- **Decision**: When a tree's only unique value is one repo-invariant/freshness check, lift that assertion into
  an always-on `tests/architectural/` test (`pytestmark = [pytest.mark.architectural]`) and keep the tree
  out-of-matrix with a sharpened reason naming the new gate — mirroring
  `test_completion_manifest_freshness.py` (#4479).
- **Rationale**: Cheapest correct fix; avoids sharding a behaviorally-redundant tree just to catch one drift.

## Decision 6 — Population-(b) marker homes are explicit
- **Decision**: For a population-(b) dir kept out-of-matrix, the sharpened reason names its actual marker home:
  `corpus` (`ci-router.yml` `tests-corpus` + `packs.yml`), `windows_ci` (`ci-windows.yml`, discovered via
  `git grep` of the marker), or nightly `performance`/`e2e`/`interpreter` (`ci-nightly.yml`). Promotion to
  per-PR requires a new module row with an identifiable source root + a measured run; too-slow → a deliberate
  nightly marker split (in scope per discovery).
- **Rationale**: A decision must name *which* existing lane already runs the tests, or mint a real per-PR home.

## Decision 7 — No dependency change → supply-chain directive not triggered
- **Decision**: The mission adds no package in any ecosystem; DIRECTIVE_051 / supply-chain-install-safety is
  **not applicable**. Recorded explicitly (silence is not compliance).
- **Adversarial evidence**: No security-impacting dependency decision exists to challenge; the adversarial pass
  for this mission targets the *disposition reasons* (are they decisions or disguised snapshots?), handled at
  the post-plan / post-tasks squad point-cuts.

## Inventory snapshot (measured 2026-09-18)
- Population (a) — secondary `tests/specify_cli/**`: **60 dirs**, 447 direct test files. Owning-module matches
  exist for many (merge, status, review, next, lanes, missions, upgrade, …); aggregates (`core_misc`) already
  claim a few siblings.
- Population (b) — no-per-PR-lane: **68 dirs**, 525 direct test files. Families: `integration` ×7 (136),
  `auth` ×5 (40, security), `tracker` (27), `contract` ×3 (23), `cross_cutting` ×6 (23), plus a long
  singleton tail.
- Excluded: `tests/specify_cli/cli/commands` (#4715) and the 5 named-home entries.
