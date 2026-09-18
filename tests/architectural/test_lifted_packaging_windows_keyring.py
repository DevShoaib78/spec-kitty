"""Always-on gate: ``keyring`` must not be a declared project dependency.

Lifted from ``tests/packaging/test_windows_no_keyring.py``, a
``tests/packaging`` tree recorded ``out_of_matrix`` in
``.github/ci-module-registry.yml`` — no per-PR lane selects it (#4374
disposition ledger, disposition 2 — lift-invariant).

#2979 marker-gap note: the source filename implies Windows-specific
behavior, but the assertion itself only reads ``pyproject.toml``'s static
dependency list — it never exercises any Windows-only runtime API, so it is
genuinely platform-independent and safe to lift as an always-on architectural
check rather than requiring a real ``windows_ci`` marker/runner. CLI auth
uses only the encrypted file store under ``~/.spec-kitty/auth/``, never the
OS keyring.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = [pytest.mark.architectural]


def test_keyring_not_declared_in_project_dependencies() -> None:
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    dependencies = data["project"]["dependencies"]
    assert all(not dep.startswith("keyring") for dep in dependencies), (
        "CLI auth should use only the encrypted file store under ~/.spec-kitty/auth/, so pyproject.toml must not declare keyring."
    )
