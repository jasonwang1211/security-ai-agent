# Sentinel Project — AI 輔助藍隊安全分流系統

## 專案簡介

Sentinel Project 是一個防禦導向的資安威脅偵測與應變展示系統。它的重點不是讓 AI 直接決定「是不是攻擊」，而是建立一條可解釋、可控制、可展示給教授與專題評審理解的藍隊分析流程。

系統先由 Rule-Based Detector 進行偵測，再由 deterministic logic 產生 Risk Level 與 Decision。AI Analyst Brief、Evidence Gap Analyzer、Knowledge Q&A / RAG、Approved Similar Cases 與 Relationship Graph 都是分析師輔助資訊，不會覆蓋最終判定。

## 為什麼做這個專題

許多 AI 資安展示容易把焦點放在 AI 看起來很聰明，但真實資安工作更重視可追溯、可審查與責任邊界。若讓 LLM 直接判斷攻擊是否成立，可能產生 hallucination、過度推論，或把缺乏證據的情境說成已確認入侵。

本專題採用 deterministic first, AI advisory second 的架構。攻擊分類、Risk Level 與 Decision 由規則與固定邏輯決定；AI 與 RAG 則用來協助說明判斷依據、整理證據缺口、回答防禦知識問題，以及提供相似案例比較。

## 系統流程

整體流程可以理解為：

使用者輸入 → Rule-Based Detector → 攻擊分類 → Risk Level → Decision → AI / RAG 輔助解釋 → 報告輸出

支援的輸入包含示範 payload、authentication incident、HTTP/2 Resource Exhaustion safe synthetic demo，以及防禦導向的 Knowledge Q&A。

## 核心設計理念

- 偵測是 Rule-Based Detector，不是 AI 判斷。
- Risk Level / Decision 是 deterministic，不依賴 LLM 自由裁決。
- BLOCK / MONITOR / ALLOW 是 simulated decisions，只用於展示安全分流結果。
- RAG / LLM / AI Analyst Brief / Evidence Gap Analyzer 只提供 advisory context。
- Approved Similar Cases 與 Relationship Graph 是分析師參考，不是目前事件的最終證據。
- Case Draft 與 Markdown Export 需要 Human review，不代表正式通報、入庫或自動執行。

## Demo 功能亮點

- Fast deterministic mode：快速產生 deterministic 偵測與分流結果。
- Full AI-assisted mode：提供可選的 AI/RAG 輔助分析路徑。
- Lazy RAG startup：避免啟動時就載入 heavy RAG / embedding dependency。
- Language-aware output：分析輔助輸出會依 UI 語言設定呈現。
- AI Analyst Brief：摘要目前事件、風險意義、建議下一步與不安全假設。
- Evidence Gap Analyzer：列出仍需人工補查的證據缺口。
- Knowledge Q&A / RAG：回答防禦導向資安問題，例如 HTTP/2 DoS、CVE 與 Resource Exhaustion。
- Approved Similar Cases：讀取 approved seed cases，提供相似案例與差異比較。
- Relationship Graph：以圖像方式呈現目前事件、案例與關聯資訊。
- Case Draft：產生需人工審核的 case draft。
- Markdown Export：匯出展示用 Markdown 報告。
- HTTP/2 Resource Exhaustion safe synthetic demo：提供安全的 synthetic incident summary，不產生攻擊流量。

## 安全邊界

Sentinel Project 是資安專題展示系統，不是真實 IDS / IPS，也不是攻擊或自動封鎖工具。

- 偵測是 Rule-Based Detector，不是 AI 判斷。
- Risk Level / Decision 是 deterministic。
- BLOCK / MONITOR / ALLOW 是 simulated。
- RAG / LLM / AI Analyst Brief / Evidence Gap 只提供 advisory context。
- 不做真實 firewall / WAF / EDR / account / cloud / SIEM / SOAR 動作。
- 不提供 exploit / PoC / traffic generation。
- 需要 Human review。

## 快速開始

以下是通用 PowerShell 範例，請依自己的 repository URL 與 Python 環境調整。

    git clone <your-repo-url>
    cd sentinel_project
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none

Demo 時建議先選擇 Fast deterministic mode，載入 Command Injection 或 HTTP/2 Resource Exhaustion safe demo，點擊 Run input 後查看 AI Analyst、Evidence Gap、Knowledge Q&A、Similar Cases、Graph 與 Export 相關頁籤。

## 文件導覽

- [English README](../../README.md)
- [English Project Report](../../REPORT.md)
- [User Operation Guide](../USER_OPERATION_GUIDE.md)
- [Test Report](../TEST_REPORT.md)
- [Code Review Audit](../CODE_REVIEW_AUDIT.md)
- [v2.8 Release Gate](../v2.8_release_gate.md)
- [Screenshot Gallery](../screenshots/README.md)
- [Roadmap](../ROADMAP.md)
- [Technical Notes](../TECH_NOTES.md)

## 測試與驗證

目前 v2.8 demo-ready 狀態已保留完整驗證摘要。公開文件記錄包含 pytest、ruff、mypy、gitleaks、screenshot refresh 與 release gate 結果。

重點驗證包含：

- deterministic detection 與 Risk Level / Decision 穩定性。
- Fast deterministic mode 不應載入 heavy RAG dependency。
- RAG / AI advisory output 不覆蓋 deterministic verdict。
- HTTP/2 safe demo 不產生 traffic、不提供 exploit 或 PoC。
- Screenshot gallery 與公開文件連結保持可用。

## 限制與未來工作

本專案目前定位為 demo-ready 的藍隊安全分流展示系統，仍不是 production SOC 平台。未來可持續強化：

- 更多 defensive synthetic scenarios。
- Analyst timeline / event replay。
- 更完整的 read-only graph 與 approved-case memory。
- 更成熟的 packaging 與 release polish。
- 更精細的報告輸出與審核流程。

AI 在此架構中不作為最終裁決者；它的價值是提高分析效率與可讀性，而不是取代 deterministic safety boundary。
