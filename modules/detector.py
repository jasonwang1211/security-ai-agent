class RuleBasedDetector:
    DETECTOR_NAME = "rule_based_detector"
    DETECTOR_TYPE = "rule_based"
    ATTACK_SIGNATURES = {
        "Path Traversal": ["/etc/passwd", "../", "..\\"],
        "XSS": ["<script>", "alert(", "onerror="],
        "SQL Injection": ["' or '1'='1", "'--", "union select", "drop table"],
    }

    def __init__(self):
        self.detector_name = self.DETECTOR_NAME
        self.detector_type = self.DETECTOR_TYPE
        # Keep the detector intentionally simple and rule-based.
        self.attack_signatures = {
            attack_type: list(signatures)
            for attack_type, signatures in self.ATTACK_SIGNATURES.items()
        }

    def get_metadata(self):
        return {
            "name": self.detector_name,
            "type": self.detector_type,
            "supported_attack_types": list(self.attack_signatures.keys()),
        }

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

        for attack_type, signatures in self.attack_signatures.items():
            matched = [sig for sig in signatures if sig.lower() in normalized]
            if matched:
                attack_types.append(attack_type)
                matched_signatures[attack_type] = matched

        return attack_types, matched_signatures

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
