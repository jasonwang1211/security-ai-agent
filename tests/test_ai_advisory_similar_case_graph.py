"""Focused tests for the v2.9 advisory similar-case -> GraphSnapshot adapter."""

from dataclasses import dataclass

from modules.ai_advisory.similar_case_graph import (
    CURRENT_CONTEXT_NODE_ID,
    build_similar_case_graph_snapshot,
)
from modules.graph.types import GraphEdgeKind, GraphNodeKind, GraphSnapshot


@dataclass
class _Seed:
    case_id: str
    title: str


@dataclass
class _Match:
    seed: _Seed


@dataclass
class _Current:
    context_kind: str


@dataclass
class _Result:
    current: _Current
    matches: tuple


def test_none_or_empty_matches_returns_none() -> None:
    assert build_similar_case_graph_snapshot(None) is None
    assert build_similar_case_graph_snapshot(_Result(_Current("active_event"), ())) is None


def test_builds_structured_snapshot_from_matches() -> None:
    result = _Result(
        current=_Current("active_event"),
        matches=(_Match(_Seed("CASE-SEED-001", "Command Injection Payload")),),
    )

    snapshot = build_similar_case_graph_snapshot(result)

    assert isinstance(snapshot, GraphSnapshot)
    node_ids = [node.id for node in snapshot.nodes]
    assert CURRENT_CONTEXT_NODE_ID in node_ids
    assert "CASE-SEED-001" in node_ids
    assert all(node.kind == GraphNodeKind.INCIDENT for node in snapshot.nodes)

    assert len(snapshot.edges) == 1
    edge = snapshot.edges[0]
    assert edge.source_node_id == CURRENT_CONTEXT_NODE_ID
    assert edge.target_node_id == "CASE-SEED-001"
    assert edge.kind == GraphEdgeKind.RELATED_TO

    current_node = next(node for node in snapshot.nodes if node.id == CURRENT_CONTEXT_NODE_ID)
    assert current_node.label == "Current Event"


def test_incident_context_label_and_dedup() -> None:
    result = _Result(
        current=_Current("active_auth_incident"),
        matches=(
            _Match(_Seed("CASE-SEED-002", "Auth Incident")),
            _Match(_Seed("CASE-SEED-002", "Auth Incident")),  # duplicate id is collapsed
        ),
    )

    snapshot = build_similar_case_graph_snapshot(result)

    assert snapshot is not None
    assert [node.id for node in snapshot.nodes] == [CURRENT_CONTEXT_NODE_ID, "CASE-SEED-002"]
    assert len(snapshot.edges) == 1
    current_node = next(node for node in snapshot.nodes if node.id == CURRENT_CONTEXT_NODE_ID)
    assert current_node.label == "Current Incident"


def test_blank_case_ids_are_skipped() -> None:
    result = _Result(
        current=_Current("active_event"),
        matches=(_Match(_Seed("", "no id")),),
    )

    assert build_similar_case_graph_snapshot(result) is None
