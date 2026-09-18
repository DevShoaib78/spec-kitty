"""Always-on gate: a corrupt migrations ``.pyc`` must not crash CLI startup.

Source: ``tests/specify_cli/cli/test_bytecode_heal_startup.py`` (#4124
regression), which lives under ``tests/specify_cli/cli`` — recorded
``out_of_matrix`` in ``.github/ci-module-registry.yml`` (#4374,
decide-out-of-matrix-test-dirs ledger, lift-invariant disposition; PC1
nested-family bulk-lift).

Field symptom: an interrupted ``uv tool install`` left a truncated
``base.cpython-*.pyc``; every ``spec-kitty`` command died at app assembly
before any command ran. Runs against an isolated copy of ``src/`` (so the
shared checkout's ``__pycache__`` is never corrupted for parallel workers)
and invokes the real ``-m specify_cli --version`` entrypoint — the strongest
single invariant of the source suite's three tests: startup self-heals
(purge + recompile + retry) instead of crashing.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.architectural]

_REPO_SRC = Path(__file__).resolve().parents[2] / "src"
_REPO_PACKS = Path(__file__).resolve().parents[2] / "packs"
_MIGRATIONS_CACHE = Path("specify_cli") / "upgrade" / "migrations" / "__pycache__"


def _cli_env(copy_src: Path, home: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "PYTHONPATH": str(copy_src),
            "SPEC_KITTY_PACKS_ROOT": str(_REPO_PACKS),
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "XDG_CACHE_HOME": str(home / ".cache"),
            "SPEC_KITTY_NO_UPGRADE_CHECK": "1",
        }
    )
    return env


def test_corrupt_migrations_pyc_does_not_crash_startup(tmp_path: Path) -> None:
    copy_src = tmp_path / "src"
    shutil.copytree(_REPO_SRC, copy_src, ignore=shutil.ignore_patterns("__pycache__"))
    home = tmp_path / "home"
    home.mkdir()
    env = _cli_env(copy_src, home)

    # 1. Compile the copy's base.pyc (the file an interrupted install leaves truncated).
    warm = subprocess.run(
        [sys.executable, "-c", "import specify_cli.upgrade.migrations.base"],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        timeout=180,
    )
    assert warm.returncode == 0, warm.stderr

    # 2. Corrupt it exactly like an interrupted install: truncated body, intact header.
    pycs = list((copy_src / _MIGRATIONS_CACHE).glob("base.*.pyc"))
    assert len(pycs) == 1, f"expected exactly one base.*.pyc, found {pycs}"
    data = pycs[0].read_bytes()
    pycs[0].write_bytes(data[:20] + b"\x00" * 42)

    # 3. The next CLI invocation self-heals instead of crashing.
    result = subprocess.run(
        [sys.executable, "-m", "specify_cli", "--version"],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        timeout=180,
    )
    assert result.returncode == 0, result.stderr
    assert "version" in result.stdout.lower()
    assert "repaired" in result.stderr.lower()
