---
schema_version: v2.2-live1
doc_id: report.command_injection_explainer
doc_type: report_explainer
title: Command Injection 攻擊判讀
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
  - Command Injection
finding_types: []
evidence_types:
  - payload_indicator
  - rule_match
severity:
  - HIGH
decision_labels:
  - BLOCK
rule_ids:
  - CMD-001
mitre_techniques: []
evidence_ids: []
finding_ids: []
incident_ids: []
keywords:
  - Command Injection
  - CMD-001
  - command execution
  - shell metacharacter
  - 命令注入
  - 指令執行
tags:
  - web_attack
  - detection_rule
  - attack_type
references:
  - id: local_detection_cmd_001
    type: internal_provenance
    source: detections/blue_team/command_injection/command_injection_basic.yml
    note: Verified local YAML detection rule CMD-001 with HIGH severity and Command Injection attack type.
  - id: local_triage_policy
    type: internal_provenance
    source: modules/triage_policy.py
    note: Maps Command Injection to HIGH risk and HIGH to simulated BLOCK.
  - id: owasp_os_command_injection_defense_cheat_sheet
    type: external_defensive_reference
    source: OWASP OS Command Injection Defense Cheat Sheet
    url: https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html
limitations:
  - Generic KB document uses type-level metadata only.
  - Narrative prose must not create graph edges automatically.
  - BLOCK, MONITOR, and ALLOW are simulated decisions only.
---

# Command Injection 攻擊判讀

## 目的

本文件說明 Command Injection 的防禦判讀方式，協助學生分析師理解 verified rule ID `CMD-001` 與高風險命令執行跡象。內容只用於藍隊教育與報告解釋，不提供攻擊步驟。

## 適用情境

- payload 或 request 命中 `CMD-001`。
- 輸入中出現 shell metacharacter、命令串接、可疑系統指令或執行環境跡象。
- 報告的 Decision 可能為 `BLOCK`，但需要清楚說明這只是模擬決策。

## 重要判讀

Command Injection 風險通常高於一般可疑輸入，因為成功利用可能讓攻擊者在伺服器端執行指令。rule match 仍只代表可疑特徵；是否成功執行，需檢查應用程式回應、系統日誌、程序建立、檔案變更與後續連線。

## 報告欄位對應

| 欄位 | 判讀方式 |
|---|---|
| finding_types | 不適用；此文件以 attack type 與 rule ID 為主。 |
| evidence_types | 可使用 `payload_indicator` 或 `rule_match` 描述 type-level evidence。 |
| Rule ID | 使用已驗證的 `CMD-001`。 |
| Risk Level | 通常可視為高優先度調查，但不由本文重算。 |
| Decision | `BLOCK` 是模擬阻擋建議，不是真實封鎖或主機控制。 |

## 藍隊分析步驟

1. 檢查 payload 是否包含命令串接符號、shell 關鍵字、可疑參數或編碼。
2. 查看應用程式是否有把使用者輸入傳入 shell、系統工具或腳本的功能。
3. 檢查 response、程序紀錄、系統日誌、檔案寫入與對外連線。
4. 比對是否為安全測試、課程實驗或掃描器造成的 payload。
5. 在無執行證據時，描述為「疑似 Command Injection 嘗試」，不要宣告主機已被控制。

## 模擬決策說明

`ALLOW`、`MONITOR`、`BLOCK` 都是訓練用的模擬決策。`BLOCK` 不代表系統已修改防火牆、WAF、EDR、容器政策、主機防護或雲端控制。

## 常見誤判與限制

- 日誌中的特殊符號可能來自正常參數、測試資料或編碼。
- 只看 request 不足以證明命令已執行。
- RAG、LLM 與 graph-backed explanation 不能宣告成功入侵、不能執行工具，也不能覆蓋 Risk Level 或 Decision。

## Graph RAG 準備註記

未來 KnowledgeDoc graph seed 可只使用 reviewed `attack_types` 與 `rule_ids`，並且必須先與明確提供的 `DetectionRule` objects 交叉驗證。

本文敘述、範例或標題不會建立 graph edge；automatic Graph RAG Retrieval 與 vector-to-graph expansion 不在本 batch 實作。
