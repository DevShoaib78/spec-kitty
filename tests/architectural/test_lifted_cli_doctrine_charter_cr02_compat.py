"""Always-on gate: the ``doctrine`` -> ``charter`` CR-02 compat shim stays intact.

Source: ``tests/specify_cli/cli/test_doctrine_charter_cr02_compat.py``
(mission ``charter-code-topology-01M152G1`` S4), which lives under
``tests/specify_cli/cli`` — recorded ``out_of_matrix`` in
``.github/ci-module-registry.yml`` (#4374, decide-out-of-matrix-test-dirs
ledger, lift-invariant disposition; PC1 nested-family bulk-lift).

Two invariants, ported in-process: the hidden ``doctrine`` alias still works
and warns (stderr, not stdout, so the JSON payload stays clean) while stying
absent from top-level ``--help``; and the canonical ``charter`` route
resolves with ``activated``-tagged rows rather than folding the
activation-blind and activation-filtered listings together.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.cli.commands.charter import charter_app
from specify_cli.cli.commands.doctrine import app as doctrine_app

pytestmark = [pytest.mark.architectural]

runner = CliRunner()


def _write_single_activation(repo: Path, mission_type_id: str) -> None:
    kittify = repo / ".kittify"
    kittify.mkdir(parents=True, exist_ok=True)
    (kittify / "config.yaml").write_text(
        f"mission_type_activations:\n  - {mission_type_id}\n",
        encoding="utf-8",
    )


def test_doctrine_group_hidden_alias_warns() -> None:
    top_level_help = runner.invoke(app, ["--help"])
    assert top_level_help.exit_code == 0, top_level_help.output
    assert "doctrine" not in top_level_help.output

    result = runner.invoke(app, ["doctrine", "mission-type", "list", "--json"])
    assert result.exit_code == 0, result.output
    assert "deprecated" in result.stderr.lower()
    assert "spec-kitty charter" in result.stderr

    rows = json.loads(result.stdout)
    assert rows
    assert {"id", "source_layer", "display_name"} <= rows[0].keys()

    direct = runner.invoke(doctrine_app, ["mission-type", "list", "--json"])
    assert direct.exit_code == 0, direct.output


def test_charter_group_canonical_routes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_single_activation(tmp_path, "software-dev")
    monkeypatch.chdir(tmp_path)

    activated_only = runner.invoke(charter_app, ["mission-type", "list", "--json"])
    assert activated_only.exit_code == 0, activated_only.output
    activated_rows = json.loads(activated_only.output)
    assert activated_rows
    assert all(row["action_sequence"] for row in activated_rows)

    everything = runner.invoke(charter_app, ["mission-type", "list", "--include-inactive", "--json"])
    assert everything.exit_code == 0, everything.output
    all_rows = json.loads(everything.output)

    activated_ids = {row["id"] for row in activated_rows}
    all_ids = {row["id"] for row in all_rows}
    assert activated_ids <= all_ids
    assert len(all_rows) >= len(activated_rows)

    inactive_rows = [row for row in all_rows if row["id"] not in activated_ids]
    assert inactive_rows, "expected at least one registered-but-inactive mission type"
    for row in inactive_rows:
        assert row["activated"] is False
        assert row["action_sequence"] == "(not activated)"
    for row in all_rows:
        if row["id"] in activated_ids:
            assert row["activated"] is True
