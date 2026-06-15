"""Focused tests for v2.9 EvidenceGroundingBundle construction."""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from modules.ai_advisory.evidence_bundle import (
    EVIDENCE_GROUNDING_SCHEMA_VERSION,
    EvidenceGroundingBundle,
    build_evidence_grounding_bundle,
)
from modules.ai_advisory.types import AIAdvisoryInput, EvidenceGapAnalysis

MODULE_PATH = Path(__file__).resolve().parents[1] / "modules" / "ai_advisory" / "evidence_bundle.py"


def command_input() -> AIAdvisoryInput:
    return AIAdvisoryInput(
        event_kind="payload_or_event",
        attack_type="Command Injection",
        risk_label="HIGH",
        decision_label="BLOCK",
        matched_rule_ids=["CMD-001"],
        matched_signatures=["; rm -rf"],
        evidence_labels=["shell_metacharacter_payload"],
        detection_source="rule_based_detection",
        source_label="active_event_context",
    )


def custom_gap() -> EvidenceGapAnalysis:
    return EvidenceGapAnalysis(
        confirmed_facts=["Rule CMD-001 matched."],
        missing_evidence=["Process execution telemetry is missing."],
        recommended_checks=["Review process creation logs."],
        unsafe_assumptions=["Do not claim command execution from payload alone."],
    )


def test_bundle_schema_and_official_verdict_are_copied() -> None:
    bundle = build_evidence_grounding_bundle(command_input(), evidence_gap=custom_gap())

    assert bundle.schema_version == EVIDENCE_GROUNDING_SCHEMA_VERSION
    assert bundle.context_kind == "payload_event"
    assert bundle.official_detection.detection_source == "rule_based_detection"
    assert bundle.official_detection.matched_rule_ids == ["CMD-001"]
    assert bundle.official_verdict.risk_level == "HIGH"
    assert bundle.official_verdict.decision == "BLOCK"
    assert bundle.official_verdict.simulated_decision is True


def test_bundle_uses_stable_citation_prefixes_and_serializes() -> None:
    bundle = build_evidence_grounding_bundle(command_input(), evidence_gap=custom_gap())
    citation_ids = [citation.citation_id for citation in bundle.citations]

    assert "rule-001" in citation_ids
    assert "ev-001" in citation_ids
    assert "gap-001" in citation_ids
    assert bundle.evidence_items[0].citation_id == "ev-001"
    assert EvidenceGroundingBundle.model_validate_json(bundle.model_dump_json()) == bundle


def test_builder_does_not_mutate_inputs() -> None:
    advisory_input = command_input()
    gap = custom_gap()
    advisory_snapshot = advisory_input.model_copy(deep=True)
    gap_snapshot = gap.model_copy(deep=True)

    build_evidence_grounding_bundle(advisory_input, evidence_gap=gap)

    assert advisory_input == advisory_snapshot
    assert gap == gap_snapshot


def test_optional_advisory_context_is_labeled_not_authoritative() -> None:
    retrieval_answer = SimpleNamespace(
        answer="Review defensive HTTP/2 Resource Exhaustion telemetry.",
        sources=[SimpleNamespace(source="knowledge/http2.md", kind="knowledge_doc", heading="Defense")],
        confidence="MEDIUM",
        limitations=["Advisory only."],
    )
    seed = SimpleNamespace(
        case_id="CASE-SEED-001",
        title="Command Injection Payload",
        outcome="Blocked in demo.",
        analyst_conclusion="Payload was suspicious.",
    )
    similar = SimpleNamespace(
        matches=[SimpleNamespace(seed=seed, score=120, reasons=("matched rule_ids: CMD-001",), differences=("Check execution telemetry.",))]
    )
    graph = SimpleNamespace(
        nodes=[
            SimpleNamespace(id="incident:1", label="Incident 1"),
            SimpleNamespace(id="rule:CMD-001", label="CMD-001"),
        ],
        edges=[SimpleNamespace(source_node_id="incident:1", target_node_id="rule:CMD-001", kind="MAPS_TO_RULE")],
    )

    bundle = build_evidence_grounding_bundle(
        command_input(),
        evidence_gap=custom_gap(),
        rag_answer=retrieval_answer,
        similar_case_result=similar,
        graph_snapshot=graph,
    )

    assert bundle.rag_context[0].advisory_only is True
    assert bundle.similar_cases[0].not_proof is True
    assert bundle.graph_context[0].not_detection_source is True
    assert {item.citation_id for item in bundle.rag_context} == {"rag-001"}
    assert {item.citation_id for item in bundle.similar_cases} == {"case-001"}
    assert {item.citation_id for item in bundle.graph_context} == {"graph-001"}


def test_bundle_import_stays_lightweight() -> None:
    code = """
import importlib
import json
import sys

forbidden = [
    "streamlit", "ollama", "modules.rag", "modules.rag_qa", "chromadb",
    "torch", "sentence_transformers", "requests", "httpx", "openai", "langchain",
]
importlib.import_module("modules.ai_advisory.evidence_bundle")
loaded = [
    name for name in forbidden
    if name in sys.modules or any(mod.startswith(name + ".") for mod in sys.modules)
]
print(json.dumps(loaded))
raise SystemExit(1 if loaded else 0)
"""
    result = subprocess.run([sys.executable, "-c", code], text=True, capture_output=True, check=False)

    assert result.returncode == 0, result.stdout + result.stderr


def test_source_does_not_import_runtime_rag_or_llm_dependencies() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8").casefold()
    forbidden_import_terms = (
        "modules.rag",
        "modules.rag_qa",
        "ollama",
        "chromadb",
        "sentence_transformers",
        "langchain",
        "torch",
        "streamlit",
        "openai",
        "requests",
        "httpx",
    )
    for line in source.splitlines():
        if line.strip().startswith(("import ", "from ")):
            assert not any(term in line for term in forbidden_import_terms), line
