"""Always-on gate: canonical command templates stay free of dev-time drift.

Source: ``tests/specify_cli/test_command_template_cleanliness.py`` (WP06 /
T026), which lives directly under ``tests/specify_cli`` — recorded
``out_of_matrix`` in ``.github/ci-module-registry.yml`` (#4374,
decide-out-of-matrix-test-dirs ledger, lift-invariant disposition).

The source suite mixes two different topics: content CLEANLINESS (no
leftover dev-slug/absolute-path/deprecated-terminology artifacts — this
lift) and content GUIDANCE-PRESENCE (``--mission`` reminders, frontmatter
description, WP ownership fields — a broader, separate concern left
out-of-matrix). This lift narrows to the cleanliness invariant the ledger's
one-line summary names ("no drift/leftover placeholders").
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.architectural]

from specify_cli.shims.registry import PROMPT_DRIVEN_COMMANDS

PROMPT_DRIVEN: list[str] = sorted(PROMPT_DRIVEN_COMMANDS)

_PROMPT_STEPS_DIR = Path(__file__).resolve().parents[2] / "packs" / "built-in" / "missions" / "mission-steps" / "software-dev"

_FORBIDDEN_HOME_LITERAL = "/Users/" + "robe" + "rt/"


def _template_content(command: str) -> str:
    return (_PROMPT_STEPS_DIR / command / "prompt.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("command", PROMPT_DRIVEN)
def test_no_dev_specific_mission_slugs(command: str) -> None:
    """Templates must not contain the 057-/058- dev-time feature slugs."""
    content = _template_content(command)
    for bad_slug in ("057-", "058-"):
        assert bad_slug not in content, f"{command}.md contains dev-time feature slug '{bad_slug}' - strip before shipping to consumers"


@pytest.mark.parametrize("command", PROMPT_DRIVEN)
def test_no_absolute_user_paths(command: str) -> None:
    """Templates must not contain absolute paths tied to a specific machine."""
    content = _template_content(command)
    assert _FORBIDDEN_HOME_LITERAL not in content, f"{command}.md contains a forbidden user-specific home path literal"
    assert re.search(r"/Users/[^/]+/", content) is None, f"{command}.md contains macOS absolute user path '/Users/<user>/'"
    assert re.search(r"/home/[^/]+/", content) is None, f"{command}.md contains Linux absolute user path '/home/<user>/'"


@pytest.mark.parametrize("command", PROMPT_DRIVEN)
def test_no_planning_repository_terminology(command: str) -> None:
    """Templates must not use deprecated planning-location terminology."""
    content = _template_content(command)
    assert "planning repository" not in content.lower(), f"{command}.md uses deprecated 'planning repository' terminology - use 'repository root checkout' instead"
    assert "planning repo" not in content.lower(), f"{command}.md uses deprecated 'planning repo' terminology - use 'repository root checkout' instead"
    assert "project root checkout" not in content.lower(), (
        f"{command}.md uses deprecated 'project root checkout' terminology - use 'repository root checkout' instead"
    )
    assert "main repository root" not in content.lower(), f"{command}.md uses ambiguous 'main repository root' terminology - use 'repository root checkout' instead"
