# 使用者操作指南 / User Operation Guide

本文件採「繁體中文先、English second」的雙語格式，協助第一次打開此專案的使用者、教授或審查者快速理解如何操作系統、如何解讀輸出，以及哪些邊界不能被誤解。

This guide uses Traditional Chinese first and English second in each section. It is written for a first-time reader, professor, or reviewer who needs to operate the system and understand its safety boundaries.

## 1. 專案概覽 / Project Overview

**中文**
Sentinel Project 是防禦導向的 SOC 分流原型。它結合規則式偵測、確定性風險/決策、RAG 知識問答、核准相似案例、關係圖、AI Analyst Brief、Evidence Gap Analyzer、案例草稿與匯出面板。

**English**
Sentinel Project is a defensive SOC triage prototype combining rule-based detection, deterministic risk/decision handling, RAG knowledge Q&A, approved similar cases, relationship graphs, AI Analyst Brief, Evidence Gap Analyzer, case draft, and export panels.

## 2. 這個系統會做什麼 / What This System Does

**中文**
它可以分析 payload、示範日誌事件、回答防禦型知識問題、顯示相似案例、建立關係圖、產生 AI 分析摘要、列出證據缺口，並提供人工審查導向的案例草稿與 Markdown 匯出預覽。

**English**
It analyzes payloads, demonstrates log/incident scenarios, answers defensive knowledge questions, retrieves approved similar cases, renders relationship graphs, generates an AI Analyst Brief, lists evidence gaps, and provides human-review-oriented case draft/export views.

## 3. 這個系統不會做什麼 / What This System Does Not Do

**中文**
它不攻擊真實系統、不產生 exploit 或 PoC、不產生流量、不修改防火牆/WAF/EDR/帳號/雲端/SIEM/SOAR 狀態，也不把 RAG、LLM 或歷史案例當成最終判決。

**English**
It does not attack real systems, generate exploit or PoC steps, generate traffic, modify firewall/WAF/EDR/account/cloud/SIEM/SOAR state, or treat RAG, LLM output, or historical cases as final authority.

## 4. 安全邊界 / Safety Boundary

**中文**
Detector 是 rule-based；Risk Level / Decision 是 deterministic；`BLOCK` / `MONITOR` / `ALLOW` 是 simulated；RAG / LLM / AI Analyst Brief / Evidence Gap 只作為 advisory；不執行真實防護動作；不提供 exploit、PoC 或 traffic generation；所有處置都需要 human review。

**English**
The detector is rule-based; Risk Level and Decision are deterministic; `BLOCK` / `MONITOR` / `ALLOW` are simulated; RAG / LLM / AI Analyst Brief / Evidence Gap are advisory only; no real enforcement occurs; no exploit, PoC, or traffic generation is provided; human review is required.

## 5. 環境需求 / Requirements

**中文**
需要 Windows PowerShell、Python、專案 `venv`、Streamlit、pytest/ruff/mypy，以及已建立的 `chroma_db`（若要使用 Knowledge Q&A / RAG）。本次截圖使用 repo 內 `venv` 的 Streamlit 1.58.0。

**English**
You need Windows PowerShell, Python, the project `venv`, Streamlit, pytest/ruff/mypy, and `chroma_db` if you want Knowledge Q&A / RAG. Refreshed screenshots used Streamlit 1.58.0 from the repo `venv`.

## 6. 啟用虛擬環境 / Activate venv

**中文**
```powershell
cd C:\Users\jason\Desktop\sentinel_project
.\venv\Scripts\Activate.ps1
```
如果 `venv` 不存在，請參考 [v2.8_cache_cleanup_checklist.md](v2.8_cache_cleanup_checklist.md)。

**English**
```powershell
cd C:\Users\jason\Desktop\sentinel_project
.\venv\Scripts\Activate.ps1
```
If `venv` is missing, use [v2.8_cache_cleanup_checklist.md](v2.8_cache_cleanup_checklist.md).

## 7. 啟動 Streamlit SOC 控制台 / Start Streamlit SOC Console

**中文**
```powershell
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```
畫面會顯示 SOC 控制台、狀態列、語言選擇、分析模式、Demo Scenario Launcher、輸入框與工作區分頁。截圖：[01_console_home.png](screenshots/01_console_home.png)。

**English**
```powershell
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```
The console shows the status bar, language selector, analysis mode selector, Demo Scenario Launcher, input box, and workspace tabs. Screenshot: [01_console_home.png](screenshots/01_console_home.png).

## 8. 啟動 CLI 模式 / Start CLI Mode

**中文**
```powershell
python app.py
```
CLI 適合 payload 分析、日誌處理、Knowledge Q&A 與 follow-up。v2.8-C 後，RAG 會在第一次需要時才初始化。

**English**
```powershell
python app.py
```
CLI mode supports payload analysis, log handling, Knowledge Q&A, and follow-up. After v2.8-C, RAG initializes lazily when needed.

## 9. 建議示範流程 / Recommended Demo Flow

**中文**
1. 啟動 Streamlit。
2. 選擇 UI 語言；AI Analyst Brief、Evidence Gap 與 Knowledge Q&A 會依照語言設定輸出。
3. 載入 Command Injection demo。
4. 執行 Fast deterministic analysis 並展示 `HIGH / BLOCK`。
5. 開啟 AI Analyst Brief 與 Evidence Gap Analyzer。
6. 問一個 Knowledge Q&A 問題。
7. 點 Find Similar Cases。
8. 展示 Relationship Graph。
9. 展示 Case Draft / Export。
10. 可選：Full AI-assisted。
11. 可選：HTTP/2 Resource Exhaustion demo。

**English**
1. Start Streamlit.
2. Select UI language; AI Analyst Brief, Evidence Gap, and Knowledge Q&A follow that language.
3. Load Command Injection demo.
4. Run Fast deterministic analysis and show `HIGH / BLOCK`.
5. Show AI Analyst Brief and Evidence Gap Analyzer.
6. Ask a Knowledge Q&A question.
7. Click Find Similar Cases.
8. Show Relationship Graph.
9. Show Case Draft / Export.
10. Optional: Full AI-assisted.
11. Optional: HTTP/2 Resource Exhaustion demo.

## 10. 快速確定性模式 / Fast Deterministic Mode

**中文**
使用「命令注入示範」後點「執行輸入」。預期輸出：Command Injection、`CMD-001`、`HIGH`、`BLOCK`。不要假設系統真的封鎖流量或命令真的執行成功。截圖：[02_fast_command_injection_analysis.png](screenshots/02_fast_command_injection_analysis.png)。

**English**
Load the Command Injection demo and click Run Input. Expected output: Command Injection, `CMD-001`, `HIGH`, `BLOCK`. Do not assume real blocking occurred or command execution succeeded. Screenshot: [02_fast_command_injection_analysis.png](screenshots/02_fast_command_injection_analysis.png).

## 11. 完整 AI 輔助模式 / Full AI-Assisted Mode

**中文**
切換「完整 AI 輔助」後再執行輸入。第一次可能較慢，因為 RAG/LLM 相關依賴會在需要時初始化。不要假設 AI 會覆蓋 Risk Level 或 Decision。截圖：[10_full_ai_assisted_optional.png](screenshots/10_full_ai_assisted_optional.png)。

**English**
Switch to Full AI-assisted and run input. First use may be slower because RAG/LLM dependencies initialize when needed. Do not assume AI can override Risk Level or Decision. Screenshot: [10_full_ai_assisted_optional.png](screenshots/10_full_ai_assisted_optional.png).

## 12. 示範情境啟動器 / Demo Scenario Launcher

**中文**
啟動器提供 Command Injection、SQL Injection、HTTP/2 Resource Exhaustion Suspicion、Authentication Incident 等卡片。HTTP/2 卡片只顯示短 preview，避免首頁過長；點「載入情境」會把完整 synthetic incident summary 放進文字框，不會自動執行，且完整 input 仍保留 no traffic generated、no real enforcement、human review required 等安全行。

**English**
The launcher provides Command Injection, SQL Injection, HTTP/2 Resource Exhaustion Suspicion, and Authentication Incident cards. The HTTP/2 card shows a short preview so the homepage stays compact. Load Scenario fills the input box with the full synthetic incident summary; it does not run analysis automatically, and the full input still keeps the no-traffic, no-enforcement, human-review safety lines.

## 13. AI 分析摘要 / AI Analyst Brief

**中文**
完成分析後開啟「AI 分析助理」。你會看到 deterministic advisory、`llm_status: not_used`、發生了什麼、為什麼重要、確定性判定、證據缺口與下一步。輸出語言會跟隨 UI 語言選擇：zh-TW 為繁體中文優先，en 為英文，bilingual 為精簡中英雙語。不要假設它是最終判決。截圖：[03_ai_analyst_brief.png](screenshots/03_ai_analyst_brief.png)。

**English**
After analysis, open AI Analyst. You see deterministic advisory context, `llm_status: not_used`, what happened, why it matters, deterministic verdict, evidence gaps, and next steps. Output follows the UI language selection: zh-TW is Traditional Chinese first, en is English, and bilingual is compact Chinese/English. Do not treat it as final verdict. Screenshot: [03_ai_analyst_brief.png](screenshots/03_ai_analyst_brief.png).

## 14. 證據缺口分析器 / Evidence Gap Analyzer

**中文**
Evidence Gap Analyzer 顯示還需要哪些證據，例如程序執行紀錄、伺服器 telemetry、檔案變更、外連 DNS/HTTP 等。輸出語言會跟隨 UI 語言選擇。它幫助安排複核，不宣稱入侵已確認。截圖：[04_evidence_gap_analyzer.png](screenshots/04_evidence_gap_analyzer.png)。

**English**
Evidence Gap Analyzer lists missing evidence such as process logs, server telemetry, file changes, and outbound DNS/HTTP evidence. Output follows the UI language selection. It helps plan review work and does not claim confirmed compromise. Screenshot: [04_evidence_gap_analyzer.png](screenshots/04_evidence_gap_analyzer.png).

## 15. 知識問答 / Knowledge Q&A

**中文**
在 AI Analyst 分頁提問，例如「什麼是 Command Injection？」或 HTTP/2/CVE 防禦問題。預期輸出是 RAG/知識庫說明與 advisory 邊界，並依照目前 UI 語言輸出。切換語言本身不會初始化 RAG、Chroma、embedding、Torch 或 ChatOllama；RAG 只會在 Knowledge Q&A 實際執行時初始化。不要把知識回答當成目前事件證據。截圖：[05_knowledge_qa_rag.png](screenshots/05_knowledge_qa_rag.png)。

**English**
Ask questions in the AI Analyst tab, such as “What is Command Injection?” or defensive HTTP/2/CVE questions. Expected output is a RAG/knowledge answer with advisory boundary and the selected UI language. Changing language does not initialize RAG, Chroma, embeddings, Torch, or ChatOllama by itself; RAG initializes only when Knowledge Q&A is actually used. Do not treat it as current-event evidence. Screenshot: [05_knowledge_qa_rag.png](screenshots/05_knowledge_qa_rag.png).

## 16. 相似案例 / Similar Cases

**中文**
完成分析後點「尋找相似案例」。Command Injection 預期回傳 `CASE-SEED-001`。相似案例只供參考，不覆蓋目前 Risk Level / Decision，也不證明目前事件已成功執行。截圖：[06_similar_cases.png](screenshots/06_similar_cases.png)。

**English**
After analysis, click Find Similar Cases. Command Injection should return `CASE-SEED-001`. Similar cases are references only; they do not override Risk Level / Decision or prove successful execution. Screenshot: [06_similar_cases.png](screenshots/06_similar_cases.png).

## 17. 關係圖 / Relationship Graph

**中文**
在案例情報中查看 Relationship Graph。圖會顯示目前事件、風險、決策、共享攻擊類型、規則 ID、證據類型與核准案例的關係。它是分析脈絡，不是判決引擎。截圖：[07_relationship_graph.png](screenshots/07_relationship_graph.png)。

**English**
Open Case Intelligence to view the Relationship Graph. It shows the current event, risk, decision, shared attack type, rule ID, evidence type, and approved case relationship. It is context, not a decision engine. Screenshot: [07_relationship_graph.png](screenshots/07_relationship_graph.png).

## 18. 案例草稿與匯出 / Case Draft and Export

**中文**
草稿/匯出分頁提供 Case Draft、approval-gated 操作與 Markdown Export preview。匯出預覽在 UI 內產生，不代表自動寫入正式報告或知識庫。截圖：[08_case_draft_export.png](screenshots/08_case_draft_export.png)。

**English**
The Draft / Export tab provides Case Draft controls, approval-gated actions, and a Markdown Export preview. The export preview is in-memory and does not auto-write a final report or knowledge-base entry. Screenshot: [08_case_draft_export.png](screenshots/08_case_draft_export.png).

## 19. 安全 HTTP/2 資源耗盡示範 / Safe HTTP/2 Resource Exhaustion Demo

**中文**
載入「HTTP/2 資源耗盡疑似事件」。它是 synthetic incident summary，包含 stream/reset/flow-control、proxy/CDN/app server metrics、CPU/memory/resource indicators，並明示 no traffic generated、no vulnerability reproduction material、no real enforcement、human review required。截圖：[09_http2_resource_exhaustion_demo.png](screenshots/09_http2_resource_exhaustion_demo.png)。

**English**
Load “HTTP/2 Resource Exhaustion Suspicion.” It is a synthetic incident summary with stream/reset/flow-control, proxy/CDN/app server metrics, and CPU/memory/resource indicators. It states no traffic generated, no vulnerability reproduction material, no real enforcement, and human review required. Screenshot: [09_http2_resource_exhaustion_demo.png](screenshots/09_http2_resource_exhaustion_demo.png).

## 20. 如何解讀 HIGH / BLOCK / MONITOR / ALLOW / How to Interpret HIGH / BLOCK / MONITOR / ALLOW

**中文**
`HIGH` 是確定性政策的風險標籤；`BLOCK` / `MONITOR` / `ALLOW` 是模擬決策，不會真的修改防火牆、WAF、EDR、帳號、雲端或監控系統。

**English**
`HIGH` is a deterministic risk label. `BLOCK` / `MONITOR` / `ALLOW` are simulated decisions and do not modify firewall, WAF, EDR, account, cloud, or monitoring systems.

## 21. 疑難排解 / Troubleshooting

**中文**
如果 `python -m streamlit` 找不到套件，請啟用 `venv` 或使用 `.\venv\Scripts\python.exe -m streamlit run ui/streamlit_app.py --server.fileWatcherType none`。如果 Knowledge Q&A 不可用，確認 `chroma_db` 存在；必要時執行 `python ingest_knowledge.py`。如果 Full AI-assisted 很慢，先展示 Fast deterministic。

**English**
If `python -m streamlit` cannot find Streamlit, activate `venv` or run `.\venv\Scripts\python.exe -m streamlit run ui/streamlit_app.py --server.fileWatcherType none`. If Knowledge Q&A is unavailable, confirm `chroma_db`; rebuild with `python ingest_knowledge.py` if planned. If Full AI-assisted is slow, use Fast deterministic.

## 22. 驗證與測試報告連結 / Validation and Test Report Links

**中文 / English**

- [TEST_REPORT.md](TEST_REPORT.md)
- [CODE_REVIEW_AUDIT.md](CODE_REVIEW_AUDIT.md)
- [screenshots/README.md](screenshots/README.md)
- [v2.7_release_gate.md](v2.7_release_gate.md)
- [v2.7_manual_smoke_report.md](v2.7_manual_smoke_report.md)
- [v2.8_startup_import_audit.md](v2.8_startup_import_audit.md)
- [v2.8_cache_cleanup_checklist.md](v2.8_cache_cleanup_checklist.md)

