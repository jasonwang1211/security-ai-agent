---
schema_version: v2.2-live1
doc_id: report.http2_dos_mitigation
doc_type: report_explainer
title: HTTP/2 DoS 防禦緩解指引
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
  - DoS
  - Denial of Service
  - Resource Exhaustion
  - mitigation
  - rate limit
  - timeout
  - reverse proxy
  - 緩解
tags:
  - resource_exhaustion
  - mitigation
  - report_explainer
references:
  - id: internal_no_detection_rule
    type: internal_provenance
    source: detections/blue_team/
    note: Defensive mitigation guidance only; no deterministic detection rule or enforcement action is created.
  - id: rfc_9113_http2
    type: external_defensive_reference
    source: RFC 9113 - HTTP/2
    url: https://www.rfc-editor.org/rfc/rfc9113
  - id: owasp_dos_cheat_sheet
    type: external_defensive_reference
    source: OWASP Denial of Service Cheat Sheet
    url: https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html
limitations:
  - Retrieval-only advisory document; carries no attack_types or rule_ids and creates no graph seed.
  - Mitigation guidance is defensive and advisory; the system performs no real enforcement.
  - BLOCK, MONITOR, and ALLOW are simulated decisions only.
---

# HTTP/2 DoS 防禦緩解指引（defensive mitigation）

## 目的

本文件提供針對 HTTP/2 Resource Exhaustion / DoS 風險的**防禦性**緩解（mitigation）方向，供藍隊規劃與人工決策參考。所有項目皆為防禦建議；本系統**不會**自動套用、也不會執行任何真實強制動作。

## 防禦緩解方向

- **修補 / 升級（patch / upgrade）**：將 HTTP/2 終結點（reverse proxy、application server、函式庫）更新到已修補的版本，是降低已知弱點風險最直接的方式。
- **限制並行 stream（limit concurrent streams）**：設定單一連線可同時開啟的 stream 上限（例如 SETTINGS_MAX_CONCURRENT_STREAMS），降低單連線資源放大。
- **調整 header / body 限制**：在合理範圍內限制標頭大小、HPACK 動態表與請求主體大小，避免不成比例的解析成本。
- **逾時設定（timeouts）**：為閒置連線、慢速請求與 stream 設定適當 timeout，回收長時間佔用資源的連線。
- **速率限制（rate limiting）**：對連線建立速率、每連線 stream 速率與請求速率設限。
- **reverse proxy / CDN / WAF 政策**：在前端代理層套用連線與資源政策，吸收與整形（shape）異常流量。
- **記憶體與每連線監控（memory & per-connection monitoring）**：監控記憶體壓力、每連線資源用量與 stream/連線指標，及早告警。

## 運用方式

- 上述方向需依資產實際架構、容量與業務需求，由人工評估後規劃。
- 任何變更都應先在非生產環境驗證，並保留回復方案。
- 緩解措施屬於組織自身防禦範疇；本文件不涉及對任何第三方系統的操作。

## 安全邊界 (Safety Boundary)

- RAG / AI 解釋僅供參考（advisory only），屬於分析師輔助情境，不是最終判決。
- 本內容不會覆蓋（override）確定性的 Risk Level 或 Decision；偵測與決策仍由 rule-based、deterministic 邏輯產生。
- BLOCK / MONITOR / ALLOW 皆為模擬決策（simulated），僅用於展示與教學。
- 系統未執行任何真實的 firewall / WAF / EDR / 帳號 / 監控強制動作（no real enforcement）。
- 在將任何草稿（draft）提升或正式運用（operational use）前，必須先經過人工審查（human review required）。
- 本文件不提供任何攻擊 PoC、利用步驟或流量產生（traffic generation）指引，僅供藍隊防禦判讀與教育用途。
