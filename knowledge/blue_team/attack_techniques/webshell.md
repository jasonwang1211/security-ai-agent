# Webshell

## 定義
Webshell 是指攻擊者透過上傳或植入惡意網頁腳本，讓受害伺服器提供遠端指令執行、檔案管理或持久化控制能力。

## 常見攻擊特徵
- 上傳目錄中出現可執行腳本檔案或不尋常副檔名組合。
- Web 程序對系統命令、檔案管理或外連行為異常活躍。
- 單一頁面對多種參數輸入做動態命令或檔案操作。

## 可疑 Payload / Log 特徵
- 上傳檔名含 `.php`、`.asp`、`.aspx`、`.jsp` 等可執行副檔名。
- 請求參數中出現 `cmd`、`exec`、`shell`、`pass` 等欄位。
- 伺服器端出現異常程序建立、壓縮打包、下載工具或反向連線。
- 非預期檔案建立於 Web Root、上傳目錄或暫存目錄。

## 偵測邏輯
- 監控上傳行為、檔案建立與檔案雜湊變化。
- 關聯 Web 請求與主機程序建立、權限異動及外連事件。
- 對可執行腳本內容做靜態掃描，尋找命令執行與編碼混淆特徵。

## 風險評估
- 可能造成持久化入侵、遠端控制、橫向移動與資料竊取。
- 若位於對外服務且具高權限，風險極高。

## 防禦方式
- 上傳區與執行區分離，禁止上傳目錄執行腳本。
- 限制可接受的副檔名、MIME 與檔案內容類型。
- 監控 Web Root 與上傳目錄的檔案異動。
- 在主機與網路層建立命令執行與外連告警。

## 事件應變流程
- 立即識別並隔離受影響主機或站點。
- 保留惡意檔案、日誌、程序清單與網路連線資訊。
- 搜尋是否存在其他後門檔案、排程、帳號或持久化機制。
- 清除惡意檔案並修補初始入侵點，例如上傳漏洞或弱憑證。

## 報告用摘要
系統偵測到疑似 Webshell 活動，包含可執行上傳檔案、異常命令參數或主機端可疑程序。此類事件通常代表伺服器已遭植入後門，建議立即隔離主機並執行主機層與 Web 層聯合調查。

## Structured Signals
- attack_type: Webshell
- severity: HIGH
- detection_keywords: executable upload, backdoor script, cmd parameter, file manager behavior, persistent web backdoor
- log_indicators: new script files in upload paths, requests with `cmd` or `shell` parameters, unusual child processes from web services, outbound callback traffic
- risk_score_hint: Treat as critical when a server-side executable file is confirmed or host telemetry shows post-exploitation behavior.
- recommended_action: Isolate the server, preserve forensic evidence, remove malicious files only after evidence capture, and remediate the initial intrusion vector.
