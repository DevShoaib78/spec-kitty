"""Always-on freshness gate: README.md's Governance layer section stays accurate.

Lifted from ``tests/specify_cli/docs/test_readme_governance.py`` (WP03 /
FR-005), a ``tests/specify_cli/docs`` tree recorded ``out_of_matrix`` in
``.github/ci-module-registry.yml`` — no per-PR lane selects it (#4374
disposition ledger, disposition 2 — lift-invariant).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.architectural]

REPO_ROOT = Path(__file__).resolve().parents[2]
README = REPO_ROOT / "README.md"


def _governance_section() -> str:
    content = README.read_text()
    gov_idx = content.index("## Governance layer")
    next_h2 = content.find("\n## ", gov_idx + 1)
    return content[gov_idx : next_h2 if next_h2 != -1 else len(content)]


def test_readme_has_governance_layer_section() -> None:
    content = README.read_text()
    assert "## Governance layer" in content, "README.md must contain a '## Governance layer' subsection (WP03 / FR-005)."


def test_governance_section_links_to_trail_model() -> None:
    section = _governance_section()
    rel = "docs/architecture/trail-model.md"
    assert rel in section, f"Governance layer subsection must link to {rel}."
    assert (REPO_ROOT / rel).is_file(), f"{rel} linked from README must exist."


def test_governance_section_links_to_host_surface_parity() -> None:
    section = _governance_section()
    rel = "docs/architecture/host-surface-parity.md"
    assert rel in section, f"Governance layer subsection must link to {rel}."
    assert (REPO_ROOT / rel).is_file(), f"{rel} linked from README must exist."


def test_governance_section_mentions_dispatch_only() -> None:
    section = _governance_section()
    assert 'spec-kitty dispatch "<request>"' in section
    for removed in ("advise", "ask", "do"):
        assert f"spec-kitty {removed}" not in section


def test_runtime_next_skill_references_resolve() -> None:
    skill = REPO_ROOT / "src/charter/offering/skills/spec-kitty-runtime-next/SKILL.md"
    content = skill.read_text()
    links = re.findall(r"\]\(([^)#]+\.md)\)", content)
    for link in links:
        if link.startswith("/") or link.startswith("http"):
            continue
        target = (skill.parent / link).resolve()
        assert target.exists(), f"Broken link in runtime-next/SKILL.md: {link}"
