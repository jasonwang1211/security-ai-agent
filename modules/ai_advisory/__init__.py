"""Deterministic, LLM-free AI advisory foundation (v2.7-A).

Read-only analyst context that increases AI analyst usefulness without
increasing AI authority. Nothing in this package uses an LLM, RAG, or Ollama,
and nothing here overrides the rule-based Risk Level or Decision or writes
detection rules, live knowledge, graph facts, or enforcement state.
"""

from .evidence_gap import analyze_evidence_gap
from .types import ADVISORY_BOUNDARY, AIAdvisoryInput, EvidenceGapAnalysis

__all__ = [
    "ADVISORY_BOUNDARY",
    "AIAdvisoryInput",
    "EvidenceGapAnalysis",
    "analyze_evidence_gap",
]
