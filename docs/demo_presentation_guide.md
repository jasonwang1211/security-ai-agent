# Demo Presentation Guide / 展示簡報指南（5 分鐘）

本文件協助你準備 **5 分鐘的大學課程展示 / Demo 影片 / 面試說明**。
主語言為繁體中文，技術名詞保留英文（例如 Rule-Based Detection、RAG、Graph、CASE-SEED-001、HIGH / BLOCK / MONITOR）。

> 真正可運作的系統是 Streamlit SOC 主控台。
> `docs/demo_showcase.html` 是純前端的視覺展示頁（presentation only），不是後端系統。

---

## 1. 展示目標 / Presentation Goal

用 5 分鐘清楚說明：

- 這是一個**防禦性、學術用途**的資安分流（triage）原型。
- 偵測核心是 **Rule-Based Detection（規則式偵測）**，不是用 LLM 當主要偵測器。
- Risk / Decision 是**確定性（deterministic）的專案決策**。
- `BLOCK / MONITOR / ALLOW` 都是**模擬決策（simulated）**，不會觸發任何真實防護動作。
- RAG / 相似案例 / 關係圖譜是**給分析師的解釋與情境（advisory context）**，不是最終判斷依據。
- 任何案例草稿在被信任或提升前，**都需要人工審查（human review required）**。

一句話總結：
> 「確定性偵測為地基，AI 與圖譜只負責解釋與情境，所有動作都是模擬，最後仍要人來把關。」

---

## 2. 建議開場流程 / Recommended Opening Flow

1. 開啟 `docs/demo_showcase.html`（視覺開場，建立印象）。
2. 解說系統架構流程（pipeline）。
3. 切換到 Streamlit 主控台（真正的系統）。
4. 執行 Command Injection 示範。
5. 點擊 Find Similar Cases。
6. 顯示 Graph Relations（關係圖）。
7. 顯示 Case Draft / Export Report。
8. 說明 Safety Boundary（安全邊界）。

啟動 Streamlit：

```powershell
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```

---

## 2b. 螢幕截圖示範路徑 / Screenshot-Guided Path

若無法現場啟動，或要做投影片 / 錄影，可直接照下列截圖順序講解（檔案在 `docs/screenshots/`）。
**主線一律用 Fast deterministic 模式**（快速、穩定、可重現）。

| 段落 | 截圖 | 重點 |
|---|---|---|
| 介紹主控台 | [01_console_home.png](screenshots/01_console_home.png) | SOC 主控台、示範情境啟動器、尚無 active context |
| 命令注入（主線，Fast） | [02_fast_command_injection_analysis.png](screenshots/02_fast_command_injection_analysis.png) | `Command Injection` / `HIGH` / `BLOCK`，⚡ Fast 模式橫幅 |
| AI Analyst 追問 | [04_ai_analyst_followup.png](screenshots/04_ai_analyst_followup.png) | 確定性追問解釋；命中規則 ≠ 已執行 |
| RAG 知識問答 | [05_knowledge_qa_rag.png](screenshots/05_knowledge_qa_rag.png) | RAG / 知識問答（advisory） |
| 關係圖譜 | [07_graph_relations.png](screenshots/07_graph_relations.png) | 目前事件 ↔ `CASE-SEED-001` 的共享關係 |
| 草稿 / 匯出 | [08_case_draft_export.png](screenshots/08_case_draft_export.png) | Case Draft（需核准）＋ Markdown 匯出 |

需要時也可插入 [06_similar_cases.png](screenshots/06_similar_cases.png)（核准相似案例 `CASE-SEED-001`）。

**加分 / 可選（bonus）：** [03_full_ai_assisted_analysis.png](screenshots/03_full_ai_assisted_analysis.png) —
Full AI-assisted 會跑 AI/RAG 說明層，畫面上有 `完整 AI 輔助` + `AI/RAG 輔助` 標記與紫色模式橫幅。
**首次執行較慢（模型暖機，約 30–60 秒）**，所以當作加分項展示，不要放在主線即時 demo。

---

## 3. 時間分配 / Suggested Timing Breakdown

| 時間 | 區段 | 內容 |
|---|---|---|
| 0:00–0:40 | 開場 Opening | 用 `demo_showcase.html` Hero 場景帶出題目與三個關鍵定位 |
| 0:40–1:30 | 架構 Architecture | 說明 `Input → Detector → Risk → Decision → RAG/Similar → Graph → Draft/Export` |
| 1:30–2:40 | 命令注入 Command Injection demo | 切到 Streamlit，跑 `test; rm -rf /tmp/test`，秀 HIGH / BLOCK |
| 2:40–3:30 | 相似案例 + 圖譜 | Find Similar Cases → CASE-SEED-001 → Graph Relations |
| 3:30–4:20 | 草稿 / 匯出 Draft & Export | Case Draft（需核准）→ Export Report（記憶體內 Markdown） |
| 4:20–5:00 | 安全邊界 + 結語 | 強調模擬、無真實動作、需人工審查 |

時間緊張時的取捨：優先保住「命令注入 demo」與「安全邊界」，相似案例 / 圖譜可口頭快速帶過。

---

## 4. 關鍵談話重點 / Key Talking Points

- **規則式偵測（Rule-Based Detection）**：用 YAML 規則（Detection-as-Code）偵測 Command Injection、SQL Injection、Path Traversal、XSS，結果可重現、可解釋。
- **確定性風險與決策**：相同輸入永遠得到相同的 Risk Level 與 Decision，方便驗證與教學。
- **RAG / 相似案例的角色**：從**人工整理且核准**的案例種子中，找出結構化欄位相似的歷史案例，提供分析師參考脈絡。
- **關係圖譜（Graph）**：把目前事件與相似案例用「attack / rule / evidence / risk / decision / similar」這些關係連起來，是**解釋用**的視覺化，不是新的偵測器。
- **模擬決策**：`BLOCK / MONITOR / ALLOW` 是專案模擬的結果，純粹用於展示流程。
- **人工審查**：Case Draft 預設 `safety_reviewed: false`，需要人明確核准，系統不會自動寫入知識庫。
- **多語介面**：UI 支援 繁體中文 / English / 中英雙語，固定文字與安全說明都會跟著語言切換。

---

## 5. 要強調什麼 / What to Emphasize

- 偵測是 **rule-based**，可重現、可稽核。
- Risk / Decision 是 **deterministic** 的專案決策。
- RAG / 相似案例 / 圖譜是**解釋與情境**，不是主要偵測，也不決定最終風險。
- 所有決策都是 **simulated**。
- **Human review is required** 才能信任或提升草稿。

---

## 6. 不要誇大 / What NOT to Overclaim

請**不要**這樣說（這些都不是事實）：

- ❌ 系統會「真的攔截攻擊」。
- ❌ 系統會「控制真實防火牆 / WAF / EDR」。
- ❌ 系統用 LLM 來做「主要攻擊偵測」。
- ❌ RAG 決定最終的 risk / decision。
- ❌ 相似案例可以「證明」已遭入侵或已執行。
- ❌ Case Draft 是「自動可信的知識」。

請改成這樣說（誠實版本）：

- ✅ 偵測器是 rule-based。
- ✅ Risk / Decision 是 deterministic 的專案決策。
- ✅ `BLOCK / MONITOR / ALLOW` 是模擬決策。
- ✅ 相似案例與圖譜是分析師的參考脈絡（advisory）。
- ✅ RAG / AI 解釋是可選的、情境性的。
- ✅ 信任或提升草稿前必須人工審查。

---

## 7. 後備方案 / Backup Plan（Full AI-assisted 模式很慢時）

- **預設使用 Fast deterministic 模式**展示：偵測 / 風險 / 決策完全確定且快速，不依賴 LLM / RAG。
- 若 Full AI-assisted 模式（orchestrator / LLM）反應慢或環境未就緒：
  - 直接說明「AI 解釋層是可選的，核心結論不依賴它」，然後繼續用 Fast 模式。
  - 或改用 `docs/demo_showcase.html` 的對應場景，用視覺方式講解。
- 若 Streamlit 啟動有問題：先用 `docs/demo_showcase.html` 完整講完流程，再回頭排除環境問題。
- 事前先按 `docs/final_demo_smoke_checklist.md` 跑過一次，避免臨場出錯。

---

## 8. 相關文件 / Related Docs

- 視覺展示頁：`docs/demo_showcase.html`
- 口語逐字稿：`docs/demo_script_5min.md`
- 上台前檢查表：`docs/final_demo_smoke_checklist.md`
