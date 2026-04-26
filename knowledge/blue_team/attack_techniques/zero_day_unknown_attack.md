# Zero-Day / Unknown Attack

## 定義
Zero-Day / Unknown Attack 指尚未有已知修補程式、簽章或明確特徵庫支援的攻擊活動，或其手法與既有模式顯著不同。

## 常見攻擊特徵
- 行為異常但無法完全對應既有規則。
- 新型 Payload、未知 User-Agent、非典型請求序列或新穎編碼方式。
- 系統出現異常資源使用、檔案變更、權限提升或外連，但缺乏明確 IOC。

## 可疑 Payload / Log 特徵
- 未知但高熵或混淆的參數內容。
- 罕見端點被連續探測或觸發非預期例外。
- 主機行為突然偏離正常基線，例如新程序、異常連線或系統工具被濫用。
- 告警彼此分散但在時間上高度關聯。

## 偵測邏輯
- 以異常偵測、基線偏差分析與多來源關聯分析為主。
- 檢查是否存在不符合既有操作模式的請求序列、主機事件與網路流量。
- 對未知事件提高人工分析與案例分級權重。

## 風險評估
- 因未知性高，低可見度通常代表高不確定性風險。
- 若涉及關鍵資產、權限變更或外連活動，應採保守高風險處置。

## 防禦方式
- 維持資產盤點、最小權限、網段隔離與快速修補能力。
- 建立多層日誌與遙測，提升未知攻擊的可觀測性。
- 使用行為型防護與威脅獵捕流程補足簽章不足。
- 對高風險異常事件建立人工複核機制。

## 事件應變流程
- 先界定異常範圍、時間軸與受影響資產。
- 保留完整證據，避免過早清除造成分析斷點。
- 以隔離、限權與監控加嚴方式降低潛在衝擊。
- 持續更新 IOC、假設與分析結論，必要時啟動跨團隊應變。

## 報告用摘要
系統觀察到疑似未知攻擊或 Zero-Day 型態異常，雖未完全命中既有規則，但行為與正常基線存在明顯偏差。建議採保守防禦策略，強化遙測蒐集、主機隔離與人工深度分析，以降低未知風險。

## Structured Signals
- attack_type: Zero-Day / Unknown Attack
- severity: HIGH
- detection_keywords: unknown exploit pattern, baseline deviation, novel payload, unexplained host behavior, unclassified attack sequence
- log_indicators: rare endpoints, unexplained exceptions, high-entropy payloads, new processes, unusual outbound traffic, alerts that correlate weakly but cluster in time
- risk_score_hint: Bias upward when multiple weak anomalies affect critical assets or when no known signature explains the observed behavior.
- recommended_action: Preserve evidence, isolate high-risk systems, collect broader telemetry, and perform analyst-led investigation with conservative containment.
