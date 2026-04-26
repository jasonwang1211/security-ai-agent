import os
import re

from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate

try:
    from opencc import OpenCC
except Exception:
    OpenCC = None

from config import CHROMA_PATH, EMBED_MODEL, MODEL_NAME, TOP_K


class RAGQA:
    def __init__(self):
        self.embeddings = None
        self.llm = None
        self.vectorstore = None
        self.init_error = None

        self.main_prompt = ChatPromptTemplate.from_template(
            """
你是一個資安助理。請只根據提供的內容回答問題。

回答要求：
1. 先直接回答問題。
2. 使用清楚、簡潔的繁體中文。
3. 如果內容不足，明確說明資料不足。
4. 若問題涉及攻擊手法，可補充風險與防禦重點。

參考內容：
{context}

問題：
{question}
"""
        )

        self.point_follow_prompt = ChatPromptTemplate.from_template(
            """
你是一個資安助理。請只解釋下面這一個重點，不要延伸到其他主題。

重點：
{target}

回答要求：
1. 使用繁體中文。
2. 先用一句短結論直接說明它的意思。
3. 最多補充 2 個簡短重點。
4. 不要提供程式碼範例。
5. 不要延伸到無關的攻擊手法、背景或額外主題。
"""
        )

        self.natural_follow_prompt = ChatPromptTemplate.from_template(
            """
你是一個資安助理。請延續前一個主題回答追問。

前一個焦點：
{focus}

追問：
{question}

回答要求：
1. 承接前面的焦點作答。
2. 用簡潔繁體中文回答。
3. 若資訊不足，明確說明。
"""
        )

        self.main_prompt = ChatPromptTemplate.from_template(
            """
你是資安知識問答助手，請根據提供的內容回答問題。
重要規則：
1. 回答必須只使用繁體中文。
2. 不可輸出簡體中文；若術語或表述常見為簡體寫法，請先轉換為繁體中文再回答。
3. 優先依據提供內容作答，保持準確、精簡、清楚。
4. 若內容不足以支持明確結論，請明確說明資訊不足，不要臆測。

參考內容：
{context}

問題：{question}
"""
        )

        self.point_follow_prompt = ChatPromptTemplate.from_template(
            """
你是資安知識問答助手，請針對指定重點做延伸說明。
重要規則：
1. 回答必須只使用繁體中文。
2. 不可輸出簡體中文；若術語或表述常見為簡體寫法，請先轉換為繁體中文再回答。
3. 先直接解釋重點，再補充其風險、判讀方式或防禦意義。
4. 內容要清楚、精簡，避免離題。

重點：{target}
"""
        )

        self.natural_follow_prompt = ChatPromptTemplate.from_template(
            """
你是資安知識問答助手，請根據既有主題回答後續追問。
重要規則：
1. 回答必須只使用繁體中文。
2. 不可輸出簡體中文；若術語或表述常見為簡體寫法，請先轉換為繁體中文再回答。
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

        self._initialize_components()

    def _initialize_components(self):
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
        except Exception as exc:
            self.init_error = exc
            return

        try:
            self.llm = ChatOllama(model=MODEL_NAME, temperature=0)
        except Exception as exc:
            self.init_error = exc
            self.llm = None

        if not os.path.exists(CHROMA_PATH):
            if self.init_error is None:
                self.init_error = FileNotFoundError(f"找不到向量資料庫：{CHROMA_PATH}")
            return

        try:
            self.vectorstore = Chroma(
                persist_directory=CHROMA_PATH,
                embedding_function=self.embeddings,
            )
        except Exception as exc:
            self.init_error = exc
            self.vectorstore = None

    def is_ready(self) -> bool:
        return self.vectorstore is not None and self.llm is not None

    def is_security(self, query: str) -> bool:
        security_topics = [
            "sql",
            "sql injection",
            "xss",
            "csrf",
            "anomaly",
            "anomaly detection",
            "unknown attack",
            "unknown threat",
            "zero-day",
            "zero day",
            "command injection",
            "path traversal",
            "log analysis",
            "risk scoring",
            "session",
            "cookie",
            "異常",
            "異常偵測",
            "未知攻擊",
            "未知威脅",
            "日誌",
            "風險評分",
            "漏洞",
            "攻擊",
            "防禦",
            "風險",
            "資安",
            "注入",
            "跨站",
            "弱點",
        ]
        normalized = (query or "").lower()
        return any(keyword in normalized for keyword in security_topics)

    def expand_query(self, query: str) -> str:
        expanded = query or ""
        lowered = expanded.lower()

        if "command injection" in lowered or "指令注入" in expanded:
            expanded += " Command Injection OS Command Injection Shell Injection"

        if "sql" in lowered or "sql injection" in lowered or "注入" in expanded:
            expanded += " SQL Injection database query payload"

        if "xss" in lowered or "跨站" in expanded:
            expanded += " XSS script javascript browser payload"

        if "csrf" in lowered:
            expanded += " CSRF token SameSite Referer Origin"

        if "zero-day" in lowered or "zero day" in lowered or "零日" in expanded:
            expanded += " Zero-Day exploit vulnerability patch"

        if "path traversal" in lowered or "路徑穿越" in expanded:
            expanded += " path traversal file read ../"

        return expanded

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

    def retrieve_context(self, query: str):
        if not query or self.vectorstore is None:
            return "", False

        try:
            expanded = self.expand_query(query)
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

        normalized_query = (query or "").lower()
        section_keywords = []
        if (
            "偵測" in query
            or "偵測邏輯" in query
            or "detection" in normalized_query
            or "detection logic" in normalized_query
        ):
            section_keywords = ["偵測邏輯", "Detection Logic"]
        elif "特徵" in query or "跡象" in query:
            section_keywords = ["特徵", "跡象"]
        elif "防禦" in query or "怎麼防" in query or "如何防" in query:
            section_keywords = ["防禦", "預防", "緩解"]
        elif "危害" in query or "影響" in query or "風險" in query:
            section_keywords = ["危害", "影響", "風險"]
        elif "處理" in query or "怎麼辦" in query:
            section_keywords = ["處理", "修補", "應對"]
        elif "定義" in query or "是什麼" in query:
            section_keywords = ["定義", "說明"]

        if not section_keywords:
            return context

        lines = context.splitlines()
        extracted = []
        capture = False

        for raw_line in lines:
            line = raw_line.strip()
            if line.startswith("#") and any(keyword in line for keyword in section_keywords):
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
        if not text or OpenCC is None:
            return text

        try:
            return OpenCC("s2t").convert(text)
        except Exception:
            return text

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

    def generate_answer(self, query: str, context: str):
        if not query:
            return "請先輸入問題。"
        if not context:
            return "目前找不到足夠的知識內容來回答這個問題。"

        focused_context = self.extract_relevant_section(context, query)
        chain = self.main_prompt | self.llm
        return self._to_traditional(
            self._safe_invoke(
                chain,
                {"context": focused_context, "question": query},
                "回答生成失敗，請稍後再試。",
            )
        )

    def explain_point(self, target: str):
        if not target:
            return "目前沒有可延伸說明的重點。"

        chain = self.point_follow_prompt | self.llm
        return self._to_traditional(
            self._safe_invoke(
                chain,
                {"target": target},
                "延伸說明生成失敗，請稍後再試。",
            )
        )

    def handle_natural_followup(self, focus: str, question: str):
        if not focus or not question:
            return "目前缺少足夠的上下文來回答追問。"

        chain = self.natural_follow_prompt | self.llm
        answer = self._to_traditional(
            self._safe_invoke(
                chain,
                {"focus": focus, "question": question},
                "追問回答生成失敗，請稍後再試。",
            )
        )
        return self._filter_followup_examples(answer)
