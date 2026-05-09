# Web Access Log Analysis

## Web Access Log 常見欄位
Web access log 通常記錄請求來源、HTTP 方法、路徑、查詢參數、狀態碼與使用者代理。這些欄位可協助藍隊重建事件，但單一欄位通常不足以直接定罪，需要與時間序列、身份資訊、應用程式 log 與偵測規則交叉判讀。

## 欄位說明
- `source_ip`: 請求來源。可用於關聯同來源的多次請求，但需注意 NAT、代理與雲端出口 IP。
- `method`: HTTP 方法，例如 GET、POST、PUT、DELETE。異常方法可能提高調查優先級。
- `path`: URL path，例如 `/search` 或 `/admin/login`。可顯示受影響 endpoint。
- `query`: URL 查詢字串。若出現可疑 payload，應檢查是否被應用程式處理或反射。
- `endpoint`: 正規化後的目標端點，用於聚合與報告。
- `status`: HTTP 回應狀態。`200` 不代表安全，`403` 不代表攻擊已完全阻擋，需看上下文。
- `user agent`: 若可用，可協助辨識自動化工具、異常客戶端或相同活動群組。

## 從 Query Payload 判讀常見 Web 攻擊
- XSS: query 中出現 script、事件處理器或可疑 HTML/JavaScript 片段時，應檢查是否被反射到頁面或前端渲染點。
- SQL Injection: query 中出現 SQL 關鍵字、布林條件或異常引號時，應檢查 SQL error、異常查詢結果與資料庫 log。
- Path Traversal: query 或 path 中出現 `../`、`..\\`、絕對路徑或敏感檔案名稱時，應檢查檔案存取與回應內容。

## 為什麼需要多跡象交叉判讀
可疑字串可能來自安全測試、誤輸入、編碼內容或正常業務參數。藍隊應結合 matched signatures、來源行為、endpoint、狀態碼、應用程式錯誤、回應大小、身份 log 與後續行為，避免只因單一欄位就做出最終判定。

## Structured Signals

```yaml
attack_type: general_triage
severity: MEDIUM
detection_keywords:
  - web access log
  - query payload
  - source_ip
  - endpoint
  - status
log_indicators:
  - suspicious query parameter on web endpoint
  - repeated suspicious requests from same source_ip
  - unusual status code pattern
  - path or query containing known attack indicators
risk_score_hint: MEDIUM
recommended_action: MONITOR
```
