import json
import re

from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from config import AGENT_MODEL_NAME


class LLMThreatJudge:
    RISK_PRIORITY = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
    }
    ACTION_PRIORITY = {
        "ALLOW": 1,
        "MONITOR": 2,
        "BLOCK": 3,
    }

    def __init__(self):
        self.llm = None
        self.init_error = None
        self.prompt = ChatPromptTemplate.from_template(
            """
You are an advisory LLM threat judgment layer for a security pipeline.

Safety rules:
1. The rule-based detector is authoritative when it returns ALERT.
2. If detector_result.status is ALERT, you must mark is_suspicious as true.
3. If detector_result.status is ALERT, do not recommend ALLOW.
4. If detector_result.status is CLEAN, you may still flag suspicious behavior.
5. Return JSON only. Do not include markdown.
6. Keep reasoning brief, concrete, and security-focused.

Required JSON schema:
{{
  "is_suspicious": true,
  "suggested_attack_types": ["SQL Injection"],
  "confidence": 0.0,
  "reasoning": "short explanation",
  "recommended_risk": "LOW",
  "recommended_action": "ALLOW"
}}

Allowed recommended_risk values: LOW, MEDIUM, HIGH.
Allowed recommended_action values: ALLOW, MONITOR, BLOCK.

Inputs:
- Query: {query}
- Detector result: {detector_result}
- RAG context: {rag_context}
- Extracted signals: {signals}
- State: {state}
"""
        )
        self._initialize_llm()

    def _initialize_llm(self):
        try:
            self.llm = ChatOllama(model=AGENT_MODEL_NAME, temperature=0)
        except Exception as exc:
            self.init_error = exc
            self.llm = None

    def judge(self, query, detector_result, rag_context="", signals=None, state=None):
        fallback = self._build_fallback_result(query, detector_result)

        if self.llm is None:
            return fallback

        payload = {
            "query": self._trim_text(query, 1000),
            "detector_result": self._safe_dump(detector_result),
            "rag_context": self._trim_text(rag_context, 2000),
            "signals": self._safe_dump(signals or {}),
            "state": self._safe_dump(state or {}),
        }

        try:
            chain = self.prompt | self.llm
            response = chain.invoke(payload)
            content = getattr(response, "content", "") or ""
            parsed = self._parse_json(content)
            if not isinstance(parsed, dict):
                return fallback
            result = self._merge_with_fallback(parsed, fallback)
            result["llm_status"] = "ACTIVE"
            return result
        except Exception:
            return fallback

    def _build_fallback_result(self, query, detector_result):
        detector_result = detector_result or {}
        detector_status = str(detector_result.get("status") or "").upper().strip()
        attack_types = self._normalize_attack_types(detector_result.get("attack_types"))

        if detector_status == "ALERT":
            reasoning_parts = ["Rule-based detector returned ALERT, so the input remains suspicious."]
            if attack_types:
                reasoning_parts.append(f"Detected attack types: {', '.join(attack_types)}.")

            return {
                "is_suspicious": True,
                "suggested_attack_types": attack_types,
                "confidence": 0.9,
                "reasoning": " ".join(reasoning_parts),
                "recommended_risk": "HIGH",
                "recommended_action": "BLOCK",
                "llm_status": "FALLBACK",
            }

        reasoning = "LLM judgment unavailable or invalid; falling back to the clean rule-based result."
        if query:
            reasoning += " Continue monitoring if the query context appears unusual."

        return {
            "is_suspicious": False,
            "suggested_attack_types": attack_types,
            "confidence": 0.5,
            "reasoning": reasoning,
            "recommended_risk": "LOW",
            "recommended_action": "ALLOW",
            "llm_status": "FALLBACK",
        }

    def _merge_with_fallback(self, llm_result, fallback):
        attack_types = fallback["suggested_attack_types"][:]
        for attack_type in self._normalize_attack_types(llm_result.get("suggested_attack_types")):
            if attack_type not in attack_types:
                attack_types.append(attack_type)

        fallback_risk = self._normalize_risk(fallback.get("recommended_risk"))
        llm_risk = self._normalize_risk(llm_result.get("recommended_risk"))
        recommended_risk = self._stricter_risk(fallback_risk, llm_risk)

        fallback_action = self._normalize_action(fallback.get("recommended_action"))
        llm_action = self._normalize_action(llm_result.get("recommended_action"))
        recommended_action = self._stricter_action(fallback_action, llm_action)

        is_suspicious = bool(
            fallback.get("is_suspicious")
            or llm_result.get("is_suspicious")
            or recommended_risk != "LOW"
            or recommended_action != "ALLOW"
            or bool(attack_types)
        )

        reasoning = str(llm_result.get("reasoning") or "").strip() or fallback["reasoning"]
        confidence = self._normalize_confidence(llm_result.get("confidence"), fallback["confidence"])

        return {
            "is_suspicious": is_suspicious,
            "suggested_attack_types": attack_types,
            "confidence": confidence,
            "reasoning": reasoning,
            "recommended_risk": recommended_risk,
            "recommended_action": recommended_action,
        }

    def _parse_json(self, text):
        if not text:
            return None

        cleaned = text.strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            return None

        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    def _normalize_attack_types(self, value):
        if not value:
            return []

        if isinstance(value, str):
            candidates = [value]
        else:
            try:
                candidates = list(value)
            except TypeError:
                candidates = [value]

        attack_types = []
        for item in candidates:
            attack_type = str(item or "").strip()
            if attack_type and attack_type not in attack_types:
                attack_types.append(attack_type)
        return attack_types

    def _normalize_risk(self, risk):
        normalized = str(risk or "LOW").upper().strip()
        if normalized not in self.RISK_PRIORITY:
            return "LOW"
        return normalized

    def _normalize_action(self, action):
        normalized = str(action or "ALLOW").upper().strip()
        if normalized not in self.ACTION_PRIORITY:
            return "ALLOW"
        return normalized

    def _stricter_risk(self, left, right):
        left = self._normalize_risk(left)
        right = self._normalize_risk(right)
        if self.RISK_PRIORITY[right] > self.RISK_PRIORITY[left]:
            return right
        return left

    def _stricter_action(self, left, right):
        left = self._normalize_action(left)
        right = self._normalize_action(right)
        if self.ACTION_PRIORITY[right] > self.ACTION_PRIORITY[left]:
            return right
        return left

    def _normalize_confidence(self, value, fallback):
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            confidence = float(fallback)
        return max(0.0, min(1.0, confidence))

    def _trim_text(self, value, limit):
        text = str(value or "").strip()
        if len(text) <= limit:
            return text
        return text[:limit] + "...[truncated]"

    def _safe_dump(self, value):
        try:
            return json.dumps(value, ensure_ascii=True, default=str)
        except Exception:
            return str(value)
