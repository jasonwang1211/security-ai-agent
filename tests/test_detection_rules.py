import pytest
from pydantic import ValidationError

from modules.detection_rules import DetectionRule


def valid_rule_data(**overrides):
    data = {
        "id": "XSS-001",
        "title": "Basic XSS Script Indicators",
        "attack_type": "XSS",
        "severity": "MEDIUM",
        "confidence": 0.8,
        "patterns": ["<script>", "alert("],
    }
    data.update(overrides)
    return data


def test_detection_rule_valid_model_can_be_created():
    rule = DetectionRule(**valid_rule_data())

    assert rule.id == "XSS-001"
    assert rule.severity == "MEDIUM"
    assert rule.confidence == 0.8
    assert rule.patterns
    assert rule.match_mode == "substring"
    assert rule.case_sensitive is False
    assert rule.enabled is True
    assert rule.notes == ""


@pytest.mark.parametrize("field", ["id", "title", "attack_type"])
def test_detection_rule_required_string_fields_must_not_be_empty(field):
    with pytest.raises(ValidationError):
        DetectionRule(**valid_rule_data(**{field: "  "}))


def test_detection_rule_rejects_invalid_severity():
    with pytest.raises(ValidationError):
        DetectionRule(**valid_rule_data(severity="CRITICAL"))


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_detection_rule_confidence_must_be_between_zero_and_one(confidence):
    with pytest.raises(ValidationError):
        DetectionRule(**valid_rule_data(confidence=confidence))


def test_detection_rule_rejects_empty_patterns():
    with pytest.raises(ValidationError):
        DetectionRule(**valid_rule_data(patterns=[]))


def test_detection_rule_rejects_blank_pattern_string():
    with pytest.raises(ValidationError):
        DetectionRule(**valid_rule_data(patterns=["<script>", " "]))


def test_detection_rule_rejects_regex_match_mode_in_phase_4a_1():
    with pytest.raises(ValidationError):
        DetectionRule(**valid_rule_data(match_mode="regex"))


def test_detection_rule_matches_substring_case_insensitive_by_default():
    rule = DetectionRule(**valid_rule_data(patterns=["<script>"]))

    assert rule.matches("<SCRIPT>alert(1)</SCRIPT>") == ["<script>"]


def test_detection_rule_respects_case_sensitive_true():
    rule = DetectionRule(**valid_rule_data(patterns=["<script>"], case_sensitive=True))

    assert rule.matches("<SCRIPT>") == []
    assert rule.matches("<script>") == ["<script>"]


def test_detection_rule_disabled_rule_does_not_match():
    rule = DetectionRule(**valid_rule_data(patterns=["<script>"], enabled=False))

    assert rule.matches("<script>") == []


def test_detection_rule_duplicate_patterns_are_removed_preserving_order():
    rule = DetectionRule(**valid_rule_data(patterns=["<script>", "alert(", "<script>"]))

    assert rule.patterns == ["<script>", "alert("]
