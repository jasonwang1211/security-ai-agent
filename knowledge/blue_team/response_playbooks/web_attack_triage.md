# Web Attack Triage Playbook

## XSS Triage
### Immediate Actions
1. 保留原始請求、時間、來源 IP、受影響 endpoint。
2. 檢查 payload 是否被反射到 response body、HTML template 或前端渲染點。
3. 暫時提高相關 endpoint 的監控等級。

### Mitigation
1. 依 HTML、JavaScript、URL、attribute context 套用正確輸出 encoding。
2. 啟用或收緊 Content Security Policy (CSP)。
3. 避免將使用者輸入直接寫入 DOM 或 template。

### Follow-up
1. 查詢同來源 IP 或同 endpoint 是否有其他 XSS payload。
2. 加入 XSS regression test cases。
3. 補上 WAF / IDS 偵測規則與告警。

## SQL Injection Triage
### Immediate Actions
1. 保留原始請求、參數、來源 IP、時間與受影響 endpoint。
2. 檢查 SQL error、登入繞過、異常查詢結果或資料外洩跡象。
3. 暫時提高受影響 endpoint 的監控等級。

### Mitigation
1. 使用 parameterized queries 或 prepared statements。
2. 移除字串拼接 SQL。
3. 驗證輸入格式並限制不必要的特殊字元。

### Follow-up
1. 查詢同來源 IP 是否有多次注入嘗試。
2. 檢查資料庫 audit log。
3. 加入 SQL injection regression test cases。

## Path Traversal Triage
### Immediate Actions
1. 保留原始請求、路徑參數、來源 IP、時間與 endpoint。
2. 檢查是否有敏感檔案讀取跡象。
3. 檢視相關檔案存取日誌。

### Mitigation
1. 對路徑做 normalization。
2. 使用 allowlist 限制可存取檔案與目錄。
3. 阻擋 traversal pattern、絕對路徑與敏感系統檔案路徑。

### Follow-up
1. 查詢同來源 IP 是否有其他 traversal 嘗試。
2. 檢查是否有 `/etc/passwd`、config、secret、`.env` 等目標。
3. 加入 path traversal regression test cases。

## Command Injection Triage
### Immediate Actions
1. 保留原始請求、參數、來源 IP、時間與 endpoint。
2. 檢查是否有非預期 process 被啟動。
3. 檢查 shell metacharacters、pipe、command chaining patterns。

### Mitigation
1. 避免將使用者輸入直接傳入 shell command。
2. 使用安全 API 取代 shell execution。
3. 對命令參數使用 allowlist。

### Follow-up
1. 查詢 process logs 與系統 audit logs。
2. 檢查是否有 lateral movement 或 privilege escalation 跡象。
3. 加入 command injection regression test cases。

## Structured Signals

```yaml
attack_type: general_triage
severity: HIGH
detection_keywords:
  - web attack triage
  - XSS
  - SQL Injection
  - Path Traversal
  - Command Injection
log_indicators:
  - suspicious query payload
  - matched web attack signature
  - affected endpoint with abnormal request
  - repeated suspicious source_ip activity
risk_score_hint: HIGH
recommended_action: BLOCK
```
