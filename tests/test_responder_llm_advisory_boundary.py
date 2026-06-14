"""v2.8 Part B: in the LLM-suspicious report path (non-rule-matched inputs in
Full AI-assisted mode), the official Risk Level / Decision must stay deterministic.

The LLM may still surface advisory fields (LLM suggested risk / action, confidence,
reasoning), but its recommended_risk / recommended_action / anomaly_score must NOT
overwrite or become the official Risk Level / Decision shown to the analyst.
"""

from modules.responder import Responder

# Aggressive LLM output trying to push the official verdict to HIGH / BLOCK.
AGGRESSIVE_LLM = {
    "is_suspicious": True,
    "confidence": 0.99,
    "anomaly_score": 0.99,
    "recommended_risk": "HIGH",
    "recommended_action": "BLOCK",
    "llm_status": "OK",
    "suggested_attack_types": ["Brute Force"],
    "reasoning": "model thinks this is severe",
}


def test_derive_suspicious_outcome_is_deterministic_regardless_of_llm() -> None:
    responder = Responder()
    variants = [
        AGGRESSIVE_LLM,
        {"recommended_risk": "LOW", "recommended_action": "ALLOW", "confidence": 0.99, "llm_status": "OK"},
        {"recommended_risk": "HIGH", "recommended_action": "BLOCK", "anomaly_score": 1.0, "llm_status": "OK", "confidence": 0.95},
        {"llm_status": "FALLBACK", "confidence": 0.1},
        {},
        None,
    ]
    for llm_result in variants:
        assert responder._derive_llm_suspicious_outcome(llm_result) == ("MEDIUM", "MONITOR")


def test_llm_recommended_risk_decision_cannot_become_official_verdict() -> None:
    responder = Responder()

    report = responder.build_llm_suspicious_triage_report(
        "suspicious behavior log line",
        AGGRESSIVE_LLM,
        {"keywords": ["suspicious"]},
    )
    lines = report.splitlines()

    # Official Risk Level / Decision lines are the deterministic MEDIUM / MONITOR.
    assert "Risk Level: MEDIUM" in lines
    assert "Decision: MONITOR" in lines
    # The LLM's HIGH / BLOCK never appears as an official Risk Level / Decision line.
    assert "Risk Level: HIGH" not in lines
    assert "Decision: BLOCK" not in lines
    # The LLM values are still visible, but clearly labeled as advisory.
    assert "LLM Recommended Risk: HIGH" in report
    assert "LLM Suggested Decision: BLOCK" in report


def test_suspicious_report_states_verdict_is_deterministic_and_llm_advisory() -> None:
    responder = Responder()

    report = responder.build_llm_suspicious_triage_report(
        "suspicious behavior log line", AGGRESSIVE_LLM, {"keywords": ["x"]}
    )

    # The boundary note must clarify advisory-only and non-override, and must not
    # present an LLM-derived value as the final system decision.
    assert "advisory only" in report
    assert "do not override the official Risk Level or Decision" in report
    assert "Risk Level / Decision set by deterministic policy" in report
    # Simulated-decision boundary remains.
    assert "模擬決策" in report or "simulated" in report.casefold()


def test_low_confidence_or_fallback_llm_still_deterministic_monitor() -> None:
    responder = Responder()

    report = responder.build_llm_suspicious_triage_report(
        "suspicious behavior log line",
        {"is_suspicious": True, "confidence": 0.2, "llm_status": "FALLBACK",
         "recommended_risk": "HIGH", "recommended_action": "BLOCK"},
        {"keywords": ["x"]},
    )
    lines = report.splitlines()

    assert "Risk Level: MEDIUM" in lines
    assert "Decision: MONITOR" in lines
    assert "Risk Level: HIGH" not in lines
    assert "Decision: BLOCK" not in lines
