"""Evidence-grounding bundle for v2.9 structured analyst briefs.

The bundle is a deterministic, side-effect-free bridge between already-computed
security facts and an advisory analyst brief. It never calls an LLM, starts
retrieval, mutates graph/case/knowledge state, or recomputes the official Risk
Level / Decision.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .evidence_gap import analyze_evidence_gap
from .types import ADVISORY_BOUNDARY, AIAdvisoryInput, EvidenceGapAnalysis

EVIDENCE_GROUNDING_SCHEMA_VERSION = "v2.9-evidence-bundle1"

ContextKind = Literal["payload_event", "auth_incident"]
CitationKind = Literal[
    "evidence",
    "rule",
    "evidence_gap",
    "retrieval_context",
    "approved_case",
    "graph_context",
]

EVIDENCE_GROUNDING_BOUNDARY_LINES = (
    "Rule-Based Detector remains the detection authority.",
    "Risk Level / Decision are deterministic.",
    "BLOCK / MONITOR / ALLOW are simulated decisions only.",
    "LLM / RAG / AI Brief / Evidence Gap / Similar Cases / Graph are advisory only.",
    "LLM output must not override official Risk Level or Decision.",
    "Similar cases are not proof of compromise or successful execution.",
    "Graph context is not a detection source.",
    "No real firewall, WAF, EDR, account, cloud, SIEM, or SOAR action is executed.",
    "No exploit, PoC, traffic generation, load testing, or offensive automation is provided.",
    "Human review is required.",
)


def _require_non_blank(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value.strip()


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _clean_list(values: Any) -> list[str]:
    out: list[str] = []
    if values is None:
        return out
    for value in values:
        text = _clean_text(value)
        if text and text not in out:
            out.append(text)
    return out


def _citation_id(prefix: str, index: int) -> str:
    return f"{prefix}-{index:03d}"


class GroundingCitation(BaseModel):
    """Citation record used by the EvidenceGroundingBundle and brief."""

    model_config = ConfigDict(extra="forbid")

    citation_id: str
    kind: CitationKind
    label: str
    source: str
    advisory_only: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("citation_id", "label", "source")
    @classmethod
    def required_text_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "required text")


class GroundingProvenance(BaseModel):
    """Where a bundle section came from."""

    model_config = ConfigDict(extra="forbid")

    source_type: str
    source_id: str
    field_path: str
    description: str
    citation_ids: list[str] = Field(default_factory=list)

    @field_validator("source_type", "source_id", "field_path", "description")
    @classmethod
    def required_text_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "required text")


class ActiveContextGrounding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    context_kind: ContextKind
    event_kind: str
    attack_type: str | None = None
    finding_type: str | None = None
    incident_id: str | None = None
    source_label: str | None = None


class OfficialDetectionGrounding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detection_source: str = "rule_based_detection"
    matched_rule_ids: list[str] = Field(default_factory=list)
    matched_signatures: list[str] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)


class OfficialVerdictGrounding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_level: str | None = None
    decision: str | None = None
    simulated_decision: bool = True
    authority: str = "deterministic_policy"
    citation_ids: list[str] = Field(default_factory=list)


class EvidenceGroundingItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citation_id: str
    source_id: str | None = None
    evidence_type: str
    description: str
    value_summary: str | None = None
    provenance: str = "active_context"


class EvidenceGapGrounding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmed_facts: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    recommended_checks: list[str] = Field(default_factory=list)
    unsafe_assumptions: list[str] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)
    source: str = "deterministic_ai_advisory"
    advisory_boundary: str = ADVISORY_BOUNDARY


class RetrievalGroundingItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citation_id: str
    answer: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    confidence: str | None = None
    limitations: list[str] = Field(default_factory=list)
    advisory_only: bool = True


class SimilarCaseGroundingItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citation_id: str
    case_id: str
    title: str
    score: int
    similarity_reasons: list[str] = Field(default_factory=list)
    differences: list[str] = Field(default_factory=list)
    outcome: str | None = None
    analyst_conclusion: str | None = None
    advisory_only: bool = True
    not_proof: bool = True


class GraphGroundingItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citation_id: str
    relationship: str
    edge_kind: str | None = None
    source_node_id: str | None = None
    target_node_id: str | None = None
    advisory_only: bool = True
    not_detection_source: bool = True


class EvidenceGroundingBundle(BaseModel):
    """Single structured input contract for v2.9 analyst brief generation."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = EVIDENCE_GROUNDING_SCHEMA_VERSION
    context_kind: ContextKind
    active_context: ActiveContextGrounding
    official_detection: OfficialDetectionGrounding
    official_verdict: OfficialVerdictGrounding
    evidence_items: list[EvidenceGroundingItem] = Field(default_factory=list)
    evidence_gaps: EvidenceGapGrounding
    rag_context: list[RetrievalGroundingItem] = Field(default_factory=list)
    similar_cases: list[SimilarCaseGroundingItem] = Field(default_factory=list)
    graph_context: list[GraphGroundingItem] = Field(default_factory=list)
    citations: list[GroundingCitation] = Field(default_factory=list)
    safety_boundary: list[str] = Field(default_factory=lambda: list(EVIDENCE_GROUNDING_BOUNDARY_LINES))
    provenance: list[GroundingProvenance] = Field(default_factory=list)


def build_evidence_grounding_bundle(
    advisory_input: AIAdvisoryInput,
    *,
    evidence_gap: EvidenceGapAnalysis | None = None,
    rag_answer: Any | None = None,
    similar_case_result: Any | None = None,
    graph_snapshot: Any | None = None,
) -> EvidenceGroundingBundle:
    """Build a deterministic bundle from already-computed facts.

    Optional context arguments are consumed only when supplied. This function
    does not trigger retrieval, graph traversal, similar-case lookup, file
    writes, or LLM generation.
    """

    gap = evidence_gap or analyze_evidence_gap(advisory_input)
    context_kind = _context_kind(advisory_input)
    citations: list[GroundingCitation] = []
    provenance: list[GroundingProvenance] = []

    rule_citations = _rule_citations(advisory_input)
    citations.extend(rule_citations)
    rule_ids = [citation.citation_id for citation in rule_citations]
    if rule_ids:
        provenance.append(
            GroundingProvenance(
                source_type="active_context",
                source_id=advisory_input.source_label or advisory_input.event_kind,
                field_path="matched_rule_ids",
                description="Rule IDs copied from deterministic active context.",
                citation_ids=rule_ids,
            )
        )

    evidence_items, evidence_citations = _evidence_items(advisory_input)
    citations.extend(evidence_citations)
    if evidence_citations:
        provenance.append(
            GroundingProvenance(
                source_type="active_context",
                source_id=advisory_input.source_label or advisory_input.event_kind,
                field_path="evidence_ids/evidence_labels/matched_signatures",
                description="Evidence labels copied from active context; signatures are evidence summaries only.",
                citation_ids=[citation.citation_id for citation in evidence_citations],
            )
        )

    gap_grounding, gap_citation = _evidence_gap_grounding(gap)
    citations.append(gap_citation)
    provenance.append(
        GroundingProvenance(
            source_type="evidence_gap_analysis",
            source_id=gap.source,
            field_path="confirmed_facts/missing_evidence/recommended_checks/unsafe_assumptions",
            description="Deterministic Evidence Gap Analyzer output.",
            citation_ids=[gap_citation.citation_id],
        )
    )

    retrieval_items, retrieval_citations = _retrieval_context(rag_answer)
    citations.extend(retrieval_citations)
    if retrieval_citations:
        provenance.append(
            GroundingProvenance(
                source_type="knowledge_answer",
                source_id="provided_rag_answer",
                field_path="rag_context",
                description="Optional already-computed Knowledge Q&A context.",
                citation_ids=[citation.citation_id for citation in retrieval_citations],
            )
        )

    similar_items, similar_citations = _similar_case_context(similar_case_result)
    citations.extend(similar_citations)
    if similar_citations:
        provenance.append(
            GroundingProvenance(
                source_type="approved_similar_cases",
                source_id="provided_similar_case_result",
                field_path="similar_cases",
                description="Optional already-computed approved similar-case result.",
                citation_ids=[citation.citation_id for citation in similar_citations],
            )
        )

    graph_items, graph_citations = _graph_context(graph_snapshot)
    citations.extend(graph_citations)
    if graph_citations:
        provenance.append(
            GroundingProvenance(
                source_type="graph_snapshot",
                source_id="provided_graph_snapshot",
                field_path="graph_context",
                description="Optional already-computed graph relationship context.",
                citation_ids=[citation.citation_id for citation in graph_citations],
            )
        )

    verdict_citation_ids = rule_ids or [item.citation_id for item in evidence_citations]

    return EvidenceGroundingBundle(
        context_kind=context_kind,
        active_context=ActiveContextGrounding(
            context_kind=context_kind,
            event_kind=advisory_input.event_kind,
            attack_type=advisory_input.attack_type,
            finding_type=advisory_input.finding_type,
            incident_id=advisory_input.incident_id,
            source_label=advisory_input.source_label,
        ),
        official_detection=OfficialDetectionGrounding(
            detection_source=advisory_input.detection_source,
            matched_rule_ids=list(advisory_input.matched_rule_ids),
            matched_signatures=list(advisory_input.matched_signatures),
            citation_ids=rule_ids,
        ),
        official_verdict=OfficialVerdictGrounding(
            risk_level=advisory_input.risk_label,
            decision=advisory_input.decision_label,
            simulated_decision=True,
            authority="deterministic_policy",
            citation_ids=verdict_citation_ids,
        ),
        evidence_items=evidence_items,
        evidence_gaps=gap_grounding,
        rag_context=retrieval_items,
        similar_cases=similar_items,
        graph_context=graph_items,
        citations=citations,
        safety_boundary=list(EVIDENCE_GROUNDING_BOUNDARY_LINES),
        provenance=provenance,
    )


def _context_kind(advisory_input: AIAdvisoryInput) -> ContextKind:
    haystack = " ".join(
        _clean_text(value)
        for value in (advisory_input.event_kind, advisory_input.finding_type, advisory_input.source_label)
    ).casefold()
    if "auth" in haystack or advisory_input.incident_id:
        return "auth_incident"
    return "payload_event"


def _rule_citations(advisory_input: AIAdvisoryInput) -> list[GroundingCitation]:
    citations: list[GroundingCitation] = []
    for index, rule_id in enumerate(_clean_list(advisory_input.matched_rule_ids), start=1):
        citation_id = _citation_id("rule", index)
        citations.append(
            GroundingCitation(
                citation_id=citation_id,
                kind="rule",
                label=f"Rule {rule_id}",
                source=advisory_input.detection_source,
                metadata={"rule_id": rule_id},
            )
        )
    return citations


def _evidence_items(
    advisory_input: AIAdvisoryInput,
) -> tuple[list[EvidenceGroundingItem], list[GroundingCitation]]:
    labels = _clean_list(advisory_input.evidence_labels)
    source_ids = _clean_list(advisory_input.evidence_ids)
    signatures = _clean_list(advisory_input.matched_signatures)
    count = max(len(labels), len(source_ids), len(signatures))
    items: list[EvidenceGroundingItem] = []
    citations: list[GroundingCitation] = []

    for zero_index in range(count):
        index = zero_index + 1
        citation_id = _citation_id("ev", index)
        source_id = source_ids[zero_index] if zero_index < len(source_ids) else None
        evidence_type = labels[zero_index] if zero_index < len(labels) else "matched_signature"
        signature = signatures[zero_index] if zero_index < len(signatures) else None
        description = (
            f"Structured evidence label: {evidence_type}"
            if evidence_type != "matched_signature"
            else "Matched signature from deterministic detector."
        )
        items.append(
            EvidenceGroundingItem(
                citation_id=citation_id,
                source_id=source_id,
                evidence_type=evidence_type,
                description=description,
                value_summary=signature,
                provenance=advisory_input.source_label or "active_context",
            )
        )
        citations.append(
            GroundingCitation(
                citation_id=citation_id,
                kind="evidence",
                label=evidence_type,
                source=advisory_input.source_label or "active_context",
                metadata={"source_id": source_id, "value_summary": signature},
            )
        )
    return items, citations


def _evidence_gap_grounding(gap: EvidenceGapAnalysis) -> tuple[EvidenceGapGrounding, GroundingCitation]:
    citation = GroundingCitation(
        citation_id="gap-001",
        kind="evidence_gap",
        label="Evidence Gap Analyzer",
        source=gap.source,
        metadata={"llm_status": gap.llm_status},
    )
    grounding = EvidenceGapGrounding(
        confirmed_facts=list(gap.confirmed_facts),
        missing_evidence=list(gap.missing_evidence),
        recommended_checks=list(gap.recommended_checks),
        unsafe_assumptions=list(gap.unsafe_assumptions),
        citation_ids=[citation.citation_id],
        source=gap.source,
        advisory_boundary=gap.advisory_boundary,
    )
    return grounding, citation


def _retrieval_context(rag_answer: Any | None) -> tuple[list[RetrievalGroundingItem], list[GroundingCitation]]:
    if rag_answer is None:
        return [], []
    answer = _clean_text(getattr(rag_answer, "answer", ""))
    if not answer:
        return [], []
    citation_id = "rag-001"
    source_items = []
    for source in getattr(rag_answer, "sources", []) or []:
        source_items.append(
            {
                "source": _clean_text(getattr(source, "source", "")),
                "kind": _clean_text(getattr(source, "kind", "")),
                "heading": _clean_text(getattr(source, "heading", "")) or None,
                "identifier": _clean_text(getattr(source, "identifier", "")) or None,
            }
        )
    item = RetrievalGroundingItem(
        citation_id=citation_id,
        answer=answer,
        sources=source_items,
        confidence=_clean_text(getattr(rag_answer, "confidence", "")) or None,
        limitations=_clean_list(getattr(rag_answer, "limitations", []) or []),
        advisory_only=True,
    )
    citation = GroundingCitation(
        citation_id=citation_id,
        kind="retrieval_context",
        label="Knowledge Q&A / RAG context",
        source="provided_answer_with_sources",
        metadata={"source_count": len(source_items), "confidence": item.confidence},
    )
    return [item], [citation]


def _similar_case_context(
    similar_case_result: Any | None,
) -> tuple[list[SimilarCaseGroundingItem], list[GroundingCitation]]:
    matches = list(getattr(similar_case_result, "matches", []) or [])
    items: list[SimilarCaseGroundingItem] = []
    citations: list[GroundingCitation] = []
    for index, match in enumerate(matches, start=1):
        seed = getattr(match, "seed", None)
        case_id = _clean_text(getattr(seed, "case_id", ""))
        title = _clean_text(getattr(seed, "title", ""))
        if not case_id or not title:
            continue
        citation_id = _citation_id("case", index)
        item = SimilarCaseGroundingItem(
            citation_id=citation_id,
            case_id=case_id,
            title=title,
            score=int(getattr(match, "score", 0) or 0),
            similarity_reasons=_clean_list(getattr(match, "reasons", []) or []),
            differences=_clean_list(getattr(match, "differences", []) or []),
            outcome=_clean_text(getattr(seed, "outcome", "")) or None,
            analyst_conclusion=_clean_text(getattr(seed, "analyst_conclusion", "")) or None,
            advisory_only=True,
            not_proof=True,
        )
        items.append(item)
        citations.append(
            GroundingCitation(
                citation_id=citation_id,
                kind="approved_case",
                label=f"{case_id} - {title}",
                source="approved_case_seed",
                metadata={"case_id": case_id, "score": item.score, "not_proof": True},
            )
        )
    return items, citations


def _graph_context(graph_snapshot: Any | None) -> tuple[list[GraphGroundingItem], list[GroundingCitation]]:
    if graph_snapshot is None:
        return [], []
    nodes = list(getattr(graph_snapshot, "nodes", []) or [])
    edges = list(getattr(graph_snapshot, "edges", []) or [])
    labels = {_clean_text(getattr(node, "id", "")): _clean_text(getattr(node, "label", "")) for node in nodes}
    items: list[GraphGroundingItem] = []
    citations: list[GroundingCitation] = []
    for index, edge in enumerate(edges[:8], start=1):
        source_node_id = _clean_text(getattr(edge, "source_node_id", ""))
        target_node_id = _clean_text(getattr(edge, "target_node_id", ""))
        edge_kind = _clean_text(getattr(edge, "kind", ""))
        source_label = labels.get(source_node_id, source_node_id)
        target_label = labels.get(target_node_id, target_node_id)
        if not source_node_id or not target_node_id:
            continue
        citation_id = _citation_id("graph", index)
        relationship = f"{source_label} -> {target_label}"
        items.append(
            GraphGroundingItem(
                citation_id=citation_id,
                relationship=relationship,
                edge_kind=edge_kind,
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                advisory_only=True,
                not_detection_source=True,
            )
        )
        citations.append(
            GroundingCitation(
                citation_id=citation_id,
                kind="graph_context",
                label=relationship,
                source="provided_graph_snapshot",
                metadata={"edge_kind": edge_kind, "not_detection_source": True},
            )
        )
    return items, citations


__all__ = [
    "EVIDENCE_GROUNDING_BOUNDARY_LINES",
    "EVIDENCE_GROUNDING_SCHEMA_VERSION",
    "ActiveContextGrounding",
    "EvidenceGapGrounding",
    "EvidenceGroundingBundle",
    "EvidenceGroundingItem",
    "GraphGroundingItem",
    "GroundingCitation",
    "GroundingProvenance",
    "OfficialDetectionGrounding",
    "OfficialVerdictGrounding",
    "RetrievalGroundingItem",
    "SimilarCaseGroundingItem",
    "build_evidence_grounding_bundle",
]
