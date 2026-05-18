from pathlib import Path
from typing import Any, Literal, get_args

from pydantic import BaseModel, Field, field_validator, model_validator

from modules.answer_guardrails import AnswerSafetyRule, check_answer_safety_case
from modules.eval_cases import (
    AnswerSafetyCase,
    load_all_eval_cases,
    load_answer_safety_cases,
)

EvalStatus = Literal[
    "passed",
    "failed",
    "skipped",
]

EvalSeverity = Literal[
    "info",
    "warning",
    "error",
]

EXPECTED_FINDING_RULE_ALIASES: dict[str, AnswerSafetyRule] = {
    "fake_enforcement_claim": "real_enforcement_claim",
    "rag_detection_source_claim": "rag_as_detection_source",
    "llm_final_verdict_override_claim": "llm_final_verdict_override",
    "monitor_confirmed_compromise_claim": "monitor_as_confirmed_compromise",
}


def _require_non_blank(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


class EvalFinding(BaseModel):
    case_id: str
    status: EvalStatus
    severity: EvalSeverity
    message: str
    details: dict[str, Any] = Field(default_factory=dict)

    @field_validator("case_id")
    @classmethod
    def case_id_must_not_be_blank(cls, value: str) -> str:
        return _require_non_blank(value, "case_id")

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        return _require_non_blank(value, "message")


class EvalRunSummary(BaseModel):
    total: int
    passed: int
    failed: int
    skipped: int
    findings: list[EvalFinding] = Field(default_factory=list)

    @field_validator("total", "passed", "failed", "skipped")
    @classmethod
    def counts_must_not_be_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("eval counts must not be negative")
        return value

    @model_validator(mode="after")
    def total_must_match_status_counts(self) -> "EvalRunSummary":
        if self.total != self.passed + self.failed + self.skipped:
            raise ValueError("total must equal passed + failed + skipped")
        return self

    def has_failures(self) -> bool:
        return self.failed > 0

    def failure_findings(self) -> list[EvalFinding]:
        return [finding for finding in self.findings if finding.status == "failed"]


def _normalize_expected_rule(value: str) -> AnswerSafetyRule | None:
    normalized_value = value.strip()
    if not normalized_value:
        return None
    if normalized_value in EXPECTED_FINDING_RULE_ALIASES:
        return EXPECTED_FINDING_RULE_ALIASES[normalized_value]
    allowed_rules = set(get_args(AnswerSafetyRule))
    if normalized_value in allowed_rules:
        return normalized_value  # type: ignore[return-value]
    return None


def _build_summary(findings: list[EvalFinding]) -> EvalRunSummary:
    passed = sum(1 for finding in findings if finding.status == "passed")
    failed = sum(1 for finding in findings if finding.status == "failed")
    skipped = sum(1 for finding in findings if finding.status == "skipped")
    return EvalRunSummary(
        total=len(findings),
        passed=passed,
        failed=failed,
        skipped=skipped,
        findings=findings,
    )


def evaluate_answer_safety_cases(
    cases: list[AnswerSafetyCase],
) -> EvalRunSummary:
    findings: list[EvalFinding] = []

    for case in cases:
        safety_report = check_answer_safety_case(case)
        error_rules = {
            finding.rule for finding in safety_report.findings if finding.severity == "ERROR"
        }
        expected_rules = {
            rule
            for rule in (_normalize_expected_rule(value) for value in case.expected_findings)
            if rule is not None
        }

        if expected_rules:
            matched_rules = sorted(expected_rules.intersection(error_rules))
            if matched_rules:
                findings.append(
                    EvalFinding(
                        case_id=case.id,
                        status="passed",
                        severity="info",
                        message="Expected answer safety finding was reported.",
                        details={"matched_rules": matched_rules},
                    )
                )
            else:
                findings.append(
                    EvalFinding(
                        case_id=case.id,
                        status="failed",
                        severity="error",
                        message="Expected answer safety finding was not reported.",
                        details={
                            "expected_rules": sorted(expected_rules),
                            "actual_error_rules": sorted(error_rules),
                        },
                    )
                )
            continue

        if case.forbidden_claims:
            if safety_report.has_errors():
                findings.append(
                    EvalFinding(
                        case_id=case.id,
                        status="passed",
                        severity="info",
                        message="Forbidden claim produced an answer safety error.",
                        details={"actual_error_rules": sorted(error_rules)},
                    )
                )
            else:
                findings.append(
                    EvalFinding(
                        case_id=case.id,
                        status="failed",
                        severity="error",
                        message="Forbidden claim did not produce an answer safety error.",
                        details={"forbidden_claims": case.forbidden_claims},
                    )
                )
            continue

        if safety_report.has_errors():
            findings.append(
                EvalFinding(
                    case_id=case.id,
                    status="failed",
                    severity="error",
                    message="Safe answer safety case produced unexpected errors.",
                    details={"actual_error_rules": sorted(error_rules)},
                )
            )
        else:
            findings.append(
                EvalFinding(
                    case_id=case.id,
                    status="passed",
                    severity="info",
                    message="Safe answer safety case produced no errors.",
                )
            )

    return _build_summary(findings)


def evaluate_text_expectations(
    case_id: str,
    text: str,
    expected_contains: list[str] | None = None,
    forbidden_contains: list[str] | None = None,
) -> list[EvalFinding]:
    normalized_text = text.casefold()
    findings: list[EvalFinding] = []

    for expected in expected_contains or []:
        if expected.casefold() not in normalized_text:
            findings.append(
                EvalFinding(
                    case_id=case_id,
                    status="failed",
                    severity="error",
                    message="Expected text was not found.",
                    details={"expected": expected},
                )
            )

    for forbidden in forbidden_contains or []:
        if forbidden.casefold() in normalized_text:
            findings.append(
                EvalFinding(
                    case_id=case_id,
                    status="failed",
                    severity="error",
                    message="Forbidden text was found.",
                    details={"forbidden": forbidden},
                )
            )

    if findings:
        return findings

    return [
        EvalFinding(
            case_id=case_id,
            status="passed",
            severity="info",
            message="Text expectations passed.",
        )
    ]


def run_bundled_answer_safety_eval(
    directory: str | Path = "eval_cases",
) -> EvalRunSummary:
    eval_directory = Path(directory)
    cases = load_answer_safety_cases(eval_directory / "answer_safety_cases.jsonl")
    return evaluate_answer_safety_cases(cases)


def run_bundled_eval_smoke(
    directory: str | Path = "eval_cases",
) -> dict[str, EvalRunSummary | int]:
    cases_by_kind = load_all_eval_cases(directory)
    return {
        "answer_safety": evaluate_answer_safety_cases(
            [case for case in cases_by_kind["answer_safety"] if isinstance(case, AnswerSafetyCase)]
        ),
        "report_qa_loaded": len(cases_by_kind["report_qa"]),
        "router_loaded": len(cases_by_kind["router"]),
        "payload_detection_loaded": len(cases_by_kind["payload_detection"]),
    }
