# Decision Moment `01M2TKDY382VFBJTPB21F95HRM`

- **Mission:** `decide-out-of-matrix-test-dirs-01M2TKC7`
- **Origin flow:** `specify`
- **Slot key:** `specify.scope.population_b_inclusion`
- **Input key:** `population_b_scope`
- **Status:** `resolved`
- **Created:** `2026-09-18T15:51:13.768752+00:00`
- **Resolved:** `2026-09-18T15:54:56.273529+00:00`
- **Opened by:** `cli`
- **Other answer:** `false`

## Question

Should population (b) — the ~68 dirs with no per-PR path-based lane at all (tests/auth/**, tests/dossier, tests/git_ops, tests/cross_cutting/**, tests/integration/**, tests/mission, tests/tracker, etc.) — be resolved in THIS mission, or deferred to a scoped follow-up mission?

## Options

- Population (a) only — defer (b) to a follow-up
- Both (a) and (b) in this mission
- Other

## Final answer

Both populations in scope: this mission resolves all out-of-matrix entries — population (a) the ~59 secondary tests/specify_cli/** trees AND population (b) the ~68 no-per-PR-lane dirs. Each becomes a decision, not a snapshot. Excludes the already-resolved tests/specify_cli/cli/commands (#4715) and the entries that already name a per-PR/nightly home (tests, tests/docs, tests/e2e, tests/architectural, tests/ui).

## Rationale

_(none)_

## Change log

- `2026-09-18T15:51:13.768752+00:00` — opened
- `2026-09-18T15:54:56.273529+00:00` — resolved (final_answer="Both populations in scope: this mission resolves all out-of-matrix entries — population (a) the ~59 secondary tests/specify_cli/** trees AND population (b) the ~68 no-per-PR-lane dirs. Each becomes a decision, not a snapshot. Excludes the already-resolved tests/specify_cli/cli/commands (#4715) and the entries that already name a per-PR/nightly home (tests, tests/docs, tests/e2e, tests/architectural, tests/ui).")
