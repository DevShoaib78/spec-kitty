"""``spec-kitty upgrade --help`` must not point at documentation that does not exist (#4688).

The help text ended with ``See also: docs/guides/install-and-upgrade.md`` -- a
path that no longer exists (the guide lives under
``docs/guides/how-to/installation/``). These tests resolve every ``docs/...md``
path in the rendered help (and in the module docstring, which carries the same
pointer) against the repository, so a moved guide reds here instead of in a
user's terminal.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from specify_cli.cli.commands import upgrade as upgrade_module
from tests.specify_cli.cli.commands._help_snapshot import force_wide_help_console

pytestmark = [pytest.mark.unit, pytest.mark.fast]

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DOC_REF = re.compile(r"docs/[\w./-]+\.md")


def _missing(refs: set[str]) -> list[str]:
    return sorted(ref for ref in refs if not (_REPO_ROOT / ref).is_file())


def test_upgrade_help_doc_references_exist(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every ``docs/...md`` path in the rendered ``upgrade --help`` exists in the repo."""
    # Render the command on its own (no root callback / startup gates) at a
    # wrap-free width so a long path can never be split across lines.
    force_wide_help_console(monkeypatch)
    app = typer.Typer()
    app.command()(upgrade_module.upgrade)
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0, result.output
    refs = set(_DOC_REF.findall(result.output))
    assert refs, "upgrade --help lost its 'See also' documentation pointer"
    assert not _missing(refs), f"upgrade --help points at documentation that does not exist: {_missing(refs)}"


def test_upgrade_module_doc_references_exist() -> None:
    """The module docstring carries the same pointer; keep it honest too."""
    refs = set(_DOC_REF.findall(upgrade_module.__doc__ or ""))
    assert refs
    assert not _missing(refs), f"upgrade module docstring points at documentation that does not exist: {_missing(refs)}"
