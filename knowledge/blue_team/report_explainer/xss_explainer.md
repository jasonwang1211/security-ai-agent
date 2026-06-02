---
schema_version: v2.2-live1
doc_id: report.xss_explainer
doc_type: report_explainer
title: XSS 攻擊判讀
language: zh-TW
status: live
review_status: approved_for_runtime_promotion
audience:
  - student_analyst
  - taiwan_academic_blue_team
applies_to:
  - Security Triage Report
  - Detection Rule
  - Web Attack
related_tools:
  - report_followup
  - graph_explainers
  - rag_v2
attack_types:
  - XSS
finding_types: []
evidence_types:
  - payload_indicator
  - rule_match
severity:
  - MEDIUM
decision_labels:
  - MONITOR
rule_ids:
  - XSS-001
mitre_techniques: []
evidence_ids: []
finding_ids: []
incident_ids: []
keywords:
  - XSS
  - cross-site scripting
  - script injection
  - XSS-001
  - 跨站腳本
  - 網頁攻擊
tags:
  - web_attack
  - detection_rule
  - attack_type
references:
  - id: local_detection_xss_001
    type: internal_provenance
    source: detections/blue_team/xss/xss_basic.yml
    note: Verified local YAML detection rule XSS-001 with MEDIUM severity and XSS attack type.
  - id: local_triage_policy
    type: internal_provenance
    source: modules/triage_policy.py
    note: Maps XSS to MEDIUM risk and MEDIUM to simulated MONITOR.
  - id: owasp_xss_prevention_cheat_sheet
    type: external_defensive_reference
    source: OWASP Cross Site Scripting Prevention Cheat Sheet
    url: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
limitations:
  - Generic KB document uses type-level metadata only.
  - Narrative prose must not create graph edges automatically.
  - BLOCK, MONITOR, and ALLOW are simulated decisions only.
---

# XSS 攻擊判讀

## 目的

本文件用防禦角度說明 XSS 的判讀方式，協助學生分析師理解報告中的 attack type、rule ID 與模擬決策。它不是攻擊教學，也不代表系統已完成任何真實阻擋。

## 適用情境

- Security Triage Report 顯示 `XSS` 或命中 verified rule ID `XSS-001`。
- Web request、query string、表單欄位或 payload 中出現腳本注入跡象。
- 需要說明為何 RAG 或 graph-backed explanation 只能輔助解釋，不能改變 Risk Level 或 Decision。

## 重要判讀

XSS 通常涉及將腳本內容放入網頁輸入、URL、留言、表單或其他可反射到瀏覽器的資料位置。防禦分析時應確認 payload 是否真的進入可執行的瀏覽器上下文，並區分測試字串、掃描器、編碼內容與實際可利用風險。

## 報告欄位對應

| 欄位 | 判讀方式 |
|---|---|
| finding_types | 不適用；此文件以 attack type 與 rule ID 為主。 |
| evidence_types | 可使用 `payload_indicator` 或 `rule_match` 描述 type-level evidence。 |
| Rule ID | 使用已驗證的 `XSS-001`。 |
| Risk Level | 依報告 deterministic 結果解讀，不在本文中重算。 |
| Decision | 目前 deterministic policy 對 `XSS-001` 的典型決策為 `MONITOR`；這仍是模擬決策，不是真實 WAF 或瀏覽器防護。 |

## 藍隊分析步驟

1. 確認 payload 是否包含腳本、事件處理器、HTML 注入或可疑編碼。
2. 檢查輸入是否會反射、儲存或傳遞到瀏覽器可執行上下文。
3. 比對是否為合法安全測試、掃描器或課程實驗。
4. 檢查是否有使用者 session、cookie、token 或頁面敏感資料暴露風險。
5. 保留原始 request、response 與 rule match metadata，避免自行新增未證實證據。

## 模擬決策說明

`ALLOW`、`MONITOR`、`BLOCK` 在本專案中都是模擬決策。對目前的 `XSS-001` deterministic policy，metadata 保留 `MONITOR`；若未來其他情境討論阻擋，也只能作為一般防禦建議，不代表真實 WAF、CDN、瀏覽器政策或伺服器規則已被修改。

## 常見誤判與限制

- 掃描器或課程測試可能產生 XSS-like payload。
- 被編碼的字串不一定會在瀏覽器中執行。
- RAG、LLM、graph-backed explanation 不能把 rule match 改寫成已確認攻擊成功，也不能覆蓋 Risk Level 或 Decision。

## Graph RAG 準備註記

未來 KnowledgeDoc graph seed 可只使用 reviewed `attack_types` 與 `rule_ids`，並且必須先與明確提供的 `DetectionRule` objects 交叉驗證。

本文敘述不會建立 graph edge；automatic Graph RAG Retrieval 與 vector-to-graph expansion 不在本 batch 實作。
