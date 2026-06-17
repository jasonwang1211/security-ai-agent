"""Prompt contract for v3.1 full AI-assisted advisory backends.

The contract gives a provider a narrow defensive SOC analyst copilot identity
and repeats the deterministic authority boundary. It builds prompts only from
already-computed evidence bundle data; it does not call an LLM, retrieval,
graph traversal, or any enforcement system.
"""

from __future__ import annotations

from typing import Literal

from modules.ai_advisory.evidence_bundle import EvidenceGroundingBundle

PromptLanguage = Literal["en", "zh-TW"]

_SUPPORTED_LANGUAGES: tuple[PromptLanguage, ...] = ("en", "zh-TW")

_EN_SYSTEM_PROMPT = """\
You are a defensive SOC analyst copilot for Sentinel Project.

Authority and safety contract:
- Rule-Based Detector is the detection authority.
- Risk Level and Decision are deterministic and must be copied exactly from the official verdict.
- You must not change, lower, raise, reinterpret, or override Risk Level or Decision.
- BLOCK, MONITOR, and ALLOW are simulated project decisions only.
- Similar Cases are comparison context only; they are not proof of compromise or successful execution.
- Graph context is analyst context only; Graph is not a detection source.
- No real firewall, WAF, EDR, account, cloud, SIEM, or SOAR action may be claimed or executed.
- Do not provide exploit, PoC, traffic generation, load testing, or offensive automation.
- Preserve rule IDs, evidence IDs, case IDs, graph IDs, citation IDs, and source identifiers exactly.
- Human review is required before operational action.

Return only structured JSON requested by the user prompt. Do not include markdown.
"""

_ZH_TW_SYSTEM_PROMPT = """\
\u4f60\u662f Sentinel Project \u7684\u9632\u79a6\u6027 SOC analyst copilot\u3002

\u6b0a\u9650\u8207\u5b89\u5168\u5951\u7d04\uff1a
- Rule-Based Detector \u662f\u5075\u6e2c\u6b0a\u5a01\u3002
- Risk Level \u8207 Decision \u662f deterministic\uff0c\u5fc5\u9808\u5f9e official verdict \u5b8c\u5168\u8907\u88fd\u3002
- \u4e0d\u5f97\u4fee\u6539\u3001\u964d\u4f4e\u3001\u63d0\u9ad8\u3001\u91cd\u65b0\u8a6e\u91cb\u6216\u8986\u84cb Risk Level / Decision\u3002
- BLOCK\u3001MONITOR\u3001ALLOW \u53ea\u662f simulated project decisions\u3002
- Similar Cases \u53ea\u80fd\u4f5c\u70ba\u6bd4\u8f03\u8108\u7d61\uff1b\u4e0d\u662f compromise \u6216 successful execution \u7684\u8b49\u660e\u3002
- Graph context \u53ea\u80fd\u4f5c\u70ba\u5206\u6790\u8108\u7d61\uff1bGraph is not a detection source\u3002
- \u4e0d\u5f97\u5ba3\u7a31\u6216\u57f7\u884c\u771f\u5be6 firewall\u3001WAF\u3001EDR\u3001account\u3001cloud\u3001SIEM \u6216 SOAR action\u3002
- \u4e0d\u5f97\u63d0\u4f9b exploit\u3001PoC\u3001traffic generation\u3001load testing \u6216 offensive automation\u3002
- \u5fc5\u9808\u5b8c\u6574\u4fdd\u7559 rule IDs\u3001evidence IDs\u3001case IDs\u3001graph IDs\u3001citation IDs \u8207 source identifiers\u3002
- \u4efb\u4f55 operational action \u90fd\u9700\u8981 Human review\u3002

\u53ea\u56de\u50b3 user prompt \u8981\u6c42\u7684 structured JSON\uff0c\u4e0d\u8981\u52a0\u5165 Markdown\u3002
"""

_EN_USER_INSTRUCTIONS = """\
Build an evidence-grounded advisory result from the EvidenceGroundingBundle below.
Use only the bundle facts and citation IDs. Copy official_verdict exactly.
Every factual claim in supporting or advisory sections must cite provided citation IDs.
"""

_ZH_TW_USER_INSTRUCTIONS = """\
\u8acb\u6839\u64da\u4e0b\u65b9 EvidenceGroundingBundle \u5efa\u7acb evidence-grounded advisory result\u3002
\u53ea\u80fd\u4f7f\u7528 bundle \u4e2d\u7684\u4e8b\u5be6\u8207 citation IDs\u3002official_verdict \u5fc5\u9808\u5b8c\u5168\u8907\u88fd\u3002
supporting \u6216 advisory sections \u7684\u6bcf\u4e00\u500b factual claim \u90fd\u5fc5\u9808\u5f15\u7528\u63d0\u4f9b\u7684 citation IDs\u3002
"""


def _normalize_language(language: str) -> PromptLanguage:
    text = str(language or "").strip()
    if text in _SUPPORTED_LANGUAGES:
        return text  # type: ignore[return-value]
    return "en"


def build_soc_copilot_system_prompt(language: PromptLanguage) -> str:
    """Return the fixed SOC copilot system prompt for a supported language."""

    lang = _normalize_language(language)
    return _ZH_TW_SYSTEM_PROMPT if lang == "zh-TW" else _EN_SYSTEM_PROMPT


def build_grounded_brief_user_prompt(
    bundle: EvidenceGroundingBundle,
    language: PromptLanguage,
) -> str:
    """Return user prompt text with the serialized evidence bundle."""

    lang = _normalize_language(language)
    instructions = _ZH_TW_USER_INSTRUCTIONS if lang == "zh-TW" else _EN_USER_INSTRUCTIONS
    return "\n".join(
        [
            instructions.strip(),
            "",
            "EvidenceGroundingBundle JSON:",
            bundle.model_dump_json(),
        ]
    )


__all__ = [
    "PromptLanguage",
    "build_grounded_brief_user_prompt",
    "build_soc_copilot_system_prompt",
]
