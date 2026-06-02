---
schema_version: v2.2-live1
doc_id: report.path_traversal_explainer
doc_type: report_explainer
title: Path Traversal 攻擊判讀
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
  - Path Traversal
finding_types: []
evidence_types:
  - payload_indicator
  - rule_match
severity:
  - HIGH
decision_labels:
  - BLOCK
rule_ids:
  - PATH-001
mitre_techniques: []
evidence_ids: []
finding_ids: []
incident_ids: []
keywords:
  - Path Traversal
  - directory traversal
  - PATH-001
  - file path
  - 路徑穿越
  - 檔案路徑
tags:
  - web_attack
  - detection_rule
  - attack_type
references:
  - id: local_detection_path_001
    type: internal_provenance
    source: detections/blue_team/path_traversal/path_traversal_basic.yml
    note: Verified local YAML detection rule PATH-001 with HIGH severity and Path Traversal attack type.
  - id: local_triage_policy
    type: internal_provenance
    source: modules/triage_policy.py
    note: Maps Path Traversal to HIGH risk and HIGH to simulated BLOCK.
  - id: owasp_path_traversal_reference
    type: external_defensive_reference
    source: OWASP Path Traversal
    url: https://owasp.org/www-community/attacks/Path_Traversal
limitations:
  - Generic KB document uses type-level metadata only.
  - Narrative prose must not create graph edges automatically.
  - BLOCK, MONITOR, and ALLOW are simulated decisions only.
---

# Path Traversal 攻擊判讀

## 目的

本文件說明 Path Traversal 的防禦判讀方式，協助學生分析師理解檔案路徑相關告警與 verified rule ID `PATH-001`。內容用於教育與報告解釋，不代表已確認檔案外洩。

## 適用情境

- 請求路徑、參數或 payload 命中 `PATH-001`。
- URL 或輸入中出現嘗試跳脫目錄、讀取系統檔案或存取非預期路徑的跡象。
- 分析師需要分辨可疑測試字串與實際可利用風險。

## 重要判讀

Path Traversal 通常嘗試利用路徑組合或檔案讀取功能，存取應用程式預期目錄以外的資源。rule match 只代表輸入有路徑穿越特徵；是否成功讀取檔案，需要觀察 response、狀態碼、檔案內容、應用程式日誌與伺服器權限。

## 報告欄位對應

| 欄位 | 判讀方式 |
|---|---|
| finding_types | 不適用；此文件以 attack type 與 rule ID 為主。 |
| evidence_types | 可使用 `payload_indicator` 或 `rule_match` 描述 type-level evidence。 |
| Rule ID | 使用已驗證的 `PATH-001`。 |
| Risk Level | 依報告 deterministic 結果解讀，不在本文中重算。 |
| Decision | 目前 deterministic policy 對 `PATH-001` 的典型決策為 `BLOCK`；這仍是模擬決策，不是真實檔案系統或 WAF 控制。 |

## 藍隊分析步驟

1. 檢查 payload 是否包含目錄跳脫、編碼路徑或敏感檔名跡象。
2. 查看 response 是否包含檔案內容、錯誤訊息或異常下載行為。
3. 檢查應用程式是否有檔案讀取、下載、模板或靜態資源服務功能。
4. 比對是否為掃描器、課程測試或安全驗證活動。
5. 若無法確認成功讀取，應寫成疑似嘗試或需要複核。

## 模擬決策說明

`ALLOW`、`MONITOR`、`BLOCK` 均為模擬決策。對目前的 `PATH-001` deterministic policy，metadata 保留 `BLOCK`；這不代表已修改 WAF、路由、檔案權限或伺服器設定。

## 常見誤判與限制

- 正常檔名、URL 編碼或測試參數可能看起來像路徑穿越。
- 日誌可能只記錄 request，無法證明 response 中含有敏感檔案。
- RAG、LLM 與 graph-backed explanation 不能宣告檔案外洩或覆蓋 Risk Level / Decision。

## Graph RAG 準備註記

未來 KnowledgeDoc graph seed 可只使用 reviewed `attack_types` 與 `rule_ids`，並且必須先與明確提供的 `DetectionRule` objects 交叉驗證。

本文敘述不會建立 graph edge；automatic Graph RAG Retrieval 與 vector-to-graph expansion 不在本 batch 實作。
