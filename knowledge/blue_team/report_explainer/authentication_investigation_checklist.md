---
schema_version: v2.2-live1
doc_id: report.authentication_investigation_checklist
doc_type: report_explainer
title: 身分驗證事件調查清單
language: zh-TW
status: live
review_status: approved_for_runtime_promotion
audience:
  - student_analyst
  - taiwan_academic_blue_team
applies_to:
  - Security Triage Report
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
  - authentication checklist
  - login investigation
  - possible_account_compromise
  - 身分驗證
  - 登入調查
  - 調查清單
tags:
  - authentication
  - checklist
  - analyst_workflow
references:
  - id: local_scenario_a_correlator
    type: internal_provenance
    source: modules/evidence_correlator.py
    note: Defines the authentication sequence correlation and evidence types used by Scenario A.
  - id: local_security_triage_report_doc
    type: internal_provenance
    source: knowledge/blue_team/report_explainer/security_triage_report.md
    note: Existing live report explainer describes report fields, evidence, findings, and simulation notice.
  - id: local_scenario_a_integration_test
    type: internal_provenance
    source: tests/test_scenario_a_integration.py
    note: Verifies Scenario A report flow and follow-up behavior.
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

# 身分驗證事件調查清單

## 目的

本文件提供身分驗證事件的防禦調查清單，協助學生分析師用一致方式檢查可疑登入序列。它是教育與報告解釋用 KB，不會執行任何工具。

## 適用情境

- 報告出現登入失敗、登入成功、時間窗或帳號可疑行為。
- finding concept 涉及 `possible_account_compromise`。
- 需要將 MONITOR 模擬決策轉成可操作的人工檢查項目。

## 重要判讀

身分驗證調查應優先確認事件是否同屬一個有意義的序列，而不是只看單一登入結果。登入失敗後成功可能重要，但仍需排除正常使用者行為、網路環境差異與自動化客戶端造成的誤判。

## 報告欄位對應

| 欄位 | 判讀方式 |
|---|---|
| finding_types | 以 `possible_account_compromise` 表示調查主題。 |
| evidence_types | 檢查 `failed_count`、`time_window`、`success_after_failures` 是否存在。 |
| instance IDs | 通用文件不綁定固定 evidence、finding 或 incident ID；scenario-specific 文件才可加入。 |
| Rule ID | 不適用；此文件不綁定特定 detection rule。 |
| Risk Level | 作為調查優先度參考，不在本文件中重算。 |
| Decision | MONITOR 表示模擬複核路徑，不是真實監控部署。 |

## 藍隊分析步驟

1. 確認時間窗：失敗事件與成功事件是否在合理時間範圍內相連。
2. 確認主體：帳號、來源 IP、裝置、瀏覽器、User-Agent、目標端點是否一致或可解釋。
3. 檢查 MFA：是否有 MFA challenge、成功、失敗、拒絕或繞過跡象。
4. 檢查登入後行為：是否有敏感資料存取、權限變更、token 建立或異常 API 呼叫。
5. 檢查誤判來源：VPN、NAT、密碼重設、同步服務、校園實驗或維運測試。
6. 保留原始日誌與報告中已存在的穩定 ID，不新增未證實 evidence。
7. 以「需要複核」或「證據不足」描述不確定處，避免過度斷言。

## 模擬決策說明

`ALLOW`、`MONITOR`、`BLOCK` 在本專案中都是模擬決策。`MONITOR` 不代表已啟用真實監控工具；它代表訓練報告建議分析師保留證據與追蹤。

## 常見誤判與限制

- 使用者密碼輸入錯誤後成功登入很常見。
- 校園網路、代理伺服器或 VPN 可能造成來源 IP 聚合。
- RAG、LLM 與 graph-backed explanation 只能提供說明，不能決定攻擊或覆蓋 Risk Level / Decision。

## Graph RAG 準備註記

本文件提供 curated knowledge source context，不建立 KnowledgeDoc graph-seed edge。`finding_types` 與 `evidence_types` 只作為 retrieval / explanation metadata。

本文清單、段落與 prose 不會建立 graph edge。
