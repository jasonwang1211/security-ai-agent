# Sentinel Project — AI 輔助藍隊安全分流系統

## 專案簡介

Sentinel Project 是一個防禦導向的資安威脅偵測與應變展示系統。主要展示介面是 Streamlit Analyst Console，而不是後端 API。使用者可以透過 UI 載入安全示範情境、執行 deterministic analysis、查看 AI advisory panels、比較 approved cases、檢視 Relationship Graph，並產生需要 Human review 的報告草稿與 Markdown Export。

本專題的重點不是讓 AI 直接判斷攻擊，而是示範一條可解釋、可控制、可展示給教授與專題評審理解的藍隊分析流程。

## 為什麼做這個專題

許多 AI 資安展示容易讓人誤以為 AI 可以直接決定「這是不是攻擊」或「系統要不要封鎖」。在真實安全場景中，這很危險，因為 LLM 可能產生 hallucination、過度推論，或把缺乏證據的情境說成已確認入侵。

Sentinel Project 採用 deterministic first, AI advisory second 的設計。Rule-Based Detector 與 deterministic policy 負責偵測、Risk Level 與 Decision；AI Analyst Brief、Evidence Gap Analyzer、Knowledge Q&A / RAG、Approved Similar Cases 與 Relationship Graph 則協助分析師理解與複核。

## 系統流程

```text
使用者輸入 / demo scenario
  -> Rule-Based Detector
  -> 攻擊分類
  -> deterministic Risk Level
  -> simulated Decision
  -> advisory context
     -> AI Analyst Brief
     -> Evidence Gap Analyzer
     -> Knowledge Q&A / RAG
     -> Approved Similar Cases
     -> Relationship Graph
  -> Human-reviewed Case Draft / Markdown Export
```

## Streamlit UI 是主展示介面

UI entry point:

```text
ui/streamlit_app.py
```

啟動指令：

```powershell
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```

建議 Demo 操作流程：

1. 選擇 Fast deterministic mode。
2. 載入 Command Injection demo 或 HTTP/2 Resource Exhaustion safe demo。
3. 點擊 Run input。
4. 查看 attack type、Risk Level、simulated Decision。
5. 查看 AI Analyst Brief 與 Evidence Gap Analyzer。
6. 查看 Knowledge Q&A / RAG、Approved Similar Cases、Relationship Graph。
7. 查看 Case Draft 與 Markdown Export。

## Demo 功能亮點

- Fast deterministic mode：快速產生可重現的偵測與分流結果。
- Full AI-assisted mode：提供可選的 AI/RAG 輔助分析路徑。
- Lazy RAG startup：避免啟動時就載入 heavy RAG / embedding dependency。
- Language-aware output：advisory panels 會依 UI 語言設定呈現。
- AI Analyst Brief：摘要目前事件、風險意義、建議下一步與不安全假設。
- Evidence Gap Analyzer：列出 confirmed facts、missing evidence、review tasks 與 unsafe assumptions。
- Knowledge Q&A / RAG：回答防禦導向資安問題，例如 HTTP/2 DoS、CVE 與 Resource Exhaustion。
- Approved Similar Cases：讀取 approved seed cases，提供相似案例與差異比較。
- Relationship Graph：以圖像方式呈現目前事件、案例與關聯資訊。
- Case Draft / Markdown Export：產生需要 Human review 的報告素材。
- HTTP/2 Resource Exhaustion safe synthetic demo：提供安全的 synthetic incident summary，不產生攻擊流量。

## 安全邊界

- 偵測是 Rule-Based Detector，不是 AI 判斷。
- Risk Level / Decision 是 deterministic。
- BLOCK / MONITOR / ALLOW 是 simulated。
- RAG / LLM / AI Analyst Brief / Evidence Gap 只提供 advisory context。
- 不做真實 firewall / WAF / EDR / account / cloud / SIEM / SOAR 動作。
- 不提供 exploit / PoC / traffic generation。
- 需要 Human review。

## 快速開始

```powershell
git clone <your-repo-url>
cd sentinel_project
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```

## 文件導覽

- [English README](../../README.md)
- [English Project Report](../../REPORT.md)
- [UI Walkthrough](../UI_WALKTHROUGH.md)
- [User Operation Guide](../USER_OPERATION_GUIDE.md)
- [Screenshot Gallery](../screenshots/README.md)（繁中 UI 截圖保留於 `docs/screenshots/zh-TW/`，英文 UI 截圖見 `docs/screenshots/en/`）
- [Test Report](../TEST_REPORT.md)
- [Code Review Audit](../CODE_REVIEW_AUDIT.md)

## 測試與驗證

目前 v2.8 demo-ready 驗證摘要：

- pytest：`1168 passed`
- ruff：passed
- mypy：passed
- gitleaks：passed
- screenshot refresh：completed

這些驗證代表 demo behavior 與 safety boundary 有被測試，不代表 production IDS/IPS effectiveness。

## 限制與未來工作

本專案不是 production IDS/IPS，不是 red-team tool，不提供 exploit generator，也不是 autonomous response system。未來可以持續補強更多 defensive synthetic scenarios、analyst timeline / event replay、read-only graph 與 approved-case memory，以及更完整的報告匯出流程。
