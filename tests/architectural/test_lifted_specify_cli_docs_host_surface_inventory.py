"""Always-on freshness gate: docs/architecture/host-surface-parity.md stays complete.

Lifted from ``tests/specify_cli/docs/test_host_surface_inventory.py`` (WP05 /
FR-001 / NFR-003), a ``tests/specify_cli/docs`` tree recorded
``out_of_matrix`` in ``.github/ci-module-registry.yml`` — no per-PR lane
selects it (#4374 disposition ledger, disposition 2 — lift-invariant).

Every supported host surface must have exactly one row with a valid
``parity_status``, and every non-``at_parity``/pointer row must explain the
gap in its notes column.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.architectural]

REPO_ROOT = Path(__file__).resolve().parents[2]
PARITY_DOC = REPO_ROOT / "docs/architecture/host-surface-parity.md"

# Pulled from src/specify_cli/upgrade/migrations/m_0_9_1_complete_lane_migration.py::AGENT_DIRS
# plus Agent Skills surfaces.
EXPECTED_SURFACES = frozenset(
    {
        "claude",
        "copilot",
        "gemini",
        "cursor",
        "qwen",
        "opencode",
        "windsurf",
        "kilocode",
        "auggie",
        "q",
        "kiro",
        "agent",
        "codex",
        "vibe",
        "pi",
        "letta",
        "llxprt",
    }
)

VALID_PARITY_STATUS = {"at_parity", "partial", "missing"}


def _parse_rows() -> list[dict[str, str]]:
    content = PARITY_DOC.read_text()
    lines = content.splitlines()
    in_table = False
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
    for line in lines:
        if line.startswith("| surface_key"):
            header = [c.strip() for c in line.strip("|").split("|")]
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) != len(header or []):
                continue
            rows.append(dict(zip(header or [], cells, strict=False)))
        elif in_table and not line.startswith("|"):
            in_table = False
    return rows


def test_parity_doc_exists() -> None:
    assert PARITY_DOC.exists(), "docs/architecture/host-surface-parity.md must exist"


def test_every_surface_has_a_row() -> None:
    rows = _parse_rows()
    present_surfaces = {row["surface_key"] for row in rows}
    missing = EXPECTED_SURFACES - present_surfaces
    assert not missing, f"Missing rows for surfaces: {sorted(missing)}"


def test_no_duplicate_surface_rows() -> None:
    rows = _parse_rows()
    keys = [row["surface_key"] for row in rows]
    dupes = {k for k in keys if keys.count(k) > 1}
    assert not dupes, f"Duplicate rows for surfaces: {sorted(dupes)}"


def test_every_row_has_valid_parity_status() -> None:
    rows = _parse_rows()
    for row in rows:
        assert row["parity_status"] in VALID_PARITY_STATUS, f"Invalid parity_status for {row['surface_key']}: {row['parity_status']}"


def test_every_non_parity_row_has_notes() -> None:
    """FR-006 — pointer/partial/missing rows must explain the gap in notes."""
    rows = _parse_rows()
    for row in rows:
        if row["parity_status"] != "at_parity" or row.get("guidance_style") == "pointer":
            assert row.get("notes"), (
                f"Row {row['surface_key']} (parity_status={row['parity_status']}, guidance_style={row.get('guidance_style')}) must have a non-empty notes column."
            )
