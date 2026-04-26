# Path Traversal

## 定義
Path Traversal 是指攻擊者操控檔案路徑參數，嘗試跳脫預期目錄範圍並讀取、覆寫或探測不應公開的系統檔案。

## 常見攻擊特徵
- 檔案下載、匯出、模板載入或圖片預覽功能接受外部路徑參數。
- 輸入中出現目錄回跳序列或作業系統敏感路徑。
- 服務端缺少正規化與目錄限制。

## 可疑 Payload / Log 特徵
- `../`
- `..\\`
- `/etc/passwd`
- `C:\\Windows\\System32`
- `%2e%2e%2f`
- 連續多層目錄回跳或混合編碼路徑。

## 偵測邏輯
- 比對請求參數中是否包含目錄回跳、敏感檔名或編碼變形。
- 檢查檔案存取失敗日誌、403/404 模式與異常檔案讀取行為。
- 觀察單一來源是否對多個系統檔名進行枚舉。

## 風險評估
- 可能造成設定檔、憑證、原始碼或帳號資訊外洩。
- 若可讀取系統敏感檔案或上傳區路徑被利用，風險偏高。

## 防禦方式
- 對檔案存取使用固定根目錄與安全白名單。
- 先做路徑正規化，再驗證最終路徑仍位於允許範圍。
- 避免將使用者輸入直接拼接到檔案系統路徑。
- 為敏感檔案與異常路徑請求建立告警。

## 事件應變流程
- 確認受影響端點、檔案參數與已被嘗試存取的路徑。
- 檢查 Web、應用程式與作業系統日誌是否有敏感檔案被讀取跡象。
- 暫時封鎖可疑來源並修補路徑驗證與目錄限制。
- 檢視是否有憑證、設定或金鑰外洩，必要時輪替秘密資訊。

## 報告用摘要
系統偵測到疑似 Path Traversal 行為，請求中包含目錄回跳或敏感檔案路徑特徵。此類攻擊可能導致設定檔與系統資訊外洩，建議立即檢查檔案存取控制、路徑正規化邏輯與相關日誌。

## Structured Signals
- attack_type: Path Traversal
- severity: HIGH
- detection_keywords: directory traversal, dot dot slash, encoded traversal, sensitive file access, path normalization bypass
- log_indicators: requests containing `../`, `..\\`, `%2e%2e%2f`, access attempts to `/etc/passwd` or system directories, repeated file enumeration
- risk_score_hint: Raise score when sensitive files, configuration paths, or upload directories are targeted.
- recommended_action: Block malicious requests, validate and normalize file paths, inspect access logs for sensitive file reads, and rotate exposed secrets if needed.
