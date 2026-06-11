# Sentinel Project 專題報告（繁體中文）

## 摘要

Sentinel Project 是一個 AI 輔助藍隊安全分流系統，設計目標是展示可解釋、可控制、具安全邊界的資安分析流程。系統以 Rule-Based Detector 作為偵測權威，透過 deterministic logic 產生 Risk Level 與 Decision，再由 AI Analyst Brief、Evidence Gap Analyzer、Knowledge Q&A / RAG、Approved Similar Cases 與 Relationship Graph 提供分析師參考。

本專題的核心立場是：AI 可以協助整理、解釋與提醒，但不能直接覆蓋偵測結果、風險等級或決策。BLOCK / MONITOR / ALLOW 都是 simulated decisions，不代表真實封鎖、監控或通報動作。

## 專題背景與動機

資安事件分流需要速度，也需要謹慎。若完全依賴 AI 產生判斷，可能出現 hallucination、不可追溯推論、過度確認攻擊成功，或誤把 advisory context 當成 final verdict 的風險。

本專題因此將 AI 放在 analyst support layer，而不是 decision authority。系統先以可檢查的規則偵測與分類，再用 AI/RAG 類功能補充分析脈絡，例如事件摘要、證據缺口、知識問答、相似案例與圖形關聯。這種架構更適合專題展示，也更符合藍隊工作流程中的安全責任邊界。

## 系統架構

整體架構可分為五個層次：

- Input layer：接收 payload、log、demo scenario 或 knowledge question。
- Detection layer：以 Rule-Based Detector 判斷攻擊類型與擷取證據。
- Decision layer：用 deterministic logic 產生 Risk Level / Decision。
- Advisory layer：產生 AI Analyst Brief、Evidence Gap、RAG answer、Similar Cases 與 Graph context。
- Presentation layer：透過 Streamlit console 呈現互動式 demo 與報告內容。

核心流程是：使用者輸入 → Rule-Based Detector → 攻擊分類與證據擷取 → deterministic Risk Level → deterministic Decision → AI / RAG advisory context → 報告、草稿與匯出。

## 模組設計

### Rule-Based Detector

Rule-Based Detector 是偵測權威，負責根據可觀察的輸入特徵判斷事件類型。它不是 LLM prompt，也不是讓 AI 自由推論攻擊結果。

### Risk Level / Decision

Risk Level 與 Decision 由 deterministic logic 產生。Decision 包含 BLOCK、MONITOR、ALLOW，但在本專題中都是 simulated decisions，只用於展示安全分流流程。

### AI Analyst Brief

AI Analyst Brief 整理目前分析結果，說明發生了什麼、為什麼重要、目前 deterministic verdict 是什麼、有哪些建議下一步與不安全假設。它是 advisory context，不是最終裁決。

### Evidence Gap Analyzer

Evidence Gap Analyzer 協助分析師看到目前還缺少哪些佐證，例如 server telemetry、authentication sequence、proxy/CDN 指標、resource usage 或 exploit success evidence。它不會直接宣稱 compromise 或 exploitation confirmed。

### Knowledge Q&A / RAG

Knowledge Q&A / RAG 用於防禦導向知識問答，例如 CVE 與 CVSS 差異、HTTP/2 DoS 防禦觀念、Resource Exhaustion 證據缺口。回答必須維持 advisory wording，不提供 exploit、PoC 或 traffic generation。

### Approved Similar Cases

Approved Similar Cases 使用 approved seed corpus 進行 read-only comparison。它可以說明相似原因與差異，但歷史案例不能證明目前事件已成功攻擊，也不能覆蓋 Risk Level 或 Decision。

### Relationship Graph

Relationship Graph 是分析師視覺輔助，用來呈現目前事件、證據、案例與關聯資訊。它不是自動化執行工具，也不是 final fact authority。

### Case Draft / Export

Case Draft 與 Markdown Export 用於整理人類可審閱的報告草稿。這些輸出需要 Human review，不代表自動提報、入庫或執行防禦動作。

## Demo 功能

目前 v2.8 demo-ready 版本的展示重點包含：

- Fast deterministic mode。
- Full AI-assisted mode。
- Lazy RAG startup。
- Language-aware output。
- AI Analyst Brief。
- Evidence Gap Analyzer。
- Knowledge Q&A / RAG。
- Approved Similar Cases。
- Relationship Graph。
- Case Draft 與 Markdown Export。
- HTTP/2 Resource Exhaustion safe synthetic demo。

建議展示流程是先使用 Command Injection demo 說明 deterministic detection，再展示 AI Analyst 與 Evidence Gap，接著用 Knowledge Q&A 詢問 HTTP/2 DoS 或 CVE 問題，最後載入 HTTP/2 Resource Exhaustion safe demo 說明系統如何維持安全邊界。

## 安全邊界

本專題明確保留以下安全邊界：

- 偵測是 Rule-Based Detector，不是 AI 判斷。
- Risk Level / Decision 是 deterministic。
- BLOCK / MONITOR / ALLOW 是 simulated。
- RAG / LLM / AI Analyst Brief / Evidence Gap 只提供 advisory context。
- 不做真實 firewall / WAF / EDR / account / cloud / SIEM / SOAR 動作。
- 不提供 exploit / PoC / traffic generation。
- 需要 Human review。

這些限制不是功能不足，而是本專題刻意設計的安全控制：AI 可以協助理解，但不應越權成為最終決策者或執行者。

## 測試與驗證

專案目前維持 v2.8 demo-ready 驗證紀錄。正式測試與 release gate 文件記錄了 pytest、ruff、mypy、gitleaks、screenshot refresh 與文件連結檢查等結果。

驗證重點包括：

- deterministic detection 與 decision behavior。
- Fast deterministic startup 不載入 heavy RAG dependency。
- RAG / LLM / AI advisory output 不覆蓋 final verdict。
- Evidence Gap 與 Similar Cases 不宣稱未證實的 compromise。
- HTTP/2 safe synthetic demo 不產生攻擊流量。
- 公開文件與 screenshot gallery 可供 GitHub 瀏覽。

## 限制

Sentinel Project 不是 production IDS / IPS，也不是 SOC 自動化平台。它不會連接真實 firewall、WAF、EDR、account、cloud、SIEM 或 SOAR，也不會執行封鎖、停權、通報或監控部署。

此外，本專題不提供 exploit、PoC、traffic generation，也不把 CVE 情報直接視為資產已被利用的證明。所有分析都需要 Human review。

## 未來工作

後續可以延伸的方向包括：

- 增加更多 defensive synthetic scenarios。
- 建立 analyst timeline 與 event replay。
- 強化 read-only Relationship Graph 與 approved-case memory。
- 改善 packaging、release polish 與公開文件結構。
- 擴充報告審核與匯出流程。

## 結論

Sentinel Project 展示了一種較安全的 AI-assisted security triage 架構：偵測與決策保持 deterministic，AI 與 RAG 則作為 analyst advisory layer。這讓系統可以展示 AI 的輔助價值，同時避免讓 AI 直接成為不可控的最終裁決者。

對專題展示而言，這個設計能清楚說明系統流程、展示可視化分析能力，也能回答資安場景中最重要的問題：哪些是確定的？哪些只是建議？哪些必須交由人類審查？
