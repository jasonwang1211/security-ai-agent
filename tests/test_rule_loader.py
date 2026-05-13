import pytest

from modules.rule_loader import collect_matches, load_detection_rule, load_detection_rules


SAMPLE_RULE_PATH = "detections/blue_team/xss/xss_basic.yml"

VALID_RULE_YAML = """
id: XSS-999
title: Temporary XSS Rule
attack_type: XSS
severity: MEDIUM
confidence: 0.8
patterns:
  - "<script>"
  - "alert("
match_mode: substring
case_sensitive: false
enabled: true
"""


def write_rule(path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_load_detection_rule_loads_sample_yaml():
    rule = load_detection_rule(SAMPLE_RULE_PATH)

    assert rule.id == "XSS-001"
    assert rule.attack_type == "XSS"
    assert rule.enabled is True
    assert rule.source_path == SAMPLE_RULE_PATH


def test_load_detection_rules_recursively_loads_sample_rule():
    rules = load_detection_rules("detections")

    assert any(rule.id == "XSS-001" for rule in rules)


def test_load_detection_rules_returns_empty_list_for_missing_directory(tmp_path):
    assert load_detection_rules(tmp_path / "missing") == []


def test_load_detection_rules_does_not_return_disabled_rule(tmp_path):
    rule_path = tmp_path / "blue_team" / "xss" / "disabled.yml"
    write_rule(rule_path, VALID_RULE_YAML.replace("enabled: true", "enabled: false"))

    assert load_detection_rules(tmp_path) == []


def test_load_detection_rule_invalid_yaml_top_level_list_raises_value_error(tmp_path):
    rule_path = tmp_path / "list.yml"
    write_rule(rule_path, "- not\n- a\n- rule\n")

    with pytest.raises(ValueError):
        load_detection_rule(rule_path)


def test_load_detection_rule_missing_required_field_raises_value_error(tmp_path):
    rule_path = tmp_path / "missing_required.yml"
    write_rule(
        rule_path,
        """
id: XSS-999
title: Missing Match Mode Is Fine
attack_type: XSS
severity: MEDIUM
confidence: 0.8
""",
    )

    with pytest.raises(ValueError):
        load_detection_rule(rule_path)


def test_load_detection_rule_invalid_confidence_raises_value_error(tmp_path):
    rule_path = tmp_path / "invalid_confidence.yml"
    write_rule(rule_path, VALID_RULE_YAML.replace("confidence: 0.8", "confidence: 1.2"))

    with pytest.raises(ValueError):
        load_detection_rule(rule_path)


def test_collect_matches_maps_attack_type_to_matched_patterns():
    rules = [load_detection_rule(SAMPLE_RULE_PATH)]

    result = collect_matches("<script>alert(1)</script>", rules)

    assert result["XSS"] == ["<script>", "alert("]


def test_collect_matches_returns_empty_dict_on_benign_input():
    rules = [load_detection_rule(SAMPLE_RULE_PATH)]

    assert collect_matches("hello world", rules) == {}


def test_load_detection_rules_has_deterministic_order():
    first_load = load_detection_rules("detections")
    second_load = load_detection_rules("detections")

    assert [rule.id for rule in first_load] == [rule.id for rule in second_load]
