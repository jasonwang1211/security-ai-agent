# src/detector.py

class RuleBasedDetector:
    def __init__(self):
        # 定義一些簡單的攻擊特徵關鍵字
        self.attack_signatures = {
            "Path Traversal": ["/etc/passwd", "../", "..\\"],
            "XSS": ["<script>", "alert(", "onerror="],
            "SQL Injection": ["' OR '1'='1", "'--", "UNION SELECT", "DROP TABLE"]
        }

    def inspect(self, log_entry):
        """
        檢查單一日誌條目是否符合攻擊特徵。
        """
        path = log_entry.get('path', '').lower()
        findings = []

        for attack_type, signatures in self.attack_signatures.items():
            for sig in signatures:
                if sig.lower() in path:
                    findings.append(attack_type)
        
        if findings:
            return {
                "status": "ALERT",
                "attack_types": findings,
                "original_log": log_entry
            }
        else:
            return {
                "status": "CLEAN",
                "original_log": log_entry
            }
