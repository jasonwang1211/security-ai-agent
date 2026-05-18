import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

EvalCaseKind = Literal[
    "answer_safety",
    "report_qa",
    "router",
    "payload_detection",
]

ExpectedRiskStatus = Literal[
    "CLEAN",
    "SUSPICIOUS",
    "UNKNOWN",
]

ExpectedDecision = Literal[
    "ALLOW",
    "MONITOR",
    "BLOCK",
    "UNKNOWN",
]


def _require_non_blank(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


def _remove_blank_strings(values: list[str]) -> list[str]:
    return [value.strip() for value in values if value.strip()]


class BaseEvalCase(BaseModel):
    id: str
    kind: EvalCaseKind
    notes: str | None = None

    @field_validator("id")
    @classmethod
    def id_must_not_be_blank(cls, value: str) -> str:
        return _require_non_blank(value, "id")

    @field_validator("notes")
    @classmethod
    def notes_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None:
            return _require_non_blank(value, "notes")
        return value


class AnswerSafetyCase(BaseEvalCase):
    kind: Literal["answer_safety"] = "answer_safety"
    answer: str
    sources: list[str] = Field(default_factory=list)
    expected_findings: list[str] = Field(default_factory=list)
    forbidden_claims: list[str] = Field(default_factory=list)

    @field_validator("answer")
    @classmethod
    def answer_must_not_be_blank(cls, value: str) -> str:
        return _require_non_blank(value, "answer")

    @field_validator("sources", "expected_findings", "forbidden_claims")
    @classmethod
    def lists_should_not_include_blanks(cls, value: list[str]) -> list[str]:
        return _remove_blank_strings(value)


class ReportQACase(BaseEvalCase):
    kind: Literal["report_qa"] = "report_qa"
    question: str
    expected_contains: list[str] = Field(default_factory=list)
    forbidden_contains: list[str] = Field(default_factory=list)
    expected_sources: list[str] = Field(default_factory=list)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        return _require_non_blank(value, "question")

    @field_validator("expected_contains", "forbidden_contains", "expected_sources")
    @classmethod
    def lists_should_not_include_blanks(cls, value: list[str]) -> list[str]:
        return _remove_blank_strings(value)


class RouterCase(BaseEvalCase):
    kind: Literal["router"] = "router"
    user_input: str
    expected_input_kind: str
    expected_route: str

    @field_validator("user_input", "expected_input_kind", "expected_route")
    @classmethod
    def text_fields_must_not_be_blank(cls, value: str) -> str:
        return _require_non_blank(value, "text field")


class PayloadDetectionCase(BaseEvalCase):
    kind: Literal["payload_detection"] = "payload_detection"
    payload: str
    expected_status: ExpectedRiskStatus
    expected_attack_types: list[str] = Field(default_factory=list)
    expected_decision: ExpectedDecision = "UNKNOWN"

    @field_validator("payload")
    @classmethod
    def payload_must_not_be_blank(cls, value: str) -> str:
        return _require_non_blank(value, "payload")

    @field_validator("expected_attack_types")
    @classmethod
    def expected_attack_types_should_not_include_blanks(cls, value: list[str]) -> list[str]:
        return _remove_blank_strings(value)


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    jsonl_path = Path(path)

    with jsonl_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped_line = line.strip()
            if not stripped_line:
                continue

            try:
                record = json.loads(stripped_line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {jsonl_path} at line {line_number}") from exc

            if not isinstance(record, dict):
                raise ValueError(f"Expected JSON object in {jsonl_path} at line {line_number}")

            records.append(record)

    return records


def load_answer_safety_cases(path: str | Path) -> list[AnswerSafetyCase]:
    return [AnswerSafetyCase.model_validate(record) for record in load_jsonl(path)]


def load_report_qa_cases(path: str | Path) -> list[ReportQACase]:
    return [ReportQACase.model_validate(record) for record in load_jsonl(path)]


def load_router_cases(path: str | Path) -> list[RouterCase]:
    return [RouterCase.model_validate(record) for record in load_jsonl(path)]


def load_payload_detection_cases(path: str | Path) -> list[PayloadDetectionCase]:
    return [PayloadDetectionCase.model_validate(record) for record in load_jsonl(path)]


def _as_base_cases(cases: Iterable[BaseModel]) -> list[BaseModel]:
    return list(cases)


def load_all_eval_cases(directory: str | Path = "eval_cases") -> dict[str, list[BaseModel]]:
    eval_directory = Path(directory)
    return {
        "answer_safety": _as_base_cases(
            load_answer_safety_cases(eval_directory / "answer_safety_cases.jsonl")
        ),
        "report_qa": _as_base_cases(load_report_qa_cases(eval_directory / "report_qa_cases.jsonl")),
        "router": _as_base_cases(load_router_cases(eval_directory / "router_cases.jsonl")),
        "payload_detection": _as_base_cases(
            load_payload_detection_cases(eval_directory / "payload_detection_cases.jsonl")
        ),
    }
