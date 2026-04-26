# SQL Injection

## 定義
SQL Injection 是指攻擊者將惡意 SQL 片段插入應用程式查詢流程，企圖繞過驗證、讀取資料、修改資料或執行高風險資料庫操作。

## 常見攻擊特徵
- 應用程式以字串拼接方式組合 SQL 查詢。
- 查詢條件中出現永真式、註解符號或資料表列舉語法。
- 異常的資料庫錯誤訊息與登入繞過情境。

## 可疑 Payload / Log 特徵
- `' OR '1'='1`
- `UNION SELECT`
- `'--`
- `DROP TABLE`
- `SLEEP(`
- 參數中出現過量單引號、註解與 SQL 關鍵字組合。

## 偵測邏輯
- 比對常見 SQL 關鍵字與語法組合是否出現在使用者輸入中。
- 檢查資料庫錯誤日誌、應用程式例外與慢查詢紀錄。
- 觀察是否出現異常查詢回傳量、登入成功率異常或回應時間被刻意拉長。

## 風險評估
- 可能造成資料外洩、資料破壞、權限提升與系統橫向風險。
- 若目標為核心業務資料庫或管理帳號登入點，風險應視為高。

## 防禦方式
- 全面使用參數化查詢或 ORM 安全綁定機制。
- 對輸入資料做型別與格式驗證。
- 限制資料庫帳號權限，避免應用程式使用高權限連線。
- 建立 SQL 錯誤與異常查詢的告警規則。

## 事件應變流程
- 先確認可疑參數、受影響查詢與資料庫範圍。
- 從應用程式與資料庫日誌還原查詢脈絡。
- 封鎖惡意來源並修補拼接式查詢。
- 檢查資料是否遭異常讀取、修改或刪除，必要時啟動資料復原流程。

## 報告用摘要
系統發現疑似 SQL Injection 特徵，輸入中包含可改變查詢語意的 SQL 片段。此類攻擊可能導致資料外洩、登入繞過或資料庫破壞，建議立即檢查相關查詢邏輯、資料庫權限與異常存取紀錄。

## Structured Signals
- attack_type: SQL Injection
- severity: HIGH
- detection_keywords: sql keyword injection, union select, boolean bypass, query manipulation, database error pattern
- log_indicators: parameters containing `' OR '1'='1`, `UNION SELECT`, `'--`, `DROP TABLE`, SQL syntax errors, unusual database response timing
- risk_score_hint: Treat as high risk when core databases, authentication flows, or administrative queries are involved.
- recommended_action: Review affected queries, enforce parameterized statements, inspect database logs for abnormal access, and contain exposed accounts or datasets.
