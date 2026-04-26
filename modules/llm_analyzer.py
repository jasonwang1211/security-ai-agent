import json
import re

from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from config import MODEL_NAME


class LLMSecurityAnalyzer:
    DECISION_PRIORITY = {
        "ALLOW": 1,
        "MONITOR": 2,
        "BLOCK": 3,
    }

    def __init__(self):
        self.llm = None
        self.init_error = None
        self.prompt = ChatPromptTemplate.from_template(
            """
You are a secondary security analysis layer for a security pipeline.

Important rules:
1. Rule-based detection is authoritative.
2. You may add supporting reasoning or raise concern, but you must never reduce severity below the rule-based result.
3. Return JSON only.
4. Keep reasoning brief and concrete.

Required JSON schema:
{{
  "is_suspicious": true,
  "possible_attack_types": ["SQL Injection"],
  "reasoning": "short explanation",
  "recommended_decision": "BLOCK",
  "confidence": 0.0
}}

Inputs:
- Query: {query}
- Detector result: {detector_result}
- RAG context: {rag_context}
- Risk result: {risk_result}
- Decision result: {decision_result}
- State: {state}
"""
        )
        self._initialize_llm()

    def _initialize_llm(self):
        try:
            self.llm = ChatOllama(model=MODEL_NAME, temperature=0)
        except Exception as exc:
            self.init_error = exc
            self.llm = None

    def analyze(
        self,
        query,
        detector_result,
        rag_context,
        risk_result,
        decision_result,
        state,
    ):
        fallback = self._build_fallback_result(
            query=query,
            detector_result=detector_result,
            risk_result=risk_result,
            decision_result=decision_result,
        )

        if self.llm is None:
            return fallback

        payload = {
            "query": self._trim_text(query, 1000),
            "detector_result": self._safe_dump(detector_result),
            "rag_context": self._trim_text(rag_context, 2000),
            "risk_result": self._safe_dump(risk_result),
            "decision_result": self._safe_dump(decision_result),
            "state": self._safe_dump(state),
        }

        try:
            chain = self.prompt | self.llm
            response = chain.invoke(payload)
            content = getattr(response, "content", "") or ""
            parsed = self._parse_json(content)
            if not isinstance(parsed, dict):
                return fallback
            return self._merge_with_fallback(parsed, fallback)
        except Exception:
            return fallback

    def _build_fallback_result(self, query, detector_result, risk_result, decision_result):
        detector_result = detector_result or {}
        risk_result = risk_result or {}
        decision_result = decision_result or {}

        attack_types = list(dict.fromkeys(detector_result.get("attack_types") or []))
        detector_status = str(detector_result.get("status") or "").upper()
        recommended_decision = self._normalize_decision(decision_result.get("decision"))
        risk_level = str(risk_result.get("risk_level") or "LOW").upper()

        is_suspicious = detector_status == "ALERT" or recommended_decision != "ALLOW"

        reasoning_parts = []
        if detector_status == "ALERT":
            reasoning_parts.append("Rule-based detector flagged the input as suspicious.")
        else:
            reasoning_parts.append("No rule-based alert was triggered.")

        if attack_types:
            reasoning_parts.append(f"Detected attack types: {', '.join(attack_types)}.")

        if risk_level:
            reasoning_parts.append(f"Current risk level: {risk_level}.")

        if query and not attack_types and detector_status != "ALERT":
            reasoning_parts.append("LLM analysis unavailable, so the result falls back to the rule-based pipeline.")

        confidence = 0.9 if detector_status == "ALERT" else 0.6

        return {
            "is_suspicious": bool(is_suspicious),
            "possible_attack_types": attack_types,
            "reasoning": " ".join(reasoning_parts).strip(),
            "recommended_decision": recommended_decision,
            "confidence": float(confidence),
        }

    def _merge_with_fallback(self, llm_result, fallback):
        attack_types = fallback["possible_attack_types"][:]
        for attack_type in llm_result.get("possible_attack_types") or []:
            if isinstance(attack_type, str) and attack_type and attack_type not in attack_types:
                attack_types.append(attack_type)

        fallback_decision = self._normalize_decision(fallback.get("recommended_decision"))
        llm_decision = self._normalize_decision(llm_result.get("recommended_decision"))
        recommended_decision = self._stricter_decision(fallback_decision, llm_decision)

        is_suspicious = bool(
            fallback.get("is_suspicious")
            or llm_result.get("is_suspicious")
            or recommended_decision != "ALLOW"
            or bool(attack_types)
        )

        reasoning = str(llm_result.get("reasoning") or "").strip() or fallback["reasoning"]
        confidence = self._normalize_confidence(llm_result.get("confidence"), fallback["confidence"])

        return {
            "is_suspicious": is_suspicious,
            "possible_attack_types": attack_types,
            "reasoning": reasoning,
            "recommended_decision": recommended_decision,
            "confidence": confidence,
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

    def _normalize_decision(self, decision):
        normalized = str(decision or "ALLOW").upper().strip()
        if normalized not in self.DECISION_PRIORITY:
            return "ALLOW"
        return normalized

    def _stricter_decision(self, left, right):
        left = self._normalize_decision(left)
        right = self._normalize_decision(right)
        if self.DECISION_PRIORITY[right] > self.DECISION_PRIORITY[left]:
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
