import importlib
import os
import re
from typing import Any

from config import CHROMA_PATH, EMBED_MODEL, MODEL_NAME, TOP_K
from modules.rag.controlled_retrieval import ControlledRetrievalResult, select_controlled_sources
from modules.rag.metadata import load_metadata_from_directory
from modules.rag.source_assembly import source_citation_from_metadata
from modules.rag.types import AnswerWithSources, SourceCitation
from modules.rag_query_planner import KNOWLEDGE_ROOT, RAGQueryPlanner
from modules.report_followup import protect_answer_with_guardrails
from modules.output_language import (
    DEFAULT_OUTPUT_LANGUAGE,
    OUTPUT_LANGUAGE_BILINGUAL,
    OUTPUT_LANGUAGE_EN,
    normalize_output_language,
    output_language_instruction,
)



def _chat_prompt_template_class() -> Any:
    from langchain_core.prompts import ChatPromptTemplate

    return ChatPromptTemplate


OpenCCClass: Any = None
try:
    OpenCCClass = getattr(importlib.import_module("opencc"), "OpenCC")  # noqa: B009
except Exception:
    pass


class RAGQA:
    CONTROLLED_KNOWLEDGE_DIR = KNOWLEDGE_ROOT / "report_explainer"
    CANONICAL_RAG_TERM = "RAG（Retrieval-Augmented Generation，檢索增強生成）"
    CANONICAL_LLM_TERM = "LLM（Large Language Model，大型語言模型）"
    # v2.7-F: CVE is an identifier, not a scoring system. CVSS is the scoring
    # system. These canonical labels fix the observed "CVE（共通漏洞與風險評分系統）"
    # confusion without touching legitimate CVSS mentions or CVE-IDs.
    CANONICAL_CVE_TERM = "CVE（Common Vulnerabilities and Exposures，弱點識別編號）"
    CANONICAL_CVSS_TERM = "CVSS（Common Vulnerability Scoring System，弱點評分系統）"
    MODE3_AUTHORITY_NOTICE = (
        "最終的 Risk Level 與 Decision 由本專案的 deterministic 系統流程產生；"
        "分析師可進行複核與後續調查，但 RAG 與 LLM 不會覆蓋這些最終欄位。"
    )
    INTERNAL_METADATA_TERMS = (
        "structured signals",
        "payload_indicator",
        "payload indicator",
        "payload-indicator",
        "rule_match",
        "rule match",
        "rule-match",
    )
    MODE3_BOUNDARY_NOTICE = (
        "安全邊界：本專案中的 BLOCK、MONITOR 與 ALLOW 皆為模擬決策。"
        "RAG 與 LLM 僅提供解釋與輔助資訊，不會覆蓋最終的 Risk Level 或 Decision。"
        "此回答不代表已執行真實封鎖、監控部署、密碼重設、"
        "防火牆／WAF／EDR 設定變更或帳號處置。"
    )
    MODE3_BOUNDARY_NOTICE_EN = (
        "Safety boundary: BLOCK, MONITOR, and ALLOW are simulated project decisions. "
        "RAG and LLM content is advisory explanation only and does not override the "
        "final Risk Level or Decision. This answer does not mean real blocking, "
        "monitoring deployment, password reset, firewall/WAF/EDR configuration "
        "change, or account action was executed."
    )
    MODE3_BOUNDARY_NOTICE_BILINGUAL = (
        f"{MODE3_BOUNDARY_NOTICE} / Safety boundary: RAG and LLM content is advisory "
        "only and does not override deterministic Risk Level or Decision."
    )

    # v2.7-E: topic-scoped advisory note for Resource Exhaustion / HTTP/2 DoS /
    # CVE answers. Appended deterministically; it only adds defensive framing and
    # never rewrites the answer body or any legitimate technical term.
    RESOURCE_EXHAUSTION_ADVISORY_NOTE = (
        "防禦建議說明：以上內容屬建議人工評估性質，可作為防禦規劃參考，"
        "需依資產版本、設定、暴露面與修補狀態確認；"
        "不代表系統已執行真實封鎖或設定變更，也不提供 PoC、利用步驟或流量產生指引。"
        "CVE 等背景情報不代表目前資產已被利用。"
    )
    RESOURCE_EXHAUSTION_ADVISORY_NOTE_EN = (
        "Defensive triage note: use this content for safe analyst review and "
        "defensive planning. Confirm asset version, configuration, exposure, "
        "telemetry, and patch status. This does not mean the system applied real "
        "blocking or configuration changes, and it does not provide PoC, exploit "
        "steps, or traffic-generation guidance. CVE context is not proof that the "
        "current asset was exploited."
    )
    RESOURCE_EXHAUSTION_ADVISORY_NOTE_BILINGUAL = (
        f"{RESOURCE_EXHAUSTION_ADVISORY_NOTE} / Defensive triage note: no PoC, "
        "exploit steps, traffic generation, or real enforcement; CVE context is not proof."
    )
    RESOURCE_EXHAUSTION_TOPIC_TERMS = (
        "resource exhaustion",
        "http/2",
        "http 2",
        "denial of service",
        "vulnerability",
        "mitigation",
        "資源耗盡",
        "弱點情報",
        "漏洞",
        "安全分流",
        "防禦緩解",
        "緩解",
        "證據缺口",
        "背景情報",
        "被利用",
    )

    PROJECT_ANSWER_RULES = """
專案知識回答規則：
1. 請使用提供的本專案 blue-team knowledge 內容回答，不要改用通用資安報告格式。
2. 請遵守 Output language policy（語言政策）作答；Security Triage Report、Risk Level、Decision、AI Assist 等專有欄位可保留英文。
3. 如果問題詢問 Security Triage Report、triage report、report、分流報告、應變報告或「怎麼看」，必須說明本專案實際報告區塊：
   0. Quick Verdict
   1. Summary
   2. Evidence
   3. Why It Matters
   4. Recommended Response
   5. Simulation Notice
   6. AI Assist
4. 說明 Risk Level 與 Decision 是最終系統欄位。
5. 說明 BLOCK / MONITOR / ALLOW 是模擬決策，不是真的控制防火牆、WAF、EDR 或身份平台。
6. 說明 LLM Suggested Decision 只是 AI assist，不是 final decision。
7. 如果問題詢問 login failure、登入失敗、多次登入失敗、brute force 或暴力破解分析，且 context 中有相關內容，必須涵蓋 source_ip、target/endpoint、user、failed_count、HTTP 401/403、time window、false positive considerations。
8. 不要主要根據 Structured Signals 回答；Structured Signals 只能當作 metadata hints。
9. 若提到 RAG，其全名固定為 Retrieval-Augmented Generation（檢索增強生成），不得展開為其他名稱。
10. 最終的 Risk Level 與 Decision 由本專案的 deterministic 系統流程產生；分析師可進行複核與後續調查，但 RAG 與 LLM 不會覆蓋這些最終欄位。
""".strip()
    REPORT_GUIDE_ANSWER_RULES = """
Security Triage Report 回答要求：
1. 這題是在問本專案的 Security Triage Report 格式，請完整說明下列所有區塊，不可只說前三項：
   - 0. Quick Verdict
   - 1. Summary
   - 2. Evidence
   - 3. Why It Matters
   - 4. Recommended Response
   - 5. Simulation Notice
   - 6. AI Assist
2. 必須說明 Risk Level 代表系統的風險評估。
3. 必須說明 Decision 代表最終系統決策。
4. 必須說明 BLOCK / MONITOR / ALLOW 只是模擬決策，不是真的控制防火牆、WAF、EDR 或身份平台。
5. 必須說明 LLM Suggested Decision 只是 AI assist，不會覆蓋 final Decision。
6. RAG 只能解釋知識與報告欄位，不要判斷事件是否為攻擊，也不要替事件決定 BLOCK / MONITOR / ALLOW。
7. 不要把 Structured Signals 當主要內容；它只能作為 metadata hints。
""".strip()

    METADATA_SUPPRESSION_RULES = """
Metadata suppression rules:
1. Do not output the "Structured Signals" section.
2. Do not include YAML metadata from the knowledge file in the final answer.
3. Use Structured Signals only as internal metadata hints.
4. If the retrieved context contains Structured Signals, summarize the human-readable knowledge sections instead.
""".strip()

    # v2.7-E: defensive answer-safety instruction for security knowledge answers
    # (especially Resource Exhaustion / HTTP/2 DoS / CVE). Keeps generated wording
    # advisory and non-operational without adding offensive content.
    RAG_ANSWER_SAFETY_RULES = """
資安知識回答安全規則：
1. 僅根據提供的檢索內容（retrieved context）作答，保持藍隊防禦判讀語氣。
2. 不提供任何 PoC、利用步驟、精確攻擊參數或流量產生（traffic generation）指引。
3. 所有處置建議皆為建議人工評估、可作為防禦規劃參考，需經人工審查後才可採用。
4. 針對 HTTP/2、Resource Exhaustion、DoS 與緩解措施，請使用「建議人工評估」「可檢查」「可作為防禦規劃參考」等措辭；避免「立即採取防禦措施」「直接設定」「執行封鎖」等命令式或暗示系統會自動強制執行的說法，也不要列出精確的並行流數量、封包大小等攻擊或流量產生參數。
5. CVE 等背景情報不代表目前資產已被利用，需依資產版本、設定、暴露面與修補狀態確認。
6. 不得宣稱系統已執行真實封鎖或設定變更；BLOCK / MONITOR / ALLOW 皆為模擬決策，且不會覆蓋最終的 Risk Level 或 Decision。
7. 術語請使用正確全名，不要發明錯誤展開：CVE = Common Vulnerabilities and Exposures（弱點識別編號），CVSS = Common Vulnerability Scoring System（弱點評分系統），RAG = Retrieval-Augmented Generation（檢索增強生成），LLM = Large Language Model（大型語言模型）。CVE 是弱點識別編號，不是評分系統；評分系統是 CVSS。DoS = Denial of Service（阻斷服務），DDoS = Distributed Denial of Service（分散式阻斷服務）。
""".strip()

    def __init__(self):
        self.embeddings = None
        self.llm = None
        self.query_planner = None
        self._query_plan_cache = {}
        self.controlled_metadata_items = self._load_controlled_metadata()
        self.vectorstore = None
        self.init_error = None
        self._components_initialized = False
        self.main_prompt = None
        self.point_follow_prompt = None
        self.natural_follow_prompt = None

        self._initialize_prompts()

    def _initialize_prompts(self):
        if self.main_prompt is not None:
            return

        try:
            prompt_template = _chat_prompt_template_class()
        except Exception as exc:
            self.init_error = exc
            return

        self.main_prompt = prompt_template.from_template(
            """
你是資安知識問答助手，請根據提供的內容回答問題。
重要規則：
1. 請依參考內容開頭的 Output language policy（語言政策）指定的語言與風格作答。
2. 使用正確的資安術語全名，避免錯誤展開或簡繁混淆。
3. 優先依據提供內容作答，保持準確、精簡、清楚。
4. 若內容不足以支持明確結論，請明確說明資訊不足，不要臆測。

參考內容：
{context}

問題：{question}
"""
        )

        self.point_follow_prompt = prompt_template.from_template(
            """
你是資安知識問答助手，請針對指定重點做延伸說明。
重要規則：
1. 請遵守 Output language policy（語言政策）：預設以繁體中文為主並保留必要英文資安術語，介面語言為 English 時以英文作答。
2. 使用正確的資安術語全名，避免造成混淆。
3. 先直接解釋重點，再補充其風險、判讀方式或防禦意義。
4. 內容要清楚、精簡，避免離題。

重點：{target}
"""
        )

        self.natural_follow_prompt = prompt_template.from_template(
            """
你是資安知識問答助手，請根據既有主題回答後續追問。
重要規則：
1. 請遵守 Output language policy（語言政策）：預設以繁體中文為主並保留必要英文資安術語，介面語言為 English 時以英文作答。
2. 保持清楚、精簡、防禦導向的語氣，避免臆測。
3. 回答必須緊扣目前主題，不能轉成一般程式教學、SQL 教學或與主題無關的背景知識。
4. 請從藍隊、防禦、偵測、風險判讀、日誌分析或事件應變的角度回答。
5. 不可提供任何程式碼、正則表示式、腳本、查詢語句範例或 exploit 建構步驟。
6. 若使用者要求舉例，只能提供高信心的安全日誌跡象、可疑 Payload 樣式、藍隊偵測觀察與防禦判讀。
7. 不可使用一般程式語法、正常 SQL 語法或單一常見關鍵字當作例子，例如 `SELECT * FROM`、`INSERT INTO`、分號本身，因為這些單獨出現時不具高判斷力。
8. 若主題是 SQL Injection，優先使用這類例子：請求包含 `' OR '1'='1`、`UNION SELECT` 且伴隨異常參數、使用者可控輸入後方出現 `'--` 或註解標記、資料庫錯誤日誌重複增加、回應大小異常、登入成功率異常、回應延遲異常且疑似 time-based injection。
9. 要明確說明單一關鍵字通常不足以判定攻擊，必須結合上下文與多種跡象交叉判讀。
10. 回答要精簡。
11. 若資訊不足，請明確說明資訊不足，不要自行補造結論。

目前主題：
{focus}

追問：{question}

請直接作答。
"""
        )


    def _load_controlled_metadata(self):
        try:
            return load_metadata_from_directory(self.CONTROLLED_KNOWLEDGE_DIR)
        except Exception:
            return []

    def _initialize_components(self):
        if self._components_initialized:
            return

        self._components_initialized = True
        self._initialize_prompts()

        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings

            self.embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
        except Exception as exc:
            self.init_error = exc
            return

        try:
            from langchain_community.chat_models import ChatOllama

            self.llm = ChatOllama(model=MODEL_NAME, temperature=0)
            self.query_planner = RAGQueryPlanner(llm=self.llm)
        except Exception as exc:
            self.init_error = exc
            self.llm = None
            self.query_planner = None

        if not os.path.exists(CHROMA_PATH):
            if self.init_error is None:
                self.init_error = FileNotFoundError(f"找不到向量資料庫：{CHROMA_PATH}")
            return

        try:
            from langchain_community.vectorstores import Chroma

            self.vectorstore = Chroma(
                persist_directory=CHROMA_PATH,
                embedding_function=self.embeddings,
            )
        except Exception as exc:
            self.init_error = exc
            self.vectorstore = None

    def _ensure_initialized(self) -> None:
        # Tests may construct focused RAGQA instances via __new__ to exercise
        # answer-safety helpers without real RAG dependencies. Those objects do
        # not own runtime component state and should not initialize it here.
        if not hasattr(self, "_components_initialized"):
            return
        self._initialize_components()

    def is_ready(self) -> bool:
        self._ensure_initialized()
        return self.vectorstore is not None and self.llm is not None

    def _get_query_plan(self, query: str):
        self._ensure_initialized()
        cache_key = query or ""
        if cache_key not in self._query_plan_cache:
            if self.query_planner is None:
                self._query_plan_cache[cache_key] = None
            else:
                self._query_plan_cache[cache_key] = self.query_planner.plan(query)

        return self._query_plan_cache[cache_key]

    def is_security(self, query: str) -> bool:
        if not query:
            return False

        plan = self._get_query_plan(query)
        if plan is None:
            return False

        return plan.is_security_question

    def expand_query(self, query: str) -> str:
        plan = self._get_query_plan(query)
        if plan is not None and plan.is_security_question and plan.rewritten_query:
            return plan.rewritten_query

        return query or ""

    def load_full_source_text(self, source_path: str) -> str:
        if not source_path:
            return ""

        try:
            with open(source_path, "r", encoding="utf-8") as file:
                return file.read()
        except UnicodeDecodeError:
            try:
                with open(source_path, "r", encoding="utf-8-sig") as file:
                    return file.read()
            except UnicodeDecodeError:
                try:
                    with open(source_path, "r", encoding="cp950") as file:
                        return file.read()
                except Exception:
                    return ""
        except Exception:
            return ""

    def select_controlled_sources(self, query: str) -> ControlledRetrievalResult:
        return select_controlled_sources(query, self.controlled_metadata_items)

    def retrieve_controlled_context(self, query: str):
        result = self.select_controlled_sources(query)
        if not result.has_matches:
            return "", False, result

        sections = []
        for match in result.matches:
            source_path = match.metadata.source_path
            if not source_path:
                continue

            source_text = self.load_full_source_text(source_path)
            if source_text.strip():
                sections.append(f"[Source: {source_path}]\n{source_text.strip()}")

        context = "\n\n".join(sections).strip()
        return context, bool(context), result

    def answer_question(
        self, query: str, language: str | None = DEFAULT_OUTPUT_LANGUAGE
    ) -> str | None:
        self._ensure_initialized()
        output_language = normalize_output_language(language)
        controlled_context, ok, controlled_result = self.retrieve_controlled_context(query)
        if ok:
            answer = self._generate_answer_for_language(
                query, controlled_context, output_language
            )
            citations = [
                source_citation_from_metadata(match.metadata)
                for match in controlled_result.matches
            ]
            return self._protect_mode3_answer(
                answer,
                citations,
                rule_ids=self._rule_ids_from_controlled_result(controlled_result),
                limitations=["Controlled curated retrieval selected approved runtime metadata."],
                query=query,
                language=output_language,
            )

        context, ok = self.retrieve_context(query)
        if not ok:
            return None

        answer = self._generate_answer_for_language(query, context, output_language)
        return self._protect_mode3_answer(
            answer,
            [
                SourceCitation(
                    source="runtime/vector_fallback",
                    kind="knowledge_doc",
                    heading="Existing vector fallback",
                    identifier="vector_fallback",
                )
            ],
            limitations=["Existing vector retrieval fallback was used."],
            query=query,
            language=output_language,
        )

    def _generate_answer_for_language(self, query: str, context: str, language: str) -> str:
        try:
            return self.generate_answer(query, context, language=language)
        except TypeError:
            # Tests and older adapters may monkeypatch generate_answer(query, context).
            # Fallback preserves existing behavior without changing retrieval semantics.
            return self.generate_answer(query, context)

    def _protect_mode3_answer(
        self,
        answer: str,
        citations: list[SourceCitation],
        *,
        rule_ids: list[str] | None = None,
        limitations: list[str] | None = None,
        query: str = "",
        language: str | None = DEFAULT_OUTPUT_LANGUAGE,
    ) -> str:
        output_language = normalize_output_language(language)
        polished = self._append_topic_advisory_note(
            self._strip_structured_signals(answer), query, output_language
        )
        protected_input = AnswerWithSources(
            answer=self._append_mode3_boundary(polished, output_language),
            sources=citations,
            rule_ids=rule_ids or [],
            confidence="MEDIUM",
            limitations=limitations or [],
        )
        protected = protect_answer_with_guardrails(
            protected_input,
            known_rule_ids=self._known_controlled_rule_ids(),
        )
        return protected.answer.answer

    def _mode3_boundary_notice(self, language: str) -> str:
        if language == OUTPUT_LANGUAGE_EN:
            return self.MODE3_BOUNDARY_NOTICE_EN
        if language == OUTPUT_LANGUAGE_BILINGUAL:
            return self.MODE3_BOUNDARY_NOTICE_BILINGUAL
        return self.MODE3_BOUNDARY_NOTICE

    def _append_mode3_boundary(
        self, answer: str, language: str | None = DEFAULT_OUTPUT_LANGUAGE
    ) -> str:
        notice = self._mode3_boundary_notice(normalize_output_language(language))
        if notice in answer:
            return answer
        return f"{answer.rstrip()}\n\n{notice}"

    def _is_resource_exhaustion_topic(self, query: str) -> bool:
        """Deterministically detect Resource Exhaustion / HTTP/2 DoS / CVE topics."""
        normalized = (query or "").casefold()
        if any(term in normalized for term in self.RESOURCE_EXHAUSTION_TOPIC_TERMS):
            return True
        # Short, ambiguous tokens matched on word boundaries (e.g. avoid "dosa").
        return bool(re.search(r"\b(?:cve|dos)\b", normalized))

    def _resource_exhaustion_advisory_note(self, language: str) -> str:
        if language == OUTPUT_LANGUAGE_EN:
            return self.RESOURCE_EXHAUSTION_ADVISORY_NOTE_EN
        if language == OUTPUT_LANGUAGE_BILINGUAL:
            return self.RESOURCE_EXHAUSTION_ADVISORY_NOTE_BILINGUAL
        return self.RESOURCE_EXHAUSTION_ADVISORY_NOTE

    def _append_topic_advisory_note(
        self,
        answer: str,
        query: str,
        language: str | None = DEFAULT_OUTPUT_LANGUAGE,
    ) -> str:
        """Append a defensive advisory note for Resource Exhaustion / DoS / CVE.

        Only adds framing text; it never rewrites the answer body or any
        technical term. No-op for other topics or if already present.
        """
        if not self._is_resource_exhaustion_topic(query):
            return answer
        note = self._resource_exhaustion_advisory_note(normalize_output_language(language))
        if note in answer:
            return answer
        return f"{answer.rstrip()}\n\n{note}"

    def _rule_ids_from_controlled_result(self, result: ControlledRetrievalResult) -> list[str]:
        rule_ids: list[str] = []
        for match in result.matches:
            for rule_id in match.metadata.rule_ids:
                if rule_id not in rule_ids:
                    rule_ids.append(rule_id)
        return rule_ids

    def _known_controlled_rule_ids(self) -> set[str]:
        return {
            rule_id
            for metadata in self.controlled_metadata_items
            for rule_id in metadata.rule_ids
        }

    def _resolve_knowledge_source(self, source_path: str):
        try:
            normalized = str(source_path or "").strip().replace("\\", "/")
            if not normalized:
                return None

            root = KNOWLEDGE_ROOT.resolve()
            candidate = (root / normalized).resolve()
            if root not in candidate.parents:
                return None
            if not candidate.is_file() or candidate.suffix.lower() != ".md":
                return None
            return candidate
        except Exception:
            return None

    def _load_preferred_sources_context(self, preferred_sources):
        if not preferred_sources:
            return ""

        sections = []
        for source in preferred_sources:
            source_path = self._resolve_knowledge_source(source)
            if source_path is None:
                continue

            source_text = self.load_full_source_text(str(source_path))
            if source_text.strip():
                sections.append(f"[Source: {source}]\n{source_text.strip()}")

        return "\n\n".join(sections).strip()

    def retrieve_context(self, query: str):
        self._ensure_initialized()
        if not query:
            return "", False

        plan = self._get_query_plan(query)
        if plan is None or not plan.is_security_question:
            return "", False

        if plan.preferred_sources:
            direct_context = self._load_preferred_sources_context(plan.preferred_sources)
            if direct_context:
                return direct_context, True

        if self.vectorstore is None:
            return "", False

        try:
            expanded = plan.rewritten_query or query
            results = self.vectorstore.similarity_search_with_score(expanded, k=TOP_K)
        except Exception:
            return "", False

        if not results:
            return "", False

        best_distance = results[0][1]
        if best_distance > 1.2:
            return "", False

        top_source = results[0][0].metadata.get("source")
        full_text = self.load_full_source_text(top_source)
        if full_text.strip():
            return full_text, True

        same_source_docs = []
        for doc, _score in results:
            if doc.metadata.get("source") == top_source:
                same_source_docs.append(doc.page_content)

        context = "\n\n".join(same_source_docs).strip()
        return context, bool(context)

    def extract_relevant_section(self, context: str, query: str) -> str:
        if not context or not query:
            return context

        plan = self._get_query_plan(query)
        if plan is None or not plan.is_security_question or not plan.preferred_sections:
            return context

        lines = context.splitlines()
        extracted = []
        capture = False

        for raw_line in lines:
            line = raw_line.strip()
            if line.startswith("#") and any(
                keyword in line for keyword in plan.preferred_sections
            ):
                capture = True
                extracted.append(line)
                continue

            if capture and line.startswith("#"):
                break

            if capture:
                extracted.append(line)

        focused = "\n".join(extracted).strip()
        return focused if focused else context

    def _safe_invoke(self, chain, payload, fallback_message):
        if self.llm is None:
            return "LLM 目前不可用，無法生成回答。"

        try:
            response = chain.invoke(payload)
            return response.content.strip()
        except Exception:
            return fallback_message

    def _to_traditional(self, text: str) -> str:
        if not text or OpenCCClass is None:
            return text

        try:
            return OpenCCClass("s2t").convert(text)
        except Exception:
            return text

    def _convert_output_for_language(self, text: str, language: str | None) -> str:
        # Simplified->Traditional conversion only when Traditional Chinese is the
        # target (zh-TW or bilingual). English answers are not forced to Traditional.
        if normalize_output_language(language) == OUTPUT_LANGUAGE_EN:
            return text
        return self._to_traditional(text)

    def _filter_followup_examples(self, text: str) -> str:
        if not text:
            return text

        generic_patterns = ("select *", "insert into", "update", "delete from")
        high_signal_patterns = ("' or '1'='1", "union select", "'--")

        filtered_lines = []
        for raw_line in text.splitlines():
            lowered = raw_line.lower()
            has_generic = any(pattern in lowered for pattern in generic_patterns)
            has_high_signal = any(pattern in lowered for pattern in high_signal_patterns)

            if has_generic and not has_high_signal:
                continue

            filtered_lines.append(raw_line)

        result = "\n".join(filtered_lines).strip()
        if not result:
            return text

        return re.sub(r"\n{3,}", "\n\n", result)

    def _is_report_guide_question(self, query: str) -> bool:
        plan = self._get_query_plan(query)
        if plan is None or not plan.is_security_question:
            return False

        preferred_sources = getattr(plan, "preferred_sources", []) or []
        if "report_guides/security_triage_report_guide.md" in preferred_sources:
            return True

        topic = str(getattr(plan, "topic", "") or "").lower()
        intent = str(getattr(plan, "intent", "") or "").lower()
        return "triage_report" in topic or intent == "report_guide"

    def _build_language_instruction(self, language: str | None) -> str:
        return (
            "Output language policy:\n"
            f"{output_language_instruction(language)}"
        )

    def _build_answer_context(
        self,
        query: str,
        context: str,
        language: str | None = DEFAULT_OUTPUT_LANGUAGE,
    ) -> str:
        language_instruction = self._build_language_instruction(language)
        if self._is_report_guide_question(query):
            return f"{language_instruction}\n\n{self.RAG_ANSWER_SAFETY_RULES}\n\n{self.PROJECT_ANSWER_RULES}\n\n{self.REPORT_GUIDE_ANSWER_RULES}\n\n{self.METADATA_SUPPRESSION_RULES}\n\n{context}"

        focused_context = self.extract_relevant_section(context, query)
        return f"{language_instruction}\n\n{self.RAG_ANSWER_SAFETY_RULES}\n\n{self.PROJECT_ANSWER_RULES}\n\n{self.METADATA_SUPPRESSION_RULES}\n\n{focused_context}"

    def _strip_structured_signals(self, text: str) -> str:
        if not text:
            return text

        patterns = (
            r"(?ims)^\s*#{2,3}\s*Structured Signals\b.*\Z",
            r"(?ims)^\s*Structured Signals\s*:?\s*```(?:yaml|yml)?\s*.*?```\s*\Z",
            r"(?ims)^\s*Structured Signals\b.*\Z",
        )
        result = text
        for pattern in patterns:
            result = re.sub(pattern, "", result).rstrip()

        result = self._strip_inline_internal_metadata(result)
        result = self._normalize_visible_terminology(result)
        result = self._normalize_cve_terminology(result)
        result = self._normalize_final_authority_claims(result)
        return result if result else text

    def _strip_inline_internal_metadata(self, text: str) -> str:
        sanitized_paragraphs = []
        for paragraph in re.split(r"\n+", text):
            sanitized = self._strip_metadata_sentences(paragraph.strip())
            if sanitized:
                sanitized_paragraphs.append(sanitized)

        return "\n".join(sanitized_paragraphs).strip()

    def _strip_metadata_sentences(self, paragraph: str) -> str:
        if not paragraph or not self._contains_internal_metadata_term(paragraph):
            return paragraph

        pieces = re.split(r"(?<=[。.!?！？])\s*", paragraph)
        safe_pieces = [
            piece.strip()
            for piece in pieces
            if piece.strip() and not self._contains_internal_metadata_term(piece)
        ]
        return " ".join(safe_pieces).strip()

    def _contains_internal_metadata_term(self, text: str) -> bool:
        normalized = text.casefold()
        return any(term in normalized for term in self.INTERNAL_METADATA_TERMS)

    def _normalize_visible_terminology(self, text: str) -> str:
        result = text
        rag_patterns = (
            r"RAG\s*\(\s*Retrieval-Augmented Generation\s*\)",
            r"RAG（\s*Retrieval-Augmented Generation\s*）",
            r"RAG\s*\(\s*Reasoning and Generation with Alternatives\s*\)",
            r"RAG（\s*Reasoning and Generation with Alternatives\s*）",
        )
        llm_patterns = (
            r"LLM\s*\(\s*Large Language Model\s*\)",
            r"LLM（\s*Large Language Model\s*）",
            r"LLM\s*\(\s*Language Learning Model\s*\)",
            r"LLM（\s*Language Learning Model\s*）",
        )

        for pattern in rag_patterns:
            result = re.sub(pattern, self.CANONICAL_RAG_TERM, result, flags=re.IGNORECASE)
        for pattern in llm_patterns:
            result = re.sub(pattern, self.CANONICAL_LLM_TERM, result, flags=re.IGNORECASE)

        return result

    def _normalize_cve_terminology(self, text: str) -> str:
        """Rewrite incorrect CVE expansions (a scoring / risk-scoring system) to
        the correct CVE meaning.

        Only a bare ``CVE`` acronym directly followed by a parenthetical that
        wrongly describes a scoring system is rewritten. Legitimate CVSS mentions,
        correct CVE expansions (e.g. an identifier), and CVE-IDs like
        ``CVE-2026-49975`` are left untouched.
        """
        pattern = re.compile(
            r"(?<![A-Za-z0-9])CVE\s*[（(]\s*[^（()）]*"
            r"(?:評分|scoring system|risk scoring|風險評分)"
            r"[^（()）]*[）)]",
            re.IGNORECASE,
        )
        return pattern.sub(self.CANONICAL_CVE_TERM, text)

    def _normalize_final_authority_claims(self, text: str) -> str:
        normalized_paragraphs = []
        for paragraph in re.split(r"\n+", text):
            normalized = self._normalize_final_authority_paragraph(paragraph.strip())
            if normalized:
                normalized_paragraphs.append(normalized)

        return "\n".join(normalized_paragraphs).strip()

    def _normalize_final_authority_paragraph(self, paragraph: str) -> str:
        if not paragraph:
            return paragraph

        pieces = re.split(r"(?<=[。.!?！？])\s*", paragraph)
        normalized_pieces: list[str] = []
        authority_added = False
        for piece in pieces:
            stripped_piece = piece.strip()
            if not stripped_piece:
                continue
            if self._is_conflicting_final_authority_claim(stripped_piece):
                if not authority_added:
                    normalized_pieces.append(self.MODE3_AUTHORITY_NOTICE)
                    authority_added = True
                continue
            normalized_pieces.append(stripped_piece)

        return " ".join(normalized_pieces).strip()

    def _is_conflicting_final_authority_claim(self, text: str) -> bool:
        normalized = text.casefold()
        has_final_field = "risk level" in normalized or "decision" in normalized
        has_analyst_actor = "analyst" in normalized or "分析師" in normalized
        has_decision_action = any(
            term in normalized
            for term in ("decide", "decides", "decided", "決定", "判定", "裁定")
        )
        return has_final_field and has_analyst_actor and has_decision_action

    def generate_answer(
        self,
        query: str,
        context: str,
        language: str | None = DEFAULT_OUTPUT_LANGUAGE,
    ):
        self._ensure_initialized()
        if not query:
            return "請先輸入問題。"
        if not context:
            return "目前找不到足夠的知識內容來回答這個問題。"

        output_language = normalize_output_language(language)
        prompt_context = self._build_answer_context(query, context, output_language)
        if self.main_prompt is None:
            return "RAG answer generation is unavailable."
        chain = self.main_prompt | self.llm
        raw_answer = self._safe_invoke(
            chain,
            {"context": prompt_context, "question": query},
            "回答生成失敗，請稍後再試。",
        )
        answer = self._convert_output_for_language(raw_answer, output_language)
        return self._strip_structured_signals(answer)

    def explain_point(self, target: str):
        self._ensure_initialized()
        if not target:
            return "目前沒有可延伸說明的重點。"

        if self.point_follow_prompt is None:
            return "RAG follow-up is unavailable."

        chain = self.point_follow_prompt | self.llm
        return self._to_traditional(
            self._safe_invoke(
                chain,
                {"target": target},
                "延伸說明生成失敗，請稍後再試。",
            )
        )

    def handle_natural_followup(self, focus: str, question: str):
        self._ensure_initialized()
        if not focus or not question:
            return "目前缺少足夠的上下文來回答追問。"

        if self.natural_follow_prompt is None:
            return "RAG follow-up is unavailable."

        chain = self.natural_follow_prompt | self.llm
        answer = self._to_traditional(
            self._safe_invoke(
                chain,
                {"focus": focus, "question": question},
                "追問回答生成失敗，請稍後再試。",
            )
        )
        return self._filter_followup_examples(answer)
