# Command Injection

## 定義
Command Injection 是指攻擊者將惡意系統命令注入應用程式呼叫 shell 或外部程序的流程中，藉此執行未授權的系統操作。

## 常見攻擊特徵
- 應用程式將使用者輸入拼接進 shell 指令。
- 輸入中出現命令分隔符、管線或子命令語法。
- 可疑請求後伴隨異常程序建立、檔案變更或網路連線。

## 可疑 Payload / Log 特徵
- `;`
- `&&`
- `||`
- `| whoami`
- `` `id` ``
- `$()`
- 參數中出現作業系統命令與命令鏈結符號。

## 偵測邏輯
- 比對輸入是否含有命令分隔符、子命令語法與高風險系統指令。
- 關聯 Web 請求與主機端程序建立、Shell 啟動、檔案修改及外連事件。
- 檢查應用程式錯誤與作業系統稽核記錄中的執行痕跡。

## 風險評估
- 可能導致遠端命令執行、資料竊取、惡意下載與主機控制權喪失。
- 若可執行於高權限服務帳號下，風險極高。

## 防禦方式
- 避免使用 shell，改用安全 API 與參數陣列執行命令。
- 對可接受的輸入值採白名單限制。
- 最小化服務帳號權限並限制主機外連能力。
- 建立程序建立、Shell 啟動與敏感命令執行的監控。

## 事件應變流程
- 先確認可疑請求與後續主機行為是否存在因果關聯。
- 隔離受影響主機，保留程序、網路與檔案證據。
- 檢查是否有下載器、反向連線或持久化痕跡。
- 修補命令執行邏輯並輪替受影響憑證。

## 報告用摘要
系統發現疑似 Command Injection 特徵，輸入中含有命令鏈結或子命令語法。此類攻擊可能直接導致主機層級命令執行與資料外洩，建議立即關聯分析 Web 與主機日誌，並檢查是否存在異常程序與外連行為。

## Structured Signals
- attack_type: Command Injection
- severity: HIGH
- detection_keywords: shell metacharacter, command chaining, subshell syntax, os command, remote execution attempt
- log_indicators: parameters containing `;`, `&&`, `||`, `` ` ``, or `$()`, unexpected shell spawning, suspicious child processes, outbound connections after web requests
- risk_score_hint: Treat as high risk by default, especially when correlated with process creation, downloads, or privileged service accounts.
- recommended_action: Contain affected hosts, inspect spawned processes and outbound traffic, patch unsafe command execution paths, and rotate exposed secrets.
