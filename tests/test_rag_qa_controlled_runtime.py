from pathlib import Path
import sys
import types
from typing import Any, cast

from modules.rag.metadata import load_metadata_from_directory


def install_langchain_stubs() -> None:
    chat_models = types.ModuleType("langchain_community.chat_models")
    cast(Any, chat_models).ChatOllama = object

    embeddings = types.ModuleType("langchain_community.embeddings")
    cast(Any, embeddings).HuggingFaceEmbeddings = object

    vectorstores = types.ModuleType("langchain_community.vectorstores")
    cast(Any, vectorstores).Chroma = object

    prompts = types.ModuleType("langchain_core.prompts")

    class FakeChatPromptTemplate:
        @classmethod
        def from_template(cls, _template):
            return cls()

    cast(Any, prompts).ChatPromptTemplate = FakeChatPromptTemplate

    sys.modules.setdefault("langchain_community.chat_models", chat_models)
    sys.modules.setdefault("langchain_community.embeddings", embeddings)
    sys.modules.setdefault("langchain_community.vectorstores", vectorstores)
    sys.modules.setdefault("langchain_core.prompts", prompts)


install_langchain_stubs()

from modules.rag_qa import RAGQA  # noqa: E402
from modules.agent import SecurityAgent  # noqa: E402

REPORT_EXPLAINER_DIR = Path("knowledge/blue_team/report_explainer")


class CapturedProtectionResult:
    def __init__(self, answer):
        self.answer = answer
        self.was_fallback = False


def make_runtime(answer_text: str = "Curated answer."):
    rag = RAGQA.__new__(RAGQA)
    rag.controlled_metadata_items = load_metadata_from_directory(REPORT_EXPLAINER_DIR)
    rag._query_plan_cache = {}
    rag.query_planner = None
    rag.vectorstore = None
    rag.llm = object()
    cast(Any, rag).generate_answer = lambda _query, _context: answer_text
    return rag


def test_sql_injection_controlled_answer_does_not_use_vector_fallback(monkeypatch) -> None:
    rag = make_runtime("SQL Injection controlled answer.")
    cast(Any, rag).retrieve_context = lambda _query: (_raise_vector_fallback(), False)

    captured = {}

    def fake_protect(answer, **_kwargs):
        captured["answer"] = answer
        return CapturedProtectionResult(answer)

    monkeypatch.setattr("modules.rag_qa.protect_answer_with_guardrails", fake_protect)

    answer = rag.answer_question("什麼是 SQL Injection？")

    assert "SQL Injection controlled answer." in answer
    assert captured["answer"].sources[0].source.endswith("sql_injection_explainer.md")
    assert captured["answer"].rule_ids == ["SQLI-001"]


def test_cmd_controlled_answer_preserves_simulated_block_boundary() -> None:
    rag = make_runtime("CMD-001 explains Command Injection. BLOCK remains simulated.")

    answer = rag.answer_question(
        "請說明 CMD-001 Command Injection 的判讀重點，以及 BLOCK 是否代表真實封鎖？"
    )

    assert "CMD-001 explains Command Injection." in answer
    assert "BLOCK remains simulated" in answer
    assert "皆為模擬決策" in answer
    assert "不會覆蓋最終的 Risk Level 或 Decision" in answer
    assert "不代表已執行真實封鎖" in answer


def test_success_after_failures_controlled_answer_does_not_claim_confirmed_compromise() -> None:
    rag = make_runtime("success_after_failures is suspicious and still needs analyst review.")

    answer = rag.answer_question(
        "success_after_failures 登入成功接在多次失敗後，應如何判讀？"
    )

    assert "success_after_failures is suspicious" in answer
    assert "confirmed compromise" not in answer.casefold()


def test_guardrail_protects_mode3_answer_from_decision_override_claim() -> None:
    rag = make_runtime("The LLM changed the decision from MONITOR to BLOCK.")

    answer = rag.answer_question("CMD-001 是什麼？")

    assert "llm changed the decision" not in answer.casefold()


def test_unknown_question_uses_existing_vector_fallback(monkeypatch) -> None:
    rag = make_runtime("Vector fallback answer.")
    cast(Any, rag).retrieve_context = lambda _query: ("fallback context", True)

    captured = {}

    def fake_protect(answer, **_kwargs):
        captured["answer"] = answer
        return CapturedProtectionResult(answer)

    monkeypatch.setattr("modules.rag_qa.protect_answer_with_guardrails", fake_protect)

    answer = rag.answer_question("What is brute force?")

    assert "Vector fallback answer." in answer
    assert captured["answer"].sources[0].source == "runtime/vector_fallback"
    assert "皆為模擬決策" in answer
    assert "不會覆蓋最終的 Risk Level 或 Decision" in answer
    assert "不代表已執行真實封鎖" in answer


def test_internal_answer_contract_keeps_controlled_source_provenance(monkeypatch) -> None:
    rag = make_runtime("Controlled command-injection answer.")
    captured = {}

    def fake_protect(answer, **kwargs):
        captured["answer"] = answer
        captured["known_rule_ids"] = kwargs["known_rule_ids"]
        return CapturedProtectionResult(answer)

    monkeypatch.setattr("modules.rag_qa.protect_answer_with_guardrails", fake_protect)

    rag.answer_question("CMD-001 是什麼？")

    protected_input = captured["answer"]
    assert protected_input.sources[0].identifier == "report.command_injection_explainer"
    assert protected_input.sources[0].source.endswith("command_injection_explainer.md")
    assert protected_input.rule_ids == ["CMD-001"]
    assert "CMD-001" in captured["known_rule_ids"]


def test_inline_internal_metadata_terms_are_sanitized_before_mode3_return() -> None:
    rag = make_runtime(
        "SQL Injection may manipulate query logic. "
        "Structured Signals mention payload_indicator and rule_match. "
        "Whether exploitation succeeded still requires confirmation from application behavior, responses, or database errors."
    )

    answer = rag.answer_question("What is SQL Injection?")

    assert "Structured Signals" not in answer
    assert "payload_indicator" not in answer
    assert "rule_match" not in answer
    assert "SQL Injection may manipulate query logic." in answer
    assert "Whether exploitation succeeded still requires confirmation" in answer
    assert RAGQA.MODE3_BOUNDARY_NOTICE in answer


def test_metadata_display_variants_are_sanitized_before_mode3_return() -> None:
    rag = make_runtime(
        "SQL Injection may manipulate query logic. "
        "A rule match and payload indicator are internal metadata labels. "
        "A rule-match and payload-indicator should also stay hidden. "
        "Whether exploitation succeeded still requires confirmation from application behavior, responses, database errors, permissions, or subsequent events."
    )

    answer = rag.answer_question("What is SQL Injection?")
    normalized_answer = answer.casefold()

    assert "rule match" not in normalized_answer
    assert "payload indicator" not in normalized_answer
    assert "rule-match" not in normalized_answer
    assert "payload-indicator" not in normalized_answer
    assert "SQL Injection may manipulate query logic." in answer
    assert "Whether exploitation succeeded still requires confirmation" in answer
    assert RAGQA.MODE3_BOUNDARY_NOTICE in answer


def test_rag_and_llm_expansions_are_normalized_before_mode3_return() -> None:
    rag = make_runtime(
        "RAG（Retrieval-Augmented Generation） supports retrieval context. "
        "RAG（Reasoning and Generation with Alternatives） is an incorrect expansion. "
        "LLM（Language Learning Model） is an incorrect expansion. "
        "LLM (Large Language Model) should include the canonical Traditional Chinese label."
    )

    answer = rag.answer_question("What is SQL Injection?")

    assert RAGQA.CANONICAL_RAG_TERM in answer
    assert RAGQA.CANONICAL_LLM_TERM in answer
    assert "Reasoning and Generation with Alternatives" not in answer
    assert "Language Learning Model" not in answer
    assert "LLM (Large Language Model)" not in answer


def test_conflicting_final_authority_claim_is_rewritten_before_mode3_return() -> None:
    rag = make_runtime(
        "The final Risk Level and Decision are decided by an analyst. "
        "Analysts may review and investigate."
    )

    answer = rag.answer_question("What is SQL Injection?")

    assert "decided by an analyst" not in answer.casefold()
    assert RAGQA.MODE3_AUTHORITY_NOTICE in answer
    assert "Analysts may review and investigate." in answer


def test_mode3_prompt_context_uses_required_rag_terminology() -> None:
    rag = make_runtime()

    context = rag._build_answer_context("RAG 是什麼？", "knowledge context")

    assert "Retrieval-Augmented Generation" in context
    assert "檢索增強生成" in context
    assert "Reasoning and Generation with Alternatives" not in context


def test_agent_does_not_fall_through_to_legacy_rag_when_answer_question_returns_none() -> None:
    class ProtectedPathOnlyRAG:
        def is_ready(self):
            return True

        def answer_question(self, _query):
            return None

        def retrieve_context(self, _query):
            raise AssertionError("legacy retrieve_context must not be called")

        def generate_answer(self, _query, _context):
            raise AssertionError("legacy generate_answer must not be called")

    agent = SecurityAgent.__new__(SecurityAgent)
    agent.rag_qa = ProtectedPathOnlyRAG()

    answer = agent.build_rag_answer("CMD-001 是什麼？")

    assert answer == agent.NO_CONTEXT_MESSAGE


# --------------------------------------------------------------------------- #
# v2.7-E: RAG answer safety polish for Resource Exhaustion / HTTP/2 DoS / CVE
# --------------------------------------------------------------------------- #
RESOURCE_EXHAUSTION_QUESTIONS = [
    "HTTP/2 Resource Exhaustion 是什麼？",
    "HTTP/2 Bomb 疑似事件要怎麼安全分流？",
    "CVE 情報可以直接當成資產已被利用的證明嗎？",
    "HTTP/2 DoS 有哪些防禦緩解方式？",
    "Resource Exhaustion 證據缺口要看什麼？",
]

OFFENSIVE_PHRASES = [
    "run this exploit",
    "attack a real server",
    "send traffic to target",
    "amplify against public target",
    "working poc",
]


def test_rag_answer_safety_rules_contain_advisory_defensive_phrases() -> None:
    rules = RAGQA.RAG_ANSWER_SAFETY_RULES
    for phrase in (
        "建議人工評估",
        "可作為防禦規劃參考",
        "需依資產版本、設定、暴露面與修補狀態確認",
        "不提供任何 PoC",
        "流量產生",
        "CVE",
        "BLOCK / MONITOR / ALLOW",
        "不會覆蓋最終的 Risk Level 或 Decision",
        "不得宣稱系統已執行真實封鎖或設定變更",
    ):
        assert phrase in rules, f"safety rules missing: {phrase}"


def test_safety_rules_and_advisory_note_have_no_offensive_phrases() -> None:
    combined = (
        RAGQA.RAG_ANSWER_SAFETY_RULES + "\n" + RAGQA.RESOURCE_EXHAUSTION_ADVISORY_NOTE
    ).lower()
    for phrase in OFFENSIVE_PHRASES:
        assert phrase not in combined, f"forbidden offensive phrase present: {phrase}"


def test_build_answer_context_includes_rag_safety_rules() -> None:
    rag = make_runtime()

    context = rag._build_answer_context("HTTP/2 DoS 有哪些防禦緩解方式？", "knowledge context")

    assert "資安知識回答安全規則" in context
    assert "建議人工評估" in context
    assert "不提供任何 PoC" in context
    # Existing project rules and retrieved context are still present.
    assert "Retrieval-Augmented Generation" in context
    assert "knowledge context" in context


def test_is_resource_exhaustion_topic_matches_required_questions() -> None:
    rag = make_runtime()

    for question in RESOURCE_EXHAUSTION_QUESTIONS:
        assert rag._is_resource_exhaustion_topic(question) is True, question

    # Non Resource-Exhaustion topics and "dos" substrings must not match.
    assert rag._is_resource_exhaustion_topic("什麼是 SQL Injection？") is False
    assert rag._is_resource_exhaustion_topic("How do I cook dosa at home?") is False
    assert rag._is_resource_exhaustion_topic("") is False


def test_append_topic_advisory_note_only_for_resource_exhaustion_topics() -> None:
    rag = make_runtime()

    dos_answer = rag._append_topic_advisory_note("HTTP/2 緩解內容。", "HTTP/2 DoS 緩解方式？")
    assert "建議人工評估" in dos_answer
    assert "可作為防禦規劃參考" in dos_answer
    assert "不提供 PoC" in dos_answer

    # No advisory note for an unrelated topic; the body is returned unchanged.
    sql_answer = rag._append_topic_advisory_note("SQL Injection 說明。", "什麼是 SQL Injection？")
    assert sql_answer == "SQL Injection 說明。"

    # Idempotent: the note is not duplicated.
    twice = rag._append_topic_advisory_note(dos_answer, "HTTP/2 DoS 緩解方式？")
    assert twice.count(RAGQA.RESOURCE_EXHAUSTION_ADVISORY_NOTE) == 1


def test_cve_answer_states_cve_is_not_proof_of_exploitation() -> None:
    rag = make_runtime()

    answer = rag._append_topic_advisory_note(
        "CVE 是已知弱點識別碼。", "CVE 情報可以直接當成資產已被利用的證明嗎？"
    )

    assert "CVE 等背景情報不代表目前資產已被利用" in answer


def test_resource_exhaustion_answer_keeps_advisory_note_and_boundary() -> None:
    rag = make_runtime("HTTP/2 DoS 緩解措施可包含調整並行 stream 與 timeout。")
    cast(Any, rag).retrieve_controlled_context = lambda _query: ("", False, None)
    cast(Any, rag).retrieve_context = lambda _query: ("knowledge context", True)

    answer = rag.answer_question("HTTP/2 DoS 有哪些防禦緩解方式？")

    assert "HTTP/2 DoS 緩解措施" in answer  # legitimate technical body preserved
    assert "建議人工評估" in answer
    assert "不提供 PoC" in answer
    assert "CVE 等背景情報不代表目前資產已被利用" in answer
    assert RAGQA.MODE3_BOUNDARY_NOTICE in answer


def test_non_resource_topic_answer_has_no_advisory_note() -> None:
    rag = make_runtime("CMD-001 explains Command Injection. BLOCK remains simulated.")

    answer = rag.answer_question(
        "請說明 CMD-001 Command Injection 的判讀重點，以及 BLOCK 是否代表真實封鎖？"
    )

    assert RAGQA.RESOURCE_EXHAUSTION_ADVISORY_NOTE not in answer
    assert RAGQA.MODE3_BOUNDARY_NOTICE in answer


def _raise_vector_fallback():
    raise AssertionError("controlled retrieval should run before vector fallback")
