"""Always-on gate: every DRG mapping writer emits every declared field.

Lifted from ``tests/specify_cli/drg_writers/test_registry_completeness.py``
(mission ``doctrine-delivery-reachability``), a
``tests/specify_cli/drg_writers`` tree recorded ``out_of_matrix`` in
``.github/ci-module-registry.yml`` — no per-PR lane selects it (#4374
disposition ledger, disposition 2 — lift-invariant).

The DRG writer registry (``specify_cli.drg_writers.registry``) enumerates
every site that persists ``DRGNode``/``DRGEdge`` state, so a field added to a
model later cannot be silently dropped by a writer nobody remembered to
update. This pins the registry-completeness contract (W-1/W-1a): a
fully-populated node's declared fields, AND a genuinely novel field a writer
has never seen before, must both survive every registered mapping writer.
"""

from __future__ import annotations

import pytest
from pydantic import Field

from charter.offering.drg.migration import extractor
from charter.offering.drg.models import DRGNode, NodeKind
from specify_cli.drg_writers.registry import MAPPING_WRITERS

pytestmark = [pytest.mark.architectural]


def _full_node() -> DRGNode:
    return DRGNode(
        urn="anti_pattern:big-ball-of-mud",
        kind=NodeKind.ANTI_PATTERN,
        label="Big Ball of Mud",
        provenance="org:acme",
        tags=["smell"],
    )


def _expected_node_keys() -> set[str]:
    return set(DRGNode.model_fields) - extractor.FIELDS_WITHHELD_FROM_GRAPH_OUTPUT


class _NodeWithNovelFields(DRGNode):
    novel_scalar: str | None = "planted-node-value"
    novel_empty: list[str] = Field(default_factory=list)


def _mutated_node() -> _NodeWithNovelFields:
    return _NodeWithNovelFields(urn="anti_pattern:x", kind=NodeKind.ANTI_PATTERN, label="L", tags=["t"])


def test_every_mapping_writer_emits_every_declared_node_field() -> None:
    assert MAPPING_WRITERS  # non-empty, so the scan is not vacuous
    node = _full_node()
    for writer in MAPPING_WRITERS:
        emitted = set(writer.node_to_mapping(node))
        missing = _expected_node_keys() - emitted
        assert not missing, f"{writer.name} dropped node field(s) {missing}"


def test_every_mapping_writer_preserves_a_novel_node_field() -> None:
    """A field DRGEdge.__init__ never declared before still survives every writer."""
    node = _mutated_node()
    for writer in MAPPING_WRITERS:
        emitted = set(writer.node_to_mapping(node))
        assert "novel_scalar" in emitted, f"{writer.name} dropped novel_scalar"
        assert "novel_empty" in emitted, f"{writer.name} dropped novel_empty (the empty-value hole, W-1a)"
