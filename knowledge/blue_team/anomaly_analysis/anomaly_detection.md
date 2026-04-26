# Anomaly Detection

## 定義
Anomaly Detection 著重從正常行為基線出發，辨識偏離常態的流量、存取、程序或操作模式，以補足規則式與簽章式偵測的盲點。

## 常見攻擊特徵
- 攻擊行為可能刻意避開固定簽章，但仍會在頻率、時序或關聯性上留下異常。
- 同一帳號、主機或 API 的行為突然改變。
- 事件本身不一定高危，但多個微弱異常合併後可能代表攻擊。

## 可疑 Payload / Log 特徵
- 平常少見的端點突然被高頻存取。
- 請求參數長度、熵值或編碼型態明顯偏離歷史分布。
- 稀有時段的管理行為、權限操作或跨區域登入。
- 主機端出現新服務、新排程或不尋常外連。

## 偵測邏輯
- 為帳號、主機、應用程式與 API 建立可比較的行為基線。
- 使用統計門檻、滑動視窗、偏差分數或多訊號加權方法找出異常。
- 將異常與規則命中、資產重要性與威脅情報做關聯，以降低誤報。

## 風險評估
- 若異常發生在高價值資產、管理帳號或核心服務，應提高風險等級。
- 若異常具持續性或跨層關聯性，表示風險已超出單點事件。

## 防禦方式
- 維持高品質遙測資料與一致欄位標準。
- 持續調整基線模型，反映正常業務變動。
- 對高風險異常建立自動化告警與人工審查流程。
- 將有效異常案例回饋成新規則與新 Playbook。

## 事件應變流程
- 確認異常是否持續、擴大或與其他告警同時發生。
- 調閱相關 Web、主機、網路與身分驗證日誌進行關聯分析。
- 視風險程度採取監控加嚴、帳號限制或資產隔離。
- 將結果整理為長期監控指標與調查假設。

## 報告用摘要
系統觀察到與正常基線不一致的活動模式，需從多來源遙測中進一步確認是否屬於攻擊前兆或未知威脅。建議結合規則告警與資產情境做關聯分析，提升異常事件的判讀品質。

## Structured Signals
- attack_type: Anomaly Detection
- severity: MEDIUM to HIGH
- detection_keywords: baseline deviation, unusual frequency, rare endpoint, high entropy parameter, off-hours access, abnormal process behavior
- log_indicators: sudden traffic spikes, rare login locations, unusual admin actions, new services or scheduled tasks, unexpected outbound connections
- risk_score_hint: Raise score when anomalies affect privileged accounts, critical assets, or appear across multiple telemetry sources.
- recommended_action: Correlate with identity, host, and network logs; increase monitoring; isolate high-risk assets if anomalies persist or expand.
