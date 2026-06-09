import sys
from pathlib import Path

from modules.controller.skill_catalog import (
    EXPLAIN_ACTIVE_EVENT_SKILL,
    EXPLAIN_ACTIVE_INCIDENT_SKILL,
    KNOWLEDGE_QA_SKILL,
)
from modules.ui.ai_analyst import (
    AI_BADGE_FOLLOWUP_KEY,
    AI_BADGE_KNOWLEDGE_KEY,
    FOLLOWUP_VARIANT,
    KNOWLEDGE_VARIANT,
    ai_route_badge_key,
    ai_route_variant,
    build_ai_response_card_html,
    build_rag_empty_card_html,
    followup_questions_for_kind,
    is_insufficient_knowledge_response,
    knowledge_questions,
)
from modules.ui.i18n import t


def _response_card(question="Q?", response="answer", route_label="Deterministic follow-up",
                   skill_name="ExplainActiveEventSkill", advisory_label="Advisory only",
                   boundary_text="advisory boundary", variant="") -> str:
    return build_ai_response_card_html(
        question=question,
        response_text=response,
        route_label=route_label,
        skill_name=skill_name,
        advisory_label=advisory_label,
        boundary_text=boundary_text,
        variant=variant,
    )


def test_payload_questions_default_to_zh_tw() -> None:
    questions = followup_questions_for_kind("event")

    assert "為什麼判定為 Command Injection？" in questions
    assert "為什麼 Decision 是 BLOCK？" in questions
    # default language is zh-TW, so no English-only preset leaks in.
    assert "Why is the Decision BLOCK?" not in questions


def test_payload_questions_are_english_in_en() -> None:
    questions = followup_questions_for_kind("event", "en")

    assert "Why is this classified as Command Injection?" in questions
    assert "Why is the Decision BLOCK?" in questions
    assert "Does this mean the command actually executed?" in questions
    assert "為什麼判定為 Command Injection？" not in questions


def test_incident_questions_are_english_in_en() -> None:
    questions = followup_questions_for_kind("incident", "en")

    assert "Why is this Possible Account Compromise?" in questions
    assert "Why is the Decision MONITOR?" in questions
    assert "How are EV-003 and F-001 related?" in questions
    assert "Does this mean the account is confirmed compromised?" in questions


def test_knowledge_questions_default_to_zh_tw_safe_presets() -> None:
    questions = knowledge_questions()

    assert "什麼是 Command Injection？" in questions
    assert "Command Injection 要怎麼防？" in questions
    assert "什麼是 SQL Injection？" in questions
    assert "什麼是 XSS？" in questions
    # risky presets that the knowledge base may not cover were removed.
    assert "RAG 在這個系統中的角色是什麼？" not in questions
    assert "MONITOR 和 BLOCK 差在哪？" not in questions


def test_knowledge_questions_are_english_in_en() -> None:
    questions = knowledge_questions("en")

    assert "What is Command Injection?" in questions
    assert "How can Command Injection be prevented?" in questions
    assert "What is SQL Injection?" in questions
    assert "What is XSS?" in questions
    assert "What role does RAG play in this system?" not in questions


def test_bilingual_questions_contain_both_zh_and_en() -> None:
    payload = followup_questions_for_kind("event", "bilingual")
    incident = followup_questions_for_kind("incident", "bilingual")
    knowledge = knowledge_questions("bilingual")

    assert any("為什麼判定為 Command Injection？ / Why is this classified as Command Injection?" == q for q in payload)
    assert any("EV-003 和 F-001 有什麼關係？ / How are EV-003 and F-001 related?" == q for q in incident)
    assert any("什麼是 Command Injection？ / What is Command Injection?" == q for q in knowledge)
    assert any("什麼是 XSS？ / What is XSS?" == q for q in knowledge)


def test_insufficient_knowledge_response_detection() -> None:
    assert is_insufficient_knowledge_response("目前找不到足夠的知識內容來回答這個問題。")
    assert is_insufficient_knowledge_response("目前沒有足夠可引用來源支撐這個回答。")
    assert is_insufficient_knowledge_response("Information is insufficient from available sources.")
    # a real answer is not treated as empty.
    assert not is_insufficient_knowledge_response("Command Injection 是一種透過 shell 串接執行命令的攻擊。")
    assert not is_insufficient_knowledge_response("")


def test_rag_empty_card_escapes_text_and_includes_route_and_guidance() -> None:
    card = build_rag_empty_card_html(
        question="<b>q</b>",
        guidance_text="try Command Injection",
        route_label="RAG / Knowledge Q&A",
        skill_name="KnowledgeQASkill",
        advisory_label="Advisory only",
    )

    assert "sentinel-ai-empty" in card
    assert "<b>q</b>" not in card
    assert "&lt;b&gt;q&lt;/b&gt;" in card
    assert "try Command Injection" in card
    assert "RAG / Knowledge Q&amp;A" in card
    assert "KnowledgeQASkill" in card
    assert "Advisory only" in card


def test_unsupported_question_language_falls_back_to_zh_tw() -> None:
    assert followup_questions_for_kind("event", "fr") == followup_questions_for_kind("event", "zh-TW")
    assert knowledge_questions("fr") == knowledge_questions("zh-TW")


def test_ai_route_badge_key_maps_skills() -> None:
    assert ai_route_badge_key(EXPLAIN_ACTIVE_EVENT_SKILL) == AI_BADGE_FOLLOWUP_KEY
    assert ai_route_badge_key(EXPLAIN_ACTIVE_INCIDENT_SKILL) == AI_BADGE_FOLLOWUP_KEY
    assert ai_route_badge_key(KNOWLEDGE_QA_SKILL) == AI_BADGE_KNOWLEDGE_KEY
    # unknown skills fall back (None) so the UI can show the raw skill name.
    assert ai_route_badge_key("clarification_required") is None
    assert ai_route_badge_key(None) is None


def test_ai_route_variant_maps_skills() -> None:
    assert ai_route_variant(EXPLAIN_ACTIVE_EVENT_SKILL) == FOLLOWUP_VARIANT
    assert ai_route_variant(EXPLAIN_ACTIVE_INCIDENT_SKILL) == FOLLOWUP_VARIANT
    assert ai_route_variant(KNOWLEDGE_QA_SKILL) == KNOWLEDGE_VARIANT
    assert ai_route_variant("clarification_required") == ""
    assert ai_route_variant(None) == ""


def test_response_card_variant_color_codes_card_and_badge() -> None:
    followup = _response_card(variant=FOLLOWUP_VARIANT)
    knowledge = _response_card(variant=KNOWLEDGE_VARIANT)
    plain = _response_card()

    assert "sentinel-ai-card sentinel-ai-followup" in followup
    assert '"sentinel-ai-badge followup"' in followup
    assert "sentinel-ai-card sentinel-ai-knowledge" in knowledge
    assert '"sentinel-ai-badge knowledge"' in knowledge
    # no variant -> no color-coding class on the card or badge.
    assert "sentinel-ai-followup" not in plain
    assert "sentinel-ai-knowledge" not in plain


def test_rag_empty_card_keeps_amber_card_and_purple_badge() -> None:
    card = build_rag_empty_card_html(
        question="q",
        guidance_text="try Command Injection",
        route_label="RAG / Knowledge Q&A",
        skill_name="KnowledgeQASkill",
        advisory_label="Advisory only",
        variant=KNOWLEDGE_VARIANT,
    )

    # the card keeps the friendly amber accent (not the purple knowledge border)...
    assert "sentinel-ai-card sentinel-ai-empty" in card
    assert "sentinel-ai-card sentinel-ai-knowledge" not in card
    # ...while the route badge is still color-coded as knowledge.
    assert '"sentinel-ai-badge knowledge"' in card


def test_route_badge_labels_are_language_aware() -> None:
    assert t(AI_BADGE_FOLLOWUP_KEY, "zh-TW") == "確定性追問"
    assert t(AI_BADGE_FOLLOWUP_KEY, "en") == "Deterministic follow-up"
    assert "Deterministic follow-up" in t(AI_BADGE_FOLLOWUP_KEY, "bilingual")
    assert t(AI_BADGE_KNOWLEDGE_KEY, "zh-TW") == "RAG / 知識問答"
    assert t(AI_BADGE_KNOWLEDGE_KEY, "en") == "RAG / Knowledge Q&A"


def test_response_card_escapes_dynamic_text_and_includes_meta_row() -> None:
    card = _response_card(
        question="<script>alert('q')</script>",
        response="line one\nline two <b>bold</b>",
        route_label="Deterministic follow-up",
        skill_name="ExplainActiveEventSkill",
        advisory_label="Advisory only",
    )

    # dynamic text is escaped (no raw tags).
    assert "<script>" not in card
    assert "&lt;script&gt;" in card
    assert "<b>bold</b>" not in card
    assert "&lt;b&gt;bold&lt;/b&gt;" in card
    # metadata row: route badge + selected skill chip + advisory-only chip.
    assert "sentinel-ai-meta" in card
    assert "Deterministic follow-up" in card
    assert "ExplainActiveEventSkill" in card
    assert "Advisory only" in card
    assert "sentinel-ai-body" in card
    # line breaks are preserved in the body (rendered via CSS pre-wrap).
    assert "line one\nline two" in card


def test_response_card_omits_question_block_when_blank() -> None:
    card = _response_card(question="", response="answer")

    assert "sentinel-ai-q" not in card
    assert "answer" in card


def test_ai_analyst_helper_does_not_import_streamlit() -> None:
    source = Path("modules/ui/ai_analyst.py").read_text(encoding="utf-8")

    assert "streamlit" not in source.lower()
    assert "streamlit" not in sys.modules
