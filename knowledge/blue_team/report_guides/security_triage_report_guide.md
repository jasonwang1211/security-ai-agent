# Security Triage Report Guide

## 目的
Security Triage Report 是用來協助 SOC 或藍隊快速理解偵測結果、風險、建議處置與模擬決策的摘要。它不是最終鑑識報告，也不應取代人工複核。

## 各區塊說明

### Quick Verdict
最上方的快速結論。說明目前事件最可能的攻擊類型、風險等級、系統決策與主要理由。SOC demo 中可先讀此區塊掌握重點。

### Summary
列出偵測狀態、Attack Type、Risk Level、Decision 與 Detection Source。這是系統根據既有偵測、風險評分與決策流程產生的結構化摘要。

### Evidence
顯示原始輸入或轉換後 payload，以及 matched signatures。此區塊用來支持判斷，但單一 signature 不一定代表攻擊已成功。

### Why It Matters
說明該類攻擊對系統、資料、身份或使用者可能造成的影響。此區塊提供藍隊溝通與教育脈絡。

### Recommended Response
提供 Immediate Actions、Mitigation 與 Follow-up。它是防禦建議與調查方向，不代表系統已自動執行。

### Simulation Notice
說明防禦行為是模擬結果。此專案中的 BLOCK、MONITOR、ALLOW 用於展示決策，不是真的控制防火牆、WAF、EDR、身份平台或雲端策略。

### AI Assist
若 LLM 分析存在，此區塊提供 AI 輔助判讀。LLM Suggested Decision 只是輔助，不是最終決策；最終 Decision 仍由系統決策流程產生。

## Risk Level 的意思
- `LOW`: 目前沒有明確高風險訊號，通常可持續觀察。
- `MEDIUM`: 存在可疑或已知攻擊指標，需要監控與進一步確認。
- `HIGH`: 存在高影響攻擊類型、明確惡意跡象或需要快速處置的情境。

## Decision 的意思
- `ALLOW`: 模擬決策為允許或不採取阻擋，通常代表低風險或證據不足。
- `MONITOR`: 模擬決策為監控，代表需要保留證據、提高可見度或等待更多訊號。
- `BLOCK`: 模擬決策為阻擋，代表系統判斷風險較高，建議採取防護措施。

## 重要限制
- BLOCK / MONITOR / ALLOW 是模擬決策，不是真的控制防火牆。
- LLM Suggested Decision 是 AI assist only，不是最終決策。
- RAG 知識庫提供解釋與回應建議，不負責決定攻擊類型。
- 最終處置仍需依組織政策、業務影響與人工複核決定。

## Structured Signals

```yaml
attack_type: general_triage
severity: MEDIUM
detection_keywords:
  - Security Triage Report
  - Quick Verdict
  - Risk Level
  - Decision
  - AI Assist
log_indicators:
  - matched signatures in evidence section
  - risk level and decision fields in report
  - simulation notice indicating non-production control
  - LLM suggested decision present as assistive context
risk_score_hint: MEDIUM
recommended_action: MONITOR
```
