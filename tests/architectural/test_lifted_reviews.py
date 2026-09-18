"""Always-on gate: the SPDD/REASONS review-gate template contract holds.

Lifted from ``tests/reviews/test_review_gate_activation.py`` (WP05, contracts
FR-015/FR-017/FR-018/NFR-001), a ``tests/reviews`` tree recorded
``out_of_matrix`` in ``.github/ci-module-registry.yml`` — no per-PR lane
selects it (#4374 disposition ledger, disposition 2 — lift-invariant).

Two headline invariants from the seven-case contract: inactive rendering of
``review.md`` stays byte-identical to the synthesized pre-SPDD baseline
(NFR-001, no residue leaks when the doctrine pack is off), and active
rendering surfaces the Canvas Comparison headline plus all eight drift
outcomes (FR-015/FR-017).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from charter.offering.spdd_reasons.template_renderer import (
    REASONS_BLOCK_END,
    REASONS_BLOCK_START,
    process_spdd_blocks,
)

pytestmark = [pytest.mark.architectural]

REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEW_TEMPLATE_PATH = REPO_ROOT / "packs" / "built-in" / "missions" / "mission-steps" / "software-dev" / "review" / "prompt.md"

EIGHT_DRIFT_OUTCOMES = (
    "approved",
    "approved_with_deviation",
    "canvas_update_needed",
    "glossary_update_needed",
    "charter_follow_up",
    "follow_up_mission",
    "scope_drift_block",
    "safeguard_violation_block",
)


def _read_review_template() -> str:
    return REVIEW_TEMPLATE_PATH.read_text(encoding="utf-8")


def _baseline_for(template_text: str) -> str:
    """Synthesize the pre-WP05 ``review.md`` text by manual marker removal."""
    lines = template_text.splitlines()
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        if lines[i].strip() == REASONS_BLOCK_START:
            if out and out[-1] == "":
                out.pop()
            i += 1
            while i < n and lines[i].strip() != REASONS_BLOCK_END:
                i += 1
            i += 1
            continue
        out.append(lines[i])
        i += 1
    rendered = "\n".join(out)
    if template_text.endswith("\n"):
        rendered += "\n"
    return rendered


def test_inactive_review_template_byte_equivalent_to_baseline() -> None:
    text = _read_review_template()
    assert REASONS_BLOCK_START in text, "review.md missing SPDD start marker"
    assert REASONS_BLOCK_END in text, "review.md missing SPDD end marker"

    baseline = _baseline_for(text)
    rendered = process_spdd_blocks(text, active=False)

    assert rendered == baseline, (
        f"Inactive rendering of review.md drifted from synthesized pre-feature baseline. rendered_len={len(rendered)}, baseline_len={len(baseline)}."
    )
    assert "spdd:reasons-block" not in rendered
    assert "REASONS Canvas Comparison" not in rendered


def test_active_review_template_surfaces_headline_and_drift_outcomes() -> None:
    text = _read_review_template()
    rendered = process_spdd_blocks(text, active=True)

    assert "REASONS Canvas Comparison" in rendered
    assert REASONS_BLOCK_START not in rendered
    assert REASONS_BLOCK_END not in rendered

    for outcome in EIGHT_DRIFT_OUTCOMES:
        assert outcome in rendered, f"Active review.md missing drift outcome: {outcome}"
