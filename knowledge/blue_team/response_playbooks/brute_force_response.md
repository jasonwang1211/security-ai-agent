# Brute Force Response Playbook

## Immediate Actions
1. 保留原始登入事件、時間窗、來源 IP、使用者、endpoint、status 與 `failed_count`。
2. 確認是否有多次失敗後成功登入。
3. 檢查是否涉及管理員、VPN、SSO、雲端控制台或高權限帳號。
4. 視風險暫時提高相關帳號與 endpoint 的監控等級。

## Mitigation
1. 對可疑來源、ASN 或地理位置套用暫時封鎖或更嚴格挑戰。
2. 啟用或強化 MFA、風險式登入與 session 撤銷。
3. 對登入端點套用 rate limiting、progressive delay 與帳號保護。
4. 對受影響帳號要求密碼重設或安全性檢查。

## Follow-up
1. 查詢同來源是否攻擊其他帳號或 endpoint。
2. 查詢同一使用者是否被多個來源嘗試。
3. 檢查登入後是否有敏感操作、權限變更或資料存取。
4. 將確認指標加入 SIEM、WAF、IDS 或身份安全告警。

## Evidence to Preserve
- 原始 authentication log 與聚合結果。
- `source_ip`、`user`、`endpoint`、`status`、`failed_count`。
- 成功登入、session、MFA、密碼重設與帳號鎖定紀錄。
- 相關防火牆、WAF、VPN、SSO 或雲端身份 log。

## What Not To Do
- 不要只因單一登入失敗就封鎖使用者帳號。
- 不要在報告或 log 中暴露密碼、token 或秘密值。
- 不要在未確認成功登入前宣稱帳號已被接管。
- 不要忽略 NAT、代理或企業出口 IP 造成的誤判。

## Simulated Response Note
在本專案中，BLOCK、MONITOR、ALLOW 是模擬決策，用於展示藍隊 triage 流程；不代表系統已實際修改防火牆、身份平台或雲端控制。

## Structured Signals

```yaml
attack_type: brute_force
severity: HIGH
detection_keywords:
  - brute force response
  - account protection
  - MFA
  - rate limiting
log_indicators:
  - repeated authentication failures
  - failed_count above baseline
  - suspicious source_ip targeting login endpoint
  - successful login after repeated failures
risk_score_hint: HIGH
recommended_action: BLOCK
```
