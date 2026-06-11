# Final Demo Smoke Checklist / 最終展示檢查表

Use this checklist before a live professor/reviewer demo. It is written for the current v2.8 Streamlit SOC Analyst Console.

本檢查表適用於 v2.8 Streamlit SOC 分析主控台展示前的最後確認。

## 1. Git State / Git 狀態

```powershell
git branch --show-current
git rev-parse --short HEAD
git status --short --untracked-files=all
```

- [ ] You are on the expected demo branch.
- [ ] The current HEAD is the expected review baseline.
- [ ] Any uncommitted files are intentional documentation/screenshot work.
- [ ] No release tag, push, merge, reset, clean, or delete action is performed during smoke.

## 2. Environment / 環境確認

```powershell
.\venv\Scripts\python.exe --version
.\venv\Scripts\python.exe -m streamlit --version
```

- [ ] Virtual environment exists.
- [ ] Streamlit is available.
- [ ] Browser can open localhost.
- [ ] Optional local AI/RAG services are available only if you plan to show Full AI-assisted mode.

## 3. Start Console / 啟動主控台

```powershell
.\venv\Scripts\python.exe -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```

- [ ] Console opens without StreamlitAPIException.
- [ ] Language selector displays Traditional Chinese, English, and bilingual labels.
- [ ] Analysis mode selector is visible.
- [ ] Demo Scenario Launcher is visible.
- [ ] HTTP/2 Resource Exhaustion launcher card shows a short preview rather than the full synthetic incident summary.

## 4. Core Fast Demo / 核心快速展示

- [ ] Select Fast deterministic mode.
- [ ] Run Command Injection input: `test; rm -rf /tmp/test`.
- [ ] Active Context shows event context.
- [ ] Result shows Command Injection.
- [ ] Risk Level is `HIGH`.
- [ ] Decision is simulated `BLOCK`.
- [ ] Safety Boundary does not claim real enforcement.

## 5. AI Analyst Panels / AI 分析面板

Open the AI Analyst tab.

- [ ] AI Analyst Brief appears first.
- [ ] AI Analyst Brief states deterministic advisory / no LLM.
- [ ] AI Analyst Brief output follows the selected UI language.
- [ ] Evidence Gap Analyzer appears after AI Analyst Brief.
- [ ] Evidence Gap output follows the selected UI language.
- [ ] Follow-up Assistant appears after Evidence Gap Analyzer.
- [ ] Knowledge Q&A appears after Follow-up Assistant.
- [ ] Evidence Gap content lists missing evidence instead of claiming confirmed execution.

## 6. Knowledge Q&A / 知識問答

Ask one or more safe defensive questions:

- [ ] `HTTP/2 Resource Exhaustion 是什麼？`
- [ ] `HTTP/2 Bomb 疑似事件要怎麼安全分流？`
- [ ] `CVE 情報可以直接當成資產已被利用的證明嗎？`
- [ ] `HTTP/2 DoS 有哪些防禦緩解方式？`
- [ ] `Resource Exhaustion 證據缺口要看什麼？`

Expected:

- [ ] Routes to Knowledge Q&A / RAG.
- [ ] Output follows the selected UI language.
- [ ] Uses defensive advisory wording.
- [ ] Does not provide exploit, PoC, or traffic-generation instructions.
- [ ] Does not claim real enforcement.
- [ ] Does not confuse CVE with CVSS.
- [ ] States CVE context is not proof of exploitation.

## 7. Similar Cases / 相似案例

- [ ] Click Find Similar Cases after the Command Injection analysis.
- [ ] Approved Similar Cases shows `CASE-SEED-001`.
- [ ] Similarity reasons and key differences are visible.
- [ ] Output states historical cases are advisory only and do not override current Risk Level or Decision.

Optional additional checks:

- [ ] SQL Injection scenario maps to `CASE-SEED-003`.
- [ ] Authentication incident scenario maps to `CASE-SEED-002`.
- [ ] Authentication output says repeated failures followed by success are suspicious but do not prove compromise by themselves.

## 8. Graph Relations / 關係圖

- [ ] Graph Relations tab shows current event relationships.
- [ ] Nodes/relationships include current event, attack type, rule, evidence, risk, decision, and similar case where available.
- [ ] Graph output does not claim to be detection authority.
- [ ] After a new analysis run, stale similar-case or graph lines from the old context do not remain.

## 9. Case Draft and Export / 案例草稿與匯出

- [ ] Case Draft tab shows request/approve/cancel behavior as expected.
- [ ] Draft wording keeps human-review boundary.
- [ ] Export Report tab renders copyable report content.
- [ ] Export does not write report files to disk automatically.
- [ ] Export does not change Risk Level, Decision, or case state.

## 10. HTTP/2 Resource Exhaustion Safe Demo / HTTP/2 資源耗盡安全展示

- [ ] Demo Scenario Launcher includes `HTTP/2 Resource Exhaustion Suspicion`.
- [ ] Launcher card preview is compact and does not dominate the homepage.
- [ ] Loading the scenario fills the main textarea with the full synthetic incident summary.
- [ ] Scenario text says no traffic generated.
- [ ] Scenario text says no real enforcement.
- [ ] Scenario text says human review is required.
- [ ] AI Analyst Brief and Evidence Gap Analyzer still appear.
- [ ] RAG questions about HTTP/2 DoS stay defensive.

## 11. Screenshot Evidence / 截圖證據

Confirm these files exist under `docs/screenshots/`:

- [ ] `01_console_home.png`
- [ ] `02_fast_command_injection_analysis.png`
- [ ] `03_ai_analyst_brief.png`
- [ ] `04_evidence_gap_analyzer.png`
- [ ] `05_knowledge_qa_rag.png`
- [ ] `06_similar_cases.png`
- [ ] `07_relationship_graph.png`
- [ ] `08_case_draft_export.png`
- [ ] `09_http2_resource_exhaustion_demo.png`
- [ ] `10_full_ai_assisted_optional.png`

## 12. Safety Boundary To Say Aloud / 現場口頭安全邊界

- [ ] Detector remains rule-based.
- [ ] Risk Level / Decision remain deterministic.
- [ ] `BLOCK`, `MONITOR`, and `ALLOW` are simulated.
- [ ] RAG / LLM / AI Analyst Brief / Evidence Gap are advisory only.
- [ ] No real firewall, WAF, EDR, account, cloud, SIEM, or SOAR action is performed.
- [ ] No exploit, PoC, or traffic generation is included.
- [ ] Human review is required.

## 13. Backup Plan / 備援方案

- [ ] If Streamlit is slow, use the screenshot guide in [screenshots/README.md](screenshots/README.md).
- [ ] If Full AI-assisted mode is slow, stay in Fast deterministic mode.
- [ ] If Knowledge Q&A is slow on first use, explain v2.8 lazy-loads RAG only when needed.
- [ ] If a live browser issue occurs, use [USER_OPERATION_GUIDE.md](USER_OPERATION_GUIDE.md) and [DEMO_INDEX.md](DEMO_INDEX.md) as static evidence.

## 14. Validation References / 驗證參考

- [TEST_REPORT.md](TEST_REPORT.md)
- [CODE_REVIEW_AUDIT.md](CODE_REVIEW_AUDIT.md)
- [v2.7_release_gate.md](v2.7_release_gate.md)
- [v2.7_manual_smoke_report.md](v2.7_manual_smoke_report.md)
