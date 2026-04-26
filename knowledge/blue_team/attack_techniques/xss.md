# XSS

## 定義
跨站腳本攻擊（XSS）是指攻擊者將惡意腳本注入可被其他使用者瀏覽的內容中，藉此竊取 Session、操控頁面或冒用使用者行為。

## 常見攻擊特徵
- 使用者輸入被直接反射到 HTML、JavaScript 或 DOM 中。
- 頁面未正確做輸出編碼，導致瀏覽器將輸入內容當成可執行腳本。
- 攻擊可能分為 Reflected、Stored 與 DOM-Based 三類。

## 可疑 Payload / Log 特徵
- `<script>`
- `javascript:`
- `onerror=`
- `onload=`
- `alert(`
- URL、表單欄位或留言內容中出現 HTML 標籤與事件屬性。

## 偵測邏輯
- 比對輸入內容中是否含有常見腳本標籤、事件處理器或可執行 URI。
- 檢查應用程式是否將使用者輸入直接渲染到回應頁面。
- 分析 WAF、Proxy、Web Server 與應用程式日誌中的高頻可疑字串。

## 風險評估
- 可能造成帳號接管、敏感資料竊取、頁面竄改與釣魚跳轉。
- 若可影響高權限管理者，風險應上調為高。

## 防禦方式
- 對不同輸出情境實施正確編碼，例如 HTML、Attribute、JavaScript 與 URL Encoding。
- 啟用 Content Security Policy（CSP）降低腳本執行風險。
- 對富文字輸入採用白名單 Sanitization。
- 為 Cookie 設定 `HttpOnly` 與 `Secure`。

## 事件應變流程
- 確認受影響頁面、參數與輸入來源。
- 從日誌中追查可疑請求、來源 IP、受影響帳號與存取時間。
- 暫時封鎖惡意來源、下架受污染內容並修補輸出編碼。
- 視情況強制使用者重新登入與失效相關 Session。

## 報告用摘要
系統偵測到疑似 XSS 攻擊特徵，輸入中含有可執行腳本或事件屬性。此類攻擊可能導致瀏覽器端腳本執行、Session 竊取或頁面操控，建議立即檢查輸出編碼與相關日誌，並強化前端內容安全控制。

## Structured Signals
- attack_type: XSS
- severity: MEDIUM to HIGH
- detection_keywords: script tag, javascript uri, event handler injection, dom injection, reflected or stored payload
- log_indicators: requests containing `<script>`, `javascript:`, `onerror=`, `onload=`, `alert(`, suspicious HTML or script fragments in input fields
- risk_score_hint: Raise score when payload reaches privileged users, admin panels, or persistent content storage.
- recommended_action: Sanitize and encode output, review impacted pages and stored content, invalidate affected sessions when needed, and tighten browser-side controls such as CSP.
