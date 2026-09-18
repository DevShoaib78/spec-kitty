"""Always-on gate: mission identity (ULID ``mission_id``) resolution.

Lifted from ``tests/mission_metadata/test_mission_identity.py`` (T019 /
FR-203), a ``tests/mission_metadata`` tree recorded ``out_of_matrix`` in
``.github/ci-module-registry.yml`` — no per-PR lane selects it (#4374
disposition ledger, disposition 2 — lift-invariant).

``resolve_mission_identity`` must round-trip a real ULID ``mission_id`` from
``meta.json`` (Mission Identity Model, 083+: ``mission_id`` is the only
runtime identity), and must tolerate a legacy mission with no ``mission_id``
by returning ``None`` rather than raising.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from ulid import ULID

from specify_cli.mission_metadata import MissionIdentity, resolve_mission_identity

pytestmark = [pytest.mark.architectural]


def _write_meta(feature_dir: Path, meta: dict) -> None:
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_resolve_mission_identity_includes_mission_id(tmp_path: Path) -> None:
    ulid_val = str(ULID())
    feature_dir = tmp_path / "001-test-feature"
    _write_meta(
        feature_dir,
        {
            "mission_slug": "001-test-feature",
            "mission_number": "001",
            "mission_type": "software-dev",
            "slug": "001-test-feature",
            "friendly_name": "test feature",
            "target_branch": "main",
            "created_at": "2026-04-09T00:00:00+00:00",
            "mission_id": ulid_val,
        },
    )

    identity = resolve_mission_identity(feature_dir)

    assert isinstance(identity, MissionIdentity)
    assert identity.mission_id == ulid_val
    assert len(identity.mission_id) == 26
    ULID.from_str(identity.mission_id)


def test_resolve_mission_identity_tolerates_legacy_mission(tmp_path: Path) -> None:
    feature_dir = tmp_path / "001-legacy-feature"
    _write_meta(
        feature_dir,
        {
            "mission_slug": "001-legacy-feature",
            "mission_number": "001",
            "mission_type": "software-dev",
            "slug": "001-legacy-feature",
            "friendly_name": "legacy feature",
            "target_branch": "main",
            "created_at": "2025-01-01T00:00:00+00:00",
        },
    )

    identity = resolve_mission_identity(feature_dir)

    assert isinstance(identity, MissionIdentity)
    assert identity.mission_id is None
