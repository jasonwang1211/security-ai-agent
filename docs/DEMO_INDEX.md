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
| 專案說明 / README | [../README.md](../README.md) |

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
