# Log Analysis

## 定義
Log Analysis 是透過 Web、應用程式、系統、資料庫與安全設備日誌，重建事件脈絡並識別可疑活動的分析流程。

## 常見攻擊特徵
- 單一事件本身不明顯，但跨來源關聯後呈現異常模式。
- 失敗登入、錯誤回應、權限變更與外連事件在時間上聚集。
- 相同來源對多個端點、帳號或資產進行探測。

## 可疑 Payload / Log 特徵
- 異常大量的 401、403、404、500 或資料庫錯誤。
- 稀有 User-Agent、地理位置、來源 ASN 或代理服務。
- 同一交易流程中出現目錄回跳、SQL 關鍵字、腳本標籤或命令分隔符。
- 程序建立、檔案寫入與網路外連的時間序列吻合。

## 偵測邏輯
- 建立欄位正規化，確保時間、IP、帳號、URI、狀態碼可跨來源關聯。
- 針對高風險事件建立門檻、序列規則與聚合分析。
- 結合基線分析，識別異常峰值、罕見活動與攻擊鏈。

## 風險評估
- 日誌若完整且可關聯，能大幅提升判斷精度與事件分級能力。
- 若關鍵系統缺少日誌或保留不足，應提高不確定性風險。

## 防禦方式
- 強化集中式日誌收集、時間同步與欄位標準化。
- 針對關鍵操作與高風險資產提高日誌粒度。
- 為常見攻擊型態建立可重用的查詢與告警規則。
- 定期驗證日誌完整性與查詢可用性。

## 事件應變流程
- 先確認事件時間軸與主要資料來源。
- 關聯 Web、應用程式、主機與網路日誌，辨識攻擊路徑。
- 擷取關鍵證據，如來源 IP、帳號、Payload、檔案與程序資訊。
- 產出可追溯的分析結論與後續監控條件。

## 報告用摘要
此次分析需依賴多來源日誌重建事件脈絡，重點在識別異常請求、主機行為與關聯時間序列。建議透過集中式查詢與規則化分析，快速定位可疑來源、受影響資產與可能攻擊鏈。

## Structured Signals
- attack_type: Log Analysis
- severity: MEDIUM
- detection_keywords: cross-source correlation, error spike, suspicious request pattern, host-web linkage, timeline reconstruction
- log_indicators: bursts of 401, 403, 404, 500, repeated suspicious URIs, matching IP and account activity across web, app, database, and host logs
- risk_score_hint: Raise score when multiple telemetry sources align on the same source, account, endpoint, or attack timeline.
- recommended_action: Normalize and correlate logs, extract primary indicators, expand the investigation window, and convert findings into reusable detection logic.
