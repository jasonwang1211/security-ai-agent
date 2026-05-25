import subprocess
import sys

import pytest

from modules.graph.lookup import (
    find_nodes_by_kind,
    get_edges_for_node,
    get_incident_context,
    get_neighbors,
    get_node,
    get_related_findings,
    get_related_rules,
)
from modules.graph.types import GraphEdge, GraphEdgeKind, GraphNode, GraphNodeKind, GraphSnapshot


FORBIDDEN_RUNTIME_MODULES = [
    "app",
    "modules.rag_qa",
    "modules.rag_query_planner",
    "modules.detector",
    "modules.triage_policy",
    "modules.controller.agent",
    "modules.controller_agent",
    "chromadb",
    "ollama",
    "langchain",
    "torch",
    "sentence_transformers",
]


def make_snapshot() -> GraphSnapshot:
    return GraphSnapshot(
        nodes=[
            GraphNode(id="INC-001", kind=GraphNodeKind.INCIDENT, label="Incident"),
            GraphNode(id="EV-001", kind=GraphNodeKind.EVIDENCE, label="Evidence"),
            GraphNode(id="F-001", kind=GraphNodeKind.FINDING, label="Finding"),
            GraphNode(id="RISK_LEVEL:HIGH", kind=GraphNodeKind.RISK_LEVEL, label="HIGH"),
            GraphNode(id="DECISION:BLOCK", kind=GraphNodeKind.DECISION, label="BLOCK"),
            GraphNode(
                id="DETECTION_RULE:CMD-001",
                kind=GraphNodeKind.DETECTION_RULE,
                label="Command Injection Rule",
            ),
            GraphNode(
                id="ATTACK_TYPE:Command Injection",
                kind=GraphNodeKind.ATTACK_TYPE,
                label="Command Injection",
            ),
            GraphNode(id="EV-ORPHAN", kind=GraphNodeKind.EVIDENCE, label="Orphan Evidence"),
        ],
        edges=[
            GraphEdge(
                id="E1",
                kind=GraphEdgeKind.HAS_EVIDENCE,
                source_node_id="INC-001",
                target_node_id="EV-001",
            ),
            GraphEdge(
                id="E2",
                kind=GraphEdgeKind.HAS_FINDING,
                source_node_id="INC-001",
                target_node_id="F-001",
            ),
            GraphEdge(
                id="E3",
                kind=GraphEdgeKind.SUPPORTED_BY,
                source_node_id="F-001",
                target_node_id="EV-001",
            ),
            GraphEdge(
                id="E4",
                kind=GraphEdgeKind.HAS_RISK_LEVEL,
                source_node_id="INC-001",
                target_node_id="RISK_LEVEL:HIGH",
            ),
            GraphEdge(
                id="E5",
                kind=GraphEdgeKind.HAS_DECISION,
                source_node_id="INC-001",
                target_node_id="DECISION:BLOCK",
            ),
            GraphEdge(
                id="E6",
                kind=GraphEdgeKind.MAPS_TO_RULE,
                source_node_id="F-001",
                target_node_id="DETECTION_RULE:CMD-001",
            ),
            GraphEdge(
                id="E7",
                kind=GraphEdgeKind.RELATED_TO_ATTACK,
                source_node_id="F-001",
                target_node_id="ATTACK_TYPE:Command Injection",
            ),
            GraphEdge(
                id="E8",
                kind=GraphEdgeKind.DETECTS,
                source_node_id="DETECTION_RULE:CMD-001",
                target_node_id="ATTACK_TYPE:Command Injection",
            ),
        ],
    )


def test_get_node_returns_node_or_none() -> None:
    snapshot = make_snapshot()

    assert get_node(snapshot, "INC-001").kind == GraphNodeKind.INCIDENT
    assert get_node(snapshot, "MISSING") is None


def test_get_neighbors_returns_direct_incoming_and_outgoing_neighbors() -> None:
    snapshot = make_snapshot()

    neighbors = get_neighbors(snapshot, "F-001")

    assert [node.id for node in neighbors] == [
        "INC-001",
        "EV-001",
        "DETECTION_RULE:CMD-001",
        "ATTACK_TYPE:Command Injection",
    ]


def test_get_edges_for_node_returns_incoming_and_outgoing_edges() -> None:
    snapshot = make_snapshot()

    edges = get_edges_for_node(snapshot, "F-001")

    assert [edge.id for edge in edges] == ["E2", "E3", "E6", "E7"]


def test_find_nodes_by_kind_filters_by_graph_node_kind() -> None:
    snapshot = make_snapshot()

    evidence_nodes = find_nodes_by_kind(snapshot, GraphNodeKind.EVIDENCE)

    assert [node.id for node in evidence_nodes] == ["EV-001", "EV-ORPHAN"]


def test_get_related_findings_returns_findings_supported_by_evidence() -> None:
    snapshot = make_snapshot()

    findings = get_related_findings(snapshot, "EV-001")

    assert [node.id for node in findings] == ["F-001"]


def test_get_related_rules_returns_rules_mapped_from_finding() -> None:
    snapshot = make_snapshot()

    rules = get_related_rules(snapshot, "F-001")

    assert [node.id for node in rules] == ["DETECTION_RULE:CMD-001"]


def test_get_incident_context_returns_small_edge_driven_summary() -> None:
    snapshot = make_snapshot()

    context = get_incident_context(snapshot, "INC-001")

    assert context["incident"] == get_node(snapshot, "INC-001")
    assert [node.id for node in context["evidence"]] == ["EV-001"]
    assert [node.id for node in context["findings"]] == ["F-001"]
    assert context["risk_level"] == get_node(snapshot, "RISK_LEVEL:HIGH")
    assert context["decision"] == get_node(snapshot, "DECISION:BLOCK")
    assert [node.id for node in context["rules"]] == ["DETECTION_RULE:CMD-001"]
    assert [node.id for node in context["attack_types"]] == ["ATTACK_TYPE:Command Injection"]


def test_missing_ids_return_safe_empty_results() -> None:
    snapshot = make_snapshot()

    assert get_neighbors(snapshot, "MISSING") == []
    assert get_edges_for_node(snapshot, "MISSING") == []
    assert get_related_findings(snapshot, "MISSING") == []
    assert get_related_rules(snapshot, "MISSING") == []
    assert get_incident_context(snapshot, "MISSING") == {
        "incident": None,
        "evidence": [],
        "findings": [],
        "risk_level": None,
        "decision": None,
        "rules": [],
        "attack_types": [],
    }


@pytest.mark.parametrize(
    ("func", "args"),
    [
        (get_node, (" ",)),
        (get_neighbors, (" ",)),
        (get_edges_for_node, (" ",)),
        (get_related_findings, (" ",)),
        (get_related_rules, (" ",)),
        (get_incident_context, (" ",)),
    ],
)
def test_blank_ids_raise_value_error(func, args) -> None:
    with pytest.raises(ValueError):
        func(make_snapshot(), *args)


def test_lookup_helpers_do_not_mutate_snapshot() -> None:
    snapshot = make_snapshot()
    before = snapshot.model_dump(mode="json")

    get_node(snapshot, "INC-001")
    get_neighbors(snapshot, "F-001")
    get_edges_for_node(snapshot, "F-001")
    find_nodes_by_kind(snapshot, GraphNodeKind.EVIDENCE)
    get_related_findings(snapshot, "EV-001")
    get_related_rules(snapshot, "F-001")
    get_incident_context(snapshot, "INC-001")

    assert snapshot.model_dump(mode="json") == before


def test_graph_lookup_import_does_not_load_runtime_heavy_modules() -> None:
    code = f"""
import importlib
import json
import sys

forbidden = {FORBIDDEN_RUNTIME_MODULES!r}

importlib.import_module("modules.graph.lookup")

loaded = [
    name for name in forbidden
    if name in sys.modules or any(mod.startswith(name + ".") for mod in sys.modules)
]

print(json.dumps(loaded))
raise SystemExit(1 if loaded else 0)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
