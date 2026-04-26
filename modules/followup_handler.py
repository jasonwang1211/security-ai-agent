import re


class FollowupHandler:
    POINT_PATTERN = re.compile(r"第\s*(\d+)\s*點")
    NATURAL_PATTERNS = [
        re.compile(pattern, re.IGNORECASE)
        for pattern in [
            r"這是什麼意思",
            r"什麼意思",
            r"再詳細一點",
            r"再說明",
            r"這個呢",
            r"那這個呢",
            r"為什麼",
        ]
    ]
    CONTEXTUAL_HINTS = [
        "詳細說明",
        "更詳細",
        "展開說明",
        "補充說明",
        "可以舉例嗎",
        "為什麼",
        "怎麼判斷",
        "這是什麼意思",
        "什麼意思",
    ]
    NEW_TOPIC_KEYWORDS = [
        "xss",
        "sql injection",
        "csrf",
        "command injection",
        "path traversal",
        "zero-day",
        "zero day",
        "anomaly detection",
    ]

    def __init__(self):
        pass

    def is_point_followup(self, query: str) -> bool:
        if not query:
            return False
        return bool(self.POINT_PATTERN.search(query))

    def is_natural_followup(self, query: str) -> bool:
        if not query:
            return False
        return any(pattern.search(query) for pattern in self.NATURAL_PATTERNS)

    def is_contextual_followup(self, query: str, state: dict) -> bool:
        normalized = str(query or "").strip()
        if not normalized or not isinstance(state, dict):
            return False

        has_context = bool(state.get("last_answer") or state.get("last_focus"))
        if not has_context:
            return False

        lowered = normalized.lower()
        if any(keyword in lowered for keyword in self.NEW_TOPIC_KEYWORDS):
            return False

        short_or_brief = len(normalized) <= 20 or len(normalized.split()) <= 4
        looks_context_dependent = (
            any(hint in normalized for hint in self.CONTEXTUAL_HINTS)
            or normalized.endswith(("嗎", "呢", "？", "?"))
        )

        if self.is_point_followup(normalized):
            return False

        return short_or_brief and looks_context_dependent

    def extract_index(self, query: str):
        if not query:
            return None
        match = self.POINT_PATTERN.search(query)
        return int(match.group(1)) if match else None

    def has_valid_point_reference(self, query: str, points) -> bool:
        index = self.extract_index(query)
        return bool(points) and index is not None and 1 <= index <= len(points)

    def extract_points(self, text: str):
        if not text:
            return []

        points = []
        lines = text.splitlines()

        for raw_line in lines:
            line = raw_line.strip().replace("\u3000", " ")
            if not line:
                continue

            numbered = re.match(r"^\s*(\d+)\s*[.)：:、-]\s*(.+?)\s*$", line)
            if numbered:
                points.append(numbered.group(2).strip())
                continue

            bullet = re.match(r"^\s*[-*•]\s*(.+?)\s*$", line)
            if bullet:
                points.append(bullet.group(1).strip())

        return points
