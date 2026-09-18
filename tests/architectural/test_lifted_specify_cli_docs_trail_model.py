"""Always-on freshness gate: docs/architecture/trail-model.md subsections stay present.

Lifted from ``tests/specify_cli/docs/test_trail_model_doc.py`` (WP08), a
``tests/specify_cli/docs`` tree recorded ``out_of_matrix`` in
``.github/ci-module-registry.yml`` — no per-PR lane selects it (#4374
disposition ledger, disposition 2 — lift-invariant).
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.architectural]

REPO_ROOT = Path(__file__).resolve().parents[2]
TRAIL = REPO_ROOT / "docs/architecture/trail-model.md"


def test_trail_model_has_mode_enforcement_subsection() -> None:
    content = TRAIL.read_text()
    assert "### Mode Enforcement at Tier 2 Promotion" in content


def test_trail_model_has_correlation_links_subsection() -> None:
    content = TRAIL.read_text()
    assert "### Correlation Links (Tier 1 extension)" in content


def test_trail_model_has_saas_read_model_policy_section() -> None:
    content = TRAIL.read_text()
    assert "## SaaS Read-Model Policy" in content


def test_trail_model_has_saas_policy_table_header() -> None:
    """The 16-row policy table must be present in operator doc."""
    content = TRAIL.read_text()
    assert "| mode_of_work | event | project | include_request_text | include_evidence_ref |" in content


def test_trail_model_has_tier2_deferral_subsection() -> None:
    content = TRAIL.read_text()
    assert "## Tier 2 SaaS Projection — Deferred" in content


def test_trail_model_has_host_surfaces_subsection() -> None:
    content = TRAIL.read_text()
    assert "## Host surfaces that teach the trail" in content
    assert "host-surface-parity.md" in content


def test_trail_model_mode_prose_updated() -> None:
    """The documentation-only disclaimer must be gone."""
    content = TRAIL.read_text()
    assert "Mode-of-work is a documentation-level taxonomy in 3.2" not in content
    assert "Runtime enforcement is active" in content
