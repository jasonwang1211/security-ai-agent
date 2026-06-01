import subprocess
import sys

from modules.graph.explainers import explain_graph_reference
from modules.graph.types import (
    GraphEdge,
    GraphEdgeKind,
    GraphNode,
    GraphNodeKind,
    GraphSnapshot,
    GraphSourceRef,
)


FORBIDDEN_RUNTIME_MODULES = [
    "app",
    "modules.rag_qa",
    "chromadb",
    "ollama",
    "langchain",
    "torch",
    "sentence_transformers",
]


def make_source_ref() -> GraphSourceRef:
    return GraphSourceRef(
        source_type="incident",
        source_id="INC-001",
        field_path="findings[0].evidence_ids",
        reason="Finding explicitly references evidence.",
    )


def make_snapshot(include_relationships: bool = True) -> GraphSnapshot:
    edges = [
        GraphEdge(
            id="EDGE:HAS_EVIDENCE:INC-001->EV-003",
            kind=GraphEdgeKind.HAS_EVIDENCE,
            source_node_id="INC-001",
            target_node_id="EV-003",
            sources=[make_source_ref()],
        ),
        GraphEdge(
            id="EDGE:HAS_FINDING:INC-001->F-001",
            kind=GraphEdgeKind.HAS_FINDING,
            source_node_id="INC-001",
            target_node_id="F-001",
            sources=[make_source_ref()],
        ),
        GraphEdge(
            id="EDGE:HAS_RISK_LEVEL:INC-001->RISK_LEVEL:HIGH",
            kind=GraphEdgeKind.HAS_RISK_LEVEL,
            source_node_id="INC-001",
            target_node_id="RISK_LEVEL:HIGH",
            sources=[make_source_ref()],
        ),
        GraphEdge(
            id="EDGE:HAS_DECISION:INC-001->DECISION:MONITOR",
            kind=GraphEdgeKind.HAS_DECISION,
            source_node_id="INC-001",
            target_node_id="DECISION:MONITOR",
            sources=[make_source_ref()],
        ),
    ]
    if include_relationships:
        edges.extend(
            [
                GraphEdge(
                    id="EDGE:SUPPORTED_BY:F-001->EV-003",
                    kind=GraphEdgeKind.SUPPORTED_BY,
                    source_node_id="F-001",
                    target_node_id="EV-003",
                    sources=[make_source_ref()],
                ),
                GraphEdge(
                    id="EDGE:MAPS_TO_RULE:F-001->DETECTION_RULE:CMD-001",
                    kind=GraphEdgeKind.MAPS_TO_RULE,
                    source_node_id="F-001",
                    target_node_id="DETECTION_RULE:CMD-001",
                    sources=[make_source_ref()],
                ),
                GraphEdge(
                    id="EDGE:RELATED_TO_ATTACK:F-001->ATTACK_TYPE:Command Injection",
                    kind=GraphEdgeKind.RELATED_TO_ATTACK,
                    source_node_id="F-001",
                    target_node_id="ATTACK_TYPE:Command Injection",
                    sources=[make_source_ref()],
                ),
                GraphEdge(
                    id="EDGE:DETECTS:DETECTION_RULE:CMD-001->ATTACK_TYPE:Command Injection",
                    kind=GraphEdgeKind.DETECTS,
                    source_node_id="DETECTION_RULE:CMD-001",
                    target_node_id="ATTACK_TYPE:Command Injection",
                    sources=[make_source_ref()],
                ),
            ]
        )
    return GraphSnapshot(
        nodes=[
            GraphNode(id="INC-001", kind=GraphNodeKind.INCIDENT, label="Incident"),
            GraphNode(id="EV-003", kind=GraphNodeKind.EVIDENCE, label="Successful login after failures"),
            GraphNode(id="F-001", kind=GraphNodeKind.FINDING, label="Possible account compromise"),
            GraphNode(id="RISK_LEVEL:HIGH", kind=GraphNodeKind.RISK_LEVEL, label="HIGH"),
            GraphNode(id="DECISION:MONITOR", kind=GraphNodeKind.DECISION, label="MONITOR"),
            GraphNode(
                id="DETECTION_RULE:CMD-001",
                kind=GraphNodeKind.DETECTION_RULE,
                label="Command injection rule",
            ),
            GraphNode(
                id="ATTACK_TYPE:Command Injection",
                kind=GraphNodeKind.ATTACK_TYPE,
                label="Command Injection",
            ),
        ],
        edges=edges,
    )


def test_ev_reference_explains_explicit_supported_finding() -> None:
    answer = explain_graph_reference(make_snapshot(), "EV-003")

    assert answer.confidence == "HIGH"
    assert "EV-003" in answer.answer
    assert "F-001" in answer.answer
    assert answer.evidence_ids == ["EV-003"]
    assert answer.finding_ids == ["F-001"]


def test_finding_reference_explains_evidence_rule_and_attack_type_relationships() -> None:
    answer = explain_graph_reference(make_snapshot(), "F-001")

    assert "EV-003" in answer.answer
    assert "CMD-001" in answer.answer
    assert "Command Injection" in answer.answer
    assert answer.evidence_ids == ["EV-003"]
    assert answer.finding_ids == ["F-001"]
    assert answer.rule_ids == ["CMD-001"]


def test_rule_reference_resolves_detection_rule_and_related_edges() -> None:
    answer = explain_graph_reference(make_snapshot(), "CMD-001")

    assert "DETECTION_RULE:CMD-001" in answer.answer
    assert "F-001" in answer.answer
    assert "Command Injection" in answer.answer
    assert answer.finding_ids == ["F-001"]
    assert answer.rule_ids == ["CMD-001"]


def test_prefixed_rule_reference_returns_stable_rule_id() -> None:
    answer = explain_graph_reference(make_snapshot(), "DETECTION_RULE:CMD-001")

    assert "DETECTION_RULE:CMD-001" in answer.answer
    assert "F-001" in answer.answer
    assert "Command Injection" in answer.answer
    assert answer.finding_ids == ["F-001"]
    assert answer.rule_ids == ["CMD-001"]


def test_incident_reference_summarizes_explicit_one_hop_context() -> None:
    answer = explain_graph_reference(make_snapshot(), "INC-001")

    assert "INC-001" in answer.answer
    assert "1 explicit evidence" in answer.answer
    assert "1 explicit finding" in answer.answer
    assert "MONITOR" in answer.answer
    assert answer.evidence_ids == ["EV-003"]
    assert answer.finding_ids == ["F-001"]


def test_missing_existing_edge_does_not_create_guessed_relationship() -> None:
    answer = explain_graph_reference(make_snapshot(include_relationships=False), "EV-003")

    assert answer.confidence == "LOW"
    assert "No explicit Finding" in answer.answer
    assert answer.finding_ids == []
    assert answer.sources[0].source == "graph:EV-003"


def test_missing_reference_returns_low_confidence_without_graph_citation() -> None:
    answer = explain_graph_reference(make_snapshot(), "EV-999")

    assert answer.confidence == "LOW"
    assert answer.limitations
    assert answer.sources[0].source == "insufficient_graph_context"
    assert not answer.sources[0].source.startswith("graph:")


def test_source_citation_metadata_preserves_graph_provenance() -> None:
    answer = explain_graph_reference(make_snapshot(), "EV-003")

    citation = answer.sources[0]

    assert citation.source == "graph:EDGE:SUPPORTED_BY:F-001->EV-003"
    assert citation.metadata["edge"]["kind"] == "SUPPORTED_BY"
    assert citation.metadata["source_node"]["id"] == "F-001"
    assert citation.metadata["target_node"]["id"] == "EV-003"
    assert citation.metadata["edge"]["sources"][0]["reason"] == "Finding explicitly references evidence."


def test_graph_explainer_import_does_not_load_runtime_heavy_modules() -> None:
    code = f"""
import importlib
import json
import sys

forbidden = {FORBIDDEN_RUNTIME_MODULES!r}

importlib.import_module("modules.graph.explainers")

loaded = [
    name for name in forbidden
    if name in sys.modules or any(module.startswith(name + ".") for module in sys.modules)
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
