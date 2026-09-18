"""Always-on gate: importing ``mission_v1.events`` never loads the retired DSL stack.

Lifted from ``tests/specify_cli/mission_v1/test_import_hygiene.py`` (FR-004 /
SC-001, mission ``dead-port-disposition-01M1TZVN`` WP01), a
``tests/specify_cli/mission_v1`` tree recorded ``out_of_matrix`` in
``.github/ci-module-registry.yml`` — no per-PR lane selects it (#4374
disposition ledger, disposition 2 — lift-invariant).

``mission_v1.events`` sits on a hot path (``runtime/next/next_invocation_lifecycle.py``
emits the ``MissionNextInvoked`` observability event through it), so importing
it must never drag the retired mission-DSL v1 runtime (``compat`` / ``runner``
/ ``guards`` / ``schema``) — or its transitive ``transitions``/``six``
dependency — back into the process. Checked in an isolated subprocess so the
test cannot be satisfied by modules another test already imported.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.architectural]

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_DIR = _REPO_ROOT / "src"

_FORBIDDEN_MODULES_PROBE = (
    "import sys, specify_cli.mission_v1.events as e; "
    "bad = sorted(m for m in sys.modules if m == 'transitions' or m.startswith('transitions.') or m == 'six'); "
    "print(','.join(bad))"
)

_LOADED_PACKAGE_MODULES_PROBE = (
    "import sys, specify_cli.mission_v1.events as e; print(','.join(sorted(m for m in sys.modules if m.startswith('specify_cli.mission_v1'))))"
)


def _hermetic_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(_SRC_DIR)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("PYTHONSTARTUP", None)
    return env


def _probe(code: str) -> str:
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
        env=_hermetic_env(),
        timeout=120,
    )
    return result.stdout.strip()


def test_events_import_does_not_load_transitions() -> None:
    loaded = _probe(_FORBIDDEN_MODULES_PROBE)
    assert loaded == "", f"hot path loaded: {loaded}"


def test_events_import_loads_only_the_package_and_events() -> None:
    loaded = _probe(_LOADED_PACKAGE_MODULES_PROBE)
    assert loaded.split(",") == [
        "specify_cli.mission_v1",
        "specify_cli.mission_v1.events",
    ], f"unexpected specify_cli.mission_v1 modules loaded: {loaded}"
