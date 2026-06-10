# Demo Index / 展示資料總覽

所有展示與簡報資料的單一入口。給 demo 評審 / 面試者 / 自己上台前使用。

## 啟動系統 / Run the Streamlit SOC console

```powershell
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```

## 展示資料 / Materials

| 用途 | 檔案 |
|---|---|
| 純前端視覺展示頁（瀏覽器直接開啟；僅供展示，非後端） | [demo_showcase.html](demo_showcase.html) |
| 五分鐘簡報指南（流程、時間分配、重點） | [demo_presentation_guide.md](demo_presentation_guide.md) |
| 五分鐘口語逐字稿（可照唸） | [demo_script_5min.md](demo_script_5min.md) |
| 上台前最終檢查表 | [final_demo_smoke_checklist.md](final_demo_smoke_checklist.md) |
| UI 截圖總覽 / Screenshot index | [screenshots/README.md](screenshots/README.md) |
| 專案說明 / README | [../README.md](../README.md) |

## 建議截圖示範路徑 / Recommended Screenshot Demo Path

主線使用 **Fast deterministic** 模式（快速、穩定）。依序帶過以下截圖即可講完核心故事：

1. [01_console_home.png](screenshots/01_console_home.png) — SOC 主控台與示範情境啟動器（尚無 active context）。
2. [02_fast_command_injection_analysis.png](screenshots/02_fast_command_injection_analysis.png) — Fast 確定性命令注入結果（`HIGH` / `BLOCK`，⚡ Fast 模式橫幅）。
3. [04_ai_analyst_followup.png](screenshots/04_ai_analyst_followup.png) — AI Analyst 追問助理（確定性追問解釋）。
4. [05_knowledge_qa_rag.png](screenshots/05_knowledge_qa_rag.png) — RAG / 知識問答。
5. [06_similar_cases.png](screenshots/06_similar_cases.png) — 核准相似案例（`CASE-SEED-001`）。
6. [07_graph_relations.png](screenshots/07_graph_relations.png) — 關係圖譜。
7. [08_case_draft_export.png](screenshots/08_case_draft_export.png) — 案例草稿 / 報告匯出。

**加分 / 可選（bonus, optional）**：

- [03_full_ai_assisted_analysis.png](screenshots/03_full_ai_assisted_analysis.png) — Full AI-assisted（`完整 AI 輔助` + `AI/RAG 輔助` 標記與紫色模式橫幅）。**首次執行較慢**（AI/RAG 模型暖機），建議當加分項而非主線。

## 預期示範結果 / Expected Demo Outputs

| 示範 | 輸入 | 預期 |
|---|---|---|
| Command Injection | `test; rm -rf /tmp/test` | HIGH / BLOCK / CASE-SEED-001 |
| SQL Injection | `?id=1' OR '1'='1` | HIGH / BLOCK / CASE-SEED-003 |
| Authentication Incident | `demo_logs\scenario_a_mixed_auth.log` | HIGH / MONITOR / CASE-SEED-002 |

## 邊界提醒 / Boundaries

- 偵測為規則式（rule-based），非以 LLM 作為主要偵測器。
- Risk / Decision 為確定性（deterministic）的專案決策。
- `BLOCK` / `MONITOR` / `ALLOW` 為模擬決策；不執行任何真實防火牆 / WAF / EDR / 帳號 / 監控動作。
- RAG、相似案例與關係圖僅為分析師參考脈絡（advisory），不決定最終 risk / decision，也不證明入侵。
- 草稿在被信任或提升前需人工審查（human review required）。
