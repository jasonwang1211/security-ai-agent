# CSRF

## 定義
跨站請求偽造（CSRF）是指攻擊者誘使已登入使用者在不知情情況下向目標網站送出合法請求，導致未授權操作。

## 常見攻擊特徵
- 關鍵操作端點僅依賴 Cookie 驗證使用者身分。
- 缺少 CSRF Token、Origin/Referer 驗證或 SameSite 保護。
- 操作請求由外部來源頁面觸發。

## 可疑 Payload / Log 特徵
- 重要操作請求缺少預期 Token。
- `Origin` 或 `Referer` 與本站網域不一致。
- 使用者短時間內出現不符合操作習慣的敏感動作。
- 來自第三方頁面的自動提交表單跡象。

## 偵測邏輯
- 檢查關鍵 POST、PUT、DELETE 操作是否缺少 CSRF Token。
- 分析 `Origin`、`Referer`、Cookie 與 Session 關聯是否合理。
- 比對使用者操作時間、IP、裝置與行為軌跡是否異常。

## 風險評估
- 可能造成帳號設定變更、轉帳、權限修改或資料刪除。
- 若受影響端點屬於高風險管理功能，風險應上調。

## 防禦方式
- 對狀態變更請求實施 CSRF Token 驗證。
- 設定 Cookie 的 `SameSite`、`Secure` 與 `HttpOnly`。
- 驗證 `Origin` 與 `Referer`，並對高風險操作要求再次確認。
- 避免以 GET 執行具副作用的操作。

## 事件應變流程
- 確認受影響操作端點與被觸發的請求內容。
- 檢查使用者 Session、來源頁面與關聯瀏覽紀錄。
- 修補 Token 驗證與 Cookie 設定，必要時使 Session 失效。
- 通知受影響使用者檢查帳號變更與異常操作。

## 報告用摘要
系統偵測到疑似 CSRF 風險，關鍵操作請求缺少足夠的來源驗證或防偽機制。此類攻擊可能在使用者已登入情況下觸發未授權操作，建議立即檢查 Token、Cookie 與來源驗證設定。

## Structured Signals
- attack_type: CSRF
- severity: MEDIUM to HIGH
- detection_keywords: missing csrf token, invalid origin, referer mismatch, state-changing request, forged authenticated action
- log_indicators: sensitive POST requests without expected token, origin mismatch, referer mismatch, unusual account changes from active sessions
- risk_score_hint: Raise score when the request targets financial, admin, or account-management actions and token validation is absent.
- recommended_action: Enforce CSRF token validation, verify origin headers, harden cookie settings, and review impacted user sessions.
