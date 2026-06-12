# Sentinel Project — AI 輔助藍隊安全分流系統

## 專案簡介

Sentinel Project 是一個防禦導向的 AI-assisted blue-team security triage prototype。它以 Streamlit Analyst Console 作為主要展示介面，讓使用者可以載入安全示範情境、執行 Rule-Based Detector、查看 deterministic Risk Level / Decision，並透過 AI Analyst Brief、Evidence Gap Analyzer、Knowledge Q&A / RAG、Approved Similar Cases 與 Relationship Graph 取得分析師參考資訊。

這個專題的重點不是讓 AI 直接判斷攻擊，而是示範一條可解釋、可控制、可展示給教授與專題評審理解的藍隊分析流程。

## 為什麼做這個專題

許多 AI 資安展示容易讓人誤以為 LLM 可以直接決定「是不是攻擊」或「系統要不要封鎖」。在真實安全場景中，這很危險，因為 AI 可能產生 hallucination、過度推論，或把缺乏證據的事件說成已確認入侵。

Sentinel Project 採用 deterministic first, AI advisory second 的設計。偵測、風險等級與決策由可測試的 deterministic logic 負責；AI 與 RAG 則只負責整理脈絡、提出證據缺口、回答防禦性問題，以及協助分析師閱讀。

## 系統流程

~~~text
使用者輸入 / demo scenario
  -> Rule-Based Detector
  -> 攻擊或事件分類
  -> deterministic Risk Level
  -> simulated Decision
  -> advisory context
     -> AI Analyst Brief
     -> Evidence Gap Analyzer
     -> Knowledge Q&A / RAG
     -> Approved Similar Cases
     -> Relationship Graph
  -> Human-reviewed Case Draft / Markdown Export
~~~

## 核心設計理念

- 偵測權威是 Rule-Based Detector，不是 AI。
- Risk Level / Decision 是 deterministic，不由 LLM 決定。
- BLOCK / MONITOR / ALLOW 是 simulated decisions，只在專題內展示分流結果。
- RAG / LLM / AI Analyst Brief / Evidence Gap Analyzer / Similar Cases / Relationship Graph 只提供 advisory context。
- 歷史相似案例不能證明目前事件已被利用，也不能覆蓋目前事件的 Risk Level 或 Decision。
- 任何真實營運動作都需要 Human review。

## 為什麼偵測權威保留在 Rule-Based Detector

Rule-Based Detector 的優點是可重現、可測試、可解釋。當系統判定 Command Injection、Possible Account Compromise 或 HTTP/2 Resource Exhaustion Suspicion 時，評審可以追到規則、輸入特徵與 deterministic policy。這比讓 LLM 自行判斷更適合安全展示與教學場景。

AI 可以協助說明，但不能成為最終裁決者。

## 為什麼 AI 只提供 advisory context

AI Analyst Brief 可以把事件整理成分析師容易閱讀的摘要；Evidence Gap Analyzer 可以列出缺少哪些證據；Knowledge Q&A / RAG 可以回答防禦性知識問題；Similar Cases 與 Relationship Graph 可以提供比較與脈絡。這些都能提升展示價值，但它們不能修改偵測結果、風險等級、決策、知識庫、圖譜事實或任何真實系統狀態。

## Streamlit UI 展示重點

主要展示介面是 Streamlit Analyst Console：

~~~powershell
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
~~~

建議展示流程：

1. 選擇 Fast deterministic mode。
2. 載入 Command Injection Demo。
3. 點擊 Run input。
4. 查看 deterministic detection、Risk Level、simulated Decision。
5. 查看 AI Analyst Brief 與 Evidence Gap Analyzer。
6. 點擊 Find Similar Cases，查看 Approved Similar Cases 與 Relationship Graph。
7. 查看 Case Draft / Markdown Export。
8. 載入 HTTP/2 Resource Exhaustion Suspicion，確認它是 safe synthetic demo。

## Demo 功能亮點

- Fast deterministic mode：快速展示 deterministic detection and policy。
- Full AI-assisted mode：可選的 AI/RAG 輔助說明路徑。
- Lazy RAG startup：避免啟動時就載入 heavy RAG / embedding dependency。
- Language-aware output：UI 與 advisory panels 依語言設定呈現。
- AI Analyst Brief：摘要發生了什麼、為什麼重要、下一步建議與 unsafe assumptions。
- Evidence Gap Analyzer：分離 confirmed facts、missing evidence、recommended checks。
- Knowledge Q&A / RAG：回答防禦導向問題，例如 HTTP/2 DoS、CVE、Resource Exhaustion。
- Approved Similar Cases：讀取 approved seed cases，提供相似案例與差異比較。
- Relationship Graph：以視覺方式呈現事件、規則、風險、決策與案例脈絡。
- Case Draft / Markdown Export：產生需要 Human review 的報告素材。
- HTTP/2 Resource Exhaustion safe synthetic demo：只使用 synthetic incident summary，不產生攻擊流量。

## 安全邊界

- 偵測是 Rule-Based Detector，不是 AI 判斷。
- Risk Level / Decision 是 deterministic。
- BLOCK / MONITOR / ALLOW 是 simulated decisions only。
- RAG / LLM / AI Analyst Brief / Evidence Gap Analyzer / Similar Cases / Relationship Graph 只提供 advisory context。
- 不做真實 firewall / WAF / EDR / account / cloud / SIEM / SOAR 動作。
- 不提供 exploit code、PoC generation、traffic generation 或 offensive automation。
- 需要 Human review。

## 快速開始

~~~powershell
git clone https://github.com/jasonwang1211/security-ai-agent.git
cd security-ai-agent
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
~~~

## 文件導覽

- [English README](../../README.md)
- [English Project Report](../../REPORT.md)
- [Documentation Hub](../README.md)
- [User Operation Guide](../USER_OPERATION_GUIDE.md)
- [UI Walkthrough](../UI_WALKTHROUGH.md)
- [Screenshot Gallery](../screenshots/README.md)
- [Test Report](../TEST_REPORT.md)
- [Code Review Audit](../CODE_REVIEW_AUDIT.md)

繁中 UI 截圖保留於 docs/screenshots/zh-TW/；英文 UI 截圖保留於 docs/screenshots/en/。

## 測試與驗證

最近一次記錄的 v2.8 release-gate 驗證摘要：

- pytest：1168 passed
- ruff：passed
- mypy：passed
- gitleaks：passed
- screenshot language refresh：completed

這些驗證代表 demo behavior 與 safety boundary 有被測試，不代表 production IDS/IPS effectiveness。

## 限制與未來工作

本專案不是 production IDS/IPS，不是 red-team tool，不提供 exploit generator，也不是 autonomous response system。未來可以持續補強更多 defensive synthetic scenarios、analyst timeline / event replay、read-only graph 與 approved-case memory，以及 report export / release packaging。
