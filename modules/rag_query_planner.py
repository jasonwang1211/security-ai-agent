import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from config import MODEL_NAME


KNOWLEDGE_ROOT = Path("knowledge/blue_team")
ALLOWED_INTENTS = {
    "definition",
    "how_to_analyze",
    "report_guide",
    "defense",
    "incident_response",
    "general",
}

REPORT_GUIDE_QUERY_TERMS = (
    "security_triage_report_guide Quick Verdict Summary Evidence Why It Matters "
    "Recommended Response Simulation Notice AI Assist Risk Level Decision BLOCK "
    "MONITOR ALLOW simulated decision LLM Suggested Decision"
)
LOGIN_FAILURE_QUERY_TERMS = (
    "login_failure_analysis brute_force source_ip target endpoint user failed_count "
    "status 401 403 time window false positive credential stuffing"
)
REPORT_GUIDE_TRIGGERS = (
    "security triage report",
    "triage report",
    "report",
    "分流報告",
    "應變報告",
    "怎麼看",
)
LOGIN_FAILURE_TRIGGERS = (
    "login failure",
    "登入失敗",
    "多次登入失敗",
    "brute force",
    "暴力破解",
)
REPORT_GUIDE_SOURCE = "report_guides/security_triage_report_guide.md"
LOGIN_FAILURE_SOURCES = (
    "detection_rules/login_failure_analysis.md",
    "attack_techniques/brute_force.md",
)
BRUTE_FORCE_SOURCE = "attack_techniques/brute_force.md"


@dataclass(frozen=True)
class RAGQueryPlan:
    is_security_question: bool
    topic: str
    intent: str
    rewritten_query: str
    preferred_sources: list[str]
    preferred_sections: list[str]


class RAGQueryPlanner:
    def __init__(self, llm=None, model_name=MODEL_NAME):
        self.llm = llm
        self.model_name = model_name
        self.available_sources = self._scan_available_sources()
        self.prompt = ChatPromptTemplate.from_template(
            """
You are a retrieval query planner for a defensive blue-team RAG system.
The planner is for this project's blue-team knowledge base, including log analysis,
brute force behavior, incident response playbooks, and Security Triage Report guides.

Task:
- Do not answer the user.
- Do not decide whether an input is an attack.
- Do not decide BLOCK/MONITOR/ALLOW.
- Only classify the knowledge question and select retrieval sources.
- Return JSON only. No markdown, no explanations, no code fences.

Available knowledge source files under knowledge/blue_team:
{available_sources}

Project-specific rewrite rules:
- If the question mentions Security Triage Report, triage report, report, 分流報告,
  應變報告, or 怎麼看, the rewritten_query must include:
  "security_triage_report_guide Quick Verdict Summary Evidence Why It Matters Recommended Response Simulation Notice AI Assist Risk Level Decision BLOCK MONITOR ALLOW simulated decision LLM Suggested Decision"
- If the question mentions login failure, 登入失敗, 多次登入失敗, brute force,
  or 暴力破解, the rewritten_query must include:
  "login_failure_analysis brute_force source_ip target endpoint user failed_count status 401 403 time window false positive credential stuffing"

Required JSON schema:
{{
  "is_security_question": true,
  "topic": "security_triage_report",
  "intent": "definition|how_to_analyze|report_guide|defense|incident_response|general",
  "rewritten_query": "security_triage_report_guide Quick Verdict Summary Evidence Risk Level Decision",
  "preferred_sources": ["report_guides/security_triage_report_guide.md"],
  "preferred_sections": ["Quick Verdict", "Summary", "Evidence"]
}}

Source selection examples:
- For "Security Triage Report 怎麼看？", preferred_sources should include:
  ["report_guides/security_triage_report_guide.md"]
- For "如何判斷多次登入失敗是不是攻擊？", preferred_sources should include:
  ["detection_rules/login_failure_analysis.md", "attack_techniques/brute_force.md"]
- For "什麼是 brute force？", preferred_sources should include:
  ["attack_techniques/brute_force.md"]

Intent guidance:
- definition: user asks what something is.
- how_to_analyze: user asks how to inspect logs, fields, indicators, or triage evidence.
- report_guide: user asks how to read Security Triage Report, Risk Level, Decision, AI Assist, or report fields.
- defense: user asks mitigation, controls, prevention, or hardening.
- incident_response: user asks response steps, containment, evidence preservation, or playbook.
- general: security-related question that does not fit the above.

User question:
{question}
"""
        )

    def _scan_available_sources(self) -> set[str]:
        try:
            if not KNOWLEDGE_ROOT.exists():
                return set()

            return {
                path.relative_to(KNOWLEDGE_ROOT).as_posix()
                for path in KNOWLEDGE_ROOT.rglob("*.md")
                if path.is_file()
            }
        except Exception:
            return set()

    def _format_available_sources(self) -> str:
        if not self.available_sources:
            return "- none"

        return "\n".join(f"- {source}" for source in sorted(self.available_sources))

    def _get_llm(self):
        if self.llm is None:
            self.llm = ChatOllama(model=self.model_name, temperature=0)
        return self.llm

    def _extract_json_object(self, text: str) -> dict[str, Any] | None:
        if not text:
            return None

        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?", "", stripped, flags=re.IGNORECASE).strip()
            stripped = re.sub(r"```$", "", stripped).strip()

        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
            if not match:
                return None
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError:
                return None

        return parsed if isinstance(parsed, dict) else None

    def _with_required_rewrite_terms(self, question: str, rewritten_query: str) -> str:
        normalized_question = (question or "").lower()
        expanded_query = rewritten_query

        if any(trigger in normalized_question for trigger in REPORT_GUIDE_TRIGGERS):
            expanded_query = f"{expanded_query} {REPORT_GUIDE_QUERY_TERMS}"

        if any(trigger in normalized_question for trigger in LOGIN_FAILURE_TRIGGERS):
            expanded_query = f"{expanded_query} {LOGIN_FAILURE_QUERY_TERMS}"

        return " ".join(expanded_query.split())

    def _validate_source(self, source: str) -> str | None:
        normalized = str(source or "").strip().replace("\\", "/")
        if normalized in self.available_sources:
            return normalized
        return None

    def _with_required_sources(self, question: str, preferred_sources: list[str]) -> list[str]:
        normalized_question = (question or "").lower()
        sources = list(preferred_sources)

        if any(trigger in normalized_question for trigger in REPORT_GUIDE_TRIGGERS):
            sources.append(REPORT_GUIDE_SOURCE)

        if any(trigger in normalized_question for trigger in LOGIN_FAILURE_TRIGGERS):
            sources.extend(LOGIN_FAILURE_SOURCES)

        valid_sources = []
        for source in sources:
            normalized = self._validate_source(source)
            if normalized and normalized not in valid_sources:
                valid_sources.append(normalized)

        return valid_sources

    def _validate_plan(self, question: str, data: dict[str, Any]) -> RAGQueryPlan | None:
        if not isinstance(data.get("is_security_question"), bool):
            return None

        topic = str(data.get("topic") or "").strip()
        intent = str(data.get("intent") or "general").strip()
        rewritten_query = str(data.get("rewritten_query") or "").strip()
        preferred_sources = data.get("preferred_sources")
        preferred_sections = data.get("preferred_sections")

        if intent not in ALLOWED_INTENTS:
            intent = "general"

        if not isinstance(preferred_sources, list):
            preferred_sources = []

        if not isinstance(preferred_sections, list):
            preferred_sections = []

        preferred_sources = self._with_required_sources(question, preferred_sources)
        preferred_sections = [
            str(section).strip()
            for section in preferred_sections
            if str(section).strip()
        ]

        if not rewritten_query:
            return None

        rewritten_query = self._with_required_rewrite_terms(question, rewritten_query)

        return RAGQueryPlan(
            is_security_question=data["is_security_question"],
            topic=topic or "general_triage",
            intent=intent,
            rewritten_query=rewritten_query,
            preferred_sources=preferred_sources,
            preferred_sections=preferred_sections,
        )

    def plan(self, question: str) -> RAGQueryPlan | None:
        if not question:
            return None

        try:
            response = (self.prompt | self._get_llm()).invoke(
                {
                    "available_sources": self._format_available_sources(),
                    "question": question,
                }
            )
            content = getattr(response, "content", response)
            parsed = self._extract_json_object(str(content))
            if parsed is None:
                return None
            return self._validate_plan(question, parsed)
        except Exception:
            return None
