# Contract: per-tree disposition decision procedure (v2, post-squad)

**Binding.** For every targeted directory `D` (the 60 pop-(a) + 68 pop-(b) entries; excluding the exact dir
`tests/specify_cli/cli/commands` and the 5 named-home entries — note `tests/specify_cli/cli/commands/charter`
and `.../review` ARE in scope), choose exactly one disposition, following this procedure. **Default bias is a
hard sizing guardrail, not a lean:** promotions are capped (see §Cap); most entries resolve to a *verified*
sharpen-reason (3) or lift-invariant (2), neither of which needs a measured run, a scrub edit, or a `roots` edit.

## Pre-checks (run BEFORE choosing a disposition)

### PC1 — Nested-family eligibility (Paula F2)
Compute `D`'s recursive descendant set from disk. `D` is **ineligible for promotion** (force disposition 2/3) if
any descendant is (a) an excluded entry (`tests/specify_cli/cli/commands`) or (b) claimed by another module row
(e.g. `tests/specify_cli/cli/commands/agent` is claimed by `execution_context`). `tests/specify_cli/cli` is
explicitly promotion-blocked. Otherwise a legal promotion is **parent-only into `test_dirs` with every nested
descendant de-recorded from `out_of_matrix` in the same commit** (recursion then covers them); never add both a
parent and its child to `test_dirs` (pairwise-non-nesting red).

### PC2 — Ownership resolution (Paula F4)
If more than one row's `roots` could own `D`, pick the row whose `cov_targets` most specifically names
`specify_cli.<leaf>` (the leaf-specific row, e.g. `status`), NOT an aggregate (`unit`/`core_misc`/
`execution_context`) that merely carries the broad root. Record the chosen owner + rationale (FR-011).

### PC3 — Special-tier reconciliation (priti F2)
If `D` is under `tests/integration/**` or `tests/next/**`, it is already claimed by
`special_tiers.integration_tests_next` (job `integration-tests-next`, ~69 min). Its disposition must reconcile
with that tier (wire-up / nightly), not mint a fresh row; note the tier's job is currently **unwired**
(pre-existing honesty gap — file/annotate, do not silently paper over).

## Disposition selection
1. **Coverage question**: Is `D`'s behavior already fully exercised by an **in-matrix** covering target?
   - Yes → **Disposition 3 (sharpen-reason)**, subject to the evidence gate below.
2. Else, is `D`'s unique value a single repo-invariant/freshness check?
   - Yes → **Disposition 2 (lift-invariant)**: add an always-on `tests/architectural/` test
     (`pytestmark=[pytest.mark.architectural]`); sharpen `D`'s reason to name it. No measurement.
3. Else `D` has unique behavioral coverage AND passed PC1:
   a. Owning row exists (PC2) → add `D` parent-only to that row's `test_dirs`; de-record descendants.
   b. No owning row → **mint a row is a census-gated TWO-FILE edit** (Paula F1): first add a census-authorized
      group to `tests/release/ci_retirement_scrub.json`, then mirror its `roots`/`cov_targets` **verbatim** into
      the new registry row (bijection + verbatim guards). This is heavyweight; subject to the Cap.
   c. `python scripts/ci/capture_shard_timings.py --module <M> --write`; assert provenance parity (below).
   d. Choose `shard_count` by greedy-LPT; record in a YAML comment.
   e. skew ≤20% AND projected serial shard ≤30-min budget → **1a (promote-per-pr)**; else **1b (promote-nightly)**
      (author the marker split in `ci-nightly.yml`).
   f. Remove `D` (and descendants) from `out_of_matrix` in the same change.

## Evidence gates (make the load-bearing checks runnable, not prose)

### EG1 — Disposition-3 coverage-equivalence (Renata F1) — NOT a reworded snapshot
A sharpen-reason is admissible only if:
- **In-matrix target**: the covering path named in the reason is itself claimed by a module row or lives under
  `tests/architectural/`. A reason pointing at another `out_of_matrix` entry (circular) is rejected.
- **Direction resolved**: do NOT assume `tests/<leaf>` is "primary" because the lossy leaf-transform
  (`gate_selection._canonical_test_mirror`) names it so; the path-faithful mirror of `src/specify_cli/<x>` is
  `tests/specify_cli/<x>`. Compute which tree has superset coverage and keep THAT one in-matrix.
- **Coverage-diff evidence**: capture `pytest --cov=<module-src> --cov-branch --cov-report=json` over `D` and
  over the named in-matrix mirror; assert covered(file,line/branch) of `D` ⊆ mirror. Store the JSON under `analysis/evidence/` and embed a
  structured pointer `evidence: analysis/evidence/<file>.json` in the registry reason (WP04 resolves it). Subset is necessary, not sufficient — if `D` asserts a distinct *property* over shared lines,
  the disposition must be promote/lift, not sharpen.

### EG2 — Marker-presence for pop-(b) disposition-3 (priti F3)
Before a reason names a marker lane (corpus/windows_ci/nightly), `grep` the tree for that pytest marker. If the
tree's tests do not carry it, the reason is a disguised snapshot (#2979 class) — the tree must be marked
(route as honest-red/ticket) or given a different disposition. Never name a marker home a tree cannot reach.

### EG3 — Promotion evidence freshness + parity (Renata F2)
For every module `M` whose `shard_count` changed vs base `main`, assert from `module_capture_provenance[M]`:
`unique_tests_measured == len(module_test_durations[M]) == module_test_count[M]` (parity, closes the
uniform-weight degradation) AND `captured_at >= floor` where floor = `analysis/evidence/capture-floor.txt` recorded by WP01 (freshness). Runnable gate, not prose.

## Cap (priti F6 — hard single-PR guardrail)
This PR promotes at most **a small N** into EXISTING rows (target: the security-first set), and mints at most the
**security-critical new row(s)** via scrub. Any promotion beyond that — and every non-security new-row mint — is
**deferred to a follow-up**, recorded as a decision ("promotion warranted; deferred to #<follow-up> to bound PR
size"), NOT left as a snapshot. Aggregate-folding a rootless family into `core_misc.test_dirs` is **prohibited**
(Paula F3: selection is `roots`-based; a `src/<family>` change would not select the aggregate → false home).

## Prohibitions
No guessed `shard_count`; no sizing from file counts; no test-content edits (real red → own ticket, honest-red);
no reopening `tests/specify_cli/cli/commands` or named-home entries; no aggregate-fold-as-promotion.
