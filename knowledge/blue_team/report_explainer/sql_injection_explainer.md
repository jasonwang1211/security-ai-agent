---
schema_version: v2.2-live1
doc_id: report.sql_injection_explainer
doc_type: report_explainer
title: SQL Injection 攻擊判讀
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
  - SQL Injection
finding_types: []
evidence_types:
  - payload_indicator
  - rule_match
severity:
  - HIGH
decision_labels:
  - BLOCK
rule_ids:
  - SQLI-001
mitre_techniques: []
evidence_ids: []
finding_ids: []
incident_ids: []
keywords:
  - SQL Injection
  - SQLI
  - SQLI-001
  - query payload
  - SQL 注入
  - 資料庫查詢
tags:
  - web_attack
  - detection_rule
  - attack_type
references:
  - id: local_detection_sqli_001
    type: internal_provenance
    source: detections/blue_team/sql_injection/sql_injection_basic.yml
    note: Verified local YAML detection rule SQLI-001 with HIGH severity and SQL Injection attack type.
  - id: local_triage_policy
    type: internal_provenance
    source: modules/triage_policy.py
    note: Maps SQL Injection to HIGH risk and HIGH to simulated BLOCK.
  - id: owasp_sql_injection_prevention_cheat_sheet
    type: external_defensive_reference
    source: OWASP SQL Injection Prevention Cheat Sheet
    url: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
limitations:
  - Generic KB document uses type-level metadata only.
  - Narrative prose must not create graph edges automatically.
  - BLOCK, MONITOR, and ALLOW are simulated decisions only.
---

# SQL Injection 攻擊判讀

## 目的

本文件說明 SQL Injection 的防禦判讀方式，協助學生分析師理解報告中的 `SQL Injection` attack type 與 verified rule ID `SQLI-001`。內容聚焦偵測與調查，不提供攻擊操作指引。

## 適用情境

- Web request 或 payload 命中 `SQLI-001`。
- 報告指出可能的 SQL 查詢操控、條件繞過、錯誤訊息或資料庫關鍵字濫用。
- 分析師需要保守解釋風險，不宣告資料庫已被存取或外洩。

## 重要判讀

SQL Injection 代表輸入可能被拼接或傳入資料庫查詢，造成查詢邏輯被操控。rule match 只能指出 payload 有可疑特徵；是否成功利用仍需要確認應用程式行為、回應內容、資料庫錯誤、權限與後續事件。

## 報告欄位對應

| 欄位 | 判讀方式 |
|---|---|
| finding_types | 不適用；此文件以 attack type 與 rule ID 為主。 |
| evidence_types | 可使用 `payload_indicator` 或 `rule_match` 描述 type-level evidence。 |
| Rule ID | 使用已驗證的 `SQLI-001`。 |
| Risk Level | 依報告 deterministic 結果解讀，不在本文中重算。 |
| Decision | 目前 deterministic policy 對 `SQLI-001` 的典型決策為 `BLOCK`；這仍是模擬決策，不是真實資料庫或 WAF 控制。 |

## 藍隊分析步驟

1. 檢查 payload 是否包含 SQL 關鍵字、條件片段、註解符號或可疑編碼。
2. 查看應用程式回應是否有資料庫錯誤、資料異常或狀態碼變化。
3. 比對請求來源是否為掃描器、課程測試或已知安全測試。
4. 檢查資料庫帳號權限、查詢日誌與是否有異常資料讀取跡象。
5. 在證據不足時，使用「疑似 SQL Injection 嘗試」而不是「資料庫已遭入侵」。

## 模擬決策說明

`ALLOW`、`MONITOR`、`BLOCK` 是訓練報告中的模擬決策。對目前的 `SQLI-001` deterministic policy，metadata 保留 `BLOCK`；這不代表系統已修改 WAF、資料庫權限、應用程式路由或雲端安全群組。

## 常見誤判與限制

- 搜尋欄位、測試資料或課程實驗可能包含 SQL-like 字串。
- 編碼或日誌截斷可能讓 payload 看起來比實際更可疑或更不完整。
- RAG、LLM 與 graph-backed explanation 不能宣告資料外洩或覆蓋 Risk Level / Decision。

## Graph RAG 準備註記

未來 KnowledgeDoc graph seed 可只使用 reviewed `attack_types` 與 `rule_ids`，並且必須先與明確提供的 `DetectionRule` objects 交叉驗證。

本文不會從敘述建立 graph edge；automatic Graph RAG Retrieval 與 vector-to-graph expansion 不在本 batch 實作。
