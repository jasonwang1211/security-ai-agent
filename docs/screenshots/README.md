# UI Screenshots / UI 截圖索引

**中文**

這些截圖是在 v2.8-D 文件與畫面更新 / Fix Pass 批次中，從本機 Streamlit SOC Console 擷取。擷取方式：使用 repo `venv` 啟動 Streamlit，並以 headless Chrome DevTools Protocol 截圖。截圖不包含秘密金鑰；可見路徑僅為一般本機 repo/demo 路徑。

**English**

These screenshots were refreshed during the v2.8-D documentation / Fix Pass batch. They were captured from the local Streamlit SOC Console using the repository `venv` and headless Chrome DevTools Protocol. They do not show secrets; visible paths are normal local repo/demo paths only.

## Safety reminder / 安全提醒

- Detector remains rule-based. / 偵測器仍為規則式。
- Risk Level / Decision remain deterministic. / 風險與決策仍為確定性。
- `BLOCK` / `MONITOR` / `ALLOW` are simulated. / 這些決策是模擬結果。
- RAG / LLM / AI Analyst Brief / Evidence Gap are advisory only. / AI/RAG/證據缺口僅供參考。
- No real firewall/WAF/EDR/account/cloud/SIEM/SOAR action. / 不執行真實防護或帳號動作。
- No exploit, PoC, or traffic generation. / 不提供 exploit、PoC 或產生流量。
- Human review required. / 需要人工審查。

## Current screenshot set / 目前截圖組

| # | File | 中文說明 | English description | Demo step |
|---|---|---|---|---|
| 1 | [01_console_home.png](01_console_home.png) | 控制台首頁、狀態列、語言/模式、Demo Scenario Launcher。 | Console home, status bar, language/mode controls, Demo Scenario Launcher. | Core / Fast deterministic |
| 2 | [02_fast_command_injection_analysis.png](02_fast_command_injection_analysis.png) | Fast deterministic Command Injection，顯示 `HIGH / BLOCK` 與規則證據。 | Fast deterministic Command Injection with `HIGH / BLOCK` and rule evidence. | Core / Fast deterministic |
| 3 | [03_ai_analyst_brief.png](03_ai_analyst_brief.png) | AI Analyst Brief，顯示繁體中文優先、deterministic advisory、no LLM 與安全邊界。 | AI Analyst Brief showing selected-language output, deterministic advisory, no LLM, and boundary language. | Core / AI Analyst |
| 4 | [04_evidence_gap_analyzer.png](04_evidence_gap_analyzer.png) | Evidence Gap Analyzer，依 UI 語言列出仍需複核的證據缺口。 | Evidence Gap Analyzer listing missing evidence in the selected UI language. | Core / AI Analyst |
| 5 | [05_knowledge_qa_rag.png](05_knowledge_qa_rag.png) | Knowledge Q&A / RAG 回答，依 UI 語言輸出且僅供分析參考。 | Knowledge Q&A / RAG answer follows selected UI language and remains advisory only. | Core / RAG path |
| 6 | [06_similar_cases.png](06_similar_cases.png) | Approved Similar Cases，Command Injection 對應 `CASE-SEED-001`。 | Approved Similar Cases showing `CASE-SEED-001` for Command Injection. | Core / Case intelligence |
| 7 | [07_relationship_graph.png](07_relationship_graph.png) | Relationship Graph，顯示目前事件、風險/決策、共享欄位與核准案例。 | Relationship Graph showing current event, risk/decision, shared fields, and approved case. | Core / Case intelligence |
| 8 | [08_case_draft_export.png](08_case_draft_export.png) | Case Draft 與 Markdown Export preview。 | Case Draft and Markdown Export preview. | Core / Draft-export |
| 9 | [09_http2_resource_exhaustion_demo.png](09_http2_resource_exhaustion_demo.png) | 安全 HTTP/2 Resource Exhaustion synthetic demo；launcher card 是短 preview，完整 input 仍保留 no traffic / no enforcement。 | Safe HTTP/2 Resource Exhaustion synthetic demo; launcher card is compact while full input keeps no traffic / no enforcement text. | Optional / Safe scenario |
| 10 | [10_full_ai_assisted_optional.png](10_full_ai_assisted_optional.png) | Full AI-assisted optional path，顯示 Full AI / AI-RAG 標籤。 | Optional Full AI-assisted path showing Full AI / AI-RAG chips. | Optional / Full AI-assisted |

Older screenshot files from previous demo passes may still exist for comparison, but the table above is the current v2.8-D guided path.
