from modules.detector import RuleBasedDetector
from modules.rule_loader import load_detection_rules


def test_detector_xss_payload_still_alerts_with_yaml_adapter():
    result = RuleBasedDetector().inspect_text("<script>alert(1)</script>")

    assert result["status"] == "ALERT"
    assert "XSS" in result["attack_types"]
    assert "<script>" in result["matched_signatures"]["XSS"]
    assert "alert(" in result["matched_signatures"]["XSS"]


def test_detector_detects_yaml_only_xss_pattern():
    result = RuleBasedDetector().inspect_text("javascript:alert(1)")

    assert result["status"] == "ALERT"
    assert "XSS" in result["attack_types"]
    assert "javascript:" in result["matched_signatures"]["XSS"]


def test_detector_sql_injection_uses_yaml_rule():
    result = RuleBasedDetector().inspect_text("?id=1' OR '1'='1")

    assert result["status"] == "ALERT"
    assert "SQL Injection" in result["attack_types"]
    assert "' or '1'='1" in result["matched_signatures"]["SQL Injection"]


def test_detector_path_traversal_uses_yaml_rule():
    result = RuleBasedDetector().inspect_text("../../etc/passwd")

    assert result["status"] == "ALERT"
    assert "Path Traversal" in result["attack_types"]
    assert "/etc/passwd" in result["matched_signatures"]["Path Traversal"]
    assert "../" in result["matched_signatures"]["Path Traversal"]


def test_detector_command_injection_uses_yaml_rule():
    result = RuleBasedDetector().inspect_text("; rm -rf /tmp/test")

    assert result["status"] == "ALERT"
    assert "Command Injection" in result["attack_types"]
    assert "; rm -rf" in result["matched_signatures"]["Command Injection"]


def test_all_migrated_yaml_rules_load():
    rules = load_detection_rules("detections/blue_team")
    rule_ids = {rule.id for rule in rules}

    assert {"XSS-001", "SQLI-001", "PATH-001", "CMD-001"}.issubset(rule_ids)


def test_detector_falls_back_to_hardcoded_signatures_when_yaml_loading_fails(monkeypatch):
    def raise_loader_error(_directory):
        raise ValueError("broken yaml rule")

    monkeypatch.setattr("modules.detector.load_detection_rules", raise_loader_error)

    result = RuleBasedDetector().inspect_text("<script>alert(1)</script>")

    assert result["status"] == "ALERT"
    assert "XSS" in result["attack_types"]
    assert "<script>" in result["matched_signatures"]["XSS"]

    sql_result = RuleBasedDetector().inspect_text("' OR '1'='1")
    assert "SQL Injection" in sql_result["attack_types"]

    path_result = RuleBasedDetector().inspect_text("../../etc/passwd")
    assert "Path Traversal" in path_result["attack_types"]

    command_result = RuleBasedDetector().inspect_text("; rm -rf /tmp/test")
    assert "Command Injection" in command_result["attack_types"]


def test_detector_benign_input_remains_clean():
    result = RuleBasedDetector().inspect_text("hello world")

    assert result["status"] == "CLEAN"
    assert result["attack_types"] == []
    assert result["matched_signatures"] == {}
