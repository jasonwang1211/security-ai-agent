---
schema_version: v2.2-live1
doc_id: report.cve_context_boundary
doc_type: report_explainer
title: CVE 背景情報的判讀邊界
language: zh-TW
status: live
review_status: approved_for_runtime_promotion
audience:
  - student_analyst
  - taiwan_academic_blue_team
applies_to:
  - Security Triage Report
  - CVE Context
  - Threat Intelligence
related_tools:
  - report_followup
  - rag_v2
attack_types: []
finding_types: []
evidence_types:
  - threat_intel
  - asset_context
severity: []
decision_labels: []
rule_ids: []
mitre_techniques: []
keywords:
  - CVE
  - CVE context
  - vulnerability
  - patch status
  - reachability
  - exposure
  - 弱點情報
tags:
  - cve_context
  - threat_intel
  - report_explainer
references:
  - id: internal_no_detection_rule
    type: internal_provenance
    source: detections/blue_team/
    note: CVE context is background intelligence only; no deterministic detection rule is derived from it here.
  - id: external_cve_program
    type: external_defensive_reference
    source: CVE Program (cve.org)
    url: https://www.cve.org/
limitations:
  - Retrieval-only advisory document; carries no attack_types or rule_ids and creates no graph seed.
  - CVE presence is not proof of exploitation; verdicts stay rule-based and deterministic.
  - BLOCK, MONITOR, and ALLOW are simulated decisions only.
---

# CVE 背景情報的判讀邊界（CVE context boundary）

## 目的

本文件說明在 SOC triage 系統中，CVE 情報應如何被使用。核心原則：**CVE 的存在是背景情報（background intelligence），不是當前資產已被利用（exploited）的證明**。

## 核心原則

看到某個 CVE 與某攻擊類型相關，只代表「此類軟體在某些版本／設定下可能存在弱點」。它**不**直接代表：

- 目前這台資產一定使用受影響的版本；
- 目前這台資產的設定一定處於可被利用狀態；
- 已經有人成功利用；或
- 事件中的行為一定就是該 CVE 的利用。

## 將 CVE 轉為可行動判讀所需的條件

要把 CVE 從「背景情報」推進到「需要處理的風險」，需要補齊資產層級事實：

- **資產版本（asset version）**：實際部署的元件與版本是否落在受影響範圍。
- **設定（configuration）**：相關功能是否啟用、是否處於易受影響的設定。
- **暴露面（exposure）**：服務是否對外開放、可被誰存取。
- **修補狀態（patch status）**：是否已套用修補或緩解（mitigation）。
- **可達性（reachability）**：攻擊路徑在網路與權限上是否真的可達。
- **觀察到的行為（observed behavior）**：是否有與利用一致的實際遙測或日誌。

只有在這些條件被人工確認後，CVE 才應影響後續處置優先度——而且仍不改變本系統的 deterministic 判定。

## 在本系統中的定位

- CVE context 屬於分析師參考情境（analyst context），與 similar cases、graph 同層級。
- 它**不會**被本系統當成偵測規則，也不會自動產生 finding 或 incident。
- 任何「此資產受 CVE 影響」的結論都必須由人工依資產事實確認。

## 安全邊界 (Safety Boundary)

- RAG / AI 解釋僅供參考（advisory only），屬於分析師輔助情境，不是最終判決。
- 本內容不會覆蓋（override）確定性的 Risk Level 或 Decision；偵測與決策仍由 rule-based、deterministic 邏輯產生。
- BLOCK / MONITOR / ALLOW 皆為模擬決策（simulated），僅用於展示與教學。
- 系統未執行任何真實的 firewall / WAF / EDR / 帳號 / 監控強制動作（no real enforcement）。
- 在將任何草稿（draft）提升或正式運用（operational use）前，必須先經過人工審查（human review required）。
- 本文件不提供任何攻擊 PoC、利用步驟或流量產生（traffic generation）指引，僅供藍隊防禦判讀與教育用途。
- CVE 背景情報不得被當成目前資產已存在弱點或已遭利用的證明。
