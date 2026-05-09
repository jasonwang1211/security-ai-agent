# Brute Force

## 定義
Brute force 是攻擊者以大量嘗試猜測帳號、密碼、一次性驗證碼或其他認證秘密的行為。對藍隊而言，重點不是描述如何執行攻擊，而是從身份、來源、端點與時間序列判斷是否存在異常登入壓力。

## 常見攻擊行為
- 同一來源 IP 對同一登入端點連續產生失敗登入。
- 同一來源 IP 嘗試多個使用者帳號。
- 同一帳號在短時間內出現大量失敗登入。
- 多次失敗後突然成功登入，需要提高接管風險判讀。
- 管理員帳號、VPN、SSO、雲端控制台或後台登入頁受到集中嘗試。

## 與 Credential Stuffing 的差異
Brute force 通常偏向猜測密碼或驗證秘密，嘗試模式可能集中在少數帳號或單一來源。Credential stuffing 則通常使用外洩帳密組合嘗試登入，常見特徵是大量帳號、分散來源、低頻但廣泛的嘗試。兩者都可能造成帳號接管，但調查方向不同。

## 常見 Log 特徵
- `source_ip` 在短時間內對 `/login`、`/auth`、`/signin` 或身份服務產生多次失敗。
- HTTP `status` 出現大量 `401` 或 `403`。
- 同一 `user` 的失敗登入次數異常升高。
- `endpoint` 集中在登入、重設密碼、MFA 或 token 相關路徑。
- `failed_count` 超過環境基準或偵測門檻。

## 欄位意義
- `source_ip`: 來源位址，可用來判斷是否同一來源集中嘗試。
- `user`: 被嘗試登入的帳號，可用來判斷是否特定帳號遭鎖定。
- `endpoint`: 被攻擊或被濫用的登入相關服務。
- `status`: 認證結果或 HTTP 狀態。登入情境中 `401` 通常代表未授權，`403` 通常代表被拒絕。
- `failed_count`: 聚合後的失敗次數，用於衡量頻率與嚴重度。

## 風險判讀
風險會隨目標與上下文升高。若目標是特權帳號、失敗後有成功登入、來源分散且持續、或同時伴隨 MFA 挑戰失敗，應提高到 HIGH 並啟動事件應變。單一失敗登入通常不足以確認攻擊，需與基準、時間窗、端點與身份上下文交叉判讀。

## 防禦方式
- 對登入端點啟用 rate limiting 與 progressive delay。
- 對高風險登入啟用 MFA、風險式驗證與裝置信任檢查。
- 對異常來源、ASN、地理位置或匿名代理提高監控。
- 建立帳號鎖定與解鎖流程，避免造成使用者服務中斷。
- 對特權帳號啟用更嚴格的告警與審計。

## 事件應變流程
1. 保留原始登入 log、時間窗、來源 IP、使用者與端點。
2. 查詢同來源 IP 是否攻擊其他帳號或端點。
3. 查詢同一使用者是否被多個來源嘗試。
4. 檢查是否有失敗後成功登入或異常 session。
5. 視風險暫時封鎖來源、要求密碼重設、撤銷 session 或強制 MFA。
6. 將確認指標加入偵測規則與後續監控。

## 報告用摘要
此事件顯示登入端點出現多次失敗認證，可能代表 brute force 行為。建議保留身份與來源證據、確認是否有成功登入或帳號接管跡象，並依風險採取監控、封鎖或帳號保護措施。

## Structured Signals

```yaml
attack_type: brute_force
severity: HIGH
detection_keywords:
  - brute force
  - repeated login failure
  - failed_count
  - source_ip
  - account lockout
log_indicators:
  - same source_ip with repeated 401 or 403 responses
  - same target endpoint receiving many login failures
  - same user with repeated failed authentication
  - successful login after repeated failures
risk_score_hint: HIGH
recommended_action: BLOCK
```
