import re
from typing import Literal

from modules.rag.types import (
    ExtractedId,
    ExtractedIds,
    RAGIntent,
    RAGIntentDecision,
    RAGRetrievalPlan,
)

_IDKind = Literal[
    "evidence_id",
    "finding_id",
    "incident_id",
    "rule_id",
    "mitre_technique_id",
]
_RAGConfidence = Literal["LOW", "MEDIUM", "HIGH"]


_ID_PATTERN = re.compile(
    r"(?P<evidence>(?<![A-Z0-9])EV[\s-]?\d{3,}(?![A-Z0-9]))"
    r"|(?P<finding>(?<![A-Z0-9])F-\d{3,}(?![A-Z0-9]))"
    r"|(?P<incident>(?<![A-Z0-9])INC-[A-Z0-9]+(?:-[A-Z0-9]+)*(?![A-Z0-9]))"
    r"|(?P<rule>(?<![A-Z0-9])(?:XSS|SQLI|PATH|CMD)-\d{3,}(?![A-Z0-9]))"
    r"|(?P<mitre>(?<![A-Z0-9])T\d{4}(?:\.\d{3})?(?![A-Z0-9]))",
    re.IGNORECASE,
)

_ATTACK_TERMS = [
    "XSS",
    "SQL INJECTION",
    "SQLI",
    "COMMAND INJECTION",
    "PATH TRAVERSAL",
    "BRUTE FORCE",
    "CREDENTIAL STUFFING",
    "CSRF",
]
_KNOWLEDGE_TERMS = ["WHAT", "WHY", "HOW", "EXPLAIN", "MEAN", "是什麼", "什麼是", "如何", "怎麼"]


def extract_rag_ids(text: str) -> ExtractedIds:
    items: list[ExtractedId] = []
    seen: set[str] = set()

    for match in _ID_PATTERN.finditer(text):
        raw_value = match.group(0).strip()
        kind = _kind_from_match(match)
        normalized = _normalize_id(raw_value, kind)
        if normalized in seen:
            continue

        items.append(ExtractedId(value=raw_value, kind=kind, normalized=normalized))
        seen.add(normalized)

    return ExtractedIds(items=items)


def classify_rag_intent(question: str) -> RAGIntentDecision:
    extracted_ids = extract_rag_ids(question)
    upper_question = question.upper()

    if extracted_ids.values_by_kind("evidence_id"):
        return _decision(
            "evidence_question",
            "HIGH",
            "Question references an explicit evidence ID.",
            requires_context=True,
        )

    if extracted_ids.values_by_kind("finding_id"):
        return _decision(
            "finding_question",
            "HIGH",
            "Question references an explicit finding ID.",
            requires_context=True,
        )

    if extracted_ids.values_by_kind("rule_id") or extracted_ids.values_by_kind("mitre_technique_id"):
        return _decision(
            "rule_question",
            "HIGH",
            "Question references an explicit rule or MITRE technique ID.",
        )

    if extracted_ids.values_by_kind("incident_id") or _contains_any(
        upper_question,
        ["下一步", "接下來", "調查", "處理", "INCIDENT RESPONSE", "CHECKLIST"],
    ):
        return _decision(
            "incident_response",
            "HIGH" if extracted_ids.values_by_kind("incident_id") else "MEDIUM",
            "Question asks for incident response or investigation guidance.",
            requires_context=True,
        )

    if _contains_any(upper_question, ["FALSE POSITIVE", "誤判", "誤報"]):
        return _decision(
            "false_positive_question",
            "MEDIUM",
            "Question asks about false positives.",
        )

    if _contains_any(
        upper_question,
        ["RISK LEVEL", "DECISION", "MONITOR", "BLOCK", "ALLOW", "為什麼是 MONITOR", "為什麼是 BLOCK"],
    ):
        return _decision(
            "report_question",
            "MEDIUM",
            "Question asks about report risk level or decision fields.",
            requires_context=True,
        )

    if _contains_any(upper_question, ["RULE", "規則", "為什麼命中"]):
        return _decision("rule_question", "MEDIUM", "Question asks about detection rules.")

    if _contains_any(upper_question, ["EVIDENCE", "證據"]) or _contains_standalone_ev(upper_question):
        return _decision(
            "evidence_question",
            "MEDIUM",
            "Question asks about evidence.",
            requires_context=True,
        )

    if _contains_any(upper_question, ["FINDING", "發現", "判定項目"]):
        return _decision(
            "finding_question",
            "MEDIUM",
            "Question asks about findings.",
            requires_context=True,
        )

    if _looks_like_attack_knowledge_question(upper_question):
        return _decision(
            "attack_knowledge",
            "MEDIUM",
            "Question asks about attack knowledge.",
        )

    return _decision("unknown", "LOW", "No RAG intent rule matched.")


def build_rag_retrieval_plan(question: str) -> RAGRetrievalPlan:
    decision = classify_rag_intent(question)
    exact_ids = extract_rag_ids(question)
    preferred_doc_types: list[str] = []
    metadata_filters: dict[str, str] = {}

    if decision.intent in {"report_question", "evidence_question", "incident_response"}:
        preferred_doc_types = ["report_explainer"]
        metadata_filters = {"doc_type": "report_explainer"}
    elif decision.intent == "rule_question":
        preferred_doc_types = ["detection_rule", "report_explainer"]
    elif decision.intent == "attack_knowledge":
        preferred_doc_types = ["attack_technique"]

    return RAGRetrievalPlan(
        intent=decision.intent,
        query=question,
        metadata_filters=metadata_filters,
        exact_ids=exact_ids,
        preferred_doc_types=preferred_doc_types,
        use_vector_search=True,
    )


def lookup_extracted_ids(
    extracted_ids: ExtractedIds,
    available_ids: set[str] | list[str] | tuple[str, ...],
) -> dict[str, bool]:
    normalized_available_ids = {_normalize_available_id(value) for value in available_ids}

    return {
        item.normalized: _normalize_available_id(item.normalized) in normalized_available_ids
        for item in extracted_ids.items
    }


def has_missing_ids(result: dict[str, bool]) -> bool:
    return any(not exists for exists in result.values())


def _kind_from_match(match: re.Match[str]) -> _IDKind:
    if match.group("evidence"):
        return "evidence_id"
    if match.group("finding"):
        return "finding_id"
    if match.group("incident"):
        return "incident_id"
    if match.group("rule"):
        return "rule_id"
    return "mitre_technique_id"


def _normalize_id(value: str, kind: _IDKind) -> str:
    stripped_value = value.strip()
    if kind == "evidence_id":
        digits = re.search(r"\d{3,}", stripped_value)
        if digits:
            return f"EV-{digits.group(0)}"
    return stripped_value.upper()


def _normalize_available_id(value: str) -> str:
    return value.strip().upper()


def _decision(
    intent: RAGIntent,
    confidence: _RAGConfidence,
    reason: str,
    requires_context: bool = False,
) -> RAGIntentDecision:
    return RAGIntentDecision(
        intent=intent,
        confidence=confidence,
        reason=reason,
        requires_context=requires_context,
    )


def _contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def _contains_standalone_ev(text: str) -> bool:
    return re.search(r"(?<![A-Z0-9])EV(?![A-Z0-9])", text) is not None


def _looks_like_attack_knowledge_question(text: str) -> bool:
    return _contains_any(text, _ATTACK_TERMS) and _contains_any(text, _KNOWLEDGE_TERMS)
