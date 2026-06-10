---
schema_version: v2.2-live1
doc_id: report.http2_resource_exhaustion
doc_type: report_explainer
title: HTTP/2 Resource Exhaustion 判讀
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
  - Resource Exhaustion
  - Denial of Service
  - DoS
  - HPACK
  - flow control
  - stream
  - 資源耗盡
tags:
  - resource_exhaustion
  - availability
  - report_explainer
references:
  - id: internal_no_detection_rule
    type: internal_provenance
    source: detections/blue_team/
    note: No deterministic detection rule maps to HTTP/2 resource exhaustion; this is retrieval-only advisory context.
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
  - Narrative prose must not create graph edges automatically.
  - BLOCK, MONITOR, and ALLOW are simulated decisions only.
---

# HTTP/2 Resource Exhaustion 判讀（藍隊視角）

## 目的

本文件從藍隊（blue-team）防禦角度說明 HTTP/2 的 Resource Exhaustion（資源耗盡）類型事件，協助學生分析師理解這類可用性（availability）風險為何難以用單一 payload signature 偵測。內容僅供防禦判讀與教育用途，不提供任何攻擊操作步驟。

## 什麼是 HTTP/2 Resource Exhaustion

Resource Exhaustion 是一種以耗盡伺服器資源為目標的 Denial of Service（DoS）模式。在 HTTP/2 中，單一 TCP 連線可承載大量並行 stream，並使用 HPACK 標頭壓縮與 flow control 視窗管理。攻擊者可能利用協定特性，使**少量入站流量造成不成比例的高伺服器資源成本**（asymmetric cost），例如大量並行 stream、快速建立後重置 stream、或操弄 flow-control 視窗，導致 CPU、記憶體、連線數或 worker/執行緒被佔滿。

重點觀念：入站流量看起來可能很低，但伺服器端的 CPU、記憶體或連線狀態成本卻很高。判讀時不要只看「流量大小」，要看「資源成本是否異常不對稱」。

## 為什麼這不是一般 payload-signature 問題

傳統 Web 攻擊（如 Command Injection、SQL Injection）通常有可比對的惡意字串或 payload 特徵，rule-based detector 能用 signature 命中。Resource Exhaustion 不同：

- 每個個別請求／stream 可能完全合法，沒有惡意字串。
- 問題出在**整體行為模式與資源消耗趨勢**，而非單一封包內容。
- 因此 signature-based 偵測可能完全看不到，必須改看 metrics 與 telemetry 趨勢。

這也是為什麼這類事件在本系統中沒有對應的 deterministic detection rule，只能作為 retrieval-only 的分析師參考知識。

## 可檢查的證據（evidence to inspect）

- 伺服器 / reverse proxy 的 CPU、記憶體（memory pressure）與 worker/執行緒飽和度。
- 單一連線的並行 stream 數（concurrent stream count）與連線存活時間（connection duration）。
- stream 建立／重置（reset）速率是否異常偏高。
- HPACK 動態表大小與 flow-control 視窗是否出現 stall（停滯）。
- reverse proxy / load balancer / application server 的存取與錯誤日誌。
- 連線層級的 process metrics 與每連線資源用量。

## 可以與不能下的結論

- 可以：描述「觀察到資源成本與入站流量明顯不對稱，疑似 Resource Exhaustion 模式」。
- 可以：建議保存指標與日誌、提升給人工複核、檢查資產版本與設定。
- 不能：在缺乏資產層級遙測時宣稱「伺服器已被癱瘓」或「攻擊已成功」。
- 不能：把單一流量尖峰直接等同於蓄意攻擊；可能是正常負載、壓力測試或設定問題。

## 安全邊界 (Safety Boundary)

- RAG / AI 解釋僅供參考（advisory only），屬於分析師輔助情境，不是最終判決。
- 本內容不會覆蓋（override）確定性的 Risk Level 或 Decision；偵測與決策仍由 rule-based、deterministic 邏輯產生。
- BLOCK / MONITOR / ALLOW 皆為模擬決策（simulated），僅用於展示與教學。
- 系統未執行任何真實的 firewall / WAF / EDR / 帳號 / 監控強制動作（no real enforcement）。
- 在將任何草稿（draft）提升或正式運用（operational use）前，必須先經過人工審查（human review required）。
- 本文件不提供任何攻擊 PoC、利用步驟或流量產生（traffic generation）指引，僅供藍隊防禦判讀與教育用途。
