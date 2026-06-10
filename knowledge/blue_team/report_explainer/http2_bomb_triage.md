---
schema_version: v2.2-live1
doc_id: report.http2_bomb_triage
doc_type: report_explainer
title: HTTP/2 Bomb 疑似事件安全分流
language: zh-TW
status: live
review_status: approved_for_runtime_promotion
audience:
  - student_analyst
  - taiwan_academic_blue_team
applies_to:
  - Security Triage Report
  - Resource Exhaustion
  - Denial of Service
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
  - HTTP/2
  - HTTP/2 Bomb
  - Resource Exhaustion
  - Denial of Service
  - DoS
  - stream
  - triage
  - 分流
tags:
  - resource_exhaustion
  - triage
  - report_explainer
references:
  - id: internal_no_detection_rule
    type: internal_provenance
    source: detections/blue_team/
    note: No deterministic detection rule maps to HTTP/2 Bomb-style events; this is retrieval-only advisory context.
  - id: rfc_9113_http2
    type: external_defensive_reference
    source: RFC 9113 - HTTP/2
    url: https://www.rfc-editor.org/rfc/rfc9113
limitations:
  - Retrieval-only advisory document; carries no attack_types or rule_ids and creates no graph seed.
  - Provides defensive triage workflow only; no exploit or traffic-generation steps.
  - BLOCK, MONITOR, and ALLOW are simulated decisions only.
---

# HTTP/2 Bomb 疑似事件的安全分流（safe triage）

## 目的

本文件說明如何以**防禦、可重複、安全**的方式分流（triage）疑似 HTTP/2 Bomb 風格的 Resource Exhaustion 事件。重點完全放在 logs、telemetry 與 metrics 的判讀；本文件**不包含任何可運作的攻擊步驟、利用程式或流量產生方法**。

## 分流原則

HTTP/2 Bomb 風格事件的核心特徵是「以少量入站請求換取高伺服器資源成本」。分流時，分析師要回答的是「資產的資源狀態是否異常」，而不是「如何重現攻擊」。

## 安全分流步驟（logs / telemetry / metrics）

1. 確認資產是否啟用 HTTP/2，以及由哪一層（reverse proxy、CDN、application server）終結（terminate）連線。
2. 觀察資源指標趨勢：CPU、記憶體、連線數、每連線並行 stream 數、stream reset 速率、flow-control 視窗停滯。
3. 對照入站請求量：若資源成本相對請求量明顯偏高，記錄此不對稱現象。
4. 檢視伺服器 / proxy 的存取與錯誤日誌，找出連線是否集中於少數來源或少數連線。
5. 保存（preserve）相關時間區間的指標與日誌，作為人工複核的證據。
6. 對照部署版本與設定，連結對應的 CVE 背景情報（但不視為已被利用的證明）。
7. 將事件升級（escalate）給人工分析師審查，由人工決定後續處理。

## 可以下的結論

- 「在某時間區間觀察到資源成本與入站流量不對稱，符合 Resource Exhaustion 疑似模式。」
- 「建議保存指標與日誌、檢查資產版本／設定、並進行人工複核。」

## 不能下的結論

- 不能僅憑指標尖峰宣稱「確定遭受 HTTP/2 Bomb 攻擊」或「服務已被癱瘓」。
- 不能將正常高負載、壓力測試或設定錯誤直接判定為惡意攻擊。
- 不能假設特定 CVE 一定適用於此資產（見 CVE context boundary 文件）。

## 安全邊界 (Safety Boundary)

- RAG / AI 解釋僅供參考（advisory only），屬於分析師輔助情境，不是最終判決。
- 本內容不會覆蓋（override）確定性的 Risk Level 或 Decision；偵測與決策仍由 rule-based、deterministic 邏輯產生。
- BLOCK / MONITOR / ALLOW 皆為模擬決策（simulated），僅用於展示與教學。
- 系統未執行任何真實的 firewall / WAF / EDR / 帳號 / 監控強制動作（no real enforcement）。
- 在將任何草稿（draft）提升或正式運用（operational use）前，必須先經過人工審查（human review required）。
- 本文件不提供任何攻擊 PoC、利用步驟或流量產生（traffic generation）指引，僅供藍隊防禦判讀與教育用途。
