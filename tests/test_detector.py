from modules.detector import RuleBasedDetector


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


def test_detector_sql_injection_still_uses_hardcoded_fallback():
    result = RuleBasedDetector().inspect_text("?id=1' OR '1'='1")

    assert result["status"] == "ALERT"
    assert "SQL Injection" in result["attack_types"]


def test_detector_command_injection_still_uses_hardcoded_fallback():
    result = RuleBasedDetector().inspect_text("; rm -rf /tmp/test")

    assert result["status"] == "ALERT"
    assert "Command Injection" in result["attack_types"]


def test_detector_falls_back_to_hardcoded_signatures_when_yaml_loading_fails(monkeypatch):
    def raise_loader_error(_directory):
        raise ValueError("broken yaml rule")

    monkeypatch.setattr("modules.detector.load_detection_rules", raise_loader_error)

    result = RuleBasedDetector().inspect_text("<script>alert(1)</script>")

    assert result["status"] == "ALERT"
    assert "XSS" in result["attack_types"]
    assert "<script>" in result["matched_signatures"]["XSS"]


def test_detector_benign_input_remains_clean():
    result = RuleBasedDetector().inspect_text("hello world")

    assert result["status"] == "CLEAN"
    assert result["attack_types"] == []
    assert result["matched_signatures"] == {}
