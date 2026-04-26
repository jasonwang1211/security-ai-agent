# Brute Force

## 定義
Brute Force 是指攻擊者透過大量重複嘗試帳號密碼、驗證碼或金鑰組合，企圖取得未授權存取權限。

## 常見攻擊特徵
- 同一帳號或同一來源在短時間內出現大量失敗登入。
- 嘗試多組帳號密碼組合，呈現橫向掃描或撞庫模式。
- 驗證失敗與成功事件之間存在異常集中現象。

## 可疑 Payload / Log 特徵
- 高頻率 `/login`、`/auth`、`/signin` 請求。
- 同 IP 對多個帳號進行快速嘗試。
- 多個 IP 對同一帳號進行分散式嘗試。
- 大量 401、403 或登入失敗事件。

## 偵測邏輯
- 設定帳號與來源 IP 的失敗次數門檻。
- 分析短時間內的登入頻率、帳號覆蓋率與成功率變化。
- 關聯裝置指紋、地理位置與代理服務使用情況。

## 風險評估
- 可能造成帳號被接管、資源濫用與後續內網滲透。
- 若缺乏 MFA 或鎖定機制，風險更高。

## 防禦方式
- 啟用登入速率限制、Captcha 與帳號暫時鎖定。
- 導入 MFA 與異常登入驗證。
- 監控撞庫特徵與來源信譽。
- 對高風險帳號與管理介面採更嚴格存取控制。

## 事件應變流程
- 確認受攻擊帳號、來源 IP 與攻擊時間區間。
- 封鎖或限制惡意來源，並提高受影響帳號保護等級。
- 檢查是否已有登入成功事件與後續敏感操作。
- 通知使用者重設密碼並啟用 MFA。

## 報告用摘要
系統發現疑似 Brute Force 行為，短時間內出現異常密集的登入失敗或多帳號嘗試。此類活動可能導致帳號接管，建議立即檢查登入事件、啟用速率限制並強化多因素驗證。

## Structured Signals
- attack_type: Brute Force
- severity: MEDIUM to HIGH
- detection_keywords: repeated login failure, account guessing, credential stuffing, high request rate, distributed authentication attempts
- log_indicators: repeated 401 or 403 responses, multiple login attempts from one IP, one account targeted by many IPs, abnormal success after many failures
- risk_score_hint: Raise score when attacks target admin accounts, MFA is absent, or a successful login follows repeated failures.
- recommended_action: Apply rate limiting, block abusive sources, enforce MFA, and review affected accounts for takeover activity.
