# Sentinel Project 專題報告

## 摘要

Sentinel Project 是一個 AI-assisted blue-team security triage prototype，目標是展示如何在不破壞安全邊界的情況下，把 AI 與 RAG 放進資安分析流程。系統以 Rule-Based Detector 與 deterministic policy 作為偵測與分流權威，再透過 AI Analyst Brief、Evidence Gap Analyzer、Knowledge Q&A / RAG、Approved Similar Cases 與 Relationship Graph 提供分析師參考。

本專題不讓 AI 直接判斷攻擊是否成立，也不讓 AI 決定 Risk Level 或 Decision。BLOCK / MONITOR / ALLOW 皆為 simulated decisions，不代表真實封鎖、監控部署或 remediation。

## 專題背景與動機

在資安事件分流中，分析師需要快速判斷事件類型、風險程度、缺少哪些證據，以及下一步該查什麼。AI 可以協助整理資訊，但如果把 AI 當成最終裁決者，就可能產生錯誤信心或不安全的自動化決策。

本專題希望示範一種比較安全的架構：deterministic detection and policy 保留權威，AI/RAG 只提供 advisory context。這樣既能展示 AI 對分析師的價值，也能避免 AI 變成不可控的封鎖或攻擊工具。

## 問題定義

本系統要解決的不是「讓 AI 自動防禦所有攻擊」，而是「如何把 AI 放進藍隊分析流程，同時保留可測試、可解釋、可控的安全邊界」。

因此系統必須回答：

- 如何讓偵測結果可重現？
- 如何讓 Risk Level / Decision 不受 LLM hallucination 影響？
- 如何讓 AI 提供有用的分析摘要，但不覆蓋 deterministic verdict？
- 如何用安全 synthetic scenarios 展示 DoS / Resource Exhaustion 類型事件，而不產生攻擊流量？

## 需求與範圍

本專題包含：

- 支援 Command Injection、authentication incident、HTTP/2 Resource Exhaustion Suspicion 等 demo 情境。
- 使用 deterministic logic 產生 Risk Level 與 simulated Decision。
- 提供 Streamlit Analyst Console 作為主要展示介面。
- 提供 AI Analyst Brief、Evidence Gap Analyzer、Knowledge Q&A / RAG 等 advisory panels。
- 提供 Approved Similar Cases 與 Relationship Graph 作為 read-only analyst context。
- 提供 Case Draft / Markdown Export 作為 Human review 報告素材。

不包含：

- production IDS/IPS；
- 真實 firewall / WAF / EDR / account / cloud / SIEM / SOAR 操作；
- exploit code、PoC generation、traffic generation；
- AI-controlled final verdict；
- autonomous response。

## 系統架構

~~~text
使用者輸入 / demo scenario
  -> Streamlit Analyst Console 或 CLI
  -> Rule-Based Detector
  -> 攻擊或事件分類
  -> deterministic Risk Level
  -> simulated Decision
  -> advisory layers
     -> AI Analyst Brief
     -> Evidence Gap Analyzer
     -> Knowledge Q&A / RAG
     -> Approved Similar Cases
     -> Relationship Graph
  -> Human-reviewed Case Draft / Markdown Export
~~~

系統刻意將 authority path 設計得很小：Rule-Based Detector、Risk Level、Decision。其他 AI/RAG/graph/case-memory 功能都只能解釋、比較、整理或輔助報告。

## 模組設計

| 模組 | 責任 | 安全邊界 |
|---|---|---|
| Rule-Based Detector | 判斷支援的 payload / incident pattern。 | 偵測權威。 |
| Risk / Decision policy | 產生 deterministic Risk Level 與 simulated Decision。 | 最終 demo verdict path。 |
| Controller / orchestrator | 處理 deterministic routing 與 explicit commands。 | 不使用 LLM routing 作為權威。 |
| AI advisory | 產生 AI Analyst Brief 與 Evidence Gap。 | advisory only。 |
| Knowledge Q&A / RAG | 讀取 approved defensive knowledge context。 | advisory only，不提供 exploit。 |
| Approved Similar Cases | 讀取 approved seed cases 並比較相似案例。 | 歷史案例不能證明目前事件。 |
| Relationship Graph | 顯示 read-only relationship context。 | explanatory only。 |
| Case Draft / Export | 產生 Human review 報告素材。 | 不能當成 live remediation proof。 |

## 為什麼 Rule-Based Detector 保持權威

Rule-Based Detector 的結果可測試、可重現、可追蹤。對教授或評審來說，可以從輸入、規則 ID、matched evidence、Risk Level 與 Decision 一路追溯，不需要相信 LLM 的自然語言推論。

如果把 LLM 放在偵測權威位置，系統可能會因 hallucination、prompt sensitivity 或缺乏證據而產生不穩定結果。因此本專題把 AI 放在 advisory layer，而不是 detection authority。

## 為什麼 AI 只提供輔助分析

AI Analyst Brief、Evidence Gap Analyzer、Knowledge Q&A / RAG、Similar Cases 與 Relationship Graph 都能幫助分析師理解事件。但它們不能修改：

- Risk Level；
- Decision；
- live detection facts；
- approved knowledge；
- graph final facts；
- 真實防護或帳號狀態。

這種分工讓 AI 的價值可見，同時降低讓 AI 直接做安全決策的風險。

## 為什麼 BLOCK / MONITOR / ALLOW 是 simulated decisions

BLOCK / MONITOR / ALLOW 在本專題中是分流標籤，用來展示 deterministic policy 的輸出。它們不代表系統真的封鎖攻擊、部署監控、停用帳號、修改 cloud policy、送出 SIEM/SOAR action 或執行 remediation。

這個設計能讓 demo 看起來接近真實 SOC workflow，同時避免造成真實執行動作的誤解。

## Streamlit Analyst Console 展示設計

Streamlit UI 是本專題的主要展示入口。它提供：

- language selector；
- Fast deterministic / Full AI-assisted mode；
- demo scenario launcher；
- active context；
- deterministic analysis report；
- AI Analyst Brief；
- Evidence Gap Analyzer；
- Knowledge Q&A / RAG；
- Approved Similar Cases；
- Relationship Graph；
- Case Draft / Markdown Export。

英文 UI 截圖保留於 docs/screenshots/en/，繁中 UI 截圖保留於 docs/screenshots/zh-TW/。

## Demo 情境

| 情境 | 預期分類 | Risk Level | simulated Decision | 展示重點 |
|---|---|---|---|---|
| Command Injection Demo | Command Injection | HIGH | BLOCK | rule-based payload detection 與 evidence gap。 |
| Authentication Incident Demo | Possible Account Compromise | HIGH | MONITOR | 多次失敗後成功登入的可疑序列，但不宣稱已確認 compromised。 |
| HTTP/2 Resource Exhaustion Suspicion | HTTP/2 Resource Exhaustion Suspicion | MEDIUM | MONITOR | safe synthetic DoS / resource exhaustion triage，不產生攻擊流量。 |
| Full AI-assisted mode | 依輸入而定 | deterministic policy 保持權威 | simulated only | optional AI/RAG explanation path。 |

## 測試與驗證

最近一次記錄的 v2.8 release-gate 驗證摘要：

- pytest：1168 passed
- ruff：passed
- mypy：passed
- gitleaks：passed
- screenshot language refresh：completed

驗證重點包含 deterministic behavior、safety boundary、UI helper behavior、RAG control、language-aware output、documentation links 與 release gate。這不代表 production IDS/IPS effectiveness。

## Safety Boundary

- 偵測是 Rule-Based Detector，不是 AI 判斷。
- Risk Level / Decision 是 deterministic。
- BLOCK / MONITOR / ALLOW 是 simulated decisions only。
- RAG / LLM / AI Analyst Brief / Evidence Gap Analyzer / Similar Cases / Relationship Graph 只提供 advisory context。
- 歷史 approved cases 不能證明目前事件已被利用。
- 不做真實 firewall / WAF / EDR / account / cloud / SIEM / SOAR 動作。
- 不提供 exploit code、PoC generation、traffic generation 或 offensive automation。
- 需要 Human review。

## 與 rule-based-only / AI-only 作法比較

只使用 rule-based-only 的系統雖然穩定，但展示上較難呈現分析師需要的脈絡、證據缺口與知識查詢。只使用 AI-only 的系統雖然容易產生流暢說明，但不適合承擔偵測與決策權威。

Sentinel Project 採用混合架構：rule-based and deterministic path 負責權威，AI/RAG 負責 advisory support。

## 專題貢獻

本專題的主要貢獻如下：

- 建立可展示、可解釋的 AI-assisted blue-team triage workflow，讓教授、評審與第一次看專題的人能理解偵測、分流、複核與報告輸出的流程。
- 保留 Rule-Based Detector and deterministic policy 作為偵測與分流權威，避免由 AI 直接決定 Risk Level 或 Decision。
- 將 AI/RAG/Similar Cases/Relationship Graph 定位為 advisory only，提供分析脈絡、證據缺口、知識查詢與關聯視覺化，但不覆蓋 deterministic verdict。
- 使用 safe synthetic scenarios 展示 Command Injection、authentication incident 與 HTTP/2 Resource Exhaustion Suspicion，不提供 exploit、PoC 或 traffic generation。
- 建立 Streamlit Analyst Console，並整理英文與繁體中文公開文件、截圖與操作導覽，讓專題能以更完整的 GitHub showcase 形式呈現。

## 限制

本專題支援的是 bounded demo scenarios，不代表完整威脅偵測產品。它不執行真實封鎖、不產生攻擊流量、不提供 exploit，也不取代實際 SOC、SIEM、SOAR、EDR 或 incident response approval。

## 未來工作

- 增加更多 defensive synthetic scenarios。
- 建立 analyst timeline 與 event replay。
- 強化 read-only Relationship Graph 與 approved-case memory。
- 改善 Markdown export / report packaging。
- 持續整理公開文件、截圖與 release materials。

## 結論

Sentinel Project 展示了一種安全的 AI-assisted security triage 架構。它保留 deterministic detection and policy 作為權威，並把 AI/RAG 放在 analyst advisory layer。這讓系統能展示 AI 的輔助價值，同時避免讓 AI 成為最終裁決者、攻擊工具或真實自動化防護系統。
