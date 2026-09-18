# Decision Moment `01M2TKEFG8DJ188FN05JSAKB5Z`

- **Mission:** `decide-out-of-matrix-test-dirs-01M2TKC7`
- **Origin flow:** `specify`
- **Slot key:** `specify.scope.nightly_marker_split`
- **Input key:** `nightly_marker_split_scope`
- **Status:** `resolved`
- **Created:** `2026-09-18T15:51:31.592201+00:00`
- **Resolved:** `2026-09-18T15:55:04.523069+00:00`
- **Opened by:** `cli`
- **Other answer:** `false`

## Question

When a tree's measured duration is too slow for the per-PR matrix, disposition 1 routes it to a nightly lane with a deliberate marker split. Is authoring that nightly marker split in scope for THIS mission, or does discovering a too-slow tree spawn its own follow-up?

## Options

- In scope — this mission authors any needed nightly marker split
- Out of scope — a too-slow tree is filed as a follow-up, this mission only records the decision
- Other

## Final answer

In scope: if a tree's measured duration is too slow for the per-PR matrix, this mission authors the deliberate nightly-lane marker split (marker + lane wiring) rather than deferring it to a follow-up.

## Rationale

_(none)_

## Change log

- `2026-09-18T15:51:31.592201+00:00` — opened
- `2026-09-18T15:55:04.523069+00:00` — resolved (final_answer="In scope: if a tree's measured duration is too slow for the per-PR matrix, this mission authors the deliberate nightly-lane marker split (marker + lane wiring) rather than deferring it to a follow-up.")
