from modules.rag.metadata import KnowledgeDocMetadata
from modules.rag.retrieval_planner import (
    MetadataAwareRetrievalPlan,
    build_metadata_aware_retrieval_plan,
)
from modules.rag.source_assembly import (
    build_answer_from_plan,
    default_limitations_for_plan,
)
from modules.rag.types import AnswerWithSources, RAGConfidence


def explain_report_question(
    question: str,
    metadata_items: list[KnowledgeDocMetadata],
    context: dict[str, object] | None = None,
) -> AnswerWithSources:
    plan = build_metadata_aware_retrieval_plan(question, metadata_items)
    answer_text = _build_report_answer_text(question, plan, context or {})
    return build_answer_from_plan(
        answer_text,
        plan,
        confidence=_confidence_for_plan(plan),
        limitations=default_limitations_for_plan(plan),
    )


def explain_rule_question(
    question: str,
    metadata_items: list[KnowledgeDocMetadata],
    rule_metadata: dict[str, dict[str, object]] | None = None,
) -> AnswerWithSources:
    plan = build_metadata_aware_retrieval_plan(question, metadata_items)
    answer_text = _build_rule_answer_text(question, plan, rule_metadata or {})
    return build_answer_from_plan(
        answer_text,
        plan,
        confidence=_confidence_for_plan(plan),
        limitations=default_limitations_for_plan(plan),
    )


def _build_report_answer_text(
    question: str,
    plan: MetadataAwareRetrievalPlan,
    context: dict[str, object],
) -> str:
    question_upper = question.upper()
    evidence_ids = plan.base_plan.exact_ids.values_by_kind("evidence_id")
    context_note = _context_summary(context)

    if _contains_any(question_upper, ["MONITOR", "BLOCK", "ALLOW", "DECISION"]):
        return (
            "Decision is a simulated, policy-controlled output from the deterministic triage "
            "logic. MONITOR means observe and investigate; it is not real blocking, firewall, "
            "WAF, SIEM, or SOAR enforcement. RAG is explanation-only and cannot override the "
            f"Risk Level or Decision.{context_note}"
        )

    if "RISK LEVEL" in question_upper:
        return (
            "Risk Level describes severity, while Decision describes the simulated analyst "
            "action. Both remain deterministic and policy-controlled; RAG only explains the "
            f"report and is not a detection source.{context_note}"
        )

    if evidence_ids:
        return (
            f"{', '.join(evidence_ids)} is a stable evidence reference in the incident or "
            "report. It helps analysts cite the relevant observation, but it does not prove "
            "confirmed compromise by itself. RAG is explanation-only and the deterministic "
            f"detector and policy remain authoritative.{context_note}"
        )

    if _looks_like_next_steps_question(question_upper):
        return (
            "Recommended next steps are safe analyst review only: inspect the cited evidence, "
            "compare related findings, check affected accounts or hosts, and document whether "
            "the activity is expected. Treat possible account compromise as suspicious, not "
            f"confirmed compromise. No automated response is performed.{context_note}"
        )

    return (
        "This report explanation is source-cited and conservative. RAG is advisory only, not a "
        "detection source, and simulated BLOCK, MONITOR, or ALLOW decisions remain controlled "
        f"by deterministic policy logic.{context_note}"
    )


def _build_rule_answer_text(
    question: str,
    plan: MetadataAwareRetrievalPlan,
    rule_metadata: dict[str, dict[str, object]],
) -> str:
    rule_ids = plan.base_plan.exact_ids.values_by_kind("rule_id")
    if not rule_ids:
        return (
            "No explicit rule ID was found in the question. Rule Explainer v2 explains existing "
            "rules only; it does not generate, modify, enable, disable, or activate rules."
        )

    sections: list[str] = []
    for rule_id in rule_ids:
        metadata = _lookup_rule_metadata(rule_id, rule_metadata)
        sections.append(_summarize_rule_metadata(rule_id, metadata))

    sections.append(
        "This explanation is advisory and source-cited. It does not claim the rule matched "
        "unless matched-rule context is provided, and it does not generate or activate rules."
    )
    return " ".join(sections)


def _summarize_rule_metadata(rule_id: str, metadata: dict[str, object] | None) -> str:
    if metadata is None:
        return (
            f"{rule_id} was referenced, but rule metadata is not available in this helper "
            "context."
        )

    fields: list[str] = [f"{rule_id} is an existing detection rule identifier."]
    for label, key in [
        ("attack_type", "attack_type"),
        ("severity", "severity"),
        ("confidence", "confidence"),
        ("patterns", "patterns"),
        ("mitre_techniques", "mitre_techniques"),
    ]:
        value = metadata.get(key)
        if value:
            fields.append(f"{label}: {_format_metadata_value(value)}.")

    fields.append("It is used for explanation only and does not create or activate new rules.")
    return " ".join(fields)


def _confidence_for_plan(plan: MetadataAwareRetrievalPlan) -> RAGConfidence:
    if not plan.candidates:
        return "LOW"
    if plan.base_plan.exact_ids.has_any():
        return "HIGH"
    return "MEDIUM"


def _lookup_rule_metadata(
    rule_id: str,
    rule_metadata: dict[str, dict[str, object]],
) -> dict[str, object] | None:
    for candidate_id, metadata in rule_metadata.items():
        if candidate_id.upper() == rule_id:
            return metadata
    return None


def _format_metadata_value(value: object) -> str:
    if isinstance(value, list | tuple | set):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return ", ".join(f"{key}={item}" for key, item in value.items())
    return str(value)


def _contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def _looks_like_next_steps_question(text: str) -> bool:
    return _contains_any(
        text,
        ["NEXT STEP", "NEXT STEPS", "INVESTIGATE", "CHECKLIST", "REVIEW", "下一步", "接下來", "調查"],
    )


def _context_summary(context: dict[str, object]) -> str:
    if not context:
        return ""

    available_keys = ", ".join(sorted(str(key) for key in context))
    return f" Context keys considered: {available_keys}."
