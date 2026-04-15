import os
import re
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

CHROMA_PATH = "./chroma_db"
MODEL_NAME = "qwen2.5:7b"
TOP_K = 5

SECURITY_TOPICS = [
    "sql", "sql injection", "注入",
    "xss", "跨站",
    "csrf",
    "零日", "zero-day", "zero day",
    "command injection", "命令注入",
    "檔案上傳", "上傳漏洞",
    "path traversal", "路徑遍歷",
    "session", "認證", "cookie",
    "漏洞", "攻擊", "防禦", "資安"
]

print("🧠 載入模型中...")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

llm = ChatOllama(
    model=MODEL_NAME,
    temperature=0
)

if not os.path.exists(CHROMA_PATH):
    raise Exception("❌ 找不到 Chroma DB，請先執行 ingest_knowledge.py")

vectorstore = Chroma(
    persist_directory=CHROMA_PATH,
    embedding_function=embeddings
)

main_prompt = ChatPromptTemplate.from_template("""
你是一個資安助理。

你的任務是根據「參考資料」回答問題。
你只能使用參考資料中的內容，不可新增、不可靠腦補。

回答時請優先找出與問題最直接相關的段落：
- 如果問題問「定義、是什麼」，優先使用「定義」
- 如果問題問「特徵、跡象」，優先使用「常見特徵」或「偵測方式」
- 如果問題問「防禦、怎麼防」，優先使用「防禦方式」
- 如果問題問「危害、影響」，優先使用「常見危害」
- 如果問題問「怎麼處理」，優先使用「事件處理建議」

如果參考資料不足，直接回答：
知識庫沒有相關資料

回答規則：
1. 一律使用繁體中文
2. 先寫「結論：」
3. 再寫「重點：」
4. 最多 3 點
5. 每點 1 句
6. 優先回答問題對應欄位，不要只摘要整份文件
7. 不可加入參考資料中沒有的內容

參考資料：
{context}

問題：
{question}
""")

point_follow_prompt = ChatPromptTemplate.from_template("""
你是一個資安助理。

請解釋下面這一點的意思，只能根據這一點本身說明，不可補充其他主題，不可腦補。

內容：
{target}

回答規則：
1. 一律使用繁體中文
2. 先寫「結論：」
3. 再補充 2 點內說明
4. 用白話說明
5. 不可加入內容以外的新知識
""")

natural_follow_prompt = ChatPromptTemplate.from_template("""
你是一個資安助理。

請只根據以下焦點內容，延續回答使用者追問。
不可擴展其他主題，不可腦補。

焦點內容：
{focus}

使用者追問：
{question}

回答規則：
1. 一律使用繁體中文
2. 先寫「結論：」
3. 最多補充 2 點
4. 用白話說明
5. 只能圍繞焦點內容回答
6. 不可加入焦點內容以外的新知識
""")

last_question = ""
last_answer = ""
last_points = []
last_focus = ""

def is_security(query: str) -> bool:
    q = query.lower()
    return any(k in q for k in SECURITY_TOPICS)

def is_point_followup(query: str) -> bool:
    return bool(re.search(r"第\s*\d+\s*點", query))

def extract_relevant_section(context: str, query: str) -> str:
    q = query.lower()

    section_keywords = []

    if "特徵" in query or "跡象" in query:
        section_keywords = ["常見特徵", "偵測方式"]
    elif "防禦" in query or "怎麼防" in query:
        section_keywords = ["防禦方式"]
    elif "危害" in query or "影響" in query:
        section_keywords = ["常見危害"]
    elif "定義" in query or "是什麼" in query:
        section_keywords = ["定義"]
    elif "處理" in query or "怎麼辦" in query:
        section_keywords = ["事件處理建議"]

    if not section_keywords:
        return context

    lines = context.splitlines()
    extracted = []

    capture = False
    for line in lines:
        line = line.strip()

        if any(line.startswith(k + "：") or line.startswith(k + ":") for k in section_keywords):
            capture = True
            extracted.append(line)
            continue

        # 遇到下一個欄位就停止
        if capture and re.match(r"^(主題|定義|別名|常見特徵|常見危害|防禦方式|偵測方式|事件處理建議)[：:]", line):
            break

        if capture:
            extracted.append(line)

    return "\n".join(extracted).strip() if extracted else context

def is_natural_followup(query: str) -> bool:
    patterns = [
        r"這是什麼意思",
        r"什麼意思",
        r"說清楚",
        r"解釋清楚",
        r"詳細一點",
        r"再詳細",
        r"再說明",
        r"舉例",
        r"這個呢",
        r"那這個呢",
        r"為什麼",
        r"然後呢",
    ]
    return any(re.search(p, query) for p in patterns)

def extract_index(query: str):
    m = re.search(r"第\s*(\d+)\s*點", query)
    return int(m.group(1)) if m else None

def extract_points(text: str):
    points = []
    lines = text.splitlines()

    for raw_line in lines:
        line = raw_line.strip().replace("\u3000", " ")

        # 抓 1. xxx / 1) xxx / 1、xxx / 1：xxx
        m = re.match(r"^\s*(\d+)\s*[.)、：:]\s*(.+?)\s*$", line)
        if m:
            points.append(m.group(2).strip())
            continue

        # 抓 - xxx / • xxx
        m = re.match(r"^\s*[-•]\s*(.+?)\s*$", line)
        if m:
            points.append(m.group(1).strip())
            continue

    return points

def expand_query(query: str) -> str:
    q = query

    if "命令注入" in q:
        q += " Command Injection OS Command Injection Shell Injection 系統指令"

    if "sql" in q.lower() or "sql injection" in q.lower() or "注入" in q:
        q += " SQL Injection 資料庫 查詢"

    if "xss" in q.lower() or "跨站" in q:
        q += " XSS script javascript"

    if "csrf" in q.lower():
        q += " CSRF token SameSite Referer Origin"

    if "零日" in q or "zero-day" in q.lower() or "zero day" in q.lower():
        q += " Zero-Day zero day 零日攻擊 漏洞 未修補 exploit 資安漏洞"

    return q

def load_full_source_text(source_path: str) -> str:
    if not source_path:
        return ""

    try:
        with open(source_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(source_path, "r", encoding="utf-8-sig") as f:
                return f.read()
        except UnicodeDecodeError:
            with open(source_path, "r", encoding="cp950") as f:
                return f.read()
    except Exception:
        return ""

def retrieve_context(query: str):
    expanded = expand_query(query)
    results = vectorstore.similarity_search_with_score(expanded, k=TOP_K)
    
    if not results:
        return "", False

    best_distance = results[0][1]

    if best_distance > 1.2:
        return "", False

    # 直接讀第一名來源的原始檔全文
    top_source = results[0][0].metadata.get("source")
    full_text = load_full_source_text(top_source)

    if full_text.strip():
        return full_text, True

    # 如果原始檔讀不到，再退回同來源 chunks
    same_source_docs = []
    for doc, score in results:
        if doc.metadata.get("source") == top_source:
            same_source_docs.append(doc.page_content)

    context = "\n\n".join(same_source_docs)
    return context, True

print("\n🛡️ Security AI 啟動成功！")

while True:
    query = input("\n👤 你: ").strip()

    if query.lower() in ["exit", "quit", "離開"]:
        print("👋 再見！")
        break

    if not query:
        continue

    try:
        print("🔍 檢查中...")

        # 第 N 點追問
        if is_point_followup(query):
            idx = extract_index(query)

            if not last_points:
                print("\n🤖 AI: 目前沒有可追問的上一輪重點\n")
                continue

            if idx is None or idx < 1 or idx > len(last_points):
                print("\n🤖 AI: 找不到對應的重點項目\n")
                continue

            target = last_points[idx - 1]
            last_focus = target

            chain = point_follow_prompt | llm
            res = chain.invoke({
                "target": target
            })

            answer = res.content.strip()
            print(f"\n🤖 AI: {answer}\n")

            last_question = query
            last_answer = answer
            continue

        # 自然追問
        if is_natural_followup(query):
            if not last_focus:
                print("\n🤖 AI: 目前沒有可延續的焦點內容\n")
                continue

            chain = natural_follow_prompt | llm
            res = chain.invoke({
                "focus": last_focus,
                "question": query
            })

            answer = res.content.strip()
            print(f"\n🤖 AI: {answer}\n")

            last_question = query
            last_answer = answer
            continue

        # 非資安主題
        if not is_security(query):
            print("\n🤖 AI: 知識庫沒有相關資料\n")
            continue

        # 一般 RAG 問題
        context, ok = retrieve_context(query)

        if not ok:
            print("\n🤖 AI: 知識庫沒有相關資料\n")
            continue

        focused_context = extract_relevant_section(context, query)
        
        chain = main_prompt | llm
        res = chain.invoke({
            "context": focused_context,
            "question": query
        })

        answer = res.content.strip()
        print(f"\n🤖 AI: {answer}\n")
 
        last_question = query
        last_answer = answer
        last_points = extract_points(answer)
        last_focus = ""

    except Exception as e:
        print(f"\n❌ 錯誤: {e}\n")