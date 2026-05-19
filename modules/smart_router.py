import re
from pathlib import PurePath
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

SmartInputKind = Literal[
    "payload_or_event",
    "raw_log_line",
    "log_file_path",
    "security_knowledge_question",
    "report_followup",
    "incident_export",
    "unknown",
]

SmartRouteName = Literal[
    "payload_triage",
    "raw_log_translate",
    "log_file_ingest",
    "rag_security_qa",
    "report_followup",
    "incident_json_export",
    "clarification_required",
]

SmartRouterConfidence = Literal[
    "HIGH",
    "MEDIUM",
    "LOW",
]

HTTP_METHOD_PATTERN = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+/\S*", re.IGNORECASE)
STATUS_CODE_PATTERN = re.compile(r"\b[1-5][0-9]{2}\b")
IP_ADDRESS_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
TIMESTAMP_PATTERN = re.compile(
    r"\b(?:\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}|"
    r"[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\b"
)
REPORT_ID_PATTERN = re.compile(r"\b(?:EV|F)[ -]?\d{3,}\b", re.IGNORECASE)
LOCAL_LOG_PATH_PATTERN = re.compile(
    r"(?:[A-Za-z]:[\\/][^\s]+\.log|(?:\.{1,2}[\\/])?[^\s\\/]+[\\/][^\s]+\.log)$",
    re.IGNORECASE,
)

PAYLOAD_SIGNATURES = (
    "<script",
    "alert(",
    "' or '1'='1",
    '" or "1"="1',
    "union select",
    "../",
    "..\\",
    "/etc/passwd",
    "; rm ",
    "&&",
    "||",
    "$(",
    "| nc",
)
SECURITY_TOPIC_TERMS = (
    "xss",
    "sql injection",
    "command injection",
    "path traversal",
    "brute force",
    "credential stuffing",
    "csrf",
    "zero day",
    "zero-day",
    "attack",
    "security",
    "triage",
    "零日",
    "防禦",
    "偵測",
    "攻擊",
)
QUESTION_MARKERS = ("?", "？", "what", "why", "how", "什麼", "為什麼", "如何", "怎麼")
REPORT_FOLLOWUP_TERMS = (
    "為什麼是 monitor",
    "為什麼是 block",
    "risk level",
    "decision",
    "evidence",
    "這個報告",
)


class SmartRouterDecision(BaseModel):
    input_kind: SmartInputKind
    route: SmartRouteName
    confidence: SmartRouterConfidence = "MEDIUM"
    reason: str
    requires_clarification: bool = False

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("reason must not be empty")
        return value

    @model_validator(mode="after")
    def clarification_route_must_match_unknown(self) -> "SmartRouterDecision":
        if self.input_kind == "unknown" and self.route != "clarification_required":
            raise ValueError("unknown input must route to clarification_required")
        if self.route == "clarification_required" and self.input_kind != "unknown":
            raise ValueError("clarification_required route requires unknown input kind")
        if (self.input_kind == "unknown" or self.route == "clarification_required") and (
            not self.requires_clarification
        ):
            raise ValueError("unknown or clarification_required decisions must require clarification")
        return self


class SmartRouterPreview(BaseModel):
    decision: SmartRouterDecision
    would_execute: bool = False
    preview_text: str

    @field_validator("preview_text")
    @classmethod
    def preview_text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("preview_text must not be empty")
        return value

    @model_validator(mode="after")
    def preview_must_not_execute(self) -> "SmartRouterPreview":
        if self.would_execute:
            raise ValueError("Smart Router preview must not execute tools")
        return self


def route_user_input(user_input: str) -> SmartRouterDecision:
    text = user_input.strip()
    if not text:
        return _decision(
            "unknown",
            "clarification_required",
            "HIGH",
            "Input is blank.",
            requires_clarification=True,
        )

    if _looks_like_log_file_path(text):
        return _decision("log_file_path", "log_file_ingest", "HIGH", "Input looks like a log file path.")
    if _looks_like_raw_log_line(text):
        return _decision("raw_log_line", "raw_log_translate", "HIGH", "Input looks like a raw log line.")
    if _looks_like_incident_export(text):
        return _decision(
            "incident_export",
            "incident_json_export",
            "HIGH",
            "Input asks to export incident data.",
        )
    if _looks_like_report_followup(text):
        return _decision(
            "report_followup",
            "report_followup",
            "HIGH",
            "Input asks about report-specific evidence, risk, or decision context.",
        )
    if _looks_like_payload_or_event(text):
        return _decision(
            "payload_or_event",
            "payload_triage",
            "HIGH",
            "Input contains a strong payload or event signature.",
        )
    if _looks_like_security_question(text):
        return _decision(
            "security_knowledge_question",
            "rag_security_qa",
            "MEDIUM",
            "Input looks like a general security knowledge question.",
        )

    return _decision(
        "unknown",
        "clarification_required",
        "LOW",
        "Input does not match a known v1.7 router category.",
        requires_clarification=True,
    )


def preview_route(user_input: str) -> SmartRouterPreview:
    decision = route_user_input(user_input)
    if decision.route == "clarification_required":
        preview_text = (
            "路由預覽：目前無法判斷適合的工具，需要使用者補充資訊。"
            "此預覽不會執行任何工具，也不會改變風險等級或決策。"
        )
    else:
        preview_text = (
            f"路由預覽：系統判定此輸入適合交給 `{decision.route}`，"
            f"類型為 `{decision.input_kind}`，可信度 `{decision.confidence}`。"
            f"原因：{decision.reason} "
            "此預覽只顯示路由決策，不會執行工具，也不會改變風險等級或決策。"
        )

    return SmartRouterPreview(decision=decision, preview_text=preview_text)


def _decision(
    input_kind: SmartInputKind,
    route: SmartRouteName,
    confidence: SmartRouterConfidence,
    reason: str,
    *,
    requires_clarification: bool = False,
) -> SmartRouterDecision:
    return SmartRouterDecision(
        input_kind=input_kind,
        route=route,
        confidence=confidence,
        reason=reason,
        requires_clarification=requires_clarification,
    )


def _looks_like_log_file_path(text: str) -> bool:
    normalized = text.casefold()
    if normalized.endswith(".log"):
        return True
    if "demo_logs/" in normalized or "demo_logs\\" in normalized:
        return True
    if LOCAL_LOG_PATH_PATTERN.search(text):
        return True

    path = PurePath(text)
    return path.suffix.casefold() == ".log" and len(path.parts) > 1


def _looks_like_raw_log_line(text: str) -> bool:
    normalized = text.casefold()
    has_http_status = bool(HTTP_METHOD_PATTERN.search(text) and STATUS_CODE_PATTERN.search(text))
    has_timestamp_ip_status = bool(
        TIMESTAMP_PATTERN.search(text) and IP_ADDRESS_PATTERN.search(text) and STATUS_CODE_PATTERN.search(text)
    )
    has_structured_log_markers = any(
        marker in normalized for marker in ("source_ip", "status=401", "post /login")
    )
    has_auth_log_markers = "sshd" in normalized and "failed password" in normalized and bool(
        IP_ADDRESS_PATTERN.search(text)
    )
    return has_http_status or has_timestamp_ip_status or has_structured_log_markers or has_auth_log_markers


def _looks_like_incident_export(text: str) -> bool:
    normalized = text.casefold()
    has_export_intent = any(term in normalized for term in ("export", "匯出", "輸出"))
    has_incident_json = "incident" in normalized and "json" in normalized
    return has_export_intent and has_incident_json


def _looks_like_report_followup(text: str) -> bool:
    normalized = text.casefold()
    return bool(REPORT_ID_PATTERN.search(text) or any(term in normalized for term in REPORT_FOLLOWUP_TERMS))


def _looks_like_payload_or_event(text: str) -> bool:
    normalized = text.casefold()
    return any(signature in normalized for signature in PAYLOAD_SIGNATURES)


def _looks_like_security_question(text: str) -> bool:
    normalized = text.casefold()
    has_topic = any(term in normalized for term in SECURITY_TOPIC_TERMS)
    has_question_marker = any(marker in normalized for marker in QUESTION_MARKERS)
    return has_topic and has_question_marker
