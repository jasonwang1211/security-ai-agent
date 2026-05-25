import json
import subprocess
import sys
from typing import Any, cast

from modules.graph.exporter import graph_snapshot_to_dict, graph_snapshot_to_json
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
    source = GraphSourceRef(
        source_type="incident",
        source_id="INC-001",
        field_path="findings",
        reason="Incident explicitly references this finding.",
    )
    return GraphSnapshot(
        nodes=[
            GraphNode(
                id="INC-001",
                kind=GraphNodeKind.INCIDENT,
                label="Incident",
                sources=[source],
            ),
            GraphNode(
                id="F-001",
                kind=GraphNodeKind.FINDING,
                label="Finding",
                metadata={"risk_level": "HIGH"},
                sources=[source],
            ),
        ],
        edges=[
            GraphEdge(
                id="EDGE-001",
                kind=GraphEdgeKind.HAS_FINDING,
                source_node_id="INC-001",
                target_node_id="F-001",
                sources=[source],
            ),
            GraphEdge(
                id="EDGE-002",
                kind=GraphEdgeKind.RELATED_TO,
                source_node_id="F-001",
                target_node_id="INC-001",
                sources=[source],
            ),
        ],
    )


def test_graph_snapshot_to_dict_returns_nodes_and_edges() -> None:
    exported = graph_snapshot_to_dict(make_snapshot())
    nodes = cast(list[dict[str, Any]], exported["nodes"])
    edges = cast(list[dict[str, Any]], exported["edges"])

    assert set(exported) == {"nodes", "edges"}
    assert len(nodes) == 2
    assert len(edges) == 2


def test_graph_snapshot_to_json_returns_valid_json_string() -> None:
    exported_json = graph_snapshot_to_json(make_snapshot())
    exported = json.loads(exported_json)

    assert isinstance(exported_json, str)
    assert exported["nodes"][0]["id"] == "INC-001"
    assert exported["edges"][0]["id"] == "EDGE-001"


def test_enum_values_serialize_as_strings() -> None:
    exported = graph_snapshot_to_dict(make_snapshot())
    nodes = cast(list[dict[str, Any]], exported["nodes"])
    edges = cast(list[dict[str, Any]], exported["edges"])

    assert nodes[0]["kind"] == "INCIDENT"
    assert edges[0]["kind"] == "HAS_FINDING"


def test_source_reason_metadata_is_preserved() -> None:
    exported = graph_snapshot_to_dict(make_snapshot())
    nodes = cast(list[dict[str, Any]], exported["nodes"])
    edges = cast(list[dict[str, Any]], exported["edges"])

    assert nodes[0]["sources"][0]["source_type"] == "incident"
    assert nodes[0]["sources"][0]["source_id"] == "INC-001"
    assert edges[0]["sources"][0]["reason"] == (
        "Incident explicitly references this finding."
    )


def test_node_and_edge_order_is_preserved() -> None:
    exported = graph_snapshot_to_dict(make_snapshot())
    nodes = cast(list[dict[str, Any]], exported["nodes"])
    edges = cast(list[dict[str, Any]], exported["edges"])

    assert [node["id"] for node in nodes] == ["INC-001", "F-001"]
    assert [edge["id"] for edge in edges] == ["EDGE-001", "EDGE-002"]


def test_empty_snapshot_exports_cleanly() -> None:
    exported = graph_snapshot_to_dict(GraphSnapshot())
    exported_json = json.loads(graph_snapshot_to_json(GraphSnapshot()))

    assert exported == {"nodes": [], "edges": []}
    assert exported_json == {"nodes": [], "edges": []}


def test_export_helpers_do_not_mutate_snapshot() -> None:
    snapshot = make_snapshot()
    before = snapshot.model_dump(mode="json")

    graph_snapshot_to_dict(snapshot)
    graph_snapshot_to_json(snapshot)

    assert snapshot.model_dump(mode="json") == before


def test_graph_exporter_import_does_not_load_runtime_heavy_modules() -> None:
    code = f"""
import importlib
import json
import sys

forbidden = {FORBIDDEN_RUNTIME_MODULES!r}

importlib.import_module("modules.graph.exporter")

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
