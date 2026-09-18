"""Always-on gate: ``get_project_root_or_exit`` resolves worktrees and fails closed on git errors.

Source: ``tests/specify_cli/cli/test_helpers.py`` (T007, #4123), which lives
under ``tests/specify_cli/cli`` — recorded ``out_of_matrix`` in
``.github/ci-module-registry.yml`` (#4374, decide-out-of-matrix-test-dirs
ledger, lift-invariant disposition; PC1 nested-family bulk-lift).

Ledger assertion shape: "Fixture worktree + a git-unavailable fixture;
assert message/exit/JSON shape." Lifts the worktree-resolution invariant plus
one representative message/exit/JSON assertion per rendering path (human
exit-1 render, machine JSON envelope) rather than the source suite's full
message-content permutations.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
import typer
from rich.console import Console

from specify_cli.cli.helpers import get_project_root_or_exit

pytestmark = [pytest.mark.architectural]


def test_get_project_root_or_exit_succeeds_in_worktree(tmp_path: Path) -> None:
    main_repo = tmp_path / "main_repo"
    (main_repo / ".kittify").mkdir(parents=True)
    worktrees_dir = main_repo / ".git" / "worktrees" / "test_lane"
    worktrees_dir.mkdir(parents=True)

    worktree = tmp_path / "worktree"
    worktree.mkdir()
    (worktree / ".git").write_text(f"gitdir: {worktrees_dir}\n")

    result = get_project_root_or_exit(start=worktree)
    assert result == main_repo


def test_exit_git_resolution_failure_exits_1_and_names_git_init(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from charter.resolution import NotInsideRepositoryError
    from specify_cli.cli import helpers as helpers_mod
    from specify_cli.cli.helpers import exit_git_resolution_failure

    buf = io.StringIO()
    monkeypatch.setattr(helpers_mod, "console", Console(file=buf, force_terminal=False, highlight=False))

    with pytest.raises(typer.Exit) as excinfo:
        exit_git_resolution_failure(NotInsideRepositoryError(tmp_path), tmp_path)

    assert excinfo.value.exit_code == 1
    assert "git init" in buf.getvalue()


def test_exit_git_resolution_failure_json_envelope(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from charter.resolution import NotInsideRepositoryError
    from specify_cli.cli.helpers import exit_git_resolution_failure

    with pytest.raises(typer.Exit) as excinfo:
        exit_git_resolution_failure(NotInsideRepositoryError(tmp_path), tmp_path, json_output=True)

    assert excinfo.value.exit_code == 1
    captured = capsys.readouterr()
    assert captured.err == ""
    envelope = json.loads(captured.out)
    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "git_resolution_failed"
    assert "git init" in envelope["error"]["message"]
