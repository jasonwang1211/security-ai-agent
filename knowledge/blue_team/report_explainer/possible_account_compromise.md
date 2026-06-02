---
schema_version: v2.2-live1
doc_id: report.possible_account_compromise
doc_type: report_explainer
title: 帳號可能遭入侵的判讀
language: zh-TW
status: live
review_status: approved_for_runtime_promotion
audience:
  - student_analyst
  - taiwan_academic_blue_team
applies_to:
  - Security Triage Report
  - Finding
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
  - possible_account_compromise
  - authentication
  - success_after_failures
  - suspicious login
  - 帳號可能遭入侵
  - 登入失敗後成功
  - 身分驗證調查
tags:
  - authentication
  - finding_type
  - simulated_decision
references:
  - id: local_scenario_a_correlator
    type: internal_provenance
    source: modules/evidence_correlator.py
    note: Defines possible_account_compromise from repeated authentication failures followed by success, with HIGH risk and simulated MONITOR.
  - id: local_scenario_a_integration_test
    type: internal_provenance
    source: tests/test_scenario_a_integration.py
    note: Verifies Scenario A mixed authentication flow, report follow-up behavior, and unchanged MONITOR decision.
  - id: local_report_decision_boundary
    type: internal_provenance
    source: knowledge/blue_team/report_explainer/risk_level_decision.md
    note: Existing live report explainer states Risk Level and Decision are deterministic and simulated.
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

# 帳號可能遭入侵的判讀

## 目的

本文件協助學生分析師理解 `possible_account_compromise` 這類 finding concept 的藍隊判讀方式。它用於解釋可疑的身分驗證序列，不用來宣告帳號已經確定遭入侵。

## 適用情境

- Security Triage Report 出現多次登入失敗、時間區間、或登入失敗後成功等 type-level evidence 時。
- 報告中的 finding type 指向 `possible_account_compromise`，但仍需要人工複核使用者、來源、目標與後續活動。
- 通用 KB 文件只使用 `finding_types` 與 `evidence_types`；不綁定任何固定 evidence、finding 或 incident instance。

## 重要判讀

`possible_account_compromise` 表示報告觀察到可疑的帳號使用模式，例如短時間內多次失敗後又出現成功登入。這是需要重視的調查訊號，但不等於已確認攻擊者取得帳號。分析師仍需確認成功登入是否由本人操作、是否有 MFA 訊號、是否有異常裝置或登入後敏感操作。

## 報告欄位對應

| 欄位 | 判讀方式 |
|---|---|
| finding_types | 使用 `possible_account_compromise` 表示可疑帳號使用 finding concept。 |
| evidence_types | 常見包括 `failed_count`、`time_window`、`success_after_failures`。 |
| instance IDs | 通用文件不綁定固定 evidence、finding 或 incident ID；scenario-specific 文件才可加入。 |
| Rule ID | 不適用；此文件不綁定特定 detection rule。 |
| Risk Level | HIGH 可表示此序列值得優先複核，但不自動等於 confirmed compromise。 |
| Decision | MONITOR 是模擬決策，代表保留證據、追蹤與人工複核，不是真實監控部署。 |

## 藍隊分析步驟

1. 確認報告中已存在的穩定 ID 與 type-level evidence，不自行新增未證實 ID。
2. 檢查失敗與成功登入的時間序列、來源 IP、帳號、目標端點與使用者代理資訊。
3. 比對是否有使用者輸錯密碼、密碼重設、VPN 切換、校園網路 NAT 或自動化測試造成的誤判。
4. 檢查成功登入後是否出現敏感操作、權限變更、異常資料存取或新裝置註冊。
5. 將結論寫成「可疑且需要複核」或「證據不足」，避免直接宣告帳號已遭入侵。

## 模擬決策說明

在本專案中，`ALLOW`、`MONITOR`、`BLOCK` 都是訓練用的模擬決策。

- `ALLOW` 表示目前可見訊號不足以支持阻擋建議，但不代表環境絕對安全。
- `MONITOR` 表示需要保留證據、持續觀察或由分析師複核。
- `BLOCK` 表示報告在訓練情境中建議阻擋，但不代表系統已經真的操作防火牆、WAF、EDR、SIEM、SOAR、雲端策略或身分平台。

## 常見誤判與限制

- 使用者連續輸錯密碼後成功登入，可能是正常錯誤修正。
- 校園或公司 NAT、VPN、行動網路切換可能讓來源判讀變得模糊。
- RAG、LLM 與 graph-backed explanation 只能提供解釋與輔助脈絡，不能覆蓋 deterministic final Risk Level 或 Decision。

## Graph RAG 準備註記

本文件提供 curated knowledge source context，不建立 KnowledgeDoc graph-seed edge。`finding_types` 與 `evidence_types` 只作為 retrieval / explanation metadata。

本文敘述、範例、段落標題或自然語言說明都不會建立 graph edge。
