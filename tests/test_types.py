import pytest
from pydantic import ValidationError

from modules.types import (
    LLMAlertExplanationResultModel,
    LLMSuspiciousResultModel,
    SecurityEventModel,
)


def test_llm_suspicious_result_valid_model_can_be_created():
    result = LLMSuspiciousResultModel(
        is_suspicious=True,
        suggested_attack_types=["SQL Injection"],
        confidence=0.8,
        anomaly_score=0.7,
        reasoning="Suspicious payload structure.",
        recommended_risk="HIGH",
        recommended_action="BLOCK",
        llm_status="ACTIVE",
    )

    assert result.is_suspicious is True
    assert result.recommended_risk == "HIGH"
    assert result.recommended_action == "BLOCK"


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_llm_suspicious_result_confidence_must_be_between_zero_and_one(confidence):
    with pytest.raises(ValidationError):
        LLMSuspiciousResultModel(confidence=confidence)


@pytest.mark.parametrize("anomaly_score", [-0.1, 1.1])
def test_llm_suspicious_result_anomaly_score_must_be_between_zero_and_one(anomaly_score):
    with pytest.raises(ValidationError):
        LLMSuspiciousResultModel(anomaly_score=anomaly_score)


def test_llm_suspicious_result_invalid_recommended_risk_raises_validation_error():
    with pytest.raises(ValidationError):
        LLMSuspiciousResultModel(recommended_risk="CRITICAL")


def test_llm_suspicious_result_invalid_recommended_action_raises_validation_error():
    with pytest.raises(ValidationError):
        LLMSuspiciousResultModel(recommended_action="QUARANTINE")


def test_llm_suspicious_result_model_dump_includes_expected_keys():
    dumped = LLMSuspiciousResultModel().model_dump()

    assert set(dumped) == {
        "is_suspicious",
        "suggested_attack_types",
        "confidence",
        "anomaly_score",
        "reasoning",
        "recommended_risk",
        "recommended_action",
        "llm_status",
    }


def test_llm_alert_explanation_result_valid_model_can_be_created():
    result = LLMAlertExplanationResultModel(
        is_suspicious=True,
        possible_attack_types=["XSS"],
        reasoning="Script-like payload was detected.",
        recommended_decision="MONITOR",
        confidence=0.85,
    )

    assert result.is_suspicious is True
    assert result.recommended_decision == "MONITOR"


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_llm_alert_explanation_result_confidence_must_be_between_zero_and_one(confidence):
    with pytest.raises(ValidationError):
        LLMAlertExplanationResultModel(confidence=confidence)


def test_llm_alert_explanation_result_invalid_recommended_decision_raises_validation_error():
    with pytest.raises(ValidationError):
        LLMAlertExplanationResultModel(recommended_decision="ESCALATE")


def test_llm_alert_explanation_result_model_dump_includes_expected_keys():
    dumped = LLMAlertExplanationResultModel().model_dump()

    assert set(dumped) == {
        "is_suspicious",
        "possible_attack_types",
        "reasoning",
        "recommended_decision",
        "confidence",
    }


def test_security_event_model_preserves_event_type_and_source_ip():
    event = SecurityEventModel(
        event_type="auth_failure",
        source_ip="10.0.0.5",
        target="/login",
        user="admin",
        timestamp="2026-05-10T09:00:00Z",
        raw="login_failed src_ip=10.0.0.5 user=admin endpoint=/login status=401",
    )

    dumped = event.model_dump()

    assert dumped["event_type"] == "auth_failure"
    assert dumped["source_ip"] == "10.0.0.5"
