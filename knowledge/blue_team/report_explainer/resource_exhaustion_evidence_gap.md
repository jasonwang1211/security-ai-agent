---
schema_version: v2.2-live1
doc_id: report.resource_exhaustion_evidence_gap
doc_type: report_explainer
title: Resource Exhaustion 證據缺口分析
language: zh-TW
status: live
review_status: approved_for_runtime_promotion
audience:
  - student_analyst
  - taiwan_academic_blue_team
applies_to:
  - Security Triage Report
  - Resource Exhaustion
  - Evidence Gap
related_tools:
  - report_followup
  - rag_v2
attack_types: []
finding_types: []
evidence_types:
  - resource_metric
  - server_log
  - telemetry
severity: []
decision_labels: []
rule_ids: []
mitre_techniques:
  - T1499
keywords:
  - Resource Exhaustion
  - evidence gap
  - 證據缺口
  - memory pressure
  - stream
  - flow control
  - HTTP/2
  - DoS
tags:
  - resource_exhaustion
  - evidence_gap
  - report_explainer
references:
  - id: internal_no_detection_rule
    type: internal_provenance
    source: detections/blue_team/
    note: No deterministic detection rule maps to resource exhaustion; this is retrieval-only advisory context.
  - id: internal_evidence_gap_analyzer
    type: internal_provenance
    source: modules/ai_advisory/evidence_gap.py
    note: Aligns with the deterministic Evidence Gap Analyzer's confirmed / missing / checks / unsafe structure.
limitations:
  - Retrieval-only advisory document; carries no attack_types or rule_ids and creates no graph seed.
  - Evidence-gap guidance is advisory; it does not change Risk Level or Decision.
  - BLOCK, MONITOR, and ALLOW are simulated decisions only.
---

# Resource Exhaustion 證據缺口分析（evidence gap）

## 目的

本文件說明在判讀 Resource Exhaustion 疑似事件時，**通常缺少哪些證據（missing evidence）**，以及哪些假設是不安全的（unsafe assumptions）。目的是幫助分析師在資料不足時保持保守判讀，避免過度宣稱。

## 為什麼會有證據缺口

Resource Exhaustion 的判定高度依賴資產層級的遙測（telemetry）。在 SOC 端，初期常只看到「資源成本看似異常」的間接訊號，而缺少能證明因果與影響的直接證據。

## 常見缺少的證據（missing evidence）

- **記憶體壓力（memory pressure）**：事件期間伺服器 / proxy 的記憶體使用與回收（GC / OOM）情形。
- **stream 數量（stream count）**：單一連線的並行 stream 數與整體 stream 建立／重置速率。
- **連線存活時間（connection duration）**：異常長壽連線或大量短連線的分佈。
- **flow-control 停滯（flow-control stall）**：HTTP/2 flow-control 視窗是否長期為 0 或停滯。
- **伺服器 / proxy 日誌（server/proxy logs）**：reverse proxy、load balancer 與 application server 的存取與錯誤紀錄。
- **process metrics**：每連線 / 每 worker 的 CPU、執行緒、file descriptor 與資源用量。

## 建議補齊的檢查

- 比對資源成本與入站請求量，量化是否存在不對稱（asymmetric cost）。
- 收集事件時間區間前後的指標基線（baseline）以利對照。
- 確認連線是否集中於少數來源或少數連線。
- 連結資產版本與設定，作為 CVE 背景情報的判讀輸入（非利用證明）。

## 不安全的假設（unsafe assumptions）

- 不要假設「資源尖峰＝蓄意攻擊」；可能是正常負載、批次作業或壓力測試。
- 不要假設「看到疑似模式＝服務已被癱瘓」；可用性影響需以遙測佐證。
- 不要假設「命中某 CVE 描述＝此資產已被利用」。
- 不要把模擬決策（simulated decision）當成已執行的真實處置。

## 安全邊界 (Safety Boundary)

- RAG / AI 解釋僅供參考（advisory only），屬於分析師輔助情境，不是最終判決。
- 本內容不會覆蓋（override）確定性的 Risk Level 或 Decision；偵測與決策仍由 rule-based、deterministic 邏輯產生。
- BLOCK / MONITOR / ALLOW 皆為模擬決策（simulated），僅用於展示與教學。
- 系統未執行任何真實的 firewall / WAF / EDR / 帳號 / 監控強制動作（no real enforcement）。
- 在將任何草稿（draft）提升或正式運用（operational use）前，必須先經過人工審查（human review required）。
- 本文件不提供任何攻擊 PoC、利用步驟或流量產生（traffic generation）指引，僅供藍隊防禦判讀與教育用途。
