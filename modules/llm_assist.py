import json
import re

from langchain_core.prompts import ChatPromptTemplate

from config import AGENT_MODEL_NAME
from modules.types import LLMAlertExplanationResultModel, LLMSuspiciousResultModel


class LLMAssist:
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
    DECISION_PRIORITY = ACTION_PRIORITY

    SUSPICIOUS_BEHAVIOR_PROMPT = """
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
  "anomaly_score": 0.0,
  "reasoning": "short explanation",
  "recommended_risk": "LOW",
  "recommended_action": "ALLOW"
}}

Set anomaly_score from 0.0 to 1.0 based on unusual patterns, unexpected structure,
high entropy input, and abnormal behavior descriptions.

Allowed recommended_risk values: LOW, MEDIUM, HIGH.
Allowed recommended_action values: ALLOW, MONITOR, BLOCK.

Inputs:
- Query: {query}
- Detector result: {detector_result}
- RAG context: {rag_context}
- Extracted signals: {signals}
- State: {state}
"""

    ALERT_EXPLANATION_PROMPT = """
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

    def __init__(self):
        self.llm = None
        self.init_error = None
        self._llm_initialized = False
        self.suspicious_behavior_prompt = ChatPromptTemplate.from_template(
            self.SUSPICIOUS_BEHAVIOR_PROMPT
        )
        self.alert_explanation_prompt = ChatPromptTemplate.from_template(
            self.ALERT_EXPLANATION_PROMPT
        )

    def _initialize_llm(self):
        try:
            from langchain_community.chat_models import ChatOllama

            self.llm = ChatOllama(model=AGENT_MODEL_NAME, temperature=0)
        except Exception as exc:
            self.init_error = exc
            self.llm = None

    def _ensure_llm_initialized(self):
        if self._llm_initialized:
            return

        self._initialize_llm()
        self._llm_initialized = True

    def judge_suspicious_behavior(
        self,
        query,
        detector_result,
        rag_context="",
        signals=None,
        state=None,
    ):
        fallback = self._build_suspicious_fallback_result(query, detector_result)

        self._ensure_llm_initialized()
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
            chain = self.suspicious_behavior_prompt | self.llm
            response = chain.invoke(payload)
            content = getattr(response, "content", "") or ""
            parsed = self._parse_json(content)
            if not isinstance(parsed, dict):
                return fallback
            validated = LLMSuspiciousResultModel.model_validate(parsed).model_dump()
            result = self._merge_suspicious_with_fallback(validated, fallback)
            result["llm_status"] = "ACTIVE"
            return result
        except Exception:
            return fallback

    def explain_alert(
        self,
        query,
        detector_result,
        rag_context,
        risk_result,
        decision_result,
        state,
    ):
        fallback = self._build_alert_fallback_result(
            query=query,
            detector_result=detector_result,
            risk_result=risk_result,
            decision_result=decision_result,
        )

        self._ensure_llm_initialized()
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
            chain = self.alert_explanation_prompt | self.llm
            response = chain.invoke(payload)
            content = getattr(response, "content", "") or ""
            parsed = self._parse_json(content)
            if not isinstance(parsed, dict):
                return fallback
            validated = LLMAlertExplanationResultModel.model_validate(parsed).model_dump()
            return self._merge_alert_with_fallback(validated, fallback)
        except Exception:
            return fallback

    def _build_suspicious_fallback_result(self, query, detector_result):
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
                "anomaly_score": 0.7,
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
            "anomaly_score": 0.0,
            "reasoning": reasoning,
            "recommended_risk": "LOW",
            "recommended_action": "ALLOW",
            "llm_status": "FALLBACK",
        }

    def _merge_suspicious_with_fallback(self, llm_result, fallback):
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
        anomaly_score = self._normalize_confidence(
            llm_result.get("anomaly_score"),
            fallback["anomaly_score"],
        )

        return {
            "is_suspicious": is_suspicious,
            "suggested_attack_types": attack_types,
            "confidence": confidence,
            "anomaly_score": anomaly_score,
            "reasoning": reasoning,
            "recommended_risk": recommended_risk,
            "recommended_action": recommended_action,
        }

    def _build_alert_fallback_result(self, query, detector_result, risk_result, decision_result):
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

    def _merge_alert_with_fallback(self, llm_result, fallback):
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

    def _normalize_decision(self, decision):
        normalized = str(decision or "ALLOW").upper().strip()
        if normalized not in self.DECISION_PRIORITY:
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
