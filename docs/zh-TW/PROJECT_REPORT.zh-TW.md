# Sentinel Project 專題報告（繁體中文）

## 摘要

Sentinel Project 是一個 AI 輔助藍隊安全分流系統。它以 Rule-Based Detector 與 deterministic Risk Level / Decision logic 作為安全權威，再透過 Streamlit Analyst Console 呈現 AI Analyst Brief、Evidence Gap Analyzer、Knowledge Q&A / RAG、Approved Similar Cases、Relationship Graph、Case Draft 與 Markdown Export。

本專題的核心價值是示範如何把 AI 放進 SOC triage workflow，但不讓 AI 成為 final decision engine。AI 可以協助整理、解釋與提醒；偵測、風險與決策仍由 deterministic path 負責。

## 專題背景與動機

資安事件分流需要快速判斷，也需要清楚說明「哪些已確認、哪些還缺證據」。一般 AI security demo 容易把 AI advisory text 包裝成最終結論，讓使用者誤以為 AI 已經證明攻擊成功或可以直接執行防禦動作。

Sentinel Project 避免這個問題。系統把 deterministic authority 與 AI advisory layer 分開，讓教授或評審能清楚看到：偵測與決策從哪裡來，AI 只是輔助分析師理解事件。

## 系統架構

```text
使用者輸入 / demo scenario
  -> Streamlit Analyst Console
  -> Rule-Based Detector
  -> 攻擊分類
  -> deterministic Risk Level
  -> simulated Decision
  -> advisory layers
  -> Human-reviewed report / draft / export
```

authority path 負責 Rule-Based Detector、attack classification、Risk Level 與 Decision。advisory path 負責 AI Analyst Brief、Evidence Gap Analyzer、Knowledge Q&A / RAG、Approved Similar Cases 與 Relationship Graph。

## Streamlit Analyst Console

主展示介面是：

```text
ui/streamlit_app.py
```

啟動指令：

```powershell
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```

主要 panels / tabs：

- Input and scenario loader：載入安全 demo scenarios。
- Deterministic result：顯示 attack type、Risk Level、simulated Decision、rule ID。
- AI Analyst Brief：提供 advisory summary 與 next steps。
- Evidence Gap Analyzer：列出 confirmed facts、missing evidence 與 unsafe assumptions。
- Knowledge Q&A / RAG：回答防禦導向知識問題。
- Approved Similar Cases：比較 approved seed cases。
- Relationship Graph：呈現 read-only investigation context。
- Case Draft / Markdown Export：整理人類可審閱的報告素材。

## 模組設計

### Rule-Based Detector

Rule-Based Detector 是偵測權威，負責根據可觀察輸入特徵判斷事件類型。它不是 LLM prompt，也不是自由生成的 AI verdict。

### Risk Level / Decision

Risk Level 與 Decision 由 deterministic logic 產生。BLOCK / MONITOR / ALLOW 都是 simulated decisions，不代表真實封鎖或監控。

### AI Analyst Brief

AI Analyst Brief 用分析師語言整理目前事件、判斷脈絡、建議下一步與不安全假設。它是 advisory context，不是 final verdict。

### Evidence Gap Analyzer

Evidence Gap Analyzer 協助分析師看到還缺哪些佐證，例如 process telemetry、server logs、EDR data、resource metrics 或 exploitation evidence。

### Knowledge Q&A / RAG

Knowledge Q&A / RAG 用於防禦導向知識問答，例如 HTTP/2 DoS、Resource Exhaustion、CVE 與 CVSS。它不提供 exploit、PoC 或 traffic generation。

### Approved Similar Cases 與 Relationship Graph

Approved Similar Cases 提供 approved seed cases 的比較；Relationship Graph 提供 read-only visual context。兩者都不能證明目前事件已成功攻擊，也不能覆蓋 Risk Level 或 Decision。

## Demo 功能

| Scenario | 預期分類 | Risk Level | Simulated Decision | 展示重點 |
|---|---|---|---|---|
| Command Injection demo | Command Injection | HIGH | BLOCK | rule-based detection、AI advisory、evidence gaps |
| Authentication incident demo | Possible Account Compromise | HIGH | MONITOR | suspicious sequence triage，不宣稱 confirmed compromise |
| HTTP/2 Resource Exhaustion safe demo | HTTP/2 Resource Exhaustion Suspicion | MEDIUM | MONITOR | safe synthetic DoS triage，不產生流量 |
| Optional Full AI-assisted mode | depends on input | deterministic policy | simulated only | optional AI/RAG explanation |

## 安全邊界

- 偵測是 Rule-Based Detector，不是 AI 判斷。
- Risk Level / Decision 是 deterministic。
- BLOCK / MONITOR / ALLOW 是 simulated。
- RAG / LLM / AI Analyst Brief / Evidence Gap 只提供 advisory context。
- 不做真實 firewall / WAF / EDR / account / cloud / SIEM / SOAR 動作。
- 不提供 exploit / PoC / traffic generation。
- 需要 Human review。

## 測試與驗證

目前 v2.8 demo-ready 驗證摘要：

- pytest：`1168 passed`
- ruff：passed
- mypy：passed
- gitleaks：passed
- screenshot refresh：completed

驗證重點是 deterministic behavior、safety boundary、UI helper behavior、RAG control、language-aware output，以及 documentation link integrity。這不代表 production IDS/IPS effectiveness。

## 截圖證明什麼

繁中 UI 截圖保留於 `docs/screenshots/zh-TW/`；英文 UI 截圖請見 `docs/screenshots/en/`。

- [Console home](../screenshots/zh-TW/01_console_home.png)：主 UI、demo cards、mode controls 與 safety framing。
- [AI Analyst Brief](../screenshots/zh-TW/03_ai_analyst_brief.png)：AI advisory panel 不覆蓋 deterministic verdict。
- [Evidence Gap Analyzer](../screenshots/zh-TW/04_evidence_gap_analyzer.png)：confirmed facts、missing evidence 與 unsafe assumptions。
- [HTTP/2 safe demo](../screenshots/zh-TW/09_http2_resource_exhaustion_demo.png)：safe synthetic scenario，不產生攻擊流量。

## 限制

Sentinel Project 不是 production IDS/IPS，不是 red-team tool，不是 exploit generator，也不是 autonomous response system。它不會連接真實 firewall、WAF、EDR、account、cloud、SIEM 或 SOAR，也不會執行封鎖、停權、通報或監控部署。

## 未來工作

- 增加更多 defensive synthetic scenarios。
- 建立 analyst timeline 與 event replay。
- 強化 read-only Relationship Graph 與 approved-case memory。
- 改善 report export 與 release packaging。
- 持續整理公開文件與截圖導覽。

## 結論

Sentinel Project 展示了一種較安全的 AI-assisted security triage 架構：deterministic detection and policy 保持權威，AI/RAG 則作為 analyst advisory layer。這讓系統可以展示 AI 的輔助價值，同時避免讓 AI 直接成為不可控的最終裁決者。
