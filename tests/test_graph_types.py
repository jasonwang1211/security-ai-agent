import json
import subprocess
import sys
from typing import Any, cast

import pytest
from pydantic import ValidationError

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
    "modules.detector",
    "modules.controller.agent",
    "modules.controller_agent",
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
        reason="Finding references evidence EV-001.",
    )


def make_node() -> GraphNode:
    return GraphNode(
        id="INC-001",
        kind=GraphNodeKind.INCIDENT,
        label="Command injection incident",
        metadata={"risk_level": "HIGH"},
        sources=[make_source_ref()],
    )


def make_edge() -> GraphEdge:
    return GraphEdge(
        id="EDGE-001",
        kind=GraphEdgeKind.HAS_EVIDENCE,
        source_node_id="INC-001",
        target_node_id="EV-001",
        label="has evidence",
        metadata={"confidence": "HIGH"},
        sources=[make_source_ref()],
    )


def test_required_first_pass_node_kinds_exist() -> None:
    expected = {
        "INCIDENT",
        "EVIDENCE",
        "FINDING",
        "DETECTION_RULE",
        "ATTACK_TYPE",
        "KNOWLEDGE_DOC",
        "RISK_LEVEL",
        "DECISION",
    }

    assert expected.issubset({kind.value for kind in GraphNodeKind})


def test_deferred_node_kinds_exist_as_enum_values_only() -> None:
    expected = {"MITRE_TECHNIQUE", "SECURITY_CONTROL", "RESPONSE_PLAYBOOK"}

    assert expected.issubset({kind.value for kind in GraphNodeKind})


def test_required_first_pass_edge_kinds_exist() -> None:
    expected = {
        "HAS_EVIDENCE",
        "HAS_FINDING",
        "SUPPORTED_BY",
        "MAPS_TO_RULE",
        "DETECTS",
        "RELATED_TO_ATTACK",
        "HAS_RISK_LEVEL",
        "HAS_DECISION",
        "REFERENCES_DOC",
        "RELATED_TO",
    }

    assert expected.issubset({kind.value for kind in GraphEdgeKind})


def test_deferred_edge_kinds_exist_as_enum_values_only() -> None:
    expected = {"MAPS_TO_MITRE", "MITIGATED_BY", "HAS_PLAYBOOK"}

    assert expected.issubset({kind.value for kind in GraphEdgeKind})


def test_graph_node_can_be_created_and_serialized() -> None:
    node = make_node()

    dumped = node.model_dump()
    dumped_json = json.loads(node.model_dump_json())

    assert dumped["id"] == "INC-001"
    assert dumped["kind"] == GraphNodeKind.INCIDENT
    assert dumped_json["kind"] == "INCIDENT"
    assert dumped_json["metadata"]["risk_level"] == "HIGH"
    assert dumped_json["sources"][0]["reason"] == "Finding references evidence EV-001."


def test_graph_edge_can_be_created_and_serialized_with_source_reason_metadata() -> None:
    edge = make_edge()

    dumped = edge.model_dump()
    dumped_json = json.loads(edge.model_dump_json())

    assert dumped["kind"] == GraphEdgeKind.HAS_EVIDENCE
    assert dumped_json["kind"] == "HAS_EVIDENCE"
    assert dumped_json["source_node_id"] == "INC-001"
    assert dumped_json["target_node_id"] == "EV-001"
    assert dumped_json["sources"][0]["field_path"] == "findings[0].evidence_ids"
    assert dumped_json["sources"][0]["reason"] == "Finding references evidence EV-001."


def test_graph_snapshot_holds_nodes_and_edges_as_json_serializable_data() -> None:
    snapshot = GraphSnapshot(nodes=[make_node()], edges=[make_edge()])
    dumped_json = json.loads(snapshot.model_dump_json())

    assert dumped_json["nodes"][0]["id"] == "INC-001"
    assert dumped_json["edges"][0]["id"] == "EDGE-001"


def test_default_factories_create_independent_collections() -> None:
    first_node = GraphNode(id="NODE-1", kind=GraphNodeKind.INCIDENT, label="First")
    second_node = GraphNode(id="NODE-2", kind=GraphNodeKind.INCIDENT, label="Second")
    first_node.metadata["risk_level"] = "HIGH"
    first_node.sources.append(make_source_ref())

    assert second_node.metadata == {}
    assert second_node.sources == []

    first_edge = GraphEdge(
        id="EDGE-1",
        kind=GraphEdgeKind.HAS_EVIDENCE,
        source_node_id="NODE-1",
        target_node_id="EV-1",
    )
    second_edge = GraphEdge(
        id="EDGE-2",
        kind=GraphEdgeKind.HAS_EVIDENCE,
        source_node_id="NODE-2",
        target_node_id="EV-2",
    )
    first_edge.metadata["confidence"] = "HIGH"
    first_edge.sources.append(make_source_ref())

    assert second_edge.metadata == {}
    assert second_edge.sources == []

    first_snapshot = GraphSnapshot()
    second_snapshot = GraphSnapshot()
    first_snapshot.nodes.append(first_node)
    first_snapshot.edges.append(first_edge)

    assert second_snapshot.nodes == []
    assert second_snapshot.edges == []


def test_invalid_node_and_edge_enum_values_are_rejected() -> None:
    with pytest.raises(ValidationError):
        GraphNode(id="INC-001", kind=cast(Any, "UNKNOWN"), label="Unknown")

    with pytest.raises(ValidationError):
        GraphEdge(
            id="EDGE-001",
            kind=cast(Any, "UNKNOWN"),
            source_node_id="INC-001",
            target_node_id="EV-001",
        )


def test_blank_required_ids_labels_and_source_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        GraphSourceRef(source_type=" ", source_id="INC-001")

    with pytest.raises(ValidationError):
        GraphSourceRef(source_type="incident", source_id=" ")

    with pytest.raises(ValidationError):
        GraphNode(id=" ", kind=GraphNodeKind.INCIDENT, label="Incident")

    with pytest.raises(ValidationError):
        GraphNode(id="INC-001", kind=GraphNodeKind.INCIDENT, label=" ")

    with pytest.raises(ValidationError):
        GraphEdge(
            id=" ",
            kind=GraphEdgeKind.HAS_EVIDENCE,
            source_node_id="INC-001",
            target_node_id="EV-001",
        )

    with pytest.raises(ValidationError):
        GraphEdge(
            id="EDGE-001",
            kind=GraphEdgeKind.HAS_EVIDENCE,
            source_node_id=" ",
            target_node_id="EV-001",
        )

    with pytest.raises(ValidationError):
        GraphEdge(
            id="EDGE-001",
            kind=GraphEdgeKind.HAS_EVIDENCE,
            source_node_id="INC-001",
            target_node_id=" ",
        )


def test_blank_optional_text_fields_are_rejected_when_provided() -> None:
    with pytest.raises(ValidationError):
        GraphSourceRef(source_type="incident", source_id="INC-001", field_path=" ")

    with pytest.raises(ValidationError):
        GraphSourceRef(source_type="incident", source_id="INC-001", reason=" ")

    with pytest.raises(ValidationError):
        GraphEdge(
            id="EDGE-001",
            kind=GraphEdgeKind.HAS_EVIDENCE,
            source_node_id="INC-001",
            target_node_id="EV-001",
            label=" ",
        )


def assert_import_stays_lightweight(module_name: str) -> None:
    code = f"""
import importlib
import json
import sys

forbidden = {FORBIDDEN_RUNTIME_MODULES!r}

importlib.import_module({module_name!r})

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


def test_graph_types_import_does_not_load_runtime_heavy_modules() -> None:
    assert_import_stays_lightweight("modules.graph.types")


def test_graph_package_import_stays_lightweight() -> None:
    assert_import_stays_lightweight("modules.graph")
