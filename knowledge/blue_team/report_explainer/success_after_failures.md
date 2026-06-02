---
schema_version: v2.2-live1
doc_id: report.success_after_failures
doc_type: report_explainer
title: 登入失敗後成功的證據判讀
language: zh-TW
status: live
review_status: approved_for_runtime_promotion
audience:
  - student_analyst
  - taiwan_academic_blue_team
applies_to:
  - Security Triage Report
  - Evidence
  - Authentication Investigation
related_tools:
  - report_followup
  - graph_explainers
  - rag_v2
attack_types: []
finding_types:
  - possible_account_compromise
evidence_types:
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
  - success_after_failures
  - authentication sequence
  - failed login
  - successful login
  - 登入失敗後成功
  - 身分驗證序列
tags:
  - authentication
  - evidence_type
  - investigation
references:
  - id: local_scenario_a_correlator
    type: internal_provenance
    source: modules/evidence_correlator.py
    note: Defines success_after_failures as the successful authentication evidence after repeated failures.
  - id: local_scenario_a_demo_log
    type: internal_provenance
    source: demo_logs/scenario_a_mixed_auth.log
    note: Contains the mixed authentication log used by Scenario A integration coverage.
  - id: local_scenario_a_integration_test
    type: internal_provenance
    source: tests/test_scenario_a_integration.py
    note: Verifies success_after_failures evidence in the Scenario A report flow.
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

# 登入失敗後成功的證據判讀

## 目的

本文件說明 `success_after_failures` 這類 evidence type 的防禦意義。它幫助分析師理解為什麼登入失敗後成功值得調查，同時避免把可疑序列直接寫成確認入侵。

## 適用情境

- 報告指出同一帳號、來源、目標或時間窗內，先出現多次登入失敗，再出現成功登入。
- 分析師需要判斷這是正常使用者行為、誤報，或可能的帳號濫用。
- 通用 KB 文件只使用 type-level metadata，不綁定固定 evidence、finding 或 incident instance。

## 重要判讀

登入失敗後成功是高價值調查訊號，因為它可能代表猜測密碼、credential stuffing、暴力嘗試後終於登入成功，或使用者自己多次輸錯後成功登入。單一 evidence type 不能證明 compromise；需要結合時間、來源、帳號、MFA、裝置、地理位置與登入後行為。

## 報告欄位對應

| 欄位 | 判讀方式 |
|---|---|
| finding_types | 常與 `possible_account_compromise` 搭配判讀。 |
| evidence_types | 使用 `success_after_failures` 表示登入失敗後成功的 type-level evidence。 |
| instance IDs | 通用文件不綁定固定 evidence、finding 或 incident ID；scenario-specific 文件才可加入。 |
| Rule ID | 不適用；此文件不綁定特定 detection rule。 |
| Risk Level | 可提高調查優先度，但不得重新計算或覆蓋報告風險。 |
| Decision | 通常支援 MONITOR 類型的模擬複核決策。 |

## 藍隊分析步驟

1. 確認成功登入是否真的發生在多次失敗之後。
2. 檢查失敗與成功事件是否屬於同一使用者、來源、裝置或目標服務。
3. 查核是否存在 MFA 成功、MFA 失敗、裝置註冊、密碼變更或 session 建立紀錄。
4. 比對使用者工作時間、校園網路環境、VPN 出入口與已知維運活動。
5. 若證據不足，應標示為需要複核，而不是宣告帳號已遭入侵。

## 模擬決策說明

在本專案中，`ALLOW`、`MONITOR`、`BLOCK` 都是訓練用的模擬決策。

- `MONITOR` 表示此 evidence type 需要追蹤與人工複核。
- `BLOCK` 若出現在其他情境，也只是訓練報告的模擬建議。
- 本文件不代表系統已部署真實監控、封鎖或身分平台控制。

## 常見誤判與限制

- 使用者忘記密碼或鍵盤輸入法切換可能造成多次失敗。
- 自動同步、行動郵件客戶端或舊憑證快取可能造成重複失敗。
- RAG、LLM、graph-backed explanation 都不能把 evidence type 升級成已確認 compromise，也不能覆蓋 deterministic Risk Level 或 Decision。

## Graph RAG 準備註記

本文件提供 curated knowledge source context，不建立 KnowledgeDoc graph-seed edge。`finding_types` 與 `evidence_types` 只作為 retrieval / explanation metadata。

本文不會因提到 `success_after_failures` 而建立 evidence node 或 graph edge。
