# Risk Scoring

## 定義
Risk Scoring 是將偵測事件依攻擊類型、資產重要性、影響範圍、可信度與上下文進行量化或分級，以支援決策與應變優先順序。

## 常見攻擊特徵
- 單一事件的嚴重度不僅取決於 Payload，也與目標資產與上下文相關。
- 同類型攻擊在公開測試環境與核心生產環境中的風險不同。
- 偵測可信度、命中規則數量與關聯證據會影響最終分數。

## 可疑 Payload / Log 特徵
- 高風險 Payload 命中多條規則，例如 SQL 關鍵字加上錯誤回應。
- 事件涉及高權限帳號、管理介面或敏感資料庫。
- 來源具持續性、重複性或與既有惡意行為關聯。
- 同時伴隨主機端異常、外連或資料外傳跡象。

## 偵測邏輯
- 依攻擊型態先給基礎風險，再依資產重要性與上下文調整。
- 將命中規則數量、異常程度、關聯事件與可信度納入加權。
- 將風險分級映射到處置建議，例如 ALLOW、MONITOR、BLOCK。

## 風險評估
- 高風險事件通常涉及可直接利用、敏感資產或多重證據一致。
- 中風險事件可能需要持續觀察與人工複核。
- 低風險事件仍應保留足夠日誌以支援後續關聯分析。

## 防禦方式
- 建立一致且可解釋的風險評分標準。
- 定期校準分數門檻，避免過度阻擋或誤放高風險事件。
- 將資產分類、帳號權限與歷史事件納入評分上下文。
- 保留評分依據，支援調查、稽核與模型優化。

## 事件應變流程
- 先依風險分數決定優先級與處置深度。
- 對高風險事件立即啟動控制或封鎖機制。
- 對中風險事件進行補充蒐證與人工判讀。
- 根據後續調查結果回調分數與規則設計。

## 報告用摘要
風險評分可將偵測結果轉換為可執行的處置優先級，協助藍隊在大量事件中快速辨識高風險活動。建議綜合攻擊型態、資產敏感度、關聯證據與可信度進行分級，以支援穩定且可解釋的防禦決策。

## Structured Signals
- attack_type: Risk Scoring
- severity: MEDIUM
- detection_keywords: severity mapping, contextual weighting, asset criticality, confidence adjustment, decision threshold
- log_indicators: multiple rule hits, privileged target, critical asset exposure, correlated host events, successful exploitation signs
- risk_score_hint: Increase score when the event includes strong payload evidence, high-value assets, privileged identities, or post-exploitation indicators.
- recommended_action: Use score thresholds to prioritize triage, escalate high-risk events immediately, and recalibrate scoring based on investigation outcomes.
