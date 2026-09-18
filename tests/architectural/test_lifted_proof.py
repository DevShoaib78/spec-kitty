"""Always-on gate: the proof event-schema registry stays complete and stable.

Lifted from ``tests/proof/test_event_schemas.py``, a ``tests/proof`` tree
recorded ``out_of_matrix`` in ``.github/ci-module-registry.yml`` — no per-PR
lane selects it (#4374 disposition ledger, disposition 2 — lift-invariant).

Two invariants from ``specify_cli.proof.events`` are pinned: every declared
proof event type has a required-fields entry (the registry cannot drift out
of sync with itself), and a built payload's idempotency key is a
deterministic digest that ignores ``observed_at`` (so retries/replays of the
same proof produce the same key).
"""

from __future__ import annotations

import pytest

from specify_cli.proof.events import (
    PROOF_EVENT_REQUIRED_FIELDS,
    PROOF_EVENT_TYPES,
    build_proof_payload,
    proof_idempotency_key,
)

pytestmark = [pytest.mark.architectural]


def _base_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "subject": {
            "subject_type": "work_package",
            "subject_id": "WP04",
            "mission_id": "01JTJ8M3Z3ZV4A6J3B1Q4JQ8RM",
            "mission_slug": "1223-cli-evidence-event-schema",
            "wp_id": "WP04",
        },
        "source": "pytest",
        "actor": {
            "actor_id": "codex",
            "actor_type": "llm",
            "display_name": "Codex",
        },
        "confidence": 0.93,
        "occurred_at": "2026-06-09T12:00:00+00:00",
        "observed_at": "2026-06-09T12:00:05+00:00",
        "artifact_refs": [
            {
                "kind": "junit",
                "uri": "artifacts/test-results.xml",
                "sha256": "a" * 64,
                "size_bytes": 512,
            }
        ],
        "summary": {"status": "passed", "tests": 12},
    }
    payload.update(overrides)
    return payload


def test_every_proof_event_type_has_a_required_fields_entry() -> None:
    assert set(PROOF_EVENT_REQUIRED_FIELDS) == set(PROOF_EVENT_TYPES), "the proof event-type registry and its required-fields table have drifted out of sync"


def test_idempotency_key_is_deterministic_and_ignores_observed_at() -> None:
    first = build_proof_payload(
        "ReviewProofRecorded",
        _base_payload(review_kind="code_review", verdict="approved"),
    )
    second = build_proof_payload(
        "ReviewProofRecorded",
        _base_payload(
            review_kind="code_review",
            verdict="approved",
            observed_at="2026-06-09T12:10:00+00:00",
        ),
    )

    assert first["idempotency_key"] == second["idempotency_key"]
    assert first["idempotency_key"] == proof_idempotency_key("ReviewProofRecorded", first)
