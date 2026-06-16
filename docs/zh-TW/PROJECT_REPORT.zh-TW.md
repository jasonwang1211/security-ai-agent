# Sentinel Project 專題報告：AI 輔助藍隊安全分流系統

## 摘要

Sentinel Project 是一個 AI-assisted blue-team security triage prototype，目標是展示如何在不破壞安全邊界的情況下，把 AI 與 RAG 放進資安分析流程。系統以 Rule-Based Detector 與 deterministic policy 作為偵測與分流權威，再透過 AI Analyst Brief、Evidence Gap Analyzer、Knowledge Q&A / RAG、Approved Similar Cases 與 Relationship Graph 提供分析師參考。

本專題不讓 AI 直接判斷攻擊是否成立，也不讓 AI 決定 Risk Level 或 Decision。BLOCK / MONITOR / ALLOW 皆為 simulated decisions，不代表真實封鎖、監控部署或 remediation。

## 1. 專題背景與動機

### 1.1 資安分流的問題

資安事件分流需要快速、可解釋且可重現的判斷。分析師需要知道目前事件屬於哪一類、風險程度為何、哪些證據已確認、還缺少哪些證據，以及下一步應該如何複核。

### 1.2 AI 導入資安流程的風險

AI 可以協助整理資訊，但如果讓 AI 成為最終裁決者，就可能產生錯誤信心。LLM 可能因 hallucination、prompt sensitivity 或資料不足而過度推論，甚至把可疑事件說成已確認入侵。

### 1.3 本專題目標

本專題實作一種安全的混合架構：deterministic detection and policy 保留權威，AI/RAG 只提供 advisory context。AI 被用來整理摘要、提示證據缺口與查詢防禦知識，但不直接參與攻擊判斷、風險決策或自動化防護。

### 1.4 專題展示重點

- 以 Streamlit 串接可操作的 SOC analyst triage prototype。
- Rule-Based Detector 作為偵測權威。
- deterministic Risk Level / Decision。
- AI/RAG/Similar Cases/Relationship Graph 只作為 advisory layer。
- safe synthetic demo scenarios，不提供 exploit、PoC 或 traffic generation。

## 2. 相關概念

### 2.1 Rule-Based Detection

Rule-Based Detection 使用明確規則與特徵比對來判斷支援的 payload 或 incident pattern。它的優點是可測試、可重現、可追蹤，適合用於專題展示中的 detection authority。

### 2.2 RAG

RAG 代表 Retrieval-Augmented Generation。它可以從 approved defensive knowledge context 中取回相關內容，協助回答防禦性問題。但 RAG 回答不能證明目前事件已被利用，也不能覆蓋 deterministic verdict。

### 2.3 LLM Advisory

LLM 或 AI advisory layer 可用來摘要、解釋、產生建議檢查項目，但不能作為 Risk Level、Decision 或 real enforcement 的來源。

### 2.4 SOC Triage

SOC triage 強調快速分類、風險排序、證據整理與人工複核。本專題用 Streamlit Analyst Console 模擬這個分析流程。

### 2.5 Streamlit UI

Streamlit UI 提供一個可操作的 analyst console，包含 demo cards、active context、AI advisory panels、case intelligence、graph context 與 report export。

## 3. 系統設計

### 3.1 整體流程

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

### 3.2 Authority Path

Authority Path 包含 Rule-Based Detector、Risk Level 與 Decision。這條路徑負責目前事件的 deterministic verdict，也是系統中最重要的安全邊界。

### 3.3 Advisory Path

Advisory Path 包含 AI Analyst Brief、Evidence Gap Analyzer、Knowledge Q&A / RAG、Approved Similar Cases 與 Relationship Graph。它們可以說明、比較、整理脈絡，但不能修改 deterministic verdict。

### 3.4 Human Review Path

Case Draft 與 Markdown Export 產生的是報告素材，不是自動化 remediation。任何真實營運動作都需要 Human review。

### 3.5 為什麼不讓 AI 決定攻擊

AI 可能生成流暢但不可靠的文字。若讓 AI 直接決定攻擊與否，reviewer 很難判斷結果是否可重現。因此本專題保留 Rule-Based Detector 作為偵測權威。

### 3.6 為什麼 BLOCK / MONITOR / ALLOW 是 simulated decisions

BLOCK / MONITOR / ALLOW 用來展示 deterministic policy 的分流結果。它們不代表真實封鎖、監控部署、停用帳號、修改 cloud policy、送出 SIEM/SOAR action 或執行 remediation。

## 4. 模組設計

### 4.1 Rule-Based Detector

負責判斷支援的 payload / incident pattern，例如 Command Injection、possible account compromise sequence、HTTP/2 Resource Exhaustion Suspicion。

### 4.2 Risk Level / Decision

根據 deterministic policy 產生 Risk Level 與 simulated Decision。這些輸出不依賴 LLM。

### 4.3 AI Analyst Brief

將目前事件整理成分析師容易閱讀的摘要，包含 what happened、why it matters、deterministic verdict context、next steps 與 unsafe assumptions。

### 4.4 Evidence Gap Analyzer

列出 confirmed facts、missing evidence、recommended checks 與 unsafe assumptions。它協助分析師避免把可疑事件過度宣稱成已確認攻擊。

### 4.5 Knowledge Q&A / RAG

回答防禦導向知識問題，例如 HTTP/2 DoS、CVE、Resource Exhaustion。它不提供 exploit、PoC 或 traffic generation。

### 4.6 Approved Similar Cases

讀取 manually curated approved seed cases，提供 deterministic similarity reasons、key differences 與 advisory boundary。歷史案例不能證明目前事件。

### 4.7 Relationship Graph

以視覺方式呈現目前事件、規則、風險、決策與 approved cases 的關聯。Graph 是 explanatory only，不是 graph-based detection。

### 4.8 Case Draft / Markdown Export

提供 human-reviewed report material。Draft 與 Export 不能被視為 live remediation proof。

### 4.9 Streamlit Analyst Console

整合 scenario launcher、mode selector、active context、analysis report、AI advisory panels、case intelligence、graph context、case draft 與 markdown export。

## 5. Demo 情境

### 5.1 Command Injection Demo

輸入 payload text，預期分類為 Command Injection，Risk Level 為 HIGH，simulated Decision 為 BLOCK。展示 rule-based payload detection、rule evidence 與 evidence gap。

### 5.2 Authentication Incident Demo

使用 authentication log path 或 synthetic log content，展示多次登入失敗後成功登入的可疑序列。系統可標示 Possible Account Compromise，但不宣稱已確認帳號被盜用。

### 5.3 HTTP/2 Resource Exhaustion Safe Demo

使用 safe synthetic incident summary 展示 resource exhaustion triage。此情境不產生攻擊流量，不提供 exploit 或 PoC，也不宣稱真實 enforcement。

### 5.4 UI 截圖導覽

英文 UI 截圖保留於 docs/screenshots/en/，繁中 UI 截圖保留於 docs/screenshots/zh-TW/。公開文件透過 screenshot gallery 呈現主要功能區塊。v3.0 新增一組可讀的繁中關鍵截圖（`zh-TW/20`–`31`，overview + detail crop），以及中文展示稿 [v3.0_presentation_notes.zh-TW.md](v3.0_presentation_notes.zh-TW.md)。需注意 v2.9 Evidence-Grounded AI Brief 面板的固定段落標籤目前仍為英文（deterministic 路徑與 UI 外框已為繁體中文），屬已知限制，截圖會如實呈現中英混合，未宣稱完全中文化。

## 6. 測試與驗證

### 6.1 驗證範圍

驗證重點包含 deterministic behavior、safety boundary、UI helper behavior、RAG control、language-aware output、documentation links 與 release gate。

### 6.2 pytest

最近一次本機重跑（v3.0 docs polish，基於 v2.9.0 baseline）顯示 pytest：1236 passed。

### 6.3 ruff / mypy

最近一次重跑顯示 ruff：All checks passed；mypy：no issues found in 172 source files。

### 6.4 gitleaks

最近一次記錄的 release-gate summary 顯示 gitleaks passed，並使用 .gitleaksignore 處理 false-positive safety-boundary wording。

### 6.5 Screenshot refresh

英文與繁中 UI screenshot sets 已分離，避免英文 README 使用繁中 UI 截圖造成視覺不一致。

### 6.6 Safety Boundary 驗證

測試與文件皆需保留：AI/RAG advisory only、simulated decisions、no real enforcement、no exploit / PoC / traffic generation、Human review required。

## 7. 與其他做法比較

### 7.1 Rule-based-only 的限制

只使用 rule-based-only 的系統雖然穩定，但展示上較難呈現分析師需要的脈絡、證據缺口、知識查詢與報告輔助。

### 7.2 AI-only 的風險

只使用 AI-only 的系統雖然容易產生流暢說明，但不適合承擔偵測與決策權威，因為結果可能不可重現，也可能缺乏證據約束。

### 7.3 本專題的混合架構

Sentinel Project 採用 deterministic first, AI advisory second。Rule-Based Detector and deterministic policy 負責 authority path，AI/RAG/Similar Cases/Relationship Graph 負責 advisory support。

## 8. 專題貢獻

本專題的主要貢獻如下：

- 完成一個以 Streamlit 為主要介面的 blue-team triage prototype，可從輸入、偵測結果、風險等級、決策到報告輸出一路追蹤。
- 將偵測與決策權威限制在 Rule-Based Detector 與 deterministic policy，避免 LLM 直接影響 final verdict。
- 實作 AI Analyst Brief 與 Evidence Gap Analyzer，讓輸出不只給結論，也標示缺少哪些證據與哪些假設不應過度延伸。
- 將 RAG、Approved Similar Cases、Relationship Graph 設計成 read-only / advisory context，提供防禦知識、相似案例與關聯脈絡，但不覆蓋 deterministic verdict。
- 使用 safe synthetic scenarios 呈現 Command Injection、authentication incident 與 HTTP/2 Resource Exhaustion Suspicion，不產生攻擊流量、不提供 exploit 或 PoC。
- 整理英文與繁體中文公開文件、截圖與操作導覽，讓此 repo 可作為個人 security engineering portfolio 與後續功能延伸的基礎。

## 9. 限制

本專題支援的是 bounded demo scenarios，不代表完整威脅偵測產品。它不執行真實封鎖、不產生攻擊流量、不提供 exploit，也不取代實際 SOC、SIEM、SOAR、EDR 或 incident response approval。

## 10. 未來工作

- 增加更多 defensive synthetic scenarios。
- 建立 analyst timeline 與 event replay。
- 強化 read-only Relationship Graph 與 approved-case memory。
- 改善 Markdown export / report packaging。
- 持續整理公開文件、截圖與 release materials。

## 11. 結論

Sentinel Project 實作了一種安全的 AI-assisted security triage 架構。它保留 deterministic detection and policy 作為權威，並把 AI/RAG 放在 analyst advisory layer。這個設計讓 AI 可以協助閱讀、整理與複核，同時避免讓 AI 成為最終裁決者、攻擊工具或真實自動化防護系統。
