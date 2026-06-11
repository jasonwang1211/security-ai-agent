"""Typed contracts for the deterministic, LLM-free AI advisory layer (v2.7-A).

These contracts carry *structured facts only* from the deterministic pipeline
into advisory analyst context. They never introduce a replacement Risk Level or
Decision — the rule engine remains the sole authority. The advisory layer does
not use an LLM or RAG, and it never writes detection rules, live knowledge,
graph facts, or enforcement state.
"""

from pydantic import BaseModel, ConfigDict, Field

# Single source of truth for the advisory safety boundary text. Always attached
# to advisory output so the non-authoritative framing travels with the data.
ADVISORY_BOUNDARY = (
    "Deterministic AI-advisory analyst context only. No LLM or RAG is used. "
    "This does not change, replace, or override the rule-based Risk Level or "
    "Decision; BLOCK / MONITOR / ALLOW remain simulated. It writes no detection "
    "rules, live knowledge, graph facts, or enforcement state. No real firewall, "
    "WAF, EDR, account, cloud, SIEM, or SOAR action is executed; no exploit, PoC, "
    "or traffic generation is provided; human review is required."
)


class AIAdvisoryInput(BaseModel):
    """Structured facts handed to the advisory layer.

    Accepts already-computed deterministic facts only. Extra fields are
    forbidden so callers cannot smuggle in an alternative authoritative verdict
    (for example a field literally named ``risk_level`` or ``decision``). The
    ``risk_label`` / ``decision_label`` fields are echoes of the deterministic
    result for context; they are never recomputed here.
    """

    model_config = ConfigDict(extra="forbid")

    event_kind: str
    attack_type: str | None = None
    finding_type: str | None = None
    risk_label: str | None = None
    decision_label: str | None = None
    matched_rule_ids: list[str] = Field(default_factory=list)
    matched_signatures: list[str] = Field(default_factory=list)
    evidence_labels: list[str] = Field(default_factory=list)
    detection_source: str = "rule_based_detection"
    incident_id: str | None = None
    finding_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    source_label: str | None = None


class EvidenceGapAnalysis(BaseModel):
    """Advisory evidence-gap result.

    Intentionally exposes no field named ``risk_level`` or ``decision`` so it can
    never be mistaken for the authoritative deterministic verdict. ``llm_status``
    defaults to ``"not_used"`` and ``source`` to ``"deterministic_ai_advisory"``
    to make the LLM-free, deterministic provenance explicit.
    """

    confirmed_facts: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    recommended_checks: list[str] = Field(default_factory=list)
    unsafe_assumptions: list[str] = Field(default_factory=list)
    advisory_boundary: str = ADVISORY_BOUNDARY
    llm_status: str = "not_used"
    source: str = "deterministic_ai_advisory"

class AIAnalystBriefInput(BaseModel):
    """Input envelope for the deterministic AI Analyst Brief backend.

    The nested ``AIAdvisoryInput`` carries already-computed deterministic facts.
    Optional context fields are read-only display/advisory context and must not
    be interpreted as replacements for the authoritative verdict. Extra fields
    remain forbidden so callers cannot smuggle authoritative names into the
    brief input.
    """

    model_config = ConfigDict(extra="forbid")

    advisory_input: AIAdvisoryInput
    evidence_gap: EvidenceGapAnalysis | None = None
    similar_case_ids: list[str] = Field(default_factory=list)
    graph_relation_summary: list[str] = Field(default_factory=list)
    case_draft_status: str | None = None
    run_mode: str | None = None


class AIAnalystBrief(BaseModel):
    """Structured deterministic analyst brief.

    The output intentionally exposes no field named ``risk_level`` or
    ``decision``. Deterministic labels may appear only inside narrative list
    items, preserving the rule-based verdict as context rather than authority
    granted to the advisory layer.
    """

    what_happened: list[str] = Field(default_factory=list)
    why_it_matters: list[str] = Field(default_factory=list)
    deterministic_verdict: list[str] = Field(default_factory=list)
    advisory_summary: list[str] = Field(default_factory=list)
    evidence_gap_summary: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)
    unsafe_assumptions: list[str] = Field(default_factory=list)
    safety_boundary: str = ADVISORY_BOUNDARY
    llm_status: str = "not_used"
    source: str = "deterministic_ai_analyst_brief"
