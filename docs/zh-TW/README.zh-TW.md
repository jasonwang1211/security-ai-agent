# Sentinel Project — AI 輔助藍隊安全分流系統

## 一句話說明

Sentinel Project 是一個防禦導向的 AI-assisted blue-team security triage prototype。它以 Streamlit Analyst Console 串接 Rule-Based Detector、deterministic Risk Level / Decision、simulated decisions，以及 AI/RAG advisory context，重點是把偵測權威與 AI 輔助分析清楚分開。

## v3.0 中文展示入口

給教授審查與口頭報告使用的中文展示素材：

- 中文展示稿 / demo 流程 / 常見問題 / 失敗備援：[v3.0 中文展示稿](v3.0_presentation_notes.zh-TW.md)
- 繁中關鍵截圖（overview + 可讀 detail crop，`zh-TW/20`–`31`）：[截圖集](../screenshots/README.md)
- 對照英文版：[v3.0 Demo Script](../v3.0_demo_script.md)、[UI Walkthrough](../UI_WALKTHROUGH.md)

本次 demo 想讓審查者記住的重點：

- 規則式偵測（Rule-Based Detector）是偵測權威，不是 AI。
- Risk Level / Decision 是 deterministic，不由 LLM 決定。
- BLOCK / MONITOR / ALLOW 是模擬決策。
- Evidence-Grounded AI Brief 只供參考（advisory-only），不能覆蓋官方判定。
- 相似案例（Similar Cases）不是目前已被入侵的證明。
- 關聯圖（Relationship Graph）不是偵測來源。
- 不執行真實阻擋 / WAF / EDR / SIEM / SOAR 等動作。
- 公開展示與截圖路徑仍以 deterministic fallback 為主；v3.1 的 provider contracts 屬於後端基礎建設，預設停用，不需要 live LLM / API key 才能通過 CI。若要宣稱 live provider 可用，需另外執行 manual smoke testing。

> 已知限制：v2.9 的 Evidence-Grounded AI Brief 面板固定段落標籤目前仍是英文，
> deterministic 路徑與 UI 外框已是繁體中文。中文截圖會看到中文 UI 外框 + 英文／中英混合的
> brief 面板，請如實說明、不要宣稱已完全中文化（詳見展示稿第 9 節）。

## 專題動機

這個 repo 同時是資安專題成果與個人 security engineering portfolio project。它不是要讓 AI 自動判斷攻擊，也不是要做真實 IDS/IPS；核心問題是如何在資安分流中使用 AI 輔助分析，同時避免 AI 直接成為最終裁決者。

許多 AI 資安展示會讓人誤以為 LLM 可以直接決定「這是不是攻擊」或「要不要封鎖」。在真實安全場景中，這很危險，因為 AI 可能產生 hallucination、過度推論，或把缺乏證據的事件說成已確認入侵。

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

## 為什麼 Rule-Based Detector 保持權威

Rule-Based Detector 的優點是可重現、可測試、可解釋。reviewer 可以從輸入、規則 ID、matched evidence、Risk Level 與 Decision 一路追溯。這比讓 LLM 自行判斷更適合安全展示、專題審查與工程面試討論。

AI 可以協助說明，但不能成為最終裁決者。

## 為什麼 AI 只提供 advisory context

AI Analyst Brief 可以把事件整理成分析師容易閱讀的摘要；Evidence Gap Analyzer 可以列出缺少哪些證據；Knowledge Q&A / RAG 可以回答防禦性知識問題；Similar Cases 與 Relationship Graph 可以提供比較與脈絡。

這些功能讓分析流程更容易閱讀與複核，但不能修改偵測結果、風險等級、決策、知識庫、圖譜事實或任何真實系統狀態。

## Streamlit UI 操作重點

主要操作介面是 Streamlit Analyst Console：

~~~powershell
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
~~~

建議展示流程：

1. 確認 UI language。
2. 選擇 Fast deterministic mode。
3. 載入 Command Injection Demo。
4. 點擊 Run input。
5. 查看 deterministic detection、Risk Level、simulated Decision。
6. 查看 AI Analyst Brief 與 Evidence Gap Analyzer。
7. 點擊 Find Similar Cases，查看 Approved Similar Cases 與 Relationship Graph。
8. 查看 Case Draft / Markdown Export。
9. 載入 HTTP/2 Resource Exhaustion Suspicion，確認它是 safe synthetic demo。

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
- 相似案例不是目前事件已被入侵或已成功執行的證明。
- 關聯圖不是偵測來源。
- 公開展示與截圖路徑仍以 deterministic fallback 為主；v3.1 的 provider contracts 屬於後端基礎建設，預設停用，不需要 live LLM / API key 才能通過 CI。若要宣稱 live provider 可用，需另外執行 manual smoke testing。
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

- [v3.0 中文展示稿](v3.0_presentation_notes.zh-TW.md)
- [繁中專題報告](PROJECT_REPORT.zh-TW.md)
- [English README](../../README.md)
- [English Project Report](../../REPORT.md)
- [Documentation Hub](../README.md)
- [User Operation Guide](../USER_OPERATION_GUIDE.md)
- [UI Walkthrough](../UI_WALKTHROUGH.md)
- [Screenshot Gallery](../screenshots/README.md)
- [Test Report](../TEST_REPORT.md)
- [Code Review Audit](../CODE_REVIEW_AUDIT.md)

繁中 UI 截圖保留於 docs/screenshots/zh-TW/；英文 UI 截圖保留於 docs/screenshots/en/。

## Test Coverage / Validation Matrix

Latest v3.1 branch validation rerun for this documentation patch:

- pytest: `1268 passed`
- ruff: passed
- mypy: no issues found in 180 source files
- git diff --check: passed

Validation focuses on deterministic authority, advisory AI safety, provider fallback behavior, and UI/reporting smoke paths. The tests support demo correctness and safety-boundary regression control; they do not claim production IDS/IPS effectiveness.

| Area | What is verified | Why it matters |
|---|---|---|
| Deterministic detection / policy | Rule-Based Detector, deterministic Risk Level / Decision, simulated BLOCK / MONITOR / ALLOW behavior. | Official verdict stays reproducible; not a production IDS/IPS accuracy claim. |
| Evidence bundle / Evidence-Grounded AI Brief | Official verdict, rule IDs, evidence IDs, citation IDs, missing evidence, and unsafe assumptions are preserved. | AI/report output remains advisory and does not become the source of truth. |
| AI guardrails | Verdict override, Similar Cases-as-proof, Graph-as-detection-source, enforcement wording, exploit / PoC / traffic generation / load testing. | Keeps AI/RAG/Similar Cases/Graph advisory-only. |
| v3.1 Full AI-assisted foundation | Prompt contract, disabled default provider, fake test injection, optional local/openai-compatible contracts, provider failures and exceptions. | CI does not require live LLM, API key, Ollama, Chroma, embeddings, or network access. |
| Event-aware Q&A | Current deterministic context, rule/evidence IDs, evidence gaps, optional RAG, Similar Cases, Graph context, zh-TW and English wrappers. | Unsafe questions are refused before provider calls; official verdict is unchanged. |
| Similar Cases / Graph | Approved cases and graph context are read-only advisory context. | Similar Cases are not proof; Graph is not a detection source. |
| RAG / Knowledge Q&A | Optional advisory retrieval, controlled no-answer/unavailable behavior, lazy startup expectations. | Retrieval context does not modify Risk Level / Decision. |
| UI / reporting smoke | Streamlit helper paths, panels, export view, Run -> Find Similar Cases -> case-001 / graph-001. | Supports demo workflow confidence; not production deployment proof. |
| Docs consistency | Validation wording, screenshot references, release notes, safety-boundary language. | Keeps public review material aligned; does not replace manual review. |


## 限制與未來工作

本專案不是 production IDS/IPS，不是 red-team tool，不提供 exploit generator，也不是 autonomous response system。未來可以持續補強更多 defensive synthetic scenarios、analyst timeline / event replay、read-only graph 與 approved-case memory，以及 report export / release packaging。
