"""Pure helper for the AI Analyst follow-up / knowledge panel.

Returns language-aware suggested question presets, maps a selected skill to a
route badge, and renders a readable (escaped, wrapping) AI response card. This
module is presentation-only:

- It does not detect attacks, score risk, or decide BLOCK / MONITOR / ALLOW.
- It never overrides the deterministic Risk Level or Decision.
- It must not import any UI rendering framework.

Suggested questions are advisory query *content*. The default language is
Traditional Chinese (zh-TW).
"""

from __future__ import annotations

import html

from modules.controller.skill_catalog import (
    EXPLAIN_ACTIVE_EVENT_SKILL,
    EXPLAIN_ACTIVE_INCIDENT_SKILL,
    KNOWLEDGE_QA_SKILL,
)

DEFAULT_QUESTION_LANGUAGE = "zh-TW"
_SUPPORTED_QUESTION_LANGUAGES = ("zh-TW", "en", "bilingual")

# Route-badge i18n keys (resolved to display text by the UI layer).
AI_BADGE_FOLLOWUP_KEY = "ai_badge_followup"
AI_BADGE_KNOWLEDGE_KEY = "ai_badge_knowledge"

_PAYLOAD_FOLLOWUP_QUESTIONS: dict[str, tuple[str, ...]] = {
    "zh-TW": (
        "為什麼判定為 Command Injection？",
        "為什麼 Risk Level 是 HIGH？",
        "為什麼 Decision 是 BLOCK？",
        "這代表命令真的執行了嗎？",
        "我下一步應該調查什麼？",
    ),
    "en": (
        "Why is this classified as Command Injection?",
        "Why is the Risk Level HIGH?",
        "Why is the Decision BLOCK?",
        "Does this mean the command actually executed?",
        "What should I investigate next?",
    ),
    "bilingual": (
        "為什麼判定為 Command Injection？ / Why is this classified as Command Injection?",
        "為什麼 Risk Level 是 HIGH？ / Why is the Risk Level HIGH?",
        "為什麼 Decision 是 BLOCK？ / Why is the Decision BLOCK?",
        "這代表命令真的執行了嗎？ / Does this mean the command actually executed?",
        "我下一步應該調查什麼？ / What should I investigate next?",
    ),
}

_INCIDENT_FOLLOWUP_QUESTIONS: dict[str, tuple[str, ...]] = {
    "zh-TW": (
        "為什麼是 Possible Account Compromise？",
        "為什麼 Decision 是 MONITOR？",
        "EV-003 和 F-001 有什麼關係？",
        "這代表帳號已經被入侵了嗎？",
        "我下一步應該調查什麼？",
    ),
    "en": (
        "Why is this Possible Account Compromise?",
        "Why is the Decision MONITOR?",
        "How are EV-003 and F-001 related?",
        "Does this mean the account is confirmed compromised?",
        "What should I investigate next?",
    ),
    "bilingual": (
        "為什麼是 Possible Account Compromise？ / Why is this Possible Account Compromise?",
        "為什麼 Decision 是 MONITOR？ / Why is the Decision MONITOR?",
        "EV-003 和 F-001 有什麼關係？ / How are EV-003 and F-001 related?",
        "這代表帳號已經被入侵了嗎？ / Does this mean the account is confirmed compromised?",
        "我下一步應該調查什麼？ / What should I investigate next?",
    ),
}

# Knowledge presets are kept to attack types that the bundled knowledge files
# cover, so the RAG demo reliably returns an answer (project-architecture or
# policy-comparison questions were removed because the knowledge base may lack
# that content).
_KNOWLEDGE_QUESTIONS: dict[str, tuple[str, ...]] = {
    "zh-TW": (
        "什麼是 Command Injection？",
        "Command Injection 要怎麼防？",
        "什麼是 SQL Injection？",
        "什麼是 XSS？",
    ),
    "en": (
        "What is Command Injection?",
        "How can Command Injection be prevented?",
        "What is SQL Injection?",
        "What is XSS?",
    ),
    "bilingual": (
        "什麼是 Command Injection？ / What is Command Injection?",
        "Command Injection 要怎麼防？ / How can Command Injection be prevented?",
        "什麼是 SQL Injection？ / What is SQL Injection?",
        "什麼是 XSS？ / What is XSS?",
    ),
}

# Markers the deterministic knowledge / RAG path emits when it cannot answer.
# Used only to render a friendlier empty-result card -- it does not change the
# backend response or retrieval behavior.
_INSUFFICIENT_KNOWLEDGE_MARKERS: tuple[str, ...] = (
    "找不到足夠的知識內容",
    "沒有足夠可引用來源",
    "information is insufficient",
    "insufficient information",
)


def is_insufficient_knowledge_response(response_text: str | None) -> bool:
    """Return True if a knowledge/RAG answer signals it lacks enough content."""

    lowered = str(response_text or "").casefold()
    return any(marker.casefold() in lowered for marker in _INSUFFICIENT_KNOWLEDGE_MARKERS)


def _normalize_language(language: str | None) -> str:
    text = str(language or "").strip()
    return text if text in _SUPPORTED_QUESTION_LANGUAGES else DEFAULT_QUESTION_LANGUAGE


def followup_questions_for_kind(
    context_kind: str | None,
    language: str = DEFAULT_QUESTION_LANGUAGE,
) -> tuple[str, ...]:
    """Return language-aware follow-up questions for the active context kind.

    ``"incident"`` returns the authentication-incident presets; anything else
    (including ``"event"``) returns the payload-event presets.
    """

    lang = _normalize_language(language)
    if str(context_kind or "") == "incident":
        return _INCIDENT_FOLLOWUP_QUESTIONS[lang]
    return _PAYLOAD_FOLLOWUP_QUESTIONS[lang]


def knowledge_questions(language: str = DEFAULT_QUESTION_LANGUAGE) -> tuple[str, ...]:
    """Return the language-aware preset general security knowledge questions."""

    return _KNOWLEDGE_QUESTIONS[_normalize_language(language)]


# Route variants used for color-coding: deterministic follow-up = cyan,
# RAG knowledge = purple. Empty string means "no specific route".
FOLLOWUP_VARIANT = "followup"
KNOWLEDGE_VARIANT = "knowledge"


def ai_route_badge_key(selected_skill: str | None) -> str | None:
    """Map a selected skill to a route-badge i18n key, or None for fallback.

    Deterministic active-context follow-up skills map to the follow-up badge;
    the knowledge QA skill maps to the knowledge badge. Unknown skills return
    None so the UI can fall back to showing the raw skill name.
    """

    name = str(selected_skill or "")
    if name in {EXPLAIN_ACTIVE_EVENT_SKILL, EXPLAIN_ACTIVE_INCIDENT_SKILL}:
        return AI_BADGE_FOLLOWUP_KEY
    if name == KNOWLEDGE_QA_SKILL:
        return AI_BADGE_KNOWLEDGE_KEY
    return None


def ai_route_variant(selected_skill: str | None) -> str:
    """Return the color-coding variant for a selected skill.

    ``followup`` (deterministic active-context explanation) or ``knowledge``
    (RAG security knowledge lookup); empty string when the skill is unknown.
    """

    name = str(selected_skill or "")
    if name in {EXPLAIN_ACTIVE_EVENT_SKILL, EXPLAIN_ACTIVE_INCIDENT_SKILL}:
        return FOLLOWUP_VARIANT
    if name == KNOWLEDGE_QA_SKILL:
        return KNOWLEDGE_VARIANT
    return ""


def _variant_suffix(variant: str | None) -> str:
    value = str(variant or "").strip()
    return f" sentinel-ai-{value}" if value in {FOLLOWUP_VARIANT, KNOWLEDGE_VARIANT} else ""


def _ai_meta_row_html(
    *, route_label: str, skill_name: str, advisory_label: str, variant: str = ""
) -> str:
    route = html.escape(str(route_label or "").strip())
    skill = html.escape(str(skill_name or "").strip())
    advisory = html.escape(str(advisory_label or "").strip())
    badge_variant = str(variant or "").strip()
    badge_class = "sentinel-ai-badge"
    if badge_variant in {FOLLOWUP_VARIANT, KNOWLEDGE_VARIANT}:
        badge_class += f" {badge_variant}"
    skill_chip = f'<span class="sentinel-ai-chip">{skill}</span>' if skill else ""
    advisory_chip = (
        f'<span class="sentinel-ai-chip advisory">{advisory}</span>' if advisory else ""
    )
    return (
        '<div class="sentinel-ai-meta">'
        f'<span class="{badge_class}">{route}</span>'
        f"{skill_chip}{advisory_chip}"
        "</div>"
    )


def _ai_question_block_html(question: str) -> str:
    question_text = html.escape(str(question or "").strip())
    return f'<div class="sentinel-ai-q">Q: {question_text}</div>' if question_text else ""


def build_ai_response_card_html(
    *,
    question: str,
    response_text: str,
    route_label: str,
    skill_name: str,
    advisory_label: str,
    boundary_text: str,
    variant: str = "",
) -> str:
    """Build a readable, escaped AI response card (prose, wraps, no h-scroll).

    All dynamic text is HTML-escaped. A compact metadata row shows the route
    badge, the selected skill, and an advisory-only chip. ``variant``
    (``followup`` / ``knowledge``) color-codes the card accent and route badge
    so deterministic follow-up and RAG knowledge answers read differently. The
    body preserves line breaks and wraps long tokens via CSS
    (``white-space: pre-wrap; overflow-wrap: anywhere``).
    """

    body = html.escape(str(response_text or "").strip())
    boundary = html.escape(str(boundary_text or "").strip())
    meta = _ai_meta_row_html(
        route_label=route_label, skill_name=skill_name, advisory_label=advisory_label, variant=variant
    )
    return (
        f'<div class="sentinel-ai-card{_variant_suffix(variant)}">'
        f"{meta}"
        f"{_ai_question_block_html(question)}"
        f'<div class="sentinel-ai-body">{body}</div>'
        f'<div class="sentinel-ai-boundary">{boundary}</div>'
        "</div>"
    )


def build_rag_empty_card_html(
    *,
    question: str,
    guidance_text: str,
    route_label: str,
    skill_name: str,
    advisory_label: str,
    variant: str = KNOWLEDGE_VARIANT,
) -> str:
    """Build a friendly RAG empty-result card (not a failure-looking answer).

    Used when the knowledge / RAG path could not find enough content. The
    guidance text suggests covered attack types to try instead. The card keeps
    a friendly amber accent (``sentinel-ai-empty``); ``variant`` only colors the
    route badge.
    """

    guidance = html.escape(str(guidance_text or "").strip())
    meta = _ai_meta_row_html(
        route_label=route_label, skill_name=skill_name, advisory_label=advisory_label, variant=variant
    )
    return (
        '<div class="sentinel-ai-card sentinel-ai-empty">'
        f"{meta}"
        f"{_ai_question_block_html(question)}"
        f'<div class="sentinel-ai-body">\U0001f4da {guidance}</div>'
        "</div>"
    )
