import re

class FollowupHandler:
    def __init__(self):
        pass

    def is_point_followup(self, query: str) -> bool:
        return bool(re.search(r"第\s*\d+\s*點", query))

    def is_natural_followup(self, query: str) -> bool:
        patterns = [
            r"這是什麼意思",
            r"什麼意思",
            r"說清楚",
            r"解釋清楚",
            r"詳細一點",
            r"再詳細",
            r"再說明",
            r"舉例",
            r"這個呢",
            r"那這個呢",
            r"為什麼",
            r"然後呢",
        ]
        return any(re.search(p, query) for p in patterns)

    def extract_index(self, query: str):
        m = re.search(r"第\s*(\d+)\s*點", query)
        return int(m.group(1)) if m else None

    def extract_points(self, text: str):
        points = []
        lines = text.splitlines()

        for raw_line in lines:
            line = raw_line.strip().replace("\u3000", " ")

            # 抓 1. xxx / 1) xxx / 1、xxx / 1：xxx
            m = re.match(r"^\s*(\d+)\s*[.)、：:]\s*(.+?)\s*$", line)
            if m:
                points.append(m.group(2).strip())
                continue

            # 抓 - xxx / • xxx
            m = re.match(r"^\s*[-•]\s*(.+?)\s*$", line)
            if m:
                points.append(m.group(1).strip())
                continue

        return points