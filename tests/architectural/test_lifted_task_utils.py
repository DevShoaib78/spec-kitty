"""Always-on gate: ``set_scalar``'s append-on-miss retirement stays fail-closed.

Lifted from ``tests/task_utils/test_set_scalar_retired.py`` (FR-006, WP08,
mission upgrade-atomicity-recovery), a ``tests/task_utils`` tree recorded
``out_of_matrix`` in ``.github/ci-module-registry.yml`` — no per-PR lane
selects it (#4374 disposition ledger, disposition 2 — lift-invariant).

``set_scalar`` still updates an existing scalar key (the symbol is retained
for re-exports), but must refuse — never silently append an inline
``key: value`` line — when the key is absent. This is the guard that closes
the #3372 dual-``review_feedback``-key regression: no code path may
reintroduce an inline-appended frontmatter key via this writer.
"""

from __future__ import annotations

import pytest

from specify_cli.task_utils.support import TaskCliError, extract_scalar, set_scalar

pytestmark = [pytest.mark.architectural]


def test_set_scalar_updates_existing_key() -> None:
    frontmatter = 'work_package_id: "WP01"\nlane: "planned"\n'
    updated = set_scalar(frontmatter, "lane", "in_progress")
    assert extract_scalar(updated, "lane") == "in_progress"
    assert updated.count("lane:") == 1


def test_set_scalar_refuses_append_on_miss() -> None:
    frontmatter = 'work_package_id: "WP01"\n'
    with pytest.raises(TaskCliError):
        set_scalar(frontmatter, "lane", "planned")


def test_set_scalar_never_appends_inline_review_feedback_key() -> None:
    """The exact #3372 shape: an absent ``review_feedback`` key must NOT be
    appended inline. Fail closed instead."""
    frontmatter = 'work_package_id: "WP01"\ntitle: "Test"\n'
    with pytest.raises(TaskCliError):
        set_scalar(frontmatter, "review_feedback", "review-cycle://x/y/review-cycle-1.md")
    assert "review_feedback" not in frontmatter
