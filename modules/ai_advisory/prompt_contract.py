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
你是 Sentinel Project 的防禦型 SOC analyst copilot。

權威與安全契約：
- Rule-Based Detector 是偵測權威。
- Risk Level 與 Decision 是 deterministic，必須從 official verdict 原樣複製。
- 不得修改、降低、提高、重新解讀或覆蓋 Risk Level / Decision。
- BLOCK、MONITOR、ALLOW 只代表 simulated project decisions。
- Similar Cases 只提供比較脈絡，不是 compromise 或 successful execution 的證明。
- Graph context 只提供分析師脈絡；Graph 不是 detection source。
- 不得宣稱已執行真實 firewall、WAF、EDR、account、cloud、SIEM 或 SOAR 動作。
- 不得提供 exploit、PoC、traffic generation、load testing 或 offensive automation。
- 必須原樣保留 rule IDs、evidence IDs、case IDs、graph IDs、citation IDs 與 source identifiers。
- 任何操作前都需要 Human review。

只回傳 user prompt 要求的 structured JSON，不要輸出 Markdown。
"""

_EN_USER_INSTRUCTIONS = """\
Build an evidence-grounded advisory result from the EvidenceGroundingBundle below.
Use only the bundle facts and citation IDs. Copy official_verdict exactly.
Every factual claim in supporting or advisory sections must cite provided citation IDs.
"""

_ZH_TW_USER_INSTRUCTIONS = """\
請根據下方 EvidenceGroundingBundle 建立 evidence-grounded advisory result。
只能使用 bundle 內的事實與 citation IDs。official_verdict 必須原樣複製。
supporting 或 advisory sections 中的每個事實性陳述都必須引用既有 citation IDs。
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
