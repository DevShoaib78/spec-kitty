"""T1.5 — Regression tests: init idempotency on re-run.

Verifies:
- Running init twice in the same directory exits 0 (idempotent).
- The second run does NOT silently merge or overwrite state.
- A clear "Already initialized" message appears (in the injected console output).
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from rich.console import Console
from typer import Typer
from typer.testing import CliRunner

from specify_cli.cli.commands import init as init_module
from specify_cli.cli.commands.init import register_init_command


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

pytestmark = [pytest.mark.integration]


def test_initialized_clone_diagnoses_missing_codex_skills(monkeypatch, tmp_path):
    """An initialized clone can lack every gitignored command skill (#4425)."""
    import subprocess

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    config = tmp_path / ".kittify/config.yaml"
    config.parent.mkdir()
    config.write_text("agents:\n  available: [codex]\n", encoding="utf-8")
    mission = tmp_path / "kitty-specs/existing/spec.md"
    mission.parent.mkdir(parents=True)
    mission.write_text("Keep existing mission", encoding="utf-8")
    third_party = tmp_path / ".agents/skills/custom/SKILL.md"
    third_party.parent.mkdir(parents=True)
    third_party.write_text("Keep custom skill", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    app, buf = _make_app_with_buf()
    result = _run(app, ["init", "--ai", "codex", "--non-interactive"])
    assert result.exit_code == 1
    assert "spec-kitty agent config sync --create-missing --keep-orphaned" in " ".join(buf.getvalue().split())
    assert not (tmp_path / ".agents/skills/spec-kitty.specify").exists()
    assert config.read_text() == "agents:\n  available: [codex]\n"
    assert mission.read_text() == "Keep existing mission"
    assert third_party.read_text() == "Keep custom skill"


@pytest.mark.parametrize("selection", [[], ["--ai", "codex"], ["--ai", "CODEX;codex"]])
def test_initialized_clone_recovery_and_repeat(monkeypatch, tmp_path, selection):
    import subprocess
    from specify_cli.cli.commands.agent.config import app as config_app

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    config = tmp_path / ".kittify/config.yaml"
    config.parent.mkdir()
    config.write_text("agents:\n  available: [codex]\n")
    monkeypatch.chdir(tmp_path)
    app, _ = _make_app_with_buf()
    assert _run(app, ["init", "--non-interactive", *selection]).exit_code == 1
    recovered = CliRunner().invoke(config_app, ["sync", "--create-missing", "--keep-orphaned"])
    assert recovered.exit_code == 0, recovered.output
    for command in ("specify", "plan", "tasks"):
        assert (tmp_path / f".agents/skills/spec-kitty.{command}/SKILL.md").stat().st_size > 0
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    for _ in range(2):
        assert _run(app, ["init", "--non-interactive", *selection]).exit_code == 0
    after = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert after == before


@pytest.mark.parametrize("selection,expected", [("codex", "spec-kitty agent config add codex"), ("invalid", "Invalid --ai"), (",;", "Invalid --ai")])
def test_initialized_clone_rejects_unconfigured_selection(monkeypatch, tmp_path, selection, expected):
    config = tmp_path / ".kittify/config.yaml"
    config.parent.mkdir()
    config.write_text("agents:\n  available: [claude]\n")
    monkeypatch.chdir(tmp_path)
    app, buf = _make_app_with_buf()
    result = _run(app, ["init", "--ai", selection, "--non-interactive"])
    assert result.exit_code == 1
    assert expected in " ".join(buf.getvalue().split())
    assert config.read_text() == "agents:\n  available: [claude]\n"
    assert not (tmp_path / ".agents").exists()


@pytest.mark.parametrize("agent", ["codex", "vibe", "pi", "letta"])
@pytest.mark.parametrize("broken", ["empty", "symlink", "directory"])
def test_initialized_clone_rejects_unusable_skills(monkeypatch, tmp_path, agent, broken):
    from specify_cli.skills.command_installer import CANONICAL_COMMANDS

    config = tmp_path / ".kittify/config.yaml"
    config.parent.mkdir()
    config.write_text(f"agents:\n  available: [{agent}]\n")
    for command in CANONICAL_COMMANDS:
        path = tmp_path / f".agents/skills/spec-kitty.{command}/SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text("Preserve user-edited skill")
    target = tmp_path / ".agents/skills/spec-kitty.specify/SKILL.md"
    target.unlink()
    if broken == "empty":
        target.touch()
    elif broken == "symlink":
        target.symlink_to(config)
    else:
        target.mkdir()
    monkeypatch.chdir(tmp_path)
    app, buf = _make_app_with_buf()
    assert _run(app, ["init", "--non-interactive"]).exit_code == 1
    assert "config sync" in " ".join(buf.getvalue().split())
    assert (tmp_path / ".agents/skills/spec-kitty.plan/SKILL.md").read_text() == "Preserve user-edited skill"
    assert config.read_text() == f"agents:\n  available: [{agent}]\n"


def _make_app_with_buf() -> tuple[Typer, io.StringIO]:
    """Return app and the buffer backing the injected console."""
    buf = io.StringIO()
    console = Console(file=buf, force_terminal=False, highlight=False)
    app = Typer()

    register_init_command(
        app,
        console=console,
        show_banner=lambda: None,
        activate_mission=lambda proj, mtype, mdisplay, _con: mdisplay,
        ensure_executable_scripts=lambda path, tracker=None: None,
    )
    return app, buf


def _run(app: Typer, args: list[str]) -> object:
    runner = CliRunner()
    return runner.invoke(app, args, catch_exceptions=True)


def _fake_copy_package(project_path: Path) -> Path:
    kittify = project_path / ".kittify"
    kittify.mkdir(parents=True, exist_ok=True)
    return kittify / "templates" / "command-templates"


# ---------------------------------------------------------------------------
# T1.5: Idempotency check
# ---------------------------------------------------------------------------


def test_init_is_idempotent_on_rerun(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """T1.5: Running init twice exits 0 on both runs (idempotent).

    The second run must NOT silently merge or overwrite state — it exits
    cleanly with an "Already initialized" message in console output.
    """
    # First run — fresh directory
    app1, buf1 = _make_app_with_buf()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(init_module, "get_local_repo_root", lambda override_path=None: None)
    monkeypatch.setattr(init_module, "copy_specify_base_from_package", _fake_copy_package)

    result1 = _run(app1, ["init", "--ai", "codex", "--non-interactive"])
    assert result1.exit_code == 0, f"First init failed (exit_code={result1.exit_code})"

    # Record state after first run
    config_path = tmp_path / ".kittify" / "config.yaml"
    assert config_path.exists(), "config.yaml should exist after first init"
    config_content_after_first = config_path.read_text(encoding="utf-8")

    # Second run — already-initialized directory; use a fresh app/buffer
    app2, buf2 = _make_app_with_buf()
    result2 = _run(app2, ["init", "--ai", "codex", "--non-interactive"])

    # Must exit 0 (idempotent path, not fail-fast)
    assert result2.exit_code == 0, f"Second init should exit 0 (idempotent), got {result2.exit_code}."

    # Must emit a clear "already initialized" message in console output (not silent)
    console_out = buf2.getvalue().lower()
    assert "already" in console_out or "initialized" in console_out, (
        f"Second init console output should mention 'already initialized', but got:\n{buf2.getvalue()!r}"
    )

    # Config must be unchanged (no silent merge/overwrite)
    config_content_after_second = config_path.read_text(encoding="utf-8")
    assert config_content_after_first == config_content_after_second, "config.yaml was modified by the second init run — silent merge/overwrite detected."
