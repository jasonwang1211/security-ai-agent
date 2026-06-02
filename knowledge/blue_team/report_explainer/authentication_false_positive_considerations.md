---
schema_version: v2.2-live1
doc_id: report.authentication_false_positive_considerations
doc_type: report_explainer
title: 身分驗證誤判考量
language: zh-TW
status: live
review_status: approved_for_runtime_promotion
audience:
  - student_analyst
  - taiwan_academic_blue_team
applies_to:
  - Security Triage Report
  - Authentication Investigation
  - False Positive Review
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
  - LOW
  - HIGH
decision_labels:
  - ALLOW
  - MONITOR
rule_ids: []
mitre_techniques: []
evidence_ids: []
finding_ids: []
incident_ids: []
keywords:
  - false positive
  - authentication
  - login failure
  - success_after_failures
  - 誤判
  - 身分驗證
  - 登入失敗
tags:
  - authentication
  - false_positive
  - analyst_review
references:
  - id: local_scenario_a_correlator
    type: internal_provenance
    source: modules/evidence_correlator.py
    note: Defines Scenario A correlation boundaries and does not treat suspicious login sequence as confirmed compromise.
  - id: local_report_decision_boundary
    type: internal_provenance
    source: knowledge/blue_team/report_explainer/risk_level_decision.md
    note: Existing live report explainer states HIGH does not always mean BLOCK and AI/RAG remain advisory.
  - id: local_scenario_a_integration_test
    type: internal_provenance
    source: tests/test_scenario_a_integration.py
    note: Verifies Scenario A remains HIGH with simulated MONITOR.
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

# 身分驗證誤判考量

## 目的

本文件整理 authentication 類事件的常見 false positive 來源，協助學生分析師在保守防禦與避免過度告警之間取得平衡。它不會降低或覆蓋報告中的 deterministic Risk Level 或 Decision。

## 適用情境

- 報告顯示多次登入失敗、登入失敗後成功，或 `possible_account_compromise` finding concept。
- 分析師需要判斷是否可能為正常使用者、系統行為或測試活動。
- 決策為 `ALLOW` 或 `MONITOR` 時，需要說明為何仍需或不需進一步複核。

## 重要判讀

誤判分析不是替可疑行為背書，而是補足證據脈絡。即使存在 false positive 可能，也應先保留原始證據並確認關鍵條件，例如同一帳號、同一來源、同一目標、時間窗、MFA 與登入後行為。

## 報告欄位對應

| 欄位 | 判讀方式 |
|---|---|
| finding_types | 以 `possible_account_compromise` 表示需要複核的 finding concept。 |
| evidence_types | 檢查 `failed_count`、`time_window`、`success_after_failures` 是否可能有正常解釋。 |
| instance IDs | 通用文件不綁定固定 evidence、finding 或 incident ID；scenario-specific 文件才可加入。 |
| Rule ID | 不適用；此文件不綁定特定 detection rule。 |
| Risk Level | 不由本文件重新計算或降級。 |
| Decision | ALLOW / MONITOR 均為模擬決策，不代表真實處置已發生。 |

## 藍隊分析步驟

1. 確認登入失敗是否集中在密碼變更、帳號解鎖或開學大量登入期間。
2. 檢查使用者是否可能在多裝置或 VPN 環境中重試。
3. 查看是否有舊密碼快取、郵件客戶端、同步服務或 API token 造成重複失敗。
4. 比對成功登入後是否缺乏異常行為，或是否有正常課務、行政、維運活動說明。
5. 若缺乏足夠證據，記錄為「可能誤判，需要更多資料」，不要宣告無風險。

## 模擬決策說明

在本專案中，`ALLOW`、`MONITOR`、`BLOCK` 都是訓練用的模擬決策。`ALLOW` 不代表絕對安全，`MONITOR` 不代表真實監控已部署，`BLOCK` 不代表真實封鎖已執行。

## 常見誤判與限制

- 使用者輸錯密碼後成功登入。
- 多人共用出口 IP 或校園 NAT。
- 合法弱點掃描、課程實驗或開發測試流量。
- RAG、LLM 或 graph-backed explanation 的說明不能取代原始證據與人工判斷，也不能覆蓋 Risk Level 或 Decision。

## Graph RAG 準備註記

本文件提供 curated knowledge source context，不建立 KnowledgeDoc graph-seed edge。`finding_types` 與 `evidence_types` 只作為 retrieval / explanation metadata。

本文所有誤判類型都是文字知識與 type-level metadata；prose 不會建立 graph edge。
