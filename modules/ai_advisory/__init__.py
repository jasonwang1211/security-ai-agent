"""Deterministic, LLM-free AI advisory foundation (v2.7-A).

Read-only analyst context that increases AI analyst usefulness without
increasing AI authority. Nothing in this package uses an LLM, RAG, or Ollama,
and nothing here overrides the rule-based Risk Level or Decision or writes
detection rules, live knowledge, graph facts, or enforcement state.
"""

from .brief import AI_ANALYST_BRIEF_BOUNDARY, build_ai_analyst_brief
from .evidence_gap import analyze_evidence_gap
from .types import (
    ADVISORY_BOUNDARY,
    AIAdvisoryInput,
    AIAnalystBrief,
    AIAnalystBriefInput,
    EvidenceGapAnalysis,
)

__all__ = [
    "ADVISORY_BOUNDARY",
    "AI_ANALYST_BRIEF_BOUNDARY",
    "AIAdvisoryInput",
    "AIAnalystBrief",
    "AIAnalystBriefInput",
    "EvidenceGapAnalysis",
    "analyze_evidence_gap",
    "build_ai_analyst_brief",
]
