---
schema_version: v2.2-live1
doc_id: report.monitor_decision_investigation
doc_type: report_explainer
title: MONITOR 模擬決策與調查路徑
language: zh-TW
status: live
review_status: approved_for_runtime_promotion
audience:
  - student_analyst
  - taiwan_academic_blue_team
applies_to:
  - Security Triage Report
  - Decision
  - Authentication Investigation
related_tools:
  - report_followup
  - graph_explainers
  - rag_v2
attack_types: []
finding_types:
  - possible_account_compromise
evidence_types:
  - failed_count
  - time_window
  - success_after_failures
severity:
  - HIGH
decision_labels:
  - MONITOR
rule_ids: []
mitre_techniques: []
evidence_ids: []
finding_ids: []
incident_ids: []
keywords:
  - MONITOR
  - simulated decision
  - analyst review
  - authentication investigation
  - 模擬決策
  - 監控與複核
tags:
  - simulated_decision
  - authentication
  - analyst_workflow
references:
  - id: local_triage_policy
    type: internal_provenance
    source: modules/triage_policy.py
    note: Defines deterministic risk-to-decision mapping where MEDIUM maps to MONITOR and HIGH maps to BLOCK for payload attack types.
  - id: local_scenario_a_correlator
    type: internal_provenance
    source: modules/evidence_correlator.py
    note: Defines Scenario A possible_account_compromise as HIGH with simulated MONITOR.
  - id: local_report_decision_boundary
    type: internal_provenance
    source: knowledge/blue_team/report_explainer/risk_level_decision.md
    note: Existing live report explainer separates Risk Level from simulated Decision.
  - id: owasp_authentication_cheat_sheet
    type: external_defensive_reference
    source: OWASP Authentication Cheat Sheet
    url: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
limitations:
  - Generic KB document uses type-level metadata only.
  - evidence_ids, finding_ids, and incident_ids stay empty unless a separate scenario-specific document is reviewed.
  - Narrative prose must not create graph edges automatically.
  - BLOCK, MONITOR, and ALLOW are simulated decisions only.
---

# MONITOR 模擬決策與調查路徑

## 目的

本文件說明 Security Triage Report 中 `MONITOR` 的防禦意義。它不是被動忽略，也不是系統已經部署真實監控，而是訓練情境中的模擬決策，表示需要保留證據並由分析師複核。

## 適用情境

- 報告的 Decision 為 `MONITOR`。
- authentication finding concept 顯示可疑但尚未足以宣告 confirmed compromise。
- 學生分析師需要把 MONITOR 轉成合理的調查清單與保守結論。

## 重要判讀

`MONITOR` 通常表示目前訊號值得追蹤，但仍需要更多上下文。對 `possible_account_compromise` 來說，HIGH risk 可以與 MONITOR 同時存在：HIGH 表示風險優先度高，MONITOR 表示尚需人工確認與證據保全，不代表已執行封鎖或確認入侵。

## 報告欄位對應

| 欄位 | 判讀方式 |
|---|---|
| finding_types | 可包含 `possible_account_compromise` 等需要複核的 finding concept。 |
| evidence_types | 可包含 `failed_count`、`time_window`、`success_after_failures`。 |
| instance IDs | 通用文件不綁定固定 evidence、finding 或 incident ID；scenario-specific 文件才可加入。 |
| Rule ID | 不適用；此文件不綁定特定 detection rule。 |
| Risk Level | 不由本文件重新計算。 |
| Decision | `MONITOR` 是模擬決策，不是真實 monitoring deployment。 |

## 藍隊分析步驟

1. 確認 MONITOR 來自報告中的 deterministic Decision，而不是 LLM 自行更改。
2. 保留相關日誌、時間窗、帳號、來源 IP、目標端點與 session 記錄。
3. 檢查登入後行為是否支援升級調查，例如敏感資料存取或權限異動。
4. 查核誤判可能性，例如使用者輸錯密碼、VPN、維運測試或自動化客戶端。
5. 將輸出寫成調查建議，不寫成已經封鎖、已經監控部署或已經確認攻擊。

## 模擬決策說明

在本專案中，`ALLOW`、`MONITOR`、`BLOCK` 都是訓練用的模擬決策。

- `ALLOW` 是模擬允許或不採取阻擋。
- `MONITOR` 是模擬監控與複核路徑。
- `BLOCK` 是模擬阻擋建議，不代表真實控制已生效。

## 常見誤判與限制

- MONITOR 不應被寫成「系統已開始監控」。
- MONITOR 不代表風險低；它可能是高風險但需要人工確認。
- RAG、LLM 與 graph-backed explanation 不能覆蓋 deterministic final Risk Level 或 Decision。

## Graph RAG 準備註記

本文件提供 curated knowledge source context，不建立 KnowledgeDoc graph-seed edge。`finding_types` 與 `evidence_types` 只作為 retrieval / explanation metadata。

本文敘述不會建立 graph edge；`MONITOR` 只保留在 `decision_labels` 作為 retrieval / explanation metadata。
