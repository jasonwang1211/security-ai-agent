# Credential Stuffing

## 定義
Credential stuffing 是攻擊者使用外洩或重複使用的帳密組合嘗試登入服務的行為。藍隊分析時應聚焦於異常登入分布、帳號命中率、來源分散度與成功登入後行為。

## 與 Brute Force 的差異
Brute force 偏向猜測密碼或驗證秘密，常見為大量嘗試少數帳號。Credential stuffing 通常使用已外洩帳密，可能以大量帳號、低頻嘗試、分散來源或代理網路呈現。Credential stuffing 的風險在於一旦帳密重複使用，成功率可能高於一般猜測。

## 常見 Log 特徵
- 大量不同 `user` 在短時間內登入失敗。
- 來源 IP 分散，但 user-agent、ASN、地理位置或時間節奏相似。
- 少量帳號在多次失敗後成功登入。
- 登入成功後出現異常行為，例如更改 email、重設 MFA、匯出資料或建立 token。
- HTTP `401`、`403` 與少量 `200` 混合出現。

## 風險判讀
若事件只包含少量失敗登入，通常先列為 MONITOR。若出現大量帳號嘗試、成功登入、特權帳號命中、或登入後敏感操作，應提高到 HIGH。Credential stuffing 常需要身份 log、WAF log、應用程式 audit log 與 session log 共同判讀。

## 防禦方式
- 啟用 MFA 與風險式登入挑戰。
- 偵測已外洩或常見弱密碼，但避免在 log 中暴露密碼。
- 對異常登入來源與裝置建立風險評分。
- 對大量帳號嘗試建立速率限制與告警。
- 啟用 session 撤銷、可疑登入通知與密碼重設流程。

## 事件應變流程
1. 保留登入失敗與成功紀錄、使用者清單、來源資訊與時間窗。
2. 找出是否有成功登入、登入後敏感操作或新建 session。
3. 對受影響帳號強制 MFA、撤銷 session 或要求重設密碼。
4. 查詢同來源、同 user-agent 或同 ASN 的其他登入活動。
5. 將確認指標加入偵測規則與風險登入策略。

## 報告用摘要
此事件可能代表 credential stuffing，因為登入嘗試呈現多帳號或分散來源特徵。建議確認是否有成功登入與帳號接管跡象，並啟用 MFA、session 撤銷與風險式登入控制。

## Structured Signals

```yaml
attack_type: credential_stuffing
severity: HIGH
detection_keywords:
  - credential stuffing
  - leaked credentials
  - many users
  - distributed login failures
log_indicators:
  - many user accounts with failed login attempts
  - multiple source_ip values targeting authentication endpoints
  - failed logins followed by successful sessions
  - similar user agent across distributed sources
risk_score_hint: HIGH
recommended_action: BLOCK
```
