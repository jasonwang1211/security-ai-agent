# Sentinel Project Report / 專案報告

## 專案動機 / Project Motivation

Sentinel Project 探索如何把 AI 輔助放進 SOC 分析流程，同時避免讓 AI 取得不安全的最終判定權。系統設計重點不是「自動封鎖一切」，而是讓分析師更快看懂事件、證據缺口、相似案例與後續複核方向。

Sentinel Project explores AI-assisted SOC triage while preserving deterministic safety authority. The system helps analysts explain, compare, and document cases without giving AI final decision control.

## 目前版本重點 / Current Version Focus

目前 v2.8 demo-ready 狀態包含 v2.7 AI advisory features 與 v2.8 lazy RAG startup discipline。本次 Fix Pass 讓 UI output 依照語言選擇切換：

- `zh-TW`: 繁體中文為主，保留必要英文資安術語。
- `en`: English output.
- `bilingual`: 繁體中文先，附精簡 English support。

HTTP/2 Resource Exhaustion demo launcher card 現在只顯示短 preview；按 Load Scenario 時仍會載入完整 synthetic incident summary 與所有 safety lines。

## 架構摘要 / Architecture Summary

```text
User input or demo scenario
-> deterministic detector / log parser
-> deterministic risk and decision policy
-> Security Triage Report
-> advisory layers:
   - AI Analyst Brief
   - Evidence Gap Analyzer
   - Knowledge Q&A / RAG
   - Approved Similar Cases
   - Relationship Graph
   - Case Draft / Export
```

前三層是 authority path。後面的 AI/RAG/UI panels 只提供 advisory analyst context。

## 規則式偵測 / Rule-Based Detection

Payload detections 使用 deterministic Detection-as-Code rules，支援 Command Injection、SQL Injection、Path Traversal、XSS 等類型。Authentication log scenario 會先被正規化為 structured evidence / findings，再進入 deterministic risk 與 decision pipeline。

Example:

```text
test; rm -rf /tmp/test
-> Command Injection
-> CMD-001
-> Risk Level: HIGH
-> Decision: BLOCK (simulated)
```

## 確定性風險與決策 / Deterministic Risk and Decision

Risk Level 與 Decision 不由 LLM 產生。它們由 deterministic code 計算，並以 Security Triage Report 顯示。

- `BLOCK`: simulated block recommendation.
- `MONITOR`: simulated monitoring / analyst review recommendation.
- `ALLOW`: no sufficient deterministic evidence to block or monitor.

No real firewall, WAF, EDR, account, cloud, SIEM, or SOAR action is performed.

## AI/RAG 建議角色 / AI/RAG Advisory Role

AI/RAG layers 可以摘要、說明、指出 evidence gaps、回答防禦型知識問題、比對 approved similar cases，並協助撰寫 human-reviewed report content。

它們不能：

- override Risk Level or Decision;
- prove compromise;
- prove successful execution;
- perform real enforcement;
- provide exploit, PoC, or traffic-generation guidance.

## AI 分析摘要 / AI Analyst Brief

AI Analyst Brief 是 deterministic advisory output，`llm_status: not_used`。它會依 UI language selection 輸出繁體中文、英文或精簡雙語。

內容包含：

- 發生了什麼 / What happened.
- 為什麼重要 / Why it matters.
- 確定性判定 / Deterministic verdict.
- 建議摘要 / Advisory summary.
- 證據缺口摘要 / Evidence gap summary.
- 建議下一步 / Recommended next steps.
- 不安全的假設 / Unsafe assumptions.

## 證據缺口分析器 / Evidence Gap Analyzer

Evidence Gap Analyzer 協助分析師避免過度推論。它列出還需要確認的 telemetry、logs、process evidence、database evidence、identity/session evidence 或 resource indicators。

本次 Fix Pass 後，Evidence Gap output 也會依 UI language selection 顯示。

## 知識問答 / Knowledge Q&A

Knowledge Q&A 使用 RAG / approved knowledge 做防禦型說明。本次 Fix Pass 加入 lightweight output language policy：

- UI language changes do not initialize RAG, Chroma, embeddings, Torch, sentence-transformers, or ChatOllama.
- RAG prompt keeps one safety block and adds one selected language instruction block.
- Retrieval selection, controlled source selection, citations, CVE/CVSS normalization, and answer safety guardrails are unchanged.

## 核准相似案例 / Approved Similar Cases

Approved Similar Cases 只讀取 manually curated approved seed files。相似案例是 historical advisory reference，不會覆蓋目前事件的 Risk Level / Decision，也不證明目前事件成功執行或已被入侵。

## 關係圖 / Relationship Graph

Relationship Graph 顯示 current event、attack type、rule、evidence、risk、decision、similar case 的關係。它是 explanation context，不是 graph-based detection authority。

## 案例草稿與匯出 / Case Draft and Export

Case Draft 與 Export Report 服務於 human review。Draft remains approval-gated，Export Report 是 copyable preview，不會自動寫入正式報告或 knowledge base。

## 安全 HTTP/2 資源耗盡示範 / Safe HTTP/2 Resource Exhaustion Demo

HTTP/2 Resource Exhaustion scenario 是 synthetic incident summary。Launcher card 顯示短 preview；Load Scenario 會載入完整 input，包括：

- synthetic incident summary;
- no traffic generated;
- no vulnerability reproduction material;
- no real enforcement;
- human review required.

此 demo 不產生 HTTP/2 traffic，不提供 exploit / PoC，不宣稱 confirmed exploitation。

## 測試摘要 / Testing Summary

Automated tests cover:

- rule-based detection and deterministic policy;
- UI demo scenario preview behavior;
- output language policy;
- AI Analyst Brief language-aware output;
- Evidence Gap language-aware output;
- RAG prompt language instruction and lazy forwarding;
- RAG controlled runtime safety;
- lazy RAG startup regression;
- Streamlit UI helper rendering without importing Streamlit.

See [docs/TEST_REPORT.md](docs/TEST_REPORT.md).

## 限制 / Limitations

This is a prototype, not a production SOC platform. It does not replace SIEM/SOAR, endpoint telemetry, vulnerability management, incident response approval, or expert analyst judgment.

Known limitations:

- no real enforcement;
- no production alert ingestion pipeline;
- no autonomous remediation;
- RAG quality depends on approved knowledge content;
- case memory is a curated demo corpus, not a production case database.

## 安全邊界 / Safety Boundary

- Detector remains rule-based.
- Risk Level / Decision remain deterministic.
- `BLOCK` / `MONITOR` / `ALLOW` remain simulated.
- RAG / LLM / AI Analyst Brief / Evidence Gap are advisory only.
- No real firewall, WAF, EDR, account, cloud, SIEM, or SOAR action is performed.
- No exploit, PoC, or traffic generation is included.
- Human review is required.
