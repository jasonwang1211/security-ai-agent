# Sentinel Project — AI 輔助藍隊安全分流原型 / AI-Assisted Blue-Team Security Triage Prototype

## 專案摘要 / Project Summary

Sentinel Project 是防禦導向的 SOC 分流展示系統。它把 rule-based detection、deterministic Risk Level / Decision 與 simulated response 保留為安全底線，再用 AI Analyst Brief、Evidence Gap、RAG Knowledge Q&A、Approved Similar Cases、Relationship Graph、Case Draft 與 Export Report 提供分析師參考。

Sentinel Project is a defensive SOC-style triage prototype. Rule-based detection and deterministic risk/decision logic remain the authority path, while AI/RAG-style panels provide advisory analyst context only.

## 目前亮點 / Current Highlights

- 規則式偵測 Command Injection、SQL Injection、Path Traversal、XSS。
- Deterministic Risk Level 與 simulated `BLOCK` / `MONITOR` / `ALLOW`。
- Streamlit SOC Analyst Console，支援 Fast deterministic 與 Full AI-assisted mode。
- UI 語言選擇會影響 AI Analyst Brief、Evidence Gap 與 Knowledge Q&A output：`zh-TW` 以繁體中文為主，`en` 使用英文，`bilingual` 使用精簡中英雙語。
- HTTP/2 Resource Exhaustion demo card 使用短 preview；Load Scenario 仍會把完整 synthetic incident summary 放入主 textarea。
- AI Analyst Brief、Evidence Gap Analyzer、Knowledge Q&A / RAG、Approved Similar Cases、Relationship Graph。
- Case Draft 與 Markdown Export preview 保留 human-review boundary。
- v2.8 lazy RAG startup：Fast path 不會 eager-load Chroma / embeddings / Torch stack。

## 安全邊界 / Safety Boundary

- Detector remains rule-based.
- Risk Level / Decision remain deterministic.
- `BLOCK` / `MONITOR` / `ALLOW` are simulated project decisions.
- RAG / LLM / AI Analyst Brief / Evidence Gap are advisory only.
- No real firewall, WAF, EDR, account, cloud, SIEM, or SOAR action is performed.
- No exploit, PoC, or traffic generation is provided.
- Human review is required before operational action, case promotion, or knowledge promotion.

## 快速開始 / Quick Start

```powershell
cd C:\Users\jason\Desktop\sentinel_project
.\venv\Scripts\Activate.ps1
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```

CLI mode:

```powershell
python app.py
```

If Knowledge Q&A is unavailable after an environment rebuild, intentionally rebuild the local RAG index:

```powershell
python ingest_knowledge.py
```

## 建議展示流程 / Recommended Demo Path

1. 啟動 Streamlit console。
2. 選擇 UI 語言，確認輸出語言會跟著切換。
3. 載入 Command Injection demo。
4. 執行 Fast deterministic analysis，展示 `HIGH / BLOCK`。
5. 開啟 AI Analyst Brief 與 Evidence Gap Analyzer，確認繁體中文/英文/雙語輸出。
6. 詢問 Knowledge Q&A，例如 HTTP/2 DoS 或 CVE 問題。
7. Click Find Similar Cases and show `CASE-SEED-001`.
8. Show Relationship Graph.
9. Show Case Draft / Export preview.
10. Load the safe HTTP/2 Resource Exhaustion demo; card preview is short, full input remains safety-complete.

## 文件連結 / Documentation Links

- [User Operation Guide](docs/USER_OPERATION_GUIDE.md)
- [Test Report](docs/TEST_REPORT.md)
- [Code Review Audit](docs/CODE_REVIEW_AUDIT.md)
- [Screenshot Index](docs/screenshots/README.md)
- [Demo Index](docs/DEMO_INDEX.md)
- [Demo Presentation Guide](docs/demo_presentation_guide.md)
- [Final Demo Smoke Checklist](docs/final_demo_smoke_checklist.md)
- [v2.7 Release Notes](docs/v2.7_release_notes.md)
- [v2.7 Release Gate](docs/v2.7_release_gate.md)
- [v2.8 Startup Import Audit](docs/v2.8_startup_import_audit.md)
- [v2.8 Cache Cleanup Checklist](docs/v2.8_cache_cleanup_checklist.md)

## 架構摘要 / Architecture Summary

```text
User input or demo scenario
-> Streamlit UI or CLI
-> Controller / Orchestrator
-> Rule-Based Detector and Log Pipeline
-> TriagePolicy deterministic risk/decision
-> Simulated response notice
-> Advisory layers: AI Analyst Brief, Evidence Gap, RAG Q&A, Similar Cases, Graph
-> Human-reviewed Case Draft / Export
```

Authoritative path: deterministic detection and policy. Advisory layers explain, compare, translate output style, and identify evidence gaps, but they do not override the current event's Risk Level or Decision.

## 驗證快照 / Validation Snapshot

- v2.7 release gate: pytest `1140 passed in 15.75s`, ruff passed, mypy passed on rerun, `git diff --check` passed, Gitleaks passed with `216 commits scanned`, `no leaks found`.
- v2.8-C lazy RAG validation: startup regression tests `4 passed`, RAG focused tests `94 passed`, fast/UI analysis tests `26 passed`, full pytest `1144 passed in 11.85s`, ruff passed, mypy passed with `Success: no issues found in 160 source files`.
- v2.8-D Fix Pass adds language-aware output policy and HTTP/2 short preview tests; see [docs/TEST_REPORT.md](docs/TEST_REPORT.md) for current command results.

## 非目標 / Non-Goals

這不是 production SOC platform、WAF、EDR、SIEM、SOAR、exploit framework、traffic generator 或 autonomous enforcement system。

This is a defensive academic/demo prototype focused on clear safety boundaries, reviewable evidence, and professor-ready analyst UX.
