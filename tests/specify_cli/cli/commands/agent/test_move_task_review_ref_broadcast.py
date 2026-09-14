"""#3954 end-to-end: the real ``move-task --to approved`` entry point.

PR #4319 review condition 3: the unit tests in
``tests/status/test_zeitgeist_moment_handler.py`` exercise only the fan-out
seam (``adapters.fire_saas_fanout``). This file drives the REAL
``_do_move_task`` orchestrator against a coord router whose ``commit_status``
is the REAL ``RealCoordCommitRouter`` leg (``emit_status_transition_
transactional`` → canonical status-log append → live fan-out → the Zeitgeist
bridge), with only the network itself faked — so the exact production path a
long, multi-line approval note takes is on test:

* the volatile ``WPStatusChanged`` moment still broadcasts, carrying a
  one-line, ≤240-byte, visibly truncated ``review_ref``;
* the persisted canonical status event keeps the FULL note, newlines and all
  (``Zeitgeist carries NOW, Git carries DONE`` — planning#2269).

Non-durable approval (``auto_commit=False``) is deliberate: that is the path
where the hop's ``review_result.reference`` — and therefore the emitted
``review_ref`` — is the operator's note itself (``_mt_hop_review_result``'s
``evidence_dict`` arm, built from ``effective_approval_ref``, which considers
``--note``); the durably-persisted arm references the review-cycle pointer
instead, which is already inside the bound.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from specify_cli.agent_tasks_ports import (
    CommitArtifactResult,
    CommitStatusResult,
    GuardCapability,
    MissionHandle,
    RealCoordCommitRouter,
    TasksPorts,
)
from specify_cli.cli.commands.agent.tasks import _do_move_task, _MoveTaskArgs
from specify_cli.status import adapters
from specify_cli.status.models import Lane, StatusEvent, TransitionRequest
from specify_cli.status.store import append_event, read_events
from specify_cli.zeitgeist_client import resolution as resolution_module
from tests.mocked_env import setup_mocked_env
from tests.specify_cli.cli.commands.agent.test_tasks_ports import FakeFsReader, FakeGitOps, FakeRender
from tests.status.test_zeitgeist_moment_handler import OfferRecorder, _credential

pytestmark = pytest.mark.fast

_MISSION = "wp3954-review-ref-broadcast"
_MISSION_ID = "01JREVIEWREF000000000000000"
_WP_ID = "WP01"

# The F-46 shape: a real review summary, multi-line, well past the codec's
# 240-UTF-8-byte attr bound in both bytes and lines.
_LONG_NOTE = (
    "Approved — LGTM.\n"
    "The transition table now covers the rollback edge,\n"
    "the reducer handles out-of-order events,\n"
    "and the regression suite passes end to end.\n" + "Padding past the 240-byte bound. " * 6
)


@pytest.fixture(autouse=True)
def _zeitgeist_only_registry() -> None:
    """Zeitgeist handlers as the sole fan-out wiring, restored afterwards.

    Same isolation as the moment-handler suite: no other handler can observe
    (or swallow) the broadcast, and the production wiring is back for the
    next test.
    """
    adapters.reset_handlers()
    adapters.ensure_zeitgeist_moment_handlers()
    yield
    adapters.reset_handlers()
    adapters.ensure_zeitgeist_moment_handlers()


@pytest.fixture(autouse=True)
def _faked_transport(monkeypatch: pytest.MonkeyPatch) -> OfferRecorder:
    """Resolve credentials to a stored relay credential and never mint focus.

    Without this, the bridge would read the ambient credential store and the
    focus-lease path could touch real resolution — exactly the isolation the
    moment-handler suite applies.
    """
    monkeypatch.setattr(resolution_module, "resolve_credentials", lambda *a, **k: _credential())
    monkeypatch.setattr(resolution_module, "resolve_focus_capability", lambda *a, **k: None)
    return OfferRecorder().install(monkeypatch)


@dataclass
class _RealEmitCoordRouter:
    """``commit_status`` is the REAL router leg; only the write dir is fixed.

    ``feature_write_dir`` returns the test's mission directory (the seam the
    sibling durability tests also pin) — everything else is production:
    ``RealCoordCommitRouter.commit_status`` runs the transactional emit, which
    appends the canonical status event and fires the live fan-out.
    """

    write_dir: Path
    real_router: RealCoordCommitRouter = field(default_factory=RealCoordCommitRouter)

    def feature_write_dir(self, mission: MissionHandle) -> Path:
        return self.write_dir

    def commit_status(self, request: TransitionRequest, *, capability: GuardCapability) -> CommitStatusResult:
        return self.real_router.commit_status(request, capability=capability)

    def commit_artifact(self, *args: object, **kwargs: object) -> CommitArtifactResult:
        raise AssertionError("commit_artifact must not be called with auto_commit=False")


def _build_wp_file(tmp_path: Path, mission_slug: str, wp_id: str) -> Path:
    feature_dir = tmp_path / "kitty-specs" / mission_slug
    tasks_dir = feature_dir / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".kittify").mkdir(exist_ok=True)
    # A valid meta.json makes the topology genuinely SINGLE_BRANCH for the
    # REAL transactional emit (``read_events_transactional`` treats an absent
    # meta.json as "maybe still-coord" and hard-fails downstream) — same
    # fixture note as ``test_move_task_durability.py``'s ``_build_wp_file``.
    import json

    (feature_dir / "meta.json").write_text(
        json.dumps({"mission_id": _MISSION_ID, "mission_slug": mission_slug}),
        encoding="utf-8",
    )
    (tasks_dir / f"{wp_id}-test.md").write_text(
        f"---\n"
        f"work_package_id: {wp_id}\n"
        f"title: Test {wp_id}\n"
        f"execution_mode: code_change\n"
        f"agent: testbot\n"
        f"subtasks: [T001]\n"
        f"owned_files:\n  - src/{wp_id.lower()}/**\n"
        f"authoritative_surface: src/{wp_id.lower()}/\n"
        f"---\n\n# {wp_id}\n\n## Activity Log\n",
        encoding="utf-8",
    )
    return feature_dir


def _seed_wp_in_review(feature_dir: Path, wp_id: str) -> None:
    append_event(
        feature_dir,
        StatusEvent(
            event_id=f"test-{wp_id}-in_review",
            mission_slug=feature_dir.name,
            wp_id=wp_id,
            from_lane=Lane.FOR_REVIEW,
            to_lane=Lane.IN_REVIEW,
            at="2026-01-01T00:00:00+00:00",
            actor="test",
            force=False,
            execution_mode="worktree",
        ),
    )


def test_move_task_approval_with_long_multiline_note_broadcasts_bounded_moment(
    tmp_path: Path,
    _faked_transport: OfferRecorder,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The #3954 acceptance, through the real entry point: one broadcast
    moment with a bounded one-line ``review_ref``; the full note durable in
    the canonical status log; truncation visible to operators at INFO."""
    feature_dir = _build_wp_file(tmp_path, _MISSION, _WP_ID)
    _seed_wp_in_review(feature_dir, _WP_ID)
    coord = _RealEmitCoordRouter(write_dir=feature_dir)
    ports = TasksPorts(fs=FakeFsReader(default_planning_dir=feature_dir), coord=coord, git=FakeGitOps(), render=FakeRender())
    assert len(" ".join(_LONG_NOTE.split()).encode("utf-8")) > 240  # genuinely over-bound prose

    with (
        setup_mocked_env(
            tmp_path,
            mission_slug=_MISSION,
            target_branch="wip-lane",
            extra_patches={
                "_validate_ready_for_review": (True, []),
                "_check_unchecked_subtasks": [],
            },
        ),
        caplog.at_level(logging.INFO, logger="specify_cli.status.zeitgeist_bridge"),
    ):
        _do_move_task(
            _MoveTaskArgs(
                task_id=_WP_ID,
                to="approved",
                mission=_MISSION,
                agent=None,
                assignee=None,
                shell_pid=None,
                note=_LONG_NOTE,
                review_feedback_file=None,
                approval_ref=None,
                reviewer="reviewer-renata",
                self_review_fallback=False,
                intended_reviewer=None,
                reviewer_failure_reason=None,
                done_override_reason=None,
                force=False,
                tracker_ref=None,
                skip_review_artifact_check=False,
                auto_commit=False,
                json_output=True,
            ),
            ports=ports,
        )

    # Exactly one WPStatusChanged moment reached the relay seam, with its
    # presence frame — no drops, no retries, no second moment.
    assert _faked_transport.summaries() == [
        ("event.publish", "WPStatusChanged"),
        ("presence.publish", "command"),
    ]
    _op, args = _faked_transport.moment_offers()[0]
    assert args["kind"] == "WPStatusChanged"
    wire_ref = args["attrs"]["review_ref"]
    assert "\n" not in wire_ref
    assert len(wire_ref.encode("utf-8")) <= 240
    assert wire_ref.endswith("…")
    one_line = " ".join(_LONG_NOTE.split())
    expected_prefix = one_line.encode("utf-8")[: 240 - len("…".encode())].decode("utf-8", errors="ignore")
    assert wire_ref == expected_prefix + "…"

    # The truncation is operator-visible (INFO, not DEBUG).
    assert any("review_ref truncated" in m for m in caplog.messages)

    # Git carries DONE: the persisted canonical status event keeps the FULL
    # multi-line note on both its ``review_ref`` and its structured
    # ``review_result.reference`` — nothing was lost to the volatile bound.
    # (``.strip()`` mirrors the producer's own ``st.note.strip()`` — the
    # trailing space of the fixture padding never reaches the log.)
    approved = [e for e in read_events(feature_dir) if e.wp_id == _WP_ID and e.to_lane is Lane.APPROVED]
    assert len(approved) == 1
    event = approved[0]
    assert event.review_ref == _LONG_NOTE.strip()
    assert event.review_result is not None
    assert event.review_result.verdict == "approved"
    assert event.review_result.reference == _LONG_NOTE.strip()


def test_move_task_approval_with_short_note_rides_verbatim(
    tmp_path: Path,
    _faked_transport: OfferRecorder,
) -> None:
    """The bounding is a no-op for a note already inside the bound: the wire
    carries it byte-identical (single line, no marker), and the persisted
    event matches it exactly."""
    note = "Approved — covers the rollback edge and the reducer."
    feature_dir = _build_wp_file(tmp_path, _MISSION, _WP_ID)
    _seed_wp_in_review(feature_dir, _WP_ID)
    coord = _RealEmitCoordRouter(write_dir=feature_dir)
    ports = TasksPorts(fs=FakeFsReader(default_planning_dir=feature_dir), coord=coord, git=FakeGitOps(), render=FakeRender())

    with setup_mocked_env(
        tmp_path,
        mission_slug=_MISSION,
        target_branch="wip-lane",
        extra_patches={
            "_validate_ready_for_review": (True, []),
            "_check_unchecked_subtasks": [],
        },
    ):
        _do_move_task(
            _MoveTaskArgs(
                task_id=_WP_ID,
                to="approved",
                mission=_MISSION,
                agent=None,
                assignee=None,
                shell_pid=None,
                note=note,
                review_feedback_file=None,
                approval_ref=None,
                reviewer="reviewer-renata",
                self_review_fallback=False,
                intended_reviewer=None,
                reviewer_failure_reason=None,
                done_override_reason=None,
                force=False,
                tracker_ref=None,
                skip_review_artifact_check=False,
                auto_commit=False,
                json_output=True,
            ),
            ports=ports,
        )

    assert [op for op, _args in _faked_transport.moment_offers()] == ["event.publish"]
    _op, args = _faked_transport.moment_offers()[0]
    assert args["attrs"]["review_ref"] == " ".join(note.split())

    approved = [e for e in read_events(feature_dir) if e.wp_id == _WP_ID and e.to_lane is Lane.APPROVED]
    assert len(approved) == 1
    assert approved[0].review_ref == note
