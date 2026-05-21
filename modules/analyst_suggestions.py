import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

SuggestionKind = Literal[
    "decision_reason",
    "evidence_explanation",
    "next_steps",
    "rule_explanation",
    "risk_decision_difference",
    "safety_boundary",
]

EV_ID_PATTERN = re.compile(r"\bEV[ -]?(\d{3,})\b", re.IGNORECASE)
FINDING_ID_PATTERN = re.compile(r"\bF[ -]?(\d{3,})\b", re.IGNORECASE)
RULE_ID_PATTERN = re.compile(r"\b(SQLI|XSS|CMD|PATH)[ -]?(\d{3,})\b", re.IGNORECASE)


class AnalystSuggestion(BaseModel):
    kind: SuggestionKind
    question: str
    reason: str

    @field_validator("question", "reason")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be empty")
        return value


class AnalystSuggestionSet(BaseModel):
    suggestions: list[AnalystSuggestion] = Field(default_factory=list)

    def questions(self) -> list[str]:
        return [suggestion.question for suggestion in self.suggestions]

    def by_kind(self, kind: SuggestionKind) -> list[AnalystSuggestion]:
        return [suggestion for suggestion in self.suggestions if suggestion.kind == kind]


def suggest_followup_questions(
    report_text: str | None = None,
    decision: str | None = None,
    risk_level: str | None = None,
    evidence_ids: list[str] | None = None,
    finding_ids: list[str] | None = None,
    rule_ids: list[str] | None = None,
    limit: int = 5,
) -> AnalystSuggestionSet:
    text = str(report_text or "")
    normalized_decision = str(decision or "").upper()
    normalized_report = text.upper()
    suggestions: list[AnalystSuggestion] = []

    if "MONITOR" in normalized_decision:
        _add_suggestion(
            suggestions,
            "decision_reason",
            "為什麼是 MONITOR？",
            "Decision is MONITOR.",
        )
    if "BLOCK" in normalized_decision:
        _add_suggestion(
            suggestions,
            "decision_reason",
            "為什麼是 BLOCK？",
            "Decision is BLOCK.",
        )
    if risk_level and decision:
        _add_suggestion(
            suggestions,
            "risk_decision_difference",
            "Risk Level 跟 Decision 差在哪？",
            "Risk Level and Decision are both available.",
        )

    for evidence_id in _dedupe([*(evidence_ids or []), *extract_evidence_ids_from_text(text)]):
        _add_suggestion(
            suggestions,
            "evidence_explanation",
            f"{evidence_id} 是什麼意思？",
            "Evidence ID is present.",
        )

    for finding_id in _dedupe([*(finding_ids or []), *extract_finding_ids_from_text(text)]):
        _add_suggestion(
            suggestions,
            "evidence_explanation",
            f"{finding_id} 代表什麼？",
            "Finding ID is present.",
        )

    for rule_id in _dedupe([*(rule_ids or []), *extract_rule_ids_from_text(text)]):
        _add_suggestion(
            suggestions,
            "rule_explanation",
            f"{rule_id} 這條規則為什麼命中？",
            "Rule ID is present.",
        )

    if _looks_suspicious(text, normalized_report, normalized_decision):
        _add_suggestion(
            suggestions,
            "next_steps",
            "下一步要查什麼？",
            "Report text looks suspicious or action-oriented.",
        )

    if "SIMULATED" in normalized_report or "模擬" in text:
        _add_suggestion(
            suggestions,
            "safety_boundary",
            "這個 BLOCK / MONITOR / ALLOW 是真的執行嗎？",
            "Report mentions simulated behavior.",
        )

    if not suggestions:
        _add_suggestion(
            suggestions,
            "next_steps",
            "這份報告的重點是什麼？",
            "No specific report signals were provided.",
        )
        _add_suggestion(
            suggestions,
            "next_steps",
            "我下一步應該先查什麼？",
            "No specific report signals were provided.",
        )

    return AnalystSuggestionSet(suggestions=suggestions[: max(limit, 0)])


def extract_evidence_ids_from_text(report_text: str) -> list[str]:
    return _extract_ids(EV_ID_PATTERN, str(report_text or ""), "EV")


def extract_finding_ids_from_text(report_text: str) -> list[str]:
    return _extract_ids(FINDING_ID_PATTERN, str(report_text or ""), "F")


def extract_rule_ids_from_text(report_text: str) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for match in RULE_ID_PATTERN.finditer(str(report_text or "")):
        normalized = f"{match.group(1).upper()}-{match.group(2)}"
        if normalized not in seen:
            values.append(normalized)
            seen.add(normalized)
    return values


def _extract_ids(pattern: re.Pattern[str], text: str, prefix: str) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for match in pattern.finditer(text):
        normalized = f"{prefix}-{match.group(1)}"
        if normalized not in seen:
            values.append(normalized)
            seen.add(normalized)
    return values


def _add_suggestion(
    suggestions: list[AnalystSuggestion],
    kind: SuggestionKind,
    question: str,
    reason: str,
) -> None:
    if any(suggestion.question == question for suggestion in suggestions):
        return
    suggestions.append(AnalystSuggestion(kind=kind, question=question, reason=reason))


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = _normalize_id(value)
        if normalized and normalized not in seen:
            deduped.append(normalized)
            seen.add(normalized)
    return deduped


def _normalize_id(value: str) -> str:
    text = str(value or "").strip().upper().replace(" ", "-")
    return re.sub(r"-+", "-", text)


def _looks_suspicious(text: str, normalized_report: str, normalized_decision: str) -> bool:
    if any(decision in normalized_decision for decision in ("MONITOR", "BLOCK")):
        return True
    return any(
        term in normalized_report
        for term in (
            "SUSPICIOUS",
            "POSSIBLE COMPROMISE",
            "BRUTE FORCE",
            "ATTACK",
            "ALERT",
            "HIGH",
            "MONITOR",
            "BLOCK",
        )
    ) or any(term in text for term in ("可疑", "攻擊", "告警", "高風險"))
