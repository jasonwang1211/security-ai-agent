"""Structured evidence-grounded analyst brief generator for v2.9.

The generator accepts an EvidenceGroundingBundle and optionally a lazy-injected
client object. It validates generated JSON before use and falls back to a
safe deterministic brief whenever the generated content violates the advisory
boundary, lacks required citations, or changes the official verdict.
"""

from __future__ import annotations

import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .evidence_bundle import EvidenceGroundingBundle, GroundingCitation

GROUNDED_BRIEF_SCHEMA_VERSION = "v2.9-ai-analyst-brief1"

LLMStatus = Literal[
    "used",
    "not_used_deterministic_fallback",
    "unavailable_fallback",
    "blocked_by_guardrail",
    "invalid_json_fallback",
]

# --- Guardrail language patterns (v2.9-M2 hardening) -----------------------
#
# Each pattern describes UNSAFE *assertive* content that an AI-generated brief
# must not contain: offensive generation, real enforcement on a security
# control, account/credential manipulation, "graph detected the attack", or
# "similar cases prove compromise". Every pattern is evaluated in a
# negation-aware way (see ``_has_non_negated_match``) so defensive negated
# wording -- "do not run load testing", "graph is not the detection source",
# "similar cases do not prove compromise" -- is explicitly allowed.
#
# Verb/object groups are alternation fragments (word boundaries applied at the
# use site). Present, past, and -ing forms are included so both imperative
# ("update the firewall") and completed-action ("the firewall was updated")
# phrasings are caught.
_OFFENSIVE_VERBS = (
    r"run|running|execute|executing|launch|launching|perform|performing|"
    r"generate|generating|provide|providing|write|writing|create|creating|"
    r"build|building|produce|producing|deliver|delivering"
)
_OFFENSIVE_OBJECTS = (
    r"exploit|exploits|poc|pocs|proof[- ]of[- ]concept|traffic generation|"
    r"load test|load testing|load-test|dos attack|ddos|reverse shell"
)
_CONTROL_TARGETS = r"firewall|waf|edr|soar|siem|ids|ips"
_ENFORCEMENT_ACTIONS = (
    r"block|blocks|blocked|blocking|update|updates|updated|updating|"
    r"execute|executes|executed|executing|enforce|enforces|enforced|enforcing|"
    r"deploy|deploys|deployed|deploying|push|pushes|pushed|pushing|"
    r"apply|applies|applied|applying|configure|configures|configured|configuring|"
    r"modify|modifies|modified|modifying|quarantine|quarantines|quarantined|"
    r"isolate|isolates|isolated|isolating"
)
_ACCOUNT_ACTIONS = (
    r"reset|resets|disable|disables|disabled|enable|enables|enabled|"
    r"change|changes|changed|modify|modifies|modified|alter|alters|altered|"
    r"clear|clears|cleared|delete|deletes|deleted|remove|removes|removed|"
    r"lock|locks|locked|unlock|unlocks|unlocked|suspend|suspends|suspended|"
    r"revoke|revokes|revoked|rotate|rotates|rotated|expire|expires|expired"
)
_ACCOUNT_OBJECTS = (
    r"account|accounts|password|passwords|credential|credentials|"
    r"user|users|session|sessions"
)
_GRAPH_DETECTION_VERBS = (
    r"detected|detects|identified|identifies|revealed|reveals|"
    r"confirmed|confirms|showed|shows|uncovered|uncovers|"
    r"pinpointed|pinpoints|flagged|flags|caught|found|discovered|discovers"
)
_THREAT_OBJECTS = (
    r"the attack|an attack|attacks|the compromise|compromise|compromised|"
    r"the intrusion|intrusion|the threat|the breach|malicious activity|"
    r"the malicious (?:event|activity)"
)
_SIMILAR_PROOF_VERBS = (
    r"prove|proves|proved|confirm|confirms|confirmed|indicate|indicates|indicated|"
    r"suggest|suggests|suggested|demonstrate|demonstrates|demonstrated|"
    r"establish|establishes|established|validate|validates|validated|"
    r"support|supports|supported|is proof of|are proof of"
)
_SIMILAR_PROOF_OBJECTS = (
    r"compromise|compromised|the attack|attacks|intrusion|breach|malicious|"
    r"successful execution|current (?:event|incident)"
)

BLOCKED_LANGUAGE_PATTERNS = (
    # Offensive generation: <verb> ... <exploit / PoC / traffic-gen / load-test>
    re.compile(rf"\b(?:{_OFFENSIVE_VERBS})\b.{{0,60}}\b(?:{_OFFENSIVE_OBJECTS})\b", re.I),
    # Named offensive tooling
    re.compile(r"\b(?:hping3|slowloris|wrk|ab -n|attack script)\b", re.I),
    # Real enforcement on a security control (control -> action)
    re.compile(rf"\b(?:{_CONTROL_TARGETS})\b.{{0,60}}\b(?:{_ENFORCEMENT_ACTIONS})\b", re.I),
    # Real enforcement on a security control (action -> control)
    re.compile(rf"\b(?:{_ENFORCEMENT_ACTIONS})\b.{{0,40}}\b(?:{_CONTROL_TARGETS})\b", re.I),
    # Account / credential manipulation
    re.compile(rf"\b(?:{_ACCOUNT_ACTIONS})\b.{{0,30}}\b(?:{_ACCOUNT_OBJECTS})\b", re.I),
    # Graph claimed as having detected the attack
    re.compile(
        rf"\bgraph\b.{{0,80}}\b(?:{_GRAPH_DETECTION_VERBS})\b.{{0,30}}\b(?:{_THREAT_OBJECTS})\b",
        re.I,
    ),
    # Graph claimed as the detection source
    re.compile(
        r"\bgraph\b.{0,80}\b(?:is|was|are|were|acts as|act as|serves as|serve as|becomes|become)\b"
        r".{0,20}\b(?:the )?detection source\b",
        re.I,
    ),
    # Similar cases claimed as proof of compromise
    re.compile(
        rf"\b(?:similar|comparable|related)\s+cases?\b.{{0,80}}\b(?:{_SIMILAR_PROOF_VERBS})\b"
        rf".{{0,40}}\b(?:{_SIMILAR_PROOF_OBJECTS})\b",
        re.I,
    ),
)

# Sentence/clause-level negation markers. If any appears in the clause around an
# unsafe match, the match is treated as DEFENSIVE wording and allowed. Markers
# carry a trailing space and the clause is space-padded before matching, so a
# clause-final "not" is still detected without matching substrings of unrelated
# words (e.g. "annotation"). "not " covers do/does/is/are/must/should/cannot
# not; "n't " covers don't/doesn't/can't/shouldn't/...; "refrain " covers
# "refrain from".
NEGATION_MARKERS = (
    "not ",
    "n't ",
    "never ",
    "without ",
    "avoid ",
    "avoids ",
    "avoiding ",
    "prevent ",
    "prevents ",
    "preventing ",
    "prevented ",
    "refrain ",
)


def _require_non_blank(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value.strip()


class GroundedBriefItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    citation_ids: list[str] = Field(default_factory=list)

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "text")


class GroundedBriefOfficialVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_level: str | None = None
    decision: str | None = None
    simulated_decision: bool = True
    authority: str = "deterministic_policy"


class GroundedAnalystBrief(BaseModel):
    """Validated structured analyst brief safe for UI rendering and export."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = GROUNDED_BRIEF_SCHEMA_VERSION
    title: str
    context_summary: str
    official_verdict: GroundedBriefOfficialVerdict
    executive_summary: list[GroundedBriefItem] = Field(default_factory=list)
    what_happened: list[GroundedBriefItem] = Field(default_factory=list)
    why_it_matters: list[GroundedBriefItem] = Field(default_factory=list)
    supporting_evidence: list[GroundedBriefItem] = Field(default_factory=list)
    evidence_gap_summary: list[GroundedBriefItem] = Field(default_factory=list)
    advisory_context: list[GroundedBriefItem] = Field(default_factory=list)
    recommended_next_steps: list[GroundedBriefItem] = Field(default_factory=list)
    unsafe_assumptions: list[GroundedBriefItem] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    citations: list[GroundingCitation] = Field(default_factory=list)
    safety_boundary: list[str] = Field(default_factory=list)
    llm_status: LLMStatus

    @field_validator("title", "context_summary")
    @classmethod
    def required_text_must_not_be_empty(cls, value: str) -> str:
        return _require_non_blank(value, "required text")

    @field_validator("limitations", "safety_boundary")
    @classmethod
    def string_lists_must_not_include_blanks(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value.strip()]


def generate_grounded_analyst_brief(
    bundle: EvidenceGroundingBundle,
    llm_client: Any | None = None,
) -> GroundedAnalystBrief:
    """Generate or fallback to a validated structured analyst brief."""

    if llm_client is None:
        return build_deterministic_grounded_brief(bundle, "not_used_deterministic_fallback")

    try:
        raw = _call_client(llm_client, _brief_prompt(bundle))
    except Exception:
        return build_deterministic_grounded_brief(bundle, "unavailable_fallback")

    try:
        payload = _payload_to_dict(raw)
        brief = GroundedAnalystBrief.model_validate(payload)
    except (TypeError, ValueError, ValidationError, json.JSONDecodeError):
        return build_deterministic_grounded_brief(bundle, "invalid_json_fallback")

    guardrail_status = _guardrail_status(brief, bundle)
    if guardrail_status is not None:
        return build_deterministic_grounded_brief(bundle, guardrail_status)

    return brief.model_copy(update={"llm_status": "used"})


def build_deterministic_grounded_brief(
    bundle: EvidenceGroundingBundle,
    llm_status: LLMStatus = "not_used_deterministic_fallback",
) -> GroundedAnalystBrief:
    """Build a deterministic fallback brief from bundle fields only."""

    primary_ids = _primary_citation_ids(bundle)
    gap_ids = list(bundle.evidence_gaps.citation_ids)
    summary = _context_summary(bundle)
    executive = [
        GroundedBriefItem(
            text="Official Risk Level and Decision come from the deterministic pipeline, not from AI.",
            citation_ids=_verdict_citation_ids(bundle),
        ),
        GroundedBriefItem(
            text="This brief is evidence-grounded advisory context for human review.",
            citation_ids=primary_ids or gap_ids,
        ),
    ]
    what_happened = [
        GroundedBriefItem(
            text=_detection_summary(bundle),
            citation_ids=primary_ids,
        )
    ]
    why_it_matters = [
        GroundedBriefItem(
            text="The current event should be reviewed using the cited deterministic findings and missing-evidence list before any operational action.",
            citation_ids=primary_ids or gap_ids,
        )
    ]
    supporting = _supporting_evidence_items(bundle)
    gap_summary = [
        GroundedBriefItem(text=text, citation_ids=gap_ids)
        for text in bundle.evidence_gaps.missing_evidence[:6]
    ]
    advisory = _advisory_context_items(bundle)
    next_steps = [
        GroundedBriefItem(text=text, citation_ids=gap_ids)
        for text in bundle.evidence_gaps.recommended_checks[:6]
    ]
    unsafe = [
        GroundedBriefItem(text=text, citation_ids=gap_ids)
        for text in bundle.evidence_gaps.unsafe_assumptions[:6]
    ]
    unsafe.extend(_fixed_unsafe_assumptions(bundle))

    return GroundedAnalystBrief(
        title="Evidence-Grounded AI Analyst Brief",
        context_summary=summary,
        official_verdict=GroundedBriefOfficialVerdict(
            risk_level=bundle.official_verdict.risk_level,
            decision=bundle.official_verdict.decision,
            simulated_decision=bundle.official_verdict.simulated_decision,
            authority=bundle.official_verdict.authority,
        ),
        executive_summary=executive,
        what_happened=what_happened,
        why_it_matters=why_it_matters,
        supporting_evidence=supporting,
        evidence_gap_summary=gap_summary,
        advisory_context=advisory,
        recommended_next_steps=next_steps,
        unsafe_assumptions=unsafe,
        limitations=_limitations(bundle),
        citations=list(bundle.citations),
        safety_boundary=list(bundle.safety_boundary),
        llm_status=llm_status,
    )


def _call_client(llm_client: Any, prompt: str) -> Any:
    for method_name in ("generate_json", "invoke", "complete", "generate"):
        method = getattr(llm_client, method_name, None)
        if callable(method):
            return method(prompt)
    if callable(llm_client):
        return llm_client(prompt)
    raise TypeError("llm_client does not expose a supported call method")


def _payload_to_dict(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    content = getattr(raw, "content", raw)
    if isinstance(content, bytes):
        content = content.decode("utf-8")
    if isinstance(content, str):
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    raise TypeError("LLM response must be a dict or JSON object string")


def _brief_prompt(bundle: EvidenceGroundingBundle) -> str:
    return (
        "Return JSON matching schema v2.9-ai-analyst-brief1. Copy official_verdict exactly. "
        "Use only provided citation IDs. Do not provide exploit, PoC, traffic generation, "
        "load testing, real enforcement, or proof-of-compromise claims from advisory context.\n"
        + bundle.model_dump_json()
    )


def _guardrail_status(
    brief: GroundedAnalystBrief, bundle: EvidenceGroundingBundle
) -> LLMStatus | None:
    if brief.official_verdict != GroundedBriefOfficialVerdict(
        risk_level=bundle.official_verdict.risk_level,
        decision=bundle.official_verdict.decision,
        simulated_decision=bundle.official_verdict.simulated_decision,
        authority=bundle.official_verdict.authority,
    ):
        return "blocked_by_guardrail"
    if _contains_blocked_language(brief):
        return "blocked_by_guardrail"
    if not _citations_are_valid(brief, bundle):
        return "invalid_json_fallback"
    return None


def _contains_blocked_language(brief: GroundedAnalystBrief) -> bool:
    text = _guardrail_text(brief)
    return any(_has_non_negated_match(text, pattern) for pattern in BLOCKED_LANGUAGE_PATTERNS)


def _has_non_negated_match(text: str, pattern: re.Pattern[str]) -> bool:
    """True if ``pattern`` matches a clause that is not defensively negated."""

    for match in pattern.finditer(text):
        clause = (_sentence_around(text, match.start(), match.end()) + " ").casefold()
        if any(marker in clause for marker in NEGATION_MARKERS):
            continue
        return True
    return False


def _sentence_around(text: str, start: int, end: int) -> str:
    """Return the clause around a match, bounded by '.', ';', or newline.

    Clause-level (not whole-text) scoping keeps a negation in one sentence from
    masking an unsafe assertion in a different clause.
    """

    left = max(
        text.rfind(".", 0, start),
        text.rfind(";", 0, start),
        text.rfind("\n", 0, start),
    )
    right_candidates = [
        pos
        for pos in (text.find(".", end), text.find(";", end), text.find("\n", end))
        if pos != -1
    ]
    right = min(right_candidates) if right_candidates else len(text)
    return text[left + 1 : right]


def _citations_are_valid(brief: GroundedAnalystBrief, bundle: EvidenceGroundingBundle) -> bool:
    known = {citation.citation_id for citation in bundle.citations}
    if not brief.citations:
        return False
    for citation in brief.citations:
        if citation.citation_id not in known:
            return False
    for item in [*brief.supporting_evidence, *brief.advisory_context]:
        if not item.citation_ids:
            return False
        if any(citation_id not in known for citation_id in item.citation_ids):
            return False
    return True


def _context_summary(bundle: EvidenceGroundingBundle) -> str:
    active = bundle.active_context
    label = active.attack_type or active.finding_type or active.event_kind
    return f"{bundle.context_kind}: {label}"


def _detection_summary(bundle: EvidenceGroundingBundle) -> str:
    rule_text = ", ".join(bundle.official_detection.matched_rule_ids) or "no rule IDs recorded"
    return f"Rule-based detection source {bundle.official_detection.detection_source} recorded: {rule_text}."


def _primary_citation_ids(bundle: EvidenceGroundingBundle) -> list[str]:
    ids = list(bundle.official_detection.citation_ids)
    if ids:
        return ids
    return [item.citation_id for item in bundle.evidence_items[:2]]


def _verdict_citation_ids(bundle: EvidenceGroundingBundle) -> list[str]:
    return list(bundle.official_verdict.citation_ids or _primary_citation_ids(bundle))


def _supporting_evidence_items(bundle: EvidenceGroundingBundle) -> list[GroundedBriefItem]:
    items: list[GroundedBriefItem] = []
    for rule_id, citation_id in zip(
        bundle.official_detection.matched_rule_ids,
        bundle.official_detection.citation_ids,
        strict=False,
    ):
        items.append(GroundedBriefItem(text=f"Matched deterministic rule: {rule_id}.", citation_ids=[citation_id]))
    for evidence in bundle.evidence_items[:6]:
        text = evidence.description
        if evidence.value_summary:
            text = f"{text} Value summary: {evidence.value_summary}."
        items.append(GroundedBriefItem(text=text, citation_ids=[evidence.citation_id]))
    return items


def _advisory_context_items(bundle: EvidenceGroundingBundle) -> list[GroundedBriefItem]:
    items: list[GroundedBriefItem] = []
    for context in bundle.rag_context:
        items.append(
            GroundedBriefItem(
                text="Knowledge Q&A / RAG context is advisory only and source-backed; it does not determine the current event verdict.",
                citation_ids=[context.citation_id],
            )
        )
    for case in bundle.similar_cases:
        items.append(
            GroundedBriefItem(
                text=f"Approved similar case {case.case_id} is comparison context only and not proof of current compromise or execution.",
                citation_ids=[case.citation_id],
            )
        )
    for graph in bundle.graph_context:
        items.append(
            GroundedBriefItem(
                text=f"Graph relationship context ({graph.relationship}) is not a detection source.",
                citation_ids=[graph.citation_id],
            )
        )
    return items


def _fixed_unsafe_assumptions(bundle: EvidenceGroundingBundle) -> list[GroundedBriefItem]:
    items: list[GroundedBriefItem] = []
    if bundle.similar_cases:
        items.append(
            GroundedBriefItem(
                text="Do not treat approved similar cases as proof that the current event is compromised.",
                citation_ids=[case.citation_id for case in bundle.similar_cases[:3]],
            )
        )
    if bundle.graph_context:
        items.append(
            GroundedBriefItem(
                text="Do not treat graph context as the detection source or as an override of the official verdict.",
                citation_ids=[item.citation_id for item in bundle.graph_context[:3]],
            )
        )
    return items


def _limitations(bundle: EvidenceGroundingBundle) -> list[str]:
    limitations = [
        "This brief is advisory analyst context only.",
        "Official Risk Level and Decision are copied from deterministic policy.",
        "Human review is required before any operational action.",
    ]
    if not bundle.rag_context:
        limitations.append("No structured RAG context was supplied to this bundle.")
    if not bundle.similar_cases:
        limitations.append("No structured approved similar-case context was supplied to this bundle.")
    if not bundle.graph_context:
        limitations.append("No structured graph context was supplied to this bundle.")
    return limitations


def _guardrail_text(brief: GroundedAnalystBrief) -> str:
    """Return LLM-authored/narrative text, excluding fixed boundary boilerplate."""

    values: list[str] = [brief.title, brief.context_summary]
    for section in (
        brief.executive_summary,
        brief.what_happened,
        brief.why_it_matters,
        brief.supporting_evidence,
        brief.evidence_gap_summary,
        brief.advisory_context,
        brief.recommended_next_steps,
        brief.unsafe_assumptions,
    ):
        values.extend(item.text for item in section)
    values.extend(brief.limitations)
    return "\n".join(values)


__all__ = [
    "GROUNDED_BRIEF_SCHEMA_VERSION",
    "GroundedAnalystBrief",
    "GroundedBriefItem",
    "GroundedBriefOfficialVerdict",
    "build_deterministic_grounded_brief",
    "generate_grounded_analyst_brief",
]
