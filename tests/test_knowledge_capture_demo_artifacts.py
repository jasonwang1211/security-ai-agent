"""Tests for v3.5 knowledge capture demo and review artifacts."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from modules.knowledge_capture import ADVISORY_ONLY_WARNING
from modules.knowledge_capture.types import (
    ApprovedKnowledgeNote,
    CandidateKnowledgeNote,
    GraphEdgeCandidate,
    GraphNodeCandidate,
    RejectedKnowledgeNote,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "docs" / "examples" / "knowledge_capture"


def test_demo_script_runs_with_tmp_output_and_writes_expected_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "knowledge_capture_demo"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "demo_knowledge_capture.py"),
            "--output-dir",
            str(output_dir),
            "--clean",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "synthetic demo complete" in result.stdout
    assert "No live LLM, API, Chroma, embeddings, network" in result.stdout
    assert "not a detection source and not proof of compromise" in result.stdout

    pending_path = output_dir / "capture_store" / "pending_notes.jsonl"
    approved_path = output_dir / "capture_store" / "approved_notes.jsonl"
    rejected_path = output_dir / "capture_store" / "rejected_notes.jsonl"
    rag_path = output_dir / "rag_export.md"
    graph_path = output_dir / "graph_candidates.json"

    assert pending_path.exists()
    assert approved_path.exists()
    assert rejected_path.exists()
    assert rag_path.exists()
    assert graph_path.exists()
    assert pending_path.read_text(encoding="utf-8") == ""
    assert len(_jsonl_lines(approved_path)) == 1
    assert len(_jsonl_lines(rejected_path)) == 1

    approved = ApprovedKnowledgeNote.model_validate_json(
        (output_dir / "approved_note.json").read_text(encoding="utf-8")
    )
    rejected = RejectedKnowledgeNote.model_validate_json(
        (output_dir / "rejected_note.json").read_text(encoding="utf-8")
    )
    assert approved.status == "approved"
    assert rejected.status == "rejected"
    assert approved.provenance.official_risk_level == "HIGH"
    assert approved.provenance.official_decision == "MONITOR"

    rag_markdown = rag_path.read_text(encoding="utf-8")
    assert ADVISORY_ONLY_WARNING in rag_markdown
    assert "not proof of compromise" in rag_markdown
    assert "No real enforcement is authorized" in rag_markdown

    graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
    nodes = [GraphNodeCandidate.model_validate(item) for item in graph_payload["nodes"]]
    edges = [GraphEdgeCandidate.model_validate(item) for item in graph_payload["edges"]]
    assert nodes and edges
    assert all(node.advisory_only and node.not_detection_source and node.not_proof for node in nodes)
    assert all(edge.advisory_only and edge.not_detection_source and edge.not_proof for edge in edges)


def test_synthetic_example_json_files_validate_against_models() -> None:
    candidate = CandidateKnowledgeNote.model_validate_json(
        (EXAMPLES / "sample_candidate_note.json").read_text(encoding="utf-8")
    )
    approved = ApprovedKnowledgeNote.model_validate_json(
        (EXAMPLES / "sample_approved_note.json").read_text(encoding="utf-8")
    )
    rejected = RejectedKnowledgeNote.model_validate_json(
        (EXAMPLES / "sample_rejected_note.json").read_text(encoding="utf-8")
    )

    assert candidate.status == "pending_review"
    assert approved.status == "approved"
    assert rejected.status == "rejected"
    assert approved.advisory_only is True
    assert approved.not_detection_source is True
    assert approved.not_proof is True
    assert approved.provenance.source_event_id == "synthetic-http2-resource-exhaustion-001"
    assert approved.provenance.source_evidence_ids
    assert approved.provenance.source_rule_ids == ["HTTP2-RESOURCE-EXHAUSTION"]
    assert approved.provenance.source_gap_ids
    assert approved.provenance.source_rag_ids
    assert approved.provenance.source_case_ids == ["CASE-SEED-003"]
    assert approved.provenance.source_graph_ids
    assert approved.provenance.official_risk_level == "HIGH"
    assert approved.provenance.official_decision == "MONITOR"


def test_sample_rag_export_contains_advisory_safety_boundary() -> None:
    markdown = (EXAMPLES / "sample_rag_export.md").read_text(encoding="utf-8")

    assert ADVISORY_ONLY_WARNING in markdown
    assert "Advisory-only RAG candidate" in markdown
    assert "Not official detection logic" in markdown
    assert "Does not override Risk Level or Decision" in markdown
    assert "No real enforcement is authorized" in markdown


def test_sample_graph_candidates_are_advisory_only() -> None:
    payload: dict[str, list[dict[str, Any]]] = json.loads(
        (EXAMPLES / "sample_graph_candidates.json").read_text(encoding="utf-8")
    )
    nodes = [GraphNodeCandidate.model_validate(item) for item in payload["nodes"]]
    edges = [GraphEdgeCandidate.model_validate(item) for item in payload["edges"]]

    assert nodes
    assert edges
    assert all(node.advisory_only is True for node in nodes)
    assert all(node.not_detection_source is True for node in nodes)
    assert all(node.not_proof is True for node in nodes)
    assert all(edge.advisory_only is True for edge in edges)
    assert all(edge.not_detection_source is True for edge in edges)
    assert all(edge.not_proof is True for edge in edges)
    assert all(edge.relation == "ADVISORY_CONTEXT_FOR" for edge in edges)


def _jsonl_lines(path: Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
