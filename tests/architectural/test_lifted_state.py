"""Always-on gate: the state doctor reports the authoritative runtime root.

Lifted from ``tests/state/test_doctor_spec_kitty_home.py`` (mission
spec-kitty-home-isolation, issue #2171, FR-009/FR-010/SC-004), a
``tests/state`` tree recorded ``out_of_matrix`` in
``.github/ci-module-registry.yml`` — no per-PR lane selects it (#4374
disposition ledger, disposition 2 — lift-invariant).

The doctor's reported global-sync root must resolve to
``get_runtime_root().base`` under both env-configured and default HOME
configurations — never an independently recomputed ``~/.spec-kitty``
literal, which would silently diverge from the runtime the CLI itself uses.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from specify_cli.paths import get_runtime_root
from specify_cli.state.doctor import StateRootsReport, check_state_roots

pytestmark = [pytest.mark.architectural]


def _global_sync_root(report: StateRootsReport) -> Path:
    return next(r.resolved_path for r in report.roots if r.name == "global_sync")


def test_reported_root_matches_runtime_root_with_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """SPEC_KITTY_HOME set: reported global-sync root == runtime base == env value."""
    env_root = tmp_path / "custom-home"
    env_root.mkdir()
    monkeypatch.setenv("SPEC_KITTY_HOME", str(env_root))

    report = check_state_roots(tmp_path)

    assert _global_sync_root(report) == get_runtime_root().base == env_root


def test_reported_root_matches_runtime_root_without_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """SPEC_KITTY_HOME unset: reported root == runtime base (default ~/.spec-kitty)."""
    monkeypatch.delenv("SPEC_KITTY_HOME", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    report = check_state_roots(tmp_path)

    assert _global_sync_root(report) == get_runtime_root().base
    assert _global_sync_root(report) == tmp_path / ".spec-kitty"
