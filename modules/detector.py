from pathlib import Path

from modules.detection_rules import DetectionRule
from modules.rule_loader import collect_matches, load_detection_rules


class RuleBasedDetector:
    DETECTOR_NAME = "rule_based_detector"
    DETECTOR_TYPE = "rule_based"
    YAML_RULE_DIRECTORY = Path("detections") / "blue_team"
    ATTACK_SIGNATURES = {
        "Path Traversal": ["/etc/passwd", "../", "..\\"],
        "XSS": ["<script>", "alert(", "onerror="],
        "SQL Injection": ["' or '1'='1", "'--", "union select", "drop table"],
        "Command Injection": ["; rm ", "; rm -rf", "&&", "||", "| nc ", "$(", "`"],
    }

    def __init__(self):
        self.detector_name = self.DETECTOR_NAME
        self.detector_type = self.DETECTOR_TYPE
        # Keep the detector intentionally simple and rule-based.
        self.attack_signatures = {
            attack_type: list(signatures)
            for attack_type, signatures in self.ATTACK_SIGNATURES.items()
        }
        self.yaml_rules = self._load_yaml_rules_safely()
        self.yaml_rule_attack_types = {rule.attack_type for rule in self.yaml_rules}

    def get_metadata(self):
        return {
            "name": self.detector_name,
            "type": self.detector_type,
            "supported_attack_types": list(self.attack_signatures.keys()),
        }

    def _load_yaml_rules_safely(self):
        try:
            return load_detection_rules(self.YAML_RULE_DIRECTORY)
        except ValueError:
            return []

    def _build_result(self, attack_types, matched_signatures, original_input):
        return {
            "status": "ALERT" if attack_types else "CLEAN",
            "attack_types": attack_types,
            "matched_signatures": matched_signatures,
            "original_input": original_input,
            "detector": self.get_metadata(),
        }

    def _normalize_text(self, text):
        return str(text or "").lower()

    def _find_matches(self, text):
        normalized = self._normalize_text(text)
        attack_types = []
        matched_signatures = {}

        yaml_matches = self._detect_with_yaml_rules(text, self.yaml_rules)
        for attack_type, matched in yaml_matches.items():
            if matched:
                attack_types.append(attack_type)
                matched_signatures[attack_type] = matched

        hardcoded_matches = self._detect_with_hardcoded_signatures(normalized)
        for attack_type, matched in hardcoded_matches.items():
            if attack_type in self.yaml_rule_attack_types:
                continue
            if matched:
                attack_types.append(attack_type)
                matched_signatures[attack_type] = matched

        return attack_types, matched_signatures

    def _detect_with_yaml_rules(self, text, rules: list[DetectionRule]):
        return collect_matches(text, rules)

    def _detect_with_hardcoded_signatures(self, normalized_text):
        matched_signatures = {}
        for attack_type, signatures in self.attack_signatures.items():
            matched = [sig for sig in signatures if sig.lower() in normalized_text]
            if matched:
                matched_signatures[attack_type] = matched

        return matched_signatures

    def _scan_text(self, text, original_input):
        attack_types, matched_signatures = self._find_matches(text)
        return self._build_result(attack_types, matched_signatures, original_input)

    def inspect_text(self, text):
        """
        Inspect plain user input such as chat messages or payload strings.
        """
        return self._scan_text(text, text)

    def inspect(self, log_entry):
        """
        Preserve the original structured-log inspection entrypoint.
        """
        if isinstance(log_entry, dict):
            text = log_entry.get("path", "")
            result = self._scan_text(text, log_entry)
            result["original_log"] = log_entry
            return result

        return self._scan_text(log_entry, log_entry)
