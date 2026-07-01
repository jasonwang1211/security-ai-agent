"""Run a local synthetic demo of v3.5 human-approved knowledge capture.

The demo uses safe synthetic data only. It does not call external services,
LLMs, Chroma, embeddings, network APIs, RAG runtime ingest, or graph mutation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
from collections.abc import Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.knowledge_capture import (  # noqa: E402
    ADVISORY_ONLY_WARNING,
    KnowledgeCaptureStore,
    build_candidate_knowledge_note,
    export_approved_note_to_graph_candidates,
    export_approved_note_to_rag_markdown,
)
from modules.knowledge_capture.types import CandidateKnowledgeNote  # noqa: E402

DEFAULT_OUTPUT_DIR = Path(".tmp") / "knowledge_capture_demo"


def build_demo_candidate(*, note_id: str = "KC-DEMO-APPROVE001") -> CandidateKnowledgeNote:
    return build_candidate_knowledge_note(
        note_id=note_id,
        title="Synthetic HTTP/2 resource exhaustion triage note",
        body=(
            "Review proxy, CDN, and application server telemetry for stream resets, "
            "flow-control pressure, CPU and memory saturation, and request concurrency. "
            "This note is advisory only and must not override the deterministic verdict."
        ),
        source_event_id="synthetic-http2-resource-exhaustion-001",
        source_question="What defensive evidence should be reviewed for this synthetic HTTP/2 event?",
        source_answer_summary=(
            "The analyst should compare server resource metrics, proxy/CDN telemetry, "
            "HTTP/2 stream reset patterns, and existing deterministic evidence gaps."
        ),
        source_evidence_ids=["evidence-http2-reset-rate", "evidence-server-resource-metrics"],
        source_rule_ids=["HTTP2-RESOURCE-EXHAUSTION"],
        source_gap_ids=["gap-origin-server-telemetry", "gap-client-distribution"],
        source_rag_ids=["rag-http2-resource-exhaustion-defensive-guidance"],
        source_case_ids=["CASE-SEED-003"],
        source_graph_ids=["graph-current-event", "graph-related-http2-context"],
        official_risk_level="HIGH",
        official_decision="MONITOR",
        created_by="demo-analyst",
        confidence_label="MEDIUM",
    )


def build_demo_rejected_candidate() -> CandidateKnowledgeNote:
    return build_candidate_knowledge_note(
        note_id="KC-DEMO-REJECT001",
        title="Synthetic rejected note with insufficient detail",
        body="This note is safe but too vague for future reuse without more evidence references.",
        source_event_id="synthetic-http2-resource-exhaustion-001",
        source_question="Should this vague note be retained?",
        source_answer_summary="Rejected in the demo because it lacks enough reusable analyst detail.",
        source_evidence_ids=["evidence-http2-reset-rate"],
        source_rule_ids=["HTTP2-RESOURCE-EXHAUSTION"],
        official_risk_level="HIGH",
        official_decision="MONITOR",
        created_by="demo-analyst",
        confidence_label="LOW",
    )


def run_demo(output_dir: Path = DEFAULT_OUTPUT_DIR, *, clean: bool = False) -> dict[str, Path]:
    output_dir = output_dir.resolve()
    if clean:
        clean_demo_output(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    store = KnowledgeCaptureStore(output_dir / "capture_store")
    candidate = build_demo_candidate()
    rejected_candidate = build_demo_rejected_candidate()

    store.append_pending_note(candidate)
    store.append_pending_note(rejected_candidate)
    rejected = store.reject_note(
        rejected_candidate.note_id,
        rejected_by="demo-reviewer",
        rejection_reason="Synthetic demo rejection: safe but too vague for reuse.",
    )
    approved = store.approve_note(
        candidate.note_id,
        approved_by="demo-reviewer",
        edited_body=(
            "Review proxy, CDN, and application server telemetry for stream resets, "
            "flow-control pressure, CPU and memory saturation, and request concurrency. "
            "Treat this as advisory context only; it is not proof of compromise and "
            "does not override the deterministic Risk Level or Decision."
        ),
        approval_notes="Synthetic demo approval for review workflow demonstration.",
    )

    rag_candidate = export_approved_note_to_rag_markdown(approved)
    graph_nodes, graph_edges = export_approved_note_to_graph_candidates(approved)

    paths = {
        "pending_jsonl": store.pending_path,
        "approved_jsonl": store.approved_path,
        "rejected_jsonl": store.rejected_path,
        "approved_note_json": output_dir / "approved_note.json",
        "rejected_note_json": output_dir / "rejected_note.json",
        "rag_export_markdown": output_dir / "rag_export.md",
        "graph_candidates_json": output_dir / "graph_candidates.json",
        "safety_summary": output_dir / "safety_summary.txt",
    }

    paths["approved_note_json"].write_text(
        approved.model_dump_json(indent=2), encoding="utf-8", newline="\n"
    )
    paths["rejected_note_json"].write_text(
        rejected.model_dump_json(indent=2), encoding="utf-8", newline="\n"
    )
    paths["rag_export_markdown"].write_text(
        rag_candidate.markdown, encoding="utf-8", newline="\n"
    )
    paths["graph_candidates_json"].write_text(
        json.dumps(
            {
                "nodes": [node.model_dump(mode="json") for node in graph_nodes],
                "edges": [edge.model_dump(mode="json") for edge in graph_edges],
            },
            indent=2,
        ),
        encoding="utf-8",
        newline="\n",
    )
    paths["safety_summary"].write_text(_safety_summary(), encoding="utf-8", newline="\n")
    return paths


def clean_demo_output(output_dir: Path) -> None:
    known_files = {
        "approved_note.json",
        "rejected_note.json",
        "rag_export.md",
        "graph_candidates.json",
        "safety_summary.txt",
    }
    if output_dir.exists():
        for file_name in known_files:
            path = output_dir / file_name
            if path.exists():
                path.unlink()
        store_dir = output_dir / "capture_store"
        if store_dir.exists():
            shutil.rmtree(store_dir)


def _safety_summary() -> str:
    return "\n".join(
        [
            ADVISORY_ONLY_WARNING,
            "",
            "Demo safety boundary:",
            "- Synthetic data only.",
            "- No live LLM, API, Chroma, embeddings, network, RAG ingest, or graph mutation.",
            "- Advisory-only output; not a detection source and not proof of compromise.",
            "- Official Risk Level / Decision are copied deterministic context and are not overridden.",
            "- No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action.",
        ]
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the synthetic v3.5 knowledge capture demo.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for demo outputs. Defaults to .tmp/knowledge_capture_demo/.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove previous generated demo files in the chosen output directory first.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    paths = run_demo(args.output_dir, clean=args.clean)
    print("v3.5 knowledge capture synthetic demo complete.")
    print(_safety_summary())
    print("\nGenerated files:")
    for label, path in paths.items():
        print(f"- {label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
