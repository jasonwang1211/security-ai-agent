# Unknown or Unusual Log Behavior

## 異常 Log 行為
異常 log 行為是指目前事件偏離已知基準，但尚未符合明確攻擊 signature。例子包含罕見 endpoint 被存取、非典型時間的管理操作、短時間流量暴增、少見來源登入、異常錯誤率或跨系統訊號不一致。

## Zero-day-like 判讀限制
某些異常可能看起來像 zero-day-like 活動，但僅憑 anomaly 不足以確認未知攻擊。未知攻擊通常缺乏穩定 signature，需要更多證據，例如受影響資產、行為鏈、持續性、權限變更、資料外流或多 telemetry 來源關聯。

## Anomaly 不等於確認攻擊
異常可能來自部署變更、使用者行為改變、測試流量、排程任務、監控工具、雲端自動化或第三方整合。藍隊應將 anomaly 視為調查起點，而不是直接定罪。

## 需要人工複核與更多證據
建議收集以下資訊：
- 事件時間線與基準比較。
- 相關 `source_ip`、`user`、`endpoint`、`status` 與 payload。
- 應用程式錯誤、身份 log、主機 log、網路流量與雲端 audit log。
- 是否有成功登入、權限變更、資料存取或 persistence 行為。

## Blue-team Conservative Response
1. 保留證據並標記事件。
2. 提高相關身份、endpoint 或資產監控。
3. 不急著宣稱攻擊成功，除非有明確證據。
4. 若涉及特權帳號、敏感資料或關鍵系統，採取較保守的隔離或封鎖。
5. 事後將確認過的指標轉成偵測規則、回歸測試或 playbook。

## Structured Signals

```yaml
attack_type: general_triage
severity: MEDIUM
detection_keywords:
  - anomaly
  - unusual log behavior
  - zero-day-like
  - manual review
log_indicators:
  - rare endpoint access
  - unusual source_ip or login location
  - unexpected status code spike
  - abnormal behavior across multiple telemetry sources
risk_score_hint: MEDIUM
recommended_action: MONITOR
```
