# Sentinel Project — AI 輔助藍隊安全分流系統

Sentinel Project 是一個防禦導向的資安威脅偵測與應變展示系統，用來示範藍隊分析師如何在可解釋、可控、可驗證的流程中處理可疑事件。

## 專題動機

這個專題的重點不是讓 AI 直接判斷「是不是攻擊」，也不是讓 AI 自動封鎖或處置事件。相反地，本系統把最終偵測與風險判定保留在可檢查的 deterministic logic 中，再讓 AI / RAG 相關功能協助分析師理解原因、補足背景、比較案例、整理證據缺口與產生報告。

換句話說，AI 在這個專題中是分析輔助層，不是最終裁決者。

## 系統架構流程

```text
使用者輸入
→ Rule-Based Detector
→ 攻擊分類
→ Risk Level
→ Decision
→ AI / RAG 輔助解釋
→ 報告輸出
```

這條流程刻意把「判定權」與「說明權」分開：Rule-Based Detector 與 deterministic policy 負責判定，AI Analyst Brief、Evidence Gap Analyzer、Knowledge Q&A / RAG、Similar Cases 與 Graph 則負責提供分析師參考。

## 核心設計理念

- 攻擊偵測是 rule-based，不是 AI 判斷。
- Risk Level / Decision 由 deterministic logic 產生。
- `BLOCK` / `MONITOR` / `ALLOW` 是 simulated decisions，只代表系統展示中的建議狀態。
- RAG / LLM / AI Analyst Brief / Evidence Gap Analyzer 只提供分析師參考，不覆蓋最終判定。
- 歷史案例、知識庫回答與關係圖都不能證明目前事件已成功入侵或已成功執行。

## 目前功能亮點

- Fast deterministic mode：快速執行規則式偵測與確定性分流。
- Full AI-assisted mode：保留可選的 AI / RAG 輔助分析路徑。
- Lazy RAG startup：避免啟動時過早載入 Chroma、embedding、Torch 等重型依賴。
- Language-aware output：UI 語言會影響 AI Analyst Brief、Evidence Gap 與 RAG 回答風格。
- AI Analyst Brief：整理目前事件、判定原因、分析摘要與下一步建議。
- Evidence Gap Analyzer：列出已確認事實、缺少的證據、建議檢查項目與不安全假設。
- Knowledge Q&A / RAG：回答防禦導向的資安知識問題。
- Approved Similar Cases：讀取人工核准的相似案例種子資料，供分析比較。
- Relationship Graph：展示目前事件、風險、決策、案例與關係脈絡。
- Case Draft：產生需要人工審查的案例草稿。
- Markdown Export：提供報告匯出預覽。
- HTTP/2 Resource Exhaustion safe synthetic demo：以合成事件摘要示範 HTTP/2 / Resource Exhaustion / DoS 分流，不產生真實流量。

## 安全邊界

- No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action.
- No exploit, PoC, or traffic generation.
- Human review required.
- Detector remains rule-based.
- Risk Level / Decision remain deterministic.
- `BLOCK` / `MONITOR` / `ALLOW` remain simulated.
- RAG / LLM / AI Analyst Brief / Evidence Gap Analyzer are advisory only.

## 快速開始

以下為通用 PowerShell 範例，請依自己的環境替換 repo URL 與 Python/venv 設定。

```powershell
git clone <your-repo-url>
cd sentinel_project
.\venv\Scripts\Activate.ps1
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```

CLI 模式：

```powershell
python app.py
```

如果重建環境後 Knowledge Q&A / RAG 無法使用，請確認本機知識索引是否已建立，再依專案文件執行必要的索引建立流程。

## Demo 操作建議

1. 開啟 Streamlit console。
2. 選擇 Fast deterministic mode。
3. 載入 Command Injection demo 或 HTTP/2 Resource Exhaustion safe demo。
4. 點擊 Run input。
5. 查看 AI Analyst Brief、Evidence Gap Analyzer、Knowledge Q&A / RAG、Approved Similar Cases、Relationship Graph、Case Draft 與 Markdown Export。
6. 說明安全邊界：這是 simulated decision，不會執行真實封鎖或處置。

建議展示順序：

- 先用 Command Injection 展示 `HIGH / BLOCK` 的 deterministic path。
- 再展示 AI Analyst Brief 與 Evidence Gap Analyzer 如何協助分析師理解事件。
- 接著展示 Similar Cases、Graph 與 Export。
- 最後載入 HTTP/2 Resource Exhaustion safe demo，強調它是合成事件摘要，不產生流量，也不提供 exploit / PoC。

## 文件與截圖

- [User Operation Guide](docs/USER_OPERATION_GUIDE.md)
- [Test Report](docs/TEST_REPORT.md)
- [Code Review Audit](docs/CODE_REVIEW_AUDIT.md)
- [Demo Index](docs/DEMO_INDEX.md)
- [Screenshot Index](docs/screenshots/README.md)

## 測試與驗證

目前 release gate / final validation 摘要：

- pytest：`1168 passed`
- ruff：passed
- mypy：passed
- gitleaks：passed，並使用 `.gitleaksignore` 處理 false-positive cases
- screenshot refresh：completed

這些驗證代表目前 demo flow、語言感知輸出、Lazy RAG startup、AI advisory panels 與截圖文件已完成同步。它們不代表系統具備 production IDS / IPS 能力。

## 非目標 / 限制

- 這不是 production IDS / IPS。
- 不會真的封鎖攻擊。
- 不做紅隊攻擊工具。
- 不產生攻擊流量。
- 不提供 exploit 或 PoC。
- AI 不作為最終裁決者。
- RAG、LLM、相似案例與關係圖都只提供分析脈絡，不覆蓋 Rule-Based Detector 與 deterministic Decision。
