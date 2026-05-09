# Login Failure Analysis

## 如何判斷多次登入失敗
多次登入失敗應以時間窗、來源、使用者、端點與結果一起判斷。單一 `401` 或 `403` 不一定代表攻擊；若相同來源或相同帳號在短時間內反覆失敗，才更接近 brute force、credential stuffing 或帳號接管前兆。

## Same Source IP + Same Target 的意義
同一 `source_ip` 對同一 `target` 或 `endpoint` 重複失敗，常見於集中式密碼猜測、掃描登入端點或自動化登入嘗試。若 `failed_count` 快速升高，且 user 或 endpoint 集中，應提高監控或封鎖優先級。

## Same User + Multiple Source IP 的意義
同一 `user` 被多個 `source_ip` 嘗試，可能代表 credential stuffing、密碼噴灑或帳號遭針對。若來源分散但時間節奏相似，應檢查 user-agent、ASN、地理位置、裝置指紋與登入後行為。

## HTTP 401 / 403 在登入事件中的意義
- `401 Unauthorized`: 常代表認證失敗或缺少有效憑證。
- `403 Forbidden`: 常代表已識別請求但權限不足、策略拒絕或風險控制阻擋。
在登入分析中，兩者都可作為失敗或拒絕訊號，但必須依應用程式語意確認。

## Failed Count Threshold 的概念
`failed_count` 門檻應依環境基準設定。例如一般使用者偶發輸入錯誤可能是低風險；短時間內同來源達到多次失敗、或同一帳號被多來源嘗試，通常需要 MONITOR 或 BLOCK。門檻應考慮服務流量、使用者行為、登入端點重要性與誤報成本。

## False Positive Considerations
- 使用者忘記密碼或輸入法造成重複失敗。
- 行動網路、企業 NAT 或代理造成多使用者共享同一 IP。
- SSO、MFA、API token 過期造成連續認證錯誤。
- 健康檢查、整合測試或自動化任務設定錯誤。
- 應用程式回傳狀態碼語意不一致。

## Example Indicators
- 同一 `source_ip` 對 `/login` 在 5 分鐘內產生大量 `401`。
- 同一 `user` 從多個地區或 ASN 出現失敗登入。
- 大量失敗後緊接成功登入。
- 特權帳號、管理後台或 VPN 登入端點被反覆嘗試。

## Structured Signals

```yaml
attack_type: brute_force
severity: HIGH
detection_keywords:
  - login_failed
  - failed_count
  - same source_ip
  - same user
  - HTTP 401
log_indicators:
  - repeated 401 or 403 on authentication endpoints
  - same source_ip and same target repeated failures
  - same user across multiple source_ip values
  - successful login after many failures
risk_score_hint: HIGH
recommended_action: BLOCK
```
