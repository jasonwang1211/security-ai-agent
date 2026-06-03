import json
import subprocess
import sys

import pytest

from modules.detection_rules import DetectionRule
from modules.graph.knowledge_doc_seed import build_knowledge_doc_seed
from modules.graph.types import GraphEdgeKind, GraphNodeKind
from modules.rag.metadata import KnowledgeDocMetadata


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


def make_rule(
    rule_id: str = "DEMO-001",
    attack_type: str = "Demo Attack",
) -> DetectionRule:
    return DetectionRule(
        id=rule_id,
        title=f"{attack_type} Rule",
        attack_type=attack_type,
        severity="HIGH",
        confidence=0.9,
        patterns=["demo"],
        source_path=f"detections/{rule_id.lower()}.yml",
    )


def make_metadata(
    doc_id: str = "report.demo_explainer",
    attack_types: list[str] | None = None,
    rule_ids: list[str] | None = None,
) -> KnowledgeDocMetadata:
    return KnowledgeDocMetadata(
        doc_id=doc_id,
        doc_type="report_explainer",
        title="Demo Explainer",
        review_status="approved_for_runtime_promotion",
        attack_types=["Demo Attack"] if attack_types is None else attack_types,
        rule_ids=["DEMO-001"] if rule_ids is None else rule_ids,
        source_path=f"knowledge/{doc_id}.md",
    )


def test_validated_arbitrary_knowledge_doc_creates_expected_seed_shape() -> None:
    metadata = make_metadata()
    rule = make_rule()

    snapshot = build_knowledge_doc_seed([metadata], [rule])

    assert [node.kind for node in snapshot.nodes] == [
        GraphNodeKind.KNOWLEDGE_DOC,
        GraphNodeKind.ATTACK_TYPE,
        GraphNodeKind.DETECTION_RULE,
    ]
    assert {node.id for node in snapshot.nodes} == {
        "KNOWLEDGE_DOC:report.demo_explainer",
        "ATTACK_TYPE:Demo Attack",
        "DETECTION_RULE:DEMO-001",
    }
    assert [edge.kind for edge in snapshot.edges] == [
        GraphEdgeKind.RELATED_TO_ATTACK,
        GraphEdgeKind.MAPS_TO_RULE,
    ]
    assert {
        (edge.source_node_id, edge.target_node_id)
        for edge in snapshot.edges
    } == {
        ("KNOWLEDGE_DOC:report.demo_explainer", "ATTACK_TYPE:Demo Attack"),
        ("KNOWLEDGE_DOC:report.demo_explainer", "DETECTION_RULE:DEMO-001"),
    }


def test_seed_is_data_driven_and_does_not_hard_code_current_doc_ids() -> None:
    metadata = make_metadata(
        doc_id="report.custom_reviewed_rule_doc",
        attack_types=["Custom Attack"],
        rule_ids=["CUSTOM-123"],
    )
    rule = make_rule("CUSTOM-123", "Custom Attack")

    snapshot = build_knowledge_doc_seed([metadata], [rule])

    assert "KNOWLEDGE_DOC:report.custom_reviewed_rule_doc" in {node.id for node in snapshot.nodes}
    assert "DETECTION_RULE:CUSTOM-123" in {node.id for node in snapshot.nodes}


def test_authentication_style_retrieval_only_doc_creates_no_seed_output() -> None:
    metadata = make_metadata(
        doc_id="report.possible_account_compromise",
        attack_types=[],
        rule_ids=[],
    )

    snapshot = build_knowledge_doc_seed([metadata], [])

    assert snapshot.nodes == []
    assert snapshot.edges == []


def test_unapproved_seed_candidate_raises_value_error() -> None:
    metadata = make_metadata().model_copy(update={"review_status": "pending_human_review"})

    with pytest.raises(ValueError, match="not approved for graph seed promotion"):
        build_knowledge_doc_seed([metadata], [make_rule()])


def test_retrieval_only_doc_without_approved_status_creates_no_seed_output() -> None:
    metadata = make_metadata(
        doc_id="report.retrieval_only",
        attack_types=[],
        rule_ids=[],
    ).model_copy(update={"review_status": None})

    snapshot = build_knowledge_doc_seed([metadata], [make_rule()])

    assert snapshot.nodes == []
    assert snapshot.edges == []


def test_attack_types_without_rule_ids_raise_value_error() -> None:
    metadata = make_metadata(attack_types=["Demo Attack"], rule_ids=[])
    metadata = metadata.model_copy(update={"rule_ids": []})

    with pytest.raises(ValueError, match="attack_types but no rule_ids"):
        build_knowledge_doc_seed([metadata], [make_rule()])


def test_rule_ids_without_attack_types_raise_value_error() -> None:
    metadata = make_metadata(attack_types=[], rule_ids=["DEMO-001"])
    metadata = metadata.model_copy(update={"attack_types": []})

    with pytest.raises(ValueError, match="rule_ids but no attack_types"):
        build_knowledge_doc_seed([metadata], [make_rule()])


def test_unknown_rule_ids_raise_value_error() -> None:
    metadata = make_metadata(rule_ids=["MISSING-001"])

    with pytest.raises(ValueError, match="unknown rule_id MISSING-001"):
        build_knowledge_doc_seed([metadata], [make_rule()])


def test_attack_rule_mismatch_raises_value_error() -> None:
    metadata = make_metadata(attack_types=["Demo Attack"], rule_ids=["DEMO-001"])
    rule = make_rule("DEMO-001", "Different Attack")

    with pytest.raises(ValueError, match="does not match reviewed attack_types"):
        build_knowledge_doc_seed([metadata], [rule])


def test_attack_type_without_matching_rule_object_raises_value_error() -> None:
    metadata = make_metadata(
        attack_types=["Demo Attack", "Second Attack"],
        rule_ids=["DEMO-001"],
    )

    with pytest.raises(ValueError, match="lack matching DetectionRule"):
        build_knowledge_doc_seed([metadata], [make_rule()])


def test_graph_source_ref_provenance_is_preserved_on_nodes_and_edges() -> None:
    snapshot = build_knowledge_doc_seed([make_metadata()], [make_rule()])

    knowledge_node = next(node for node in snapshot.nodes if node.kind == GraphNodeKind.KNOWLEDGE_DOC)
    attack_edge = next(edge for edge in snapshot.edges if edge.kind == GraphEdgeKind.RELATED_TO_ATTACK)
    rule_edge = next(edge for edge in snapshot.edges if edge.kind == GraphEdgeKind.MAPS_TO_RULE)

    assert knowledge_node.sources[0].source_type == "knowledge_doc"
    assert knowledge_node.sources[0].source_id == "report.demo_explainer"
    assert knowledge_node.sources[0].field_path == "doc_id"
    assert attack_edge.sources[0].field_path == "frontmatter.attack_types"
    assert rule_edge.sources[0].field_path == "frontmatter.rule_ids"


def test_output_serializes_as_json_compatible_graph_snapshot_data() -> None:
    snapshot = build_knowledge_doc_seed([make_metadata()], [make_rule()])

    dumped = snapshot.model_dump(mode="json")

    assert json.loads(json.dumps(dumped)) == dumped


def test_inputs_are_not_mutated() -> None:
    metadata = make_metadata()
    rule = make_rule()
    before_metadata = metadata.model_dump(mode="json")
    before_rule = rule.model_dump(mode="json")

    build_knowledge_doc_seed([metadata], [rule])

    assert metadata.model_dump(mode="json") == before_metadata
    assert rule.model_dump(mode="json") == before_rule


def test_importing_knowledge_doc_seed_does_not_load_runtime_heavy_modules() -> None:
    code = f"""
import importlib
import json
import sys

forbidden = {FORBIDDEN_RUNTIME_MODULES!r}

importlib.import_module("modules.graph.knowledge_doc_seed")

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
