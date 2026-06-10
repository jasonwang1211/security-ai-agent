# 5-Minute Demo Script / 五分鐘口語逐字稿

這是可以**直接照著講**的口語稿（繁體中文為主，技術名詞保留英文）。
語氣自然、好唸即可，不需要是學術論文。每段標了大概的時間點。
搭配 `docs/demo_presentation_guide.md`（流程）與 `docs/final_demo_smoke_checklist.md`（事前檢查）。

> 講者提醒：全程強調「偵測是規則式、決策是模擬、AI 與圖譜只負責解釋、最後要人把關」。

---

## 0:00–0:40 開場 Opening（開 `docs/demo_showcase.html`，Hero 場景）

> 「大家好。我的專案是『AI 驅動之資安威脅偵測與應變系統』，是一個**防禦性、學術用途**的資安分流原型。
> 它的定位可以用三個關鍵字說明：**Deterministic Detection（確定性偵測）**、**Simulated Response（模擬應變）**、**Human-Reviewed Knowledge（人工審查的知識）**。
> 先說最重要的一句話：這個系統的偵測核心是**規則式（Rule-Based）**，不是用 LLM 去猜攻擊；而且它所有的決策都是**模擬的**，不會真的去動任何防火牆或主機。」

---

## 0:40–1:30 架構 Architecture（showcase 架構場景）

> 「先看整體流程。使用者輸入一段 payload 或一份 log，先進到 **Rule-Based Detector**，用 YAML 規則做偵測；接著 **Risk Scorer** 給風險等級，**Decision Engine** 產生模擬決策。
> 到這裡，風險和決策就已經確定了——相同輸入永遠得到相同結果，這是刻意設計的，方便驗證也方便教學。
> 後面三段是『加值的解釋層』：**RAG / 相似案例**從**人工核准**的案例庫找相似的歷史案例；**Graph** 把事件和案例的關係視覺化；最後可以做 **Case Draft** 與 **Markdown 報告匯出**。
> 重點是：RAG 和 Graph 都是**給分析師看的脈絡**，它們**不會**改變前面的風險或決策。」

---

## 1:30–2:40 命令注入示範 Command Injection（切到 Streamlit）

`[截圖 / Screenshot: 01_console_home.png → 02_fast_command_injection_analysis.png]`（主線用 Fast deterministic 模式）

> 「現在切到真正的系統——這是一個 Streamlit 的 SOC 主控台。我用內建的『命令注入示範』。
> 輸入是 `test; rm -rf /tmp/test`，這裡有 shell 串接符號。我用 **Fast deterministic** 模式執行。
> 結果出來：偵測為 **Command Injection**，命中規則 **CMD-001**，風險是 **HIGH**，決策是 **BLOCK**。
> 這裡要特別講清楚：**這個 BLOCK 是模擬決策**，系統並沒有真的去封鎖任何東西、也沒有改任何防火牆設定。它只是把『如果是真實環境，建議怎麼處理』用模擬的方式呈現出來。」

---

## 2:40–3:30 相似案例 + 圖譜 Similar Case & Graph

`[截圖 / Screenshot: 06_similar_cases.png → 07_graph_relations.png]`

> 「接著我按 **Find Similar Cases**。系統從**已人工核准**的案例種子裡，依結構化欄位找出最相似的歷史案例——這裡找到 **CASE-SEED-001**。
> 注意：相似案例只是**參考脈絡**，它不會證明真的被入侵，也不會改變剛剛的 HIGH / BLOCK。
> 再看 **Graph Relations**。這張關係圖把『目前事件』和相似案例,用 **attack、rule、evidence、risk、decision、similar** 這些關係連起來。
> 它的價值是**解釋**：讓分析師一眼看出『為什麼系統覺得這兩個案例相關』,而不是再去做一次偵測。」

> （可選 30 秒）切到 **AI Analyst** 分頁：`[截圖 / Screenshot: 04_ai_analyst_followup.png → 05_knowledge_qa_rag.png]`
> 「追問助理用**目前事件的脈絡**做確定性解釋（例如『命中規則不代表命令真的執行了』）；知識問答則是 **RAG** 的資安知識查詢。兩者都標示**僅供參考**，不會覆蓋 Risk Level 或 Decision。」

---

## 3:30–4:20 草稿 / 匯出 Draft & Export

`[截圖 / Screenshot: 08_case_draft_export.png]`

> 「分析完之後,分析師可以把這個事件**擷取成 Case Draft**。
> 但這裡有一個刻意的設計:草稿預設是 `safety_reviewed: false`,而且**需要明確的人工核准**才會寫出檔案。系統**不會自動**把它寫進正式知識庫、也不會自動提升成可信知識。
> 最後可以**匯出 Markdown 報告**,內容包含分析結果、相似案例、關係說明,以及安全說明。報告會提醒『分享前請先審查』,而且匯出是在記憶體內產生的,不會偷偷寫進專案。」

---

## 4:20–5:00 安全邊界 + 結語 Safety Boundary & Conclusion

> 「最後是這個專案最重要的部分——**安全邊界**。
> 我要很誠實地說明它**不會**做什麼:它**不會**執行真實的封鎖,**不會**控制真實的 firewall / WAF / EDR,**不會**停用帳號或重設密碼,也**不會**自動把草稿變成可信知識。
> 它**會**做的是:用可重現的規則式偵測產生確定性結論,用 RAG 和圖譜提供解釋與情境,並且**要求人工審查**才能信任或提升任何草稿。
> 所以這個專案的價值不是『取代 SOC』,而是示範一個**安全、可驗證、可解釋**的分流流程:確定性偵測當地基,AI 與圖譜負責解釋,所有動作都是模擬,最後仍然由人來把關。謝謝大家。」

---

## （加分 / 可選）Full AI-assisted bonus

`[截圖 / Screenshot: 03_full_ai_assisted_analysis.png]`

> 「如果還有時間，可以切到 **Full AI-assisted** 模式再跑一次——畫面會多出 `完整 AI 輔助` 與 `AI/RAG 輔助` 標記，代表多跑了 AI/RAG 說明層。
> 但要說明：**首次執行較慢**（模型暖機，約 30–60 秒），而且 **Risk Level 與 Decision 還是同一套確定性結果**，AI 只是多給了解釋。所以正式 demo 我用 Fast 模式，這個當加分展示。」

---

## 重點名詞速記 / Quick Term Notes（被問到時可補充）

- **為什麼用 rule-based 偵測?** 因為要可重現、可稽核、不會幻覺;在會影響「封鎖」這種決策時,確定性比彈性更重要。
- **AI / RAG 貢獻什麼?** 提供解釋與相似歷史案例的脈絡,幫助分析師判讀,但不決定最終風險或決策。
- **Graph 關係圖在表達什麼?** 目前事件與核准相似案例之間,在攻擊類型、規則、證據、風險、決策上的共享關係——是解釋用的視覺化。
- **為什麼 BLOCK / MONITOR / ALLOW 是模擬?** 這是學術原型,刻意不接真實防護設備,避免任何誤動作;決策只用於展示流程。
- **為什麼需要人工審查?** 因為自動化可能出錯,任何要進入知識庫或被信任的內容,都應該先經過人確認,才符合防禦性、負責任的設計。
