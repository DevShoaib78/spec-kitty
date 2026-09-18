# Evidence README

**Mission**: decide-out-of-matrix-test-dirs-01M2TKC7 (#4374) · **WP**: WP01 (Disposition analysis & ledger)

This directory is the single evidence home for the mission (contracts/acceptance-checks.md v3 -- NOT
`decisions/`). Every file here is committed and cited from `../disposition-ledger.md`'s `evidence-pointer`
column. WP01 produced this evidence; WP02-WP04 consume it and add their own alongside it (never replacing it).

## Files in this directory

| File | Produced by | What it records |
|---|---|---|
| `capture-floor.txt` | WP01 (T005) | ISO-8601 UTC mission-start floor. Every `module_capture_provenance[M].captured_at` WP03 writes for a promoted module must be `>=` this value (acceptance-checks.md v3 §4, freshness gate). |
| `pc1_nested_family_analysis.txt` | WP01 (T001) | For all 128 targeted dirs: existence, direct-file test-bearing check, recursive descendant count, and the exact PC1 blocked-by list. Confirms exactly two dirs are PC1 promotion-blocked: `tests/specify_cli/cli` (contains the excluded `tests/specify_cli/cli/commands` + the execution_context-claimed `tests/specify_cli/cli/commands/agent`) and `tests/specify_cli` (contains multiple claimed descendants plus the same excluded dir). |
| `pop_a_import_census.txt` | WP01 (T002) | Top-5 `specify_cli.*`/`charter.*`/`kernel.*`/`glossary.*`/`mission_runtime.*`/`runtime.*` import targets per population-(a) tree (recursive grep + regex over `from`/`import` statements). This is the PC2 ownership-resolution evidence: an owning row is only claimed when the census target matches that row's `cov_targets`/`roots` (leaf-specific), never on a shared-root aggregate alone. |
| `file_counts.txt` | WP01 (T002/T006) | Recursive `test_*.py`/`*_test.py` file counts per targeted dir -- the coarse single-invariant-vs-broad-behavioral heuristic used to decide which small (1-3 file) trees were worth individually inspecting for lift-candidacy (T006). |
| `pop_b_marker_grep.txt` | WP01 (T004) | Per population-(b) tree: `grep -rl "pytest.mark.<marker>"` result for marker in `{corpus, windows_ci, performance, e2e, stress}`. This is the EG2 evidence (contracts/disposition-decision-procedure.md v2) backing every pop-(b) sharpen-reason that names a marker lane. A tree with `NONE` found is NEVER dispositioned as marker-scoped -- it is flagged in the ledger as a #2979-class gap and dispositioned deferred-promotion instead. |

## Why there is no coverage-diff JSON in this WP (honest account, not a gap papered over)

Disposition-3 rows in the ledger fall into two evidentially distinct classes:

1. **Marker-scoped sharpens** (population-b, 18 rows + 7 PC3 special-tier rows): the claim is "this tree's
   real home is a marker-selected nightly/corpus/windows lane or the already-claimed special tier," backed by
   EG2 (grep verification, `pop_b_marker_grep.txt`, or the registry's own `special_tiers` block). No
   coverage-diff is required or meaningful here -- the claim is about *reachability*, not *redundancy*.
2. **Mirror-equivalence sharpens** (EG1): the claim would be "this tree's behavior is a provable SUBSET of an
   ALREADY-IN-MATRIX tree/gate's coverage." This is the expensive, must-be-real evidence class the contract
   (EG1) requires a genuine `pytest --cov` diff for.

WP01 surveyed the 128 targeted dirs for genuine EG1 candidates. The field is thin, for a structural reason:
EG1 requires the covering target to be **already in-matrix** (a `modules[]` row or `tests/architectural/`),
and the overwhelming majority of population-(a)'s "secondary tree" candidates are themselves **rootless** (no
owning row at all -- see `pop_a_import_census.txt`), so there is no legitimate in-matrix mirror to diff
against for them; "covered by `make test-full`" is not an in-matrix claim and is exactly the kind of
disguised snapshot this mission exists to eliminate.

**The one candidate investigated**: `tests/specify_cli/cli/commands/charter` (+ its sibling `.../review`)
against the in-matrix `cli` module's primary tree (`tests/cli`) -- both are PC1-clean leaves under the `cli`
row's real `roots` (`src/specify_cli/cli/**`), and `tests/cli` being an already in-matrix mirror of the same
module made this a legitimate, checkable claim (not a disguised snapshot).

- A lightweight census (`grep -rl` for `commands.charter` / `commands.review` references inside `tests/cli/`)
  found **9 files / 60 test functions** in `tests/cli` (including `tests/cli/commands/test_charter_*.py`)
  that directly exercise `specify_cli.cli.commands.charter` -- a real, non-trivial, but UNPROVEN overlap.
  For `.../review`, the census found **zero** references anywhere in `tests/cli` -- no plausible mirror
  exists, so `.../review` was never a candidate.
- A real `pytest --cov=src/specify_cli/cli/commands/charter --cov=src/specify_cli/cli/commands/review
  --cov-branch --cov-report=json` capture over the out-of-matrix tree was STARTED (twice, once backgrounded,
  once foregrounded) to produce genuine EG1 evidence. Both attempts were still running after **8+ minutes**
  for a 29-test set with no completion in sight (`R`-state, real CPU consumption -- not hung/deadlocked, just
  very slow, plausibly the same heavy CliRunner/project-init-per-test overhead the registry's own
  `upgrade`/`agent` module comments document for their shard-count rationale). Per DIRECTIVE_028 (efficient
  local tooling) and the practical-evidence-strategy guidance ("cap mirror-equivalence claims to a handful;
  when in doubt use deferred-promotion instead"), the capture was killed rather than left to block this WP,
  and **no verdict is fabricated or asserted from partial output**.
- **Disposition recorded**: both `tests/specify_cli/cli/commands/charter` and `.../review` are
  **deferred-promotion** (owner = `cli`, the existing row) in the ledger -- the same safe default used for
  every other unresolved existing-row candidate. `.../charter` is explicitly flagged as the single best
  candidate for a follow-up standalone EG1 capture (run outside a WP01-sized budget, e.g. as part of WP03's
  own measured-capture work, which already runs `capture_shard_timings.py` against the `cli` module and could
  cheaply add a `--cov` companion run).

This is a deliberate, documented **non-decision-by-evidence-shortage**, not a silent gap: the ledger names
exactly what was tried, what it showed, and what remains open.

## Format of the grep/census evidence files

`pc1_nested_family_analysis.txt`, `pop_a_import_census.txt`, `file_counts.txt`, and `pop_b_marker_grep.txt`
are plain tab-separated / line-oriented text with a header comment block explaining the columns and the exact
method (command shape) used to produce them -- read the header of each file for the reproduction command.
