import json
import subprocess
import sys

from modules.detection_rules import DetectionRule
from modules.graph.builder import build_graph_snapshot
from modules.graph.types import GraphEdgeKind, GraphNodeKind, GraphSnapshot
from modules.types import EvidenceBundle, EvidenceItem, Finding, Incident


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


def make_detection_rule(rule_id: str = "CMD-001") -> DetectionRule:
    return DetectionRule(
        id=rule_id,
        title="Command injection payload",
        attack_type="Command Injection",
        severity="HIGH",
        confidence=0.9,
        patterns=["; rm "],
        source_path="detections/blue_team/command_injection.yml",
    )


def make_incident(
    *,
    evidence_ids: list[str] | None = None,
    attack_type: str | None = "Command Injection",
    metadata: dict[str, object] | None = None,
) -> Incident:
    evidence = EvidenceItem(
        id="EV-001",
        type="matched_signature",
        description="A structured detector signature matched.",
        value={"pattern": "; rm "},
    )
    finding = Finding(
        id="F-001",
        finding_type="payload_alert",
        title="Suspicious payload detected",
        status="ALERT",
        risk_level="HIGH",
        decision="BLOCK",
        attack_type=attack_type,
        evidence_ids=evidence_ids if evidence_ids is not None else ["EV-001"],
        summary="CMD-001 appears in free text but should not be scanned.",
        metadata=metadata or {},
    )
    return Incident(
        id="INC-20260525-001",
        title="Suspicious payload incident",
        status="ALERT",
        risk_level="HIGH",
        decision="BLOCK",
        findings=[finding],
        evidence_bundle=EvidenceBundle(incident_id="INC-20260525-001", items=[evidence]),
    )


def node_ids(snapshot: GraphSnapshot) -> set[str]:
    return {node.id for node in snapshot.nodes}


def edge_pairs(snapshot: GraphSnapshot) -> set[tuple[GraphEdgeKind, str, str]]:
    return {(edge.kind, edge.source_node_id, edge.target_node_id) for edge in snapshot.edges}


def test_builds_incident_evidence_and_finding_nodes_from_structured_input() -> None:
    snapshot = build_graph_snapshot(make_incident())

    nodes_by_id = {node.id: node for node in snapshot.nodes}

    assert nodes_by_id["INC-20260525-001"].kind == GraphNodeKind.INCIDENT
    assert nodes_by_id["EV-001"].kind == GraphNodeKind.EVIDENCE
    assert nodes_by_id["F-001"].kind == GraphNodeKind.FINDING


def test_builds_has_evidence_and_has_finding_edges() -> None:
    snapshot = build_graph_snapshot(make_incident())

    assert (
        GraphEdgeKind.HAS_EVIDENCE,
        "INC-20260525-001",
        "EV-001",
    ) in edge_pairs(snapshot)
    assert (
        GraphEdgeKind.HAS_FINDING,
        "INC-20260525-001",
        "F-001",
    ) in edge_pairs(snapshot)


def test_builds_supported_by_only_for_explicit_existing_evidence_references() -> None:
    snapshot = build_graph_snapshot(make_incident(evidence_ids=["EV-001", "EV-999"]))

    pairs = edge_pairs(snapshot)

    assert (GraphEdgeKind.SUPPORTED_BY, "F-001", "EV-001") in pairs
    assert (GraphEdgeKind.SUPPORTED_BY, "F-001", "EV-999") not in pairs
    assert "EV-999" not in node_ids(snapshot)


def test_does_not_build_guessed_supported_by_edges_when_references_are_missing() -> None:
    snapshot = build_graph_snapshot(make_incident(evidence_ids=[]))

    assert all(edge.kind != GraphEdgeKind.SUPPORTED_BY for edge in snapshot.edges)


def test_builds_risk_level_and_decision_from_explicit_incident_fields() -> None:
    snapshot = build_graph_snapshot(make_incident())

    assert "RISK_LEVEL:HIGH" in node_ids(snapshot)
    assert "DECISION:BLOCK" in node_ids(snapshot)
    assert (
        GraphEdgeKind.HAS_RISK_LEVEL,
        "INC-20260525-001",
        "RISK_LEVEL:HIGH",
    ) in edge_pairs(snapshot)
    assert (
        GraphEdgeKind.HAS_DECISION,
        "INC-20260525-001",
        "DECISION:BLOCK",
    ) in edge_pairs(snapshot)


def test_builds_attack_type_relationship_from_explicit_finding_field() -> None:
    snapshot = build_graph_snapshot(make_incident())

    assert "ATTACK_TYPE:Command Injection" in node_ids(snapshot)
    assert (
        GraphEdgeKind.RELATED_TO_ATTACK,
        "F-001",
        "ATTACK_TYPE:Command Injection",
    ) in edge_pairs(snapshot)


def test_builds_rule_relationships_only_from_explicit_metadata_and_passed_rules() -> None:
    snapshot = build_graph_snapshot(
        make_incident(metadata={"rule_id": "CMD-001"}),
        detection_rules=[make_detection_rule("CMD-001")],
    )

    assert "DETECTION_RULE:CMD-001" in node_ids(snapshot)
    assert (
        GraphEdgeKind.MAPS_TO_RULE,
        "F-001",
        "DETECTION_RULE:CMD-001",
    ) in edge_pairs(snapshot)
    assert (
        GraphEdgeKind.DETECTS,
        "DETECTION_RULE:CMD-001",
        "ATTACK_TYPE:Command Injection",
    ) in edge_pairs(snapshot)


def test_does_not_infer_rule_ids_from_free_text_or_create_rules_without_passed_rule() -> None:
    no_metadata = build_graph_snapshot(
        make_incident(metadata={}),
        detection_rules=[make_detection_rule("CMD-001")],
    )
    no_passed_rule = build_graph_snapshot(
        make_incident(metadata={"rule_ids": ["CMD-001"]}),
        detection_rules=[],
    )

    assert all(edge.kind != GraphEdgeKind.MAPS_TO_RULE for edge in no_metadata.edges)
    assert "DETECTION_RULE:CMD-001" in node_ids(no_metadata)
    assert all(edge.kind != GraphEdgeKind.MAPS_TO_RULE for edge in no_passed_rule.edges)
    assert "DETECTION_RULE:CMD-001" not in node_ids(no_passed_rule)


def test_every_edge_includes_source_and_reason() -> None:
    snapshot = build_graph_snapshot(
        make_incident(metadata={"rule_ids": ["CMD-001"]}),
        detection_rules=[make_detection_rule()],
    )

    assert snapshot.edges
    for edge in snapshot.edges:
        assert edge.sources
        assert edge.sources[0].source_type
        assert edge.sources[0].source_id
        assert edge.sources[0].reason


def test_builder_output_is_graph_snapshot_and_json_serializable() -> None:
    snapshot = build_graph_snapshot(make_incident())
    dumped = json.loads(snapshot.model_dump_json())

    assert isinstance(snapshot, GraphSnapshot)
    assert dumped["nodes"]
    assert dumped["edges"]


def test_builder_does_not_mutate_input() -> None:
    incident = make_incident(metadata={"rule_ids": ["CMD-001"]})
    rule = make_detection_rule()
    before_incident = incident.model_dump(mode="json")
    before_rule = rule.model_dump(mode="json")

    build_graph_snapshot(incident, detection_rules=[rule])

    assert incident.model_dump(mode="json") == before_incident
    assert rule.model_dump(mode="json") == before_rule


def test_graph_builder_import_does_not_load_runtime_heavy_modules() -> None:
    code = f"""
import importlib
import json
import sys

forbidden = {FORBIDDEN_RUNTIME_MODULES!r}

importlib.import_module("modules.graph.builder")

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
