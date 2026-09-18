"""Permanent out-of-matrix evidence, marker-honesty, and selection guards.

Mission decide-out-of-matrix-test-dirs (spec-kitty#4374, WP04, T015-T019) lifts the
mission's load-bearing invariants from a one-time acceptance check
(``kitty-specs/decide-out-of-matrix-test-dirs-01M2TKC7/contracts/acceptance-checks.md``)
into an always-on architectural gate, so the mission's outcome cannot silently rot on
``main`` after the mission branch merges:

* **T015** -- a module whose ``shard_count`` moved (or is a brand-new row) this mission
  carries fresh, parity-checked capture provenance (closes the uniform-weight
  degradation; NFR-003/SC-002).
* **T016** -- a registry reason that claims a marker lane is honest: the tree it
  covers actually carries that ``@pytest.mark.<lane>`` (the #2979 disguised-snapshot
  class).
* **T017** -- a registry reason is a decision, never a snapshot: no deferral phrase,
  no placeholder, and it names a concrete covering surface (NFR-005/SC-001).
* **T018** -- a reason claiming coverage-equivalence via a structured
  ``evidence: analysis/evidence/<f>.json`` pointer resolves to a committed file whose
  stored coverage proves the subset claim (Renata F1). Vacuous when the mission never
  used this claim shape (see ``analysis/evidence/README.md``): never invented here.
* **T019** -- every module row whose ``test_dirs`` this mission expanded (vs
  ``git show main:``) is durably, re-runnably selected per-PR by
  :func:`scripts.ci.gate_selection.select_modules` (Renata F3 / Paula F3).

T015 and T019 both diff the live registry against ``git show main:``. On ``main``
itself that diff is empty (zero net diff post-merge) -- both guards are written to
pass vacuously in that case rather than red every PR forever after this mission lands.

Loads (registry/timings/base-registry) happen lazily inside each test, mirroring
``test_module_shard_registry.py``'s own discipline, so a missing artefact reds for
the right reason rather than an import-time crash. This file imports that module's
loaders/constants (DRY) and must never edit it.
"""

from __future__ import annotations

import json
import re
import subprocess
from typing import Any

import pytest
import yaml

from scripts.ci.gate_selection import select_modules
from tests.architectural.test_module_shard_registry import (
    _REPO_ROOT,
    _load_registry,
    _load_timings,
    _modules,
)

pytestmark = [pytest.mark.architectural]

_MISSION_ROOT = _REPO_ROOT / "kitty-specs" / "decide-out-of-matrix-test-dirs-01M2TKC7"
_MISSION_EVIDENCE_DIR = _MISSION_ROOT / "analysis" / "evidence"
_CAPTURE_FLOOR_PATH = _MISSION_EVIDENCE_DIR / "capture-floor.txt"

_MARKER_LANES = ("corpus", "windows_ci", "performance", "e2e", "interpreter", "stress", "nightly")
# A reason "claims" a marker lane only when it names the marker right after the
# literal `pytest.mark.` prefix or a `-m ` pytest-invocation flag -- not merely by
# mentioning a CI workflow filename (e.g. "ci-nightly.yml") or an excluded-marker
# clause (e.g. "-m \"stress and not windows_ci\"" claims stress, not windows_ci).
_MARKER_CLAIM_RE = re.compile(r'(?:pytest\.mark\.|-m\s+"?)(' + "|".join(_MARKER_LANES) + r")\b")
_DEFERRAL_PHRASES = (
    "recorded deliberately",
    "measured-durations decision, never a silent default",
)
_PLACEHOLDER_WORDS = frozenset({"n/a", "none", "tbd", "todo", "pending"})
_SURFACE_RE = re.compile(r"(tests/|module|corpus|windows_ci|nightly|e2e|architectural|#\d+)")
_EVIDENCE_POINTER_RE = re.compile(r"evidence:\s*(analysis/evidence/[\w.\-/]+\.json)")


# ---------------------------------------------------------------------------
# Shared loading helpers
# ---------------------------------------------------------------------------
def _base_registry() -> dict[str, Any]:
    """The registry as committed on ``main`` -- the mission's before-picture."""
    result = subprocess.run(
        ["git", "show", "main:.github/ci-module-registry.yml"],
        capture_output=True,
        text=True,
        cwd=_REPO_ROOT,
        check=True,
    )
    payload = yaml.safe_load(result.stdout)
    assert isinstance(payload, dict), "main:.github/ci-module-registry.yml did not parse to a mapping"
    return payload


def _out_of_matrix_entries(registry: dict[str, Any]) -> list[dict[str, Any]]:
    entries = registry.get("out_of_matrix_test_dirs", [])
    assert isinstance(entries, list), "out_of_matrix_test_dirs must be a list of {reason, dirs} entries"
    return entries


# ---------------------------------------------------------------------------
# T015 -- evidence parity + freshness for changed shard_count rows
# ---------------------------------------------------------------------------
def _changed_shard_count_modules(head: dict[str, Any], base: dict[str, Any]) -> list[str]:
    base_counts = {row["module"]: row.get("shard_count") for row in _modules(base)}
    return [row["module"] for row in _modules(head) if row.get("shard_count") != base_counts.get(row["module"])]


def _capture_floor() -> str:
    assert _CAPTURE_FLOOR_PATH.exists(), f"capture floor missing: {_CAPTURE_FLOOR_PATH.relative_to(_REPO_ROOT)}"
    floor = _CAPTURE_FLOOR_PATH.read_text(encoding="utf-8").strip()
    assert floor, f"capture floor file is empty: {_CAPTURE_FLOOR_PATH}"
    return floor


def _parity_and_freshness_problems(changed: list[str], timings: dict[str, Any], floor: str) -> list[str]:
    provenance = timings.get("module_capture_provenance", {})
    durations = timings.get("module_test_durations", {})
    counts = timings.get("module_test_count", {})
    problems: list[str] = []
    for module in changed:
        prov = provenance.get(module)
        if not prov:
            problems.append(f"{module}: shard_count changed vs main but no module_capture_provenance entry")
            continue
        measured = prov.get("unique_tests_measured")
        n_durations = len(durations.get(module, []))
        n_count = counts.get(module)
        if not (measured == n_durations == n_count):
            problems.append(f"{module}: parity mismatch unique_tests_measured={measured} len(module_test_durations)={n_durations} module_test_count={n_count}")
        captured_at = str(prov.get("captured_at", ""))
        if captured_at < floor:
            problems.append(f"{module}: stale capture captured_at={captured_at!r} < floor {floor!r}")
    return problems


def test_evidence_parity_and_freshness_for_changed_modules() -> None:
    """Every module whose ``shard_count`` moved (or is new) this mission is backed by
    measured, parity-checked, floor-fresh capture provenance -- never a guess.

    Inert when no module's ``shard_count`` differs from ``main`` (including on
    ``main`` itself, post-merge) so this guard never reds an unrelated PR.
    """
    head = _load_registry()
    base = _base_registry()
    changed = _changed_shard_count_modules(head, base)
    if not changed:
        # No shard_count drift vs main -- nothing this mission promoted to verify.
        return

    timings = _load_timings()
    floor = _capture_floor()
    problems = _parity_and_freshness_problems(changed, timings, floor)
    assert not problems, "evidence parity/freshness violations:\n" + "\n".join(problems)


# ---------------------------------------------------------------------------
# T016 -- marker-presence honesty
# ---------------------------------------------------------------------------
def _marker_claims(reason: str) -> set[str]:
    return {match.group(1) for match in _MARKER_CLAIM_RE.finditer(reason)}


def _tree_carries_marker(dirs: list[str], marker: str) -> bool:
    marker_token = f"pytest.mark.{marker}"
    for entry_dir in dirs:
        tree = _REPO_ROOT / entry_dir
        if not tree.exists():
            continue
        candidates = [tree] if tree.is_file() else list(tree.rglob("*.py"))
        for path in candidates:
            if marker_token in path.read_text(encoding="utf-8"):
                return True
    return False


def test_marker_presence_honesty_for_out_of_matrix_reasons() -> None:
    """A reason naming a marker lane must be backed by a real marker in its tree.

    A reason naming a lane the tree cannot reach (a disguised snapshot, #2979) fails.
    """
    registry = _load_registry()
    problems: list[str] = []
    for entry in _out_of_matrix_entries(registry):
        reason = str(entry.get("reason", ""))
        dirs = [str(d) for d in entry.get("dirs", [])]
        for marker in sorted(_marker_claims(reason)):
            if not _tree_carries_marker(dirs, marker):
                problems.append(f"{dirs[:2]}: reason claims the {marker!r} lane but no file under {dirs} carries pytest.mark.{marker}")
    assert not problems, "marker-presence honesty violations (#2979 disguised-snapshot class):\n" + "\n".join(problems)


# ---------------------------------------------------------------------------
# T017 -- reasons are decisions, never deferrals
# ---------------------------------------------------------------------------
def _is_deferral_or_placeholder(reason: str) -> bool:
    if any(phrase in reason for phrase in _DEFERRAL_PHRASES):
        return True
    return reason.strip().lower() in _PLACEHOLDER_WORDS


def test_out_of_matrix_reasons_are_decisions_not_deferrals() -> None:
    """No reason may be a snapshot/deferral, and every reason must name a surface.

    Makes "reasons are decisions, never a silent default" (#4369/#4374 philosophy)
    a permanent invariant rather than a one-time acceptance check.
    """
    registry = _load_registry()
    problems: list[str] = []
    for entry in _out_of_matrix_entries(registry):
        reason = " ".join(str(entry.get("reason", "")).split())
        dirs = [str(d) for d in entry.get("dirs", [])][:2]
        if _is_deferral_or_placeholder(reason):
            problems.append(f"{dirs}: reason is a deferral phrase or placeholder, not a decision")
        if not _SURFACE_RE.search(reason):
            problems.append(f"{dirs}: reason names no concrete covering surface")
    assert not problems, "non-decision out-of-matrix reasons:\n" + "\n".join(problems)


# ---------------------------------------------------------------------------
# T018 -- coverage-equivalence pointer resolution (vacuous unless used)
# ---------------------------------------------------------------------------
def _subset_problem(dirs: list[str], pointer_rel: str, payload: dict[str, Any]) -> str | None:
    demoted = set(payload.get("demoted_covered", []))
    mirror = set(payload.get("mirror_covered", []))
    if not demoted or not mirror:
        return f"{dirs}: {pointer_rel} does not record both demoted_covered and mirror_covered sets"
    if not demoted <= mirror:
        return f"{dirs}: {pointer_rel} demoted_covered is not a subset of mirror_covered"
    return None


def test_coverage_pointer_reasons_resolve_and_subset() -> None:
    """A reason claiming coverage-equivalence via a structured pointer must resolve.

    The pointer file must exist (committed) and its stored JSON must show the
    demoted tree's covered set is a subset of the named in-matrix mirror -- this
    guard reads the JSON, it never re-runs coverage. Vacuous (auto-pass) when no
    reason uses this claim shape: the mission's evidence README records that
    mirror-equivalence capture was deferred to a follow-up rather than fabricated
    (``analysis/evidence/README.md``), so inventing a pointer here would itself be
    the disguised-snapshot this mission exists to eliminate.
    """
    registry = _load_registry()
    problems: list[str] = []
    pointer_seen = False
    for entry in _out_of_matrix_entries(registry):
        reason = str(entry.get("reason", ""))
        match = _EVIDENCE_POINTER_RE.search(reason)
        if not match:
            continue
        pointer_seen = True
        dirs = [str(d) for d in entry.get("dirs", [])][:2]
        pointer_rel = match.group(1)
        pointer_path = _MISSION_ROOT / pointer_rel
        if not pointer_path.exists():
            problems.append(f"{dirs}: evidence pointer {pointer_rel} does not exist")
            continue
        payload = json.loads(pointer_path.read_text(encoding="utf-8"))
        problem = _subset_problem(dirs, pointer_rel, payload)
        if problem:
            problems.append(problem)
    if not pointer_seen:
        # No reason carries a structured `evidence: analysis/evidence/<f>.json`
        # pointer -- nothing to resolve. Auto-pass; never invent a pointer.
        return
    assert not problems, "coverage-pointer resolution violations:\n" + "\n".join(problems)


# ---------------------------------------------------------------------------
# T019 -- per-PR selection for this mission's expanded test_dirs
# ---------------------------------------------------------------------------
def _expanded_test_dirs_modules(head: dict[str, Any], base: dict[str, Any]) -> dict[str, dict[str, Any]]:
    base_dirs = {row["module"]: set(row.get("test_dirs") or []) for row in _modules(base)}
    expanded: dict[str, dict[str, Any]] = {}
    for row in _modules(head):
        name = row["module"]
        added = set(row.get("test_dirs") or []) - base_dirs.get(name, set())
        if added:
            expanded[name] = {"added_test_dirs": sorted(added), "roots": list(row.get("roots") or [])}
    return expanded


def _root_probe_path(root: str) -> str:
    """A representative source path under a registry ``roots`` glob (source routing)."""
    stripped = root.rstrip("/")
    if stripped.endswith("/**"):
        return f"{stripped[:-3]}/synthetic_module.py"
    return stripped


def _selection_problems(module: str, info: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    for test_dir in info["added_test_dirs"]:
        synthetic_test = f"{test_dir}/synthetic_test.py"
        selected = select_modules([synthetic_test])
        if module not in selected:
            problems.append(f"{module}: test path {synthetic_test} does not select the owning module (got {sorted(selected)})")
    for root in info["roots"]:
        probe = _root_probe_path(root)
        selected = select_modules([probe])
        if module not in selected:
            problems.append(f"{module}: source path {probe} does not select the owning module (got {sorted(selected)})")
    return problems


def test_expanded_test_dirs_are_selected_per_pr() -> None:
    """A module row whose ``test_dirs`` this mission expanded (vs ``main``) is
    durably selected per-PR, for both a test-path change and a source-path change.

    Proves per-PR de-silencing re-runnably with zero net diff (Renata F3 / Paula
    F3), replacing the transient injected-red WP03 demonstrated live. Inert once
    the diff against ``main`` is empty (i.e. on ``main`` itself, post-merge) --
    this guard is about proving the mission's expansions route correctly while
    they are still a diff, not about asserting the mission is perpetually ongoing.
    """
    head = _load_registry()
    base = _base_registry()
    expanded = _expanded_test_dirs_modules(head, base)
    if not expanded:
        # Zero net diff vs main (e.g. running on main itself, post-merge) --
        # nothing this mission expanded to re-verify.
        return

    problems: list[str] = []
    for module, info in expanded.items():
        problems.extend(_selection_problems(module, info))
    assert not problems, "per-PR selection violations:\n" + "\n".join(problems)
