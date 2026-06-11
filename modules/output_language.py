"""Lightweight output-language policy for advisory text and RAG prompts.

This module is pure presentation policy. It must stay free of Streamlit, RAG,
vector-store, model, network, and detector imports so changing UI language never
initializes heavy runtime dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass

OUTPUT_LANGUAGE_ZH_TW = "zh-TW"
OUTPUT_LANGUAGE_EN = "en"
OUTPUT_LANGUAGE_BILINGUAL = "bilingual"
DEFAULT_OUTPUT_LANGUAGE = OUTPUT_LANGUAGE_ZH_TW
SUPPORTED_OUTPUT_LANGUAGES = (
    OUTPUT_LANGUAGE_ZH_TW,
    OUTPUT_LANGUAGE_EN,
    OUTPUT_LANGUAGE_BILINGUAL,
)


@dataclass(frozen=True)
class OutputLanguageProfile:
    """Normalized language profile used by advisory output and RAG prompts."""

    language: str
    instruction: str
    short_label: str


_ALIASES = {
    "zh": OUTPUT_LANGUAGE_ZH_TW,
    "zh_tw": OUTPUT_LANGUAGE_ZH_TW,
    "zh-tw": OUTPUT_LANGUAGE_ZH_TW,
    "traditional chinese": OUTPUT_LANGUAGE_ZH_TW,
    "繁體中文": OUTPUT_LANGUAGE_ZH_TW,
    "chinese": OUTPUT_LANGUAGE_ZH_TW,
    "en": OUTPUT_LANGUAGE_EN,
    "eng": OUTPUT_LANGUAGE_EN,
    "english": OUTPUT_LANGUAGE_EN,
    "bilingual": OUTPUT_LANGUAGE_BILINGUAL,
    "zh/en": OUTPUT_LANGUAGE_BILINGUAL,
    "zh-tw/en": OUTPUT_LANGUAGE_BILINGUAL,
    "中英雙語": OUTPUT_LANGUAGE_BILINGUAL,
    "雙語": OUTPUT_LANGUAGE_BILINGUAL,
}

_INSTRUCTIONS = {
    OUTPUT_LANGUAGE_ZH_TW: (
        "請以繁體中文為主回答，保留必要的英文資安術語與欄位名稱，例如 Risk Level、"
        "Decision、BLOCK、MONITOR、ALLOW、RAG、LLM、CVE、CVSS。使用清楚、精簡、"
        "防禦導向的 SOC 分析語氣。"
    ),
    OUTPUT_LANGUAGE_EN: (
        "Answer in English. Keep project field names such as Risk Level, Decision, "
        "BLOCK, MONITOR, and ALLOW. Use clear, concise SOC analyst wording."
    ),
    OUTPUT_LANGUAGE_BILINGUAL: (
        "Use Traditional Chinese first, then concise English support. Keep the "
        "answer compact and avoid doubling every sentence if it would make the UI too long."
    ),
}

_LABELS = {
    OUTPUT_LANGUAGE_ZH_TW: "繁體中文",
    OUTPUT_LANGUAGE_EN: "English",
    OUTPUT_LANGUAGE_BILINGUAL: "中英雙語",
}


def normalize_output_language(language: str | None) -> str:
    """Normalize UI/display language into one supported backend output language."""

    text = str(language or "").strip()
    if text in SUPPORTED_OUTPUT_LANGUAGES:
        return text
    normalized = text.casefold().replace("_", "-")
    return _ALIASES.get(normalized, DEFAULT_OUTPUT_LANGUAGE)


def output_language_profile(language: str | None) -> OutputLanguageProfile:
    """Return the immutable output profile for a UI or backend language value."""

    selected = normalize_output_language(language)
    return OutputLanguageProfile(
        language=selected,
        instruction=_INSTRUCTIONS[selected],
        short_label=_LABELS[selected],
    )


def output_language_instruction(language: str | None) -> str:
    """Return prompt/style instructions for the selected output language."""

    return output_language_profile(language).instruction


__all__ = [
    "DEFAULT_OUTPUT_LANGUAGE",
    "OUTPUT_LANGUAGE_BILINGUAL",
    "OUTPUT_LANGUAGE_EN",
    "OUTPUT_LANGUAGE_ZH_TW",
    "OutputLanguageProfile",
    "normalize_output_language",
    "output_language_instruction",
    "output_language_profile",
]
