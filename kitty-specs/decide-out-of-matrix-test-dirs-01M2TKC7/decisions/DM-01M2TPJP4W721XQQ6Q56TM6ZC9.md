# Decision Moment `01M2TPJP4W721XQQ6Q56TM6ZC9`

- **Mission:** `decide-out-of-matrix-test-dirs-01M2TKC7`
- **Origin flow:** `plan`
- **Slot key:** `plan.scope.promotion_aggressiveness`
- **Input key:** `promotion_scope`
- **Status:** `resolved`
- **Created:** `2026-09-18T16:46:15.196407+00:00`
- **Resolved:** `2026-09-18T16:46:24.083056+00:00`
- **Opened by:** `cli`
- **Other answer:** `false`

## Question

How aggressive should promotions be in this PR, given new rows are census-gated scrub edits and worst-case promotion is multi-hour/multi-PR?

## Options

- Bounded: decide all; promote existing-row trees + at most security-critical auth new-row; defer the rest
- Zero promotions
- Maximal

## Final answer

Bounded (operator-confirmed). Decide ALL 128 entries. Promote only pop-(a) trees with an existing owning module row + clean nested-family pre-check, plus at most the security-critical auth new-row via a census-gated scrub+registry edit. Everything else resolves to a verified sharpen-reason, a lift-invariant, or a recorded 'promotion-warranted; deferred to follow-up' decision. Aggregate-fold prohibited. Caps the PR to one scrub touch and a small measured-run set.

## Rationale

_(none)_

## Change log

- `2026-09-18T16:46:15.196407+00:00` — opened
- `2026-09-18T16:46:24.083056+00:00` — resolved (final_answer="Bounded (operator-confirmed). Decide ALL 128 entries. Promote only pop-(a) trees with an existing owning module row + clean nested-family pre-check, plus at most the security-critical auth new-row via a census-gated scrub+registry edit. Everything else resolves to a verified sharpen-reason, a lift-invariant, or a recorded 'promotion-warranted; deferred to follow-up' decision. Aggregate-fold prohibited. Caps the PR to one scrub touch and a small measured-run set.")
