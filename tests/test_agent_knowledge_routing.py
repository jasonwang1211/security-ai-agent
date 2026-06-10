"""Focused tests for v2.7-D direct-input knowledge-question routing.

Verifies the Agent's deterministic security-knowledge-question detector
recognizes the newly added Resource Exhaustion / HTTP/2 Bomb / CVE questions so
they reach the existing Knowledge Q&A / RAG path, while payloads and benign chat
do not. This is routing/intent only — no detector, scoring, decision, LLM, RAG,
or Ollama runtime is exercised.
"""

import pytest

from modules.agent import is_security_knowledge_question

REQUIRED_KNOWLEDGE_QUESTIONS = [
    "HTTP/2 Resource Exhaustion 是什麼？",
    "HTTP/2 Bomb 疑似事件要怎麼安全分流？",
    "CVE 情報可以直接當成資產已被利用的證明嗎？",
    "HTTP/2 DoS 有哪些防禦緩解方式？",
    "Resource Exhaustion 證據缺口要看什麼？",
]

PREVIOUSLY_SUPPORTED_QUESTIONS = [
    "XSS 是什麼？",
    "什麼是 SQL Injection？",
    "What is command injection and how to triage it?",
]


@pytest.mark.parametrize("question", REQUIRED_KNOWLEDGE_QUESTIONS)
def test_resource_exhaustion_questions_are_security_knowledge_questions(question: str) -> None:
    assert is_security_knowledge_question(question) is True


@pytest.mark.parametrize("question", PREVIOUSLY_SUPPORTED_QUESTIONS)
def test_existing_supported_questions_still_recognized(question: str) -> None:
    assert is_security_knowledge_question(question) is True


def test_payload_without_question_is_not_a_knowledge_question() -> None:
    # A payload should fall through to the detector / payload path, not RAG.
    assert is_security_knowledge_question("<script>alert(1)</script>") is False


def test_benign_chat_is_not_a_knowledge_question() -> None:
    assert is_security_knowledge_question("Please summarize today's lunch menu.") is False


def test_dos_substring_does_not_falsely_match() -> None:
    # Word-boundary guard: "dosa" must not match the "dos" token.
    assert is_security_knowledge_question("How do I cook dosa at home?") is False


def test_empty_input_is_not_a_knowledge_question() -> None:
    assert is_security_knowledge_question("") is False
    assert is_security_knowledge_question(None) is False  # type: ignore[arg-type]
