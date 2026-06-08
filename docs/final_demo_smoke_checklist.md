# Final Demo Smoke Checklist / 上台前最終檢查表

展示 / 錄影 / 面試**前**，依序跑過這份檢查表。全部勾完再上台。
（本檔為文件，不會改動任何後端或 UI 行為。）

---

## 1. Git 狀態檢查 / Git State

```powershell
git status --short --untracked-files=all   # 應乾淨，或只有預期中的未提交變更
git log -1 --oneline                       # 確認在預期的 commit
git stash list                             # 確認延後的 stash 仍在
```

- [ ] 工作目錄狀態符合預期（沒有意外修改）。
- [ ] 目前分支 / commit 正確。
- [ ] 延後的 `stash@{0}`（v2.3-B mode3 graph expansion）仍存在。

---

## 2. Python / venv 檢查 / Environment

```powershell
.\venv\Scripts\python.exe --version        # 確認虛擬環境的 Python
.\venv\Scripts\python.exe -m pytest -q      # （可選）確認測試全綠
```

- [ ] venv 可用，相依套件已安裝。
- [ ] （可選）pytest 全數通過。

---

## 3. Streamlit 啟動 / Start the Console

```powershell
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```

- [ ] 瀏覽器開啟主控台，畫面為深色 cyber/SOC 風格。
- [ ] 上方 SOC 狀態列、控制面板、示範卡片正常顯示。

---

## 4. 視覺展示頁 / Showcase Page

直接用瀏覽器開啟：`docs/demo_showcase.html`

- [ ] 頁面可直接開啟（不需後端）。
- [ ] 鍵盤 `←` / `→` / `Space` 可切換場景，`P` 可暫停。
- [ ] Previous / Next / Pause(Play) 按鈕正常。
- [ ] 7 個場景都能正常顯示（Hero、架構、命令注入、驗證事件、圖譜、草稿/匯出、安全邊界）。

---

## 5. 示範情境 / Demo Scenarios（在 Streamlit 內）

預設使用 **Fast deterministic** 模式（快速、確定性、不依賴 LLM/RAG）。
從「示範情境啟動器」載入輸入，按「執行輸入」。

| 示範 | 輸入 | 預期結果 |
|---|---|---|
| Command Injection Demo | `test; rm -rf /tmp/test` | **Command Injection / HIGH / BLOCK / CASE-SEED-001** |
| SQL Injection Demo | `?id=1' OR '1'='1` | **SQL Injection / HIGH / BLOCK / CASE-SEED-003** |
| Authentication Incident Demo | `demo_logs\scenario_a_mixed_auth.log` | **Possible Account Compromise / HIGH / MONITOR / CASE-SEED-002** |

- [ ] Command Injection → HIGH / BLOCK，Find Similar Cases → CASE-SEED-001。
- [ ] SQL Injection → HIGH / BLOCK，Find Similar Cases → CASE-SEED-003。
- [ ] Auth incident → HIGH / MONITOR，Find Similar Cases → CASE-SEED-002。
- [ ] 動態值（payload、CMD-001、shell_metacharacter_payload、incident ID、EV/F-ID）顯示正常且未被翻譯。

---

## 6. 語言檢查 / Language Checks

切換「介面語言 / Interface Language」：

- [ ] 繁體中文：固定標籤與安全說明為中文。
- [ ] English：固定標籤與安全說明為英文。
- [ ] 中英雙語：固定標籤為精簡的「中 / English」格式。
- [ ] 切換語言後，動態值（risk/decision/case ID/路徑/payload）維持不變。

---

## 7. 各面板檢查 / Panel Checks

- [ ] **Graph Relations**：互動式關係圖可顯示節點與關係（attack / rule / evidence / risk / decision / similar）。
- [ ] **Export Report**：可預覽 Markdown，安全說明與包裝段落為對應語言；下載按鈕可用，且不會在 repo 寫入檔案。
- [ ] **Case Draft**：Request / Approve / Cancel 行為正常；安全邊界 bullet 為對應語言；`safety_reviewed` 預設 false。
- [ ] **Safety Boundary**：每次執行都顯示模擬與權限邊界。
- [ ] **Performance / Route / Policy**：計時與路由/政策資訊正常顯示。

---

## 8. 現場展示要避免的事 / Things to Avoid During Live Demo

- 不要宣稱系統「真的攔截攻擊」或「控制真實防火牆 / WAF / EDR」。
- 不要說 LLM 是主要偵測器，或 RAG 決定最終 risk/decision。
- 不要說相似案例「證明」已遭入侵。
- 不要在現場才第一次切到 Full AI-assisted 模式（可能較慢）；先用 Fast 模式。
- 不要在展示途中編輯程式碼或重啟環境（Streamlit 會 rerun）。
- 不要承諾即時的雲端 / 外部呼叫；本專案不做真實外部動作。

---

## 9. 臨場排錯 / Last-Minute Troubleshooting

- **Streamlit 開不起來**：先用 `docs/demo_showcase.html` 完整講解流程，之後再排錯。
- **檔案監看造成 rerun 異常**：確認有加 `--server.fileWatcherType none`。
- **Full AI-assisted 很慢 / 未就緒**：改用 Fast deterministic 模式，並說明「AI 解釋層是可選的，核心結論不依賴它」。
- **Auth 示範找不到日誌**：確認從專案根目錄啟動，且 `demo_logs\scenario_a_mixed_auth.log` 存在。
- **語言沒變**：重新從「介面語言」下拉選擇一次；本變更只影響固定文字，不影響動態結果。
- **畫面太亮 / 對比不足**：本專案已內建深色主題（`.streamlit/config.toml`）；若仍異常，重新整理頁面。

---

## 10. 一頁式快速口訣 / One-Line Reminders

- 偵測 = rule-based。
- Risk / Decision = deterministic 專案決策。
- BLOCK / MONITOR / ALLOW = simulated。
- RAG / 相似案例 / 圖譜 = advisory 解釋與情境。
- Draft 需 human review 才能信任或提升。
