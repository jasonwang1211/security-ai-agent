from pathlib import Path

from modules.detection_rules import DetectionRule
from modules.rule_loader import load_detection_rules


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
        self.yaml_loader_error = None
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
        except ValueError as exc:
            self.yaml_loader_error = str(exc)
            return []

    def _build_result(self, attack_types, matched_signatures, original_input, metadata=None):
        return {
            "status": "ALERT" if attack_types else "CLEAN",
            "attack_types": attack_types,
            "matched_signatures": matched_signatures,
            "original_input": original_input,
            "detector": self.get_metadata(),
            "metadata": metadata or {},
        }

    def _normalize_text(self, text):
        return str(text or "").lower()

    def _find_matches(self, text):
        normalized = self._normalize_text(text)
        attack_types = []
        matched_signatures = {}

        yaml_matches, matched_yaml_rules = self._detect_with_yaml_rules(text, self.yaml_rules)
        for attack_type, matched in yaml_matches.items():
            if matched:
                attack_types.append(attack_type)
                matched_signatures[attack_type] = matched

        hardcoded_matches = self._detect_with_hardcoded_signatures(normalized)
        hardcoded_matches_used = False
        for attack_type, matched in hardcoded_matches.items():
            if attack_type in self.yaml_rule_attack_types:
                continue
            if matched:
                hardcoded_matches_used = True
                attack_types.append(attack_type)
                matched_signatures[attack_type] = matched

        metadata = self._merge_detection_metadata(matched_yaml_rules, hardcoded_matches_used)

        return attack_types, matched_signatures, metadata

    def _detect_with_yaml_rules(self, text, rules: list[DetectionRule]):
        matched_signatures: dict[str, list[str]] = {}
        matched_rules: list[DetectionRule] = []

        for rule in rules:
            matched = rule.matches(text)
            if not matched:
                continue

            attack_matches = matched_signatures.setdefault(rule.attack_type, [])
            for pattern in matched:
                if pattern not in attack_matches:
                    attack_matches.append(pattern)
            matched_rules.append(rule)

        return matched_signatures, matched_rules

    def _detect_with_hardcoded_signatures(self, normalized_text):
        matched_signatures = {}
        for attack_type, signatures in self.attack_signatures.items():
            matched = [sig for sig in signatures if sig.lower() in normalized_text]
            if matched:
                matched_signatures[attack_type] = matched

        return matched_signatures

    def _dedupe_preserve_order(self, values):
        deduped_values = []
        for value in values:
            if value not in deduped_values:
                deduped_values.append(value)
        return deduped_values

    def _build_rule_metadata(self, matched_rules: list[DetectionRule]):
        confidences = [rule.confidence for rule in matched_rules]
        return {
            "rule_ids": self._dedupe_preserve_order([rule.id for rule in matched_rules]),
            "rule_sources": self._dedupe_preserve_order(
                [rule.source_path for rule in matched_rules if rule.source_path]
            ),
            "severities": self._dedupe_preserve_order([rule.severity for rule in matched_rules]),
            "confidences": self._dedupe_preserve_order(confidences),
            "max_confidence": max(confidences) if confidences else None,
            "mitre_techniques": self._dedupe_preserve_order(
                technique
                for rule in matched_rules
                for technique in rule.mitre_techniques
            ),
            "references": self._dedupe_preserve_order(
                reference
                for rule in matched_rules
                for reference in rule.references
            ),
        }

    def _merge_detection_metadata(self, matched_yaml_rules, has_hardcoded_matches):
        has_yaml_matches = bool(matched_yaml_rules)
        if not has_yaml_matches and not has_hardcoded_matches:
            return {}

        if has_yaml_matches and has_hardcoded_matches:
            detection_source = "mixed"
        elif has_yaml_matches:
            detection_source = "yaml_rules"
        else:
            detection_source = "hardcoded_signatures"

        metadata = {"detection_source": detection_source}

        if has_yaml_matches:
            metadata.update(self._build_rule_metadata(matched_yaml_rules))

        if self.yaml_loader_error and not has_yaml_matches:
            metadata["yaml_loader_error"] = self.yaml_loader_error

        return metadata

    def _scan_text(self, text, original_input):
        attack_types, matched_signatures, metadata = self._find_matches(text)
        return self._build_result(attack_types, matched_signatures, original_input, metadata)

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
