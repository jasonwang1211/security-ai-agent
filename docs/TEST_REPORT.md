# Test Report / 測試報告

This report summarizes the validation evidence for the current Sentinel Project demo-ready state. It is documentation only and does not change runtime behavior.

本報告整理目前 Sentinel Project 展示狀態的驗證證據。本文件僅為文件更新，不改變執行邏輯。

## Validation Philosophy / 驗證原則

The project is tested around the safety boundary:

- Rule-based detector remains final detection authority.
- Risk Level and Decision remain deterministic.
- `BLOCK`, `MONITOR`, and `ALLOW` remain simulated.
- RAG / LLM / AI Analyst Brief / Evidence Gap are advisory only.
- No real firewall, WAF, EDR, account, cloud, SIEM, or SOAR action is performed.
- No exploit, PoC, or traffic generation is included.
- Human review is required.

## Current v2.8-D Fix Pass 2 Validation / 本次 v2.8-D 修正驗證

These commands were run after the v2.8-D Fix Pass 2 changes: RAG prompt language-policy completion (output follows the Output language policy instead of hardcoded Traditional-Chinese-only rules), demo-scenario load now clears stale active context, the HTTP/2 launcher preview renders as a readable summary instead of a code/log block, and this test report correction.

| Command | Result |
|---|---|
| Focused: `python -m pytest tests/test_output_language.py tests/test_ui_demo_scenarios.py tests/test_rag_qa_controlled_runtime.py tests/test_rag_intent.py tests/test_rag_controlled_retrieval.py tests/test_lazy_rag_startup.py tests/test_ai_advisory_brief.py tests/test_ai_advisory_evidence_gap.py tests/test_ui_ai_analyst_brief_view.py tests/test_ui_ai_advisory_view.py` | Passed: `158 passed` |
| `python -m ruff check .` | Passed: `All checks passed!` |
| `python -m mypy app.py modules tests` | Passed: `Success: no issues found in 162 source files` |
| `gitleaks detect --source . --verbose --redact` | Passed: `221 commits scanned`, `no leaks found` |
| `git diff --check` | Passed (only benign LF→CRLF normalization notices on text files). |
| `python -m pytest` (full suite) | Reran successfully: `1168 passed in 22.73s` — see the temp/cache caveat below. |
| `git status --short --untracked-files=all` | Completed; uncommitted changes are the Fix Pass 2 code/test edits plus documentation and screenshots. |

### Full pytest temp/cache caveat / 完整測試的暫存權限注意事項

An earlier v2.8-D full `python -m pytest` attempt did **not** finish as a clean full pass: it reached many passed tests but ended with a local temp/cache `PermissionError` during pytest `tmp_path` setup. That was a local environment temp/cache permission issue, **not** a test assertion failure. A full pass must not be claimed from such a run. After the temp/cache permission issue was resolved, the full suite was rerun and passed cleanly (`1168 passed in 22.73s`); the full-suite row above records that clean rerun. If the temp/cache permission issue recurs on another machine, rerun the full suite after clearing the temp/cache permission problem before claiming a full pass.

## v2.8-C Lazy RAG Validation Snapshot

The lazy-loading work introduced startup import protections and confirmed that heavy RAG/vector dependencies are not initialized on the fast deterministic startup path.

| Area | Evidence |
|---|---|
| Lazy RAG startup tests | `tests/test_lazy_rag_startup.py` passed. |
| Focused RAG tests | RAG and controlled runtime tests passed during v2.8-C validation. |
| Full suite | `1144 passed in 11.85s` during v2.8-C validation. |
| Static checks | ruff passed; mypy passed with `Success: no issues found in 160 source files`. |

## v2.7 Release Gate Snapshot

The v2.7 release gate evidence is recorded in [v2.7_release_gate.md](v2.7_release_gate.md). Key results:

| Command | Result |
|---|---|
| `python -m pytest` | `1140 passed in 15.75s` |
| `python -m ruff check .` | Passed |
| `python -m mypy app.py modules tests` | Passed on rerun with longer timeout: `Success: no issues found in 158 source files` |
| `git diff --check` | Passed |
| `gitleaks detect --source . --verbose --redact` | Passed: `216 commits scanned`, `no leaks found` |

## Test Coverage Areas / 測試涵蓋範圍

The automated suite covers:

- Detection rule loading and rule-based detector behavior.
- Log ingestion and authentication incident correlation.
- Evidence, finding, incident, and report schemas.
- Deterministic risk and decision behavior.
- Controller routing, ToolPolicy, skill catalog, and skill wrappers.
- RAG routing, retrieval planning, source assembly, answer guardrails, and controlled runtime behavior.
- CVE / CVSS terminology normalization and Resource Exhaustion knowledge routing.
- AI Advisory Brief backend and UI view helpers.
- Evidence Gap Analyzer backend and UI view helpers.
- Approved Similar Case retrieval and no-override boundary wording.
- Relationship graph builder, lookup, export, and UI view helpers.
- Case Draft, Case Memory, Export Report, route/policy, performance, and report section helpers.
- Streamlit UI helper parsing without importing Streamlit in pure helper tests.
- Demo scenarios and lazy RAG startup regression checks.
- Output language policy normalization, prompt instruction selection, and lightweight import behavior.
- HTTP/2 launcher short preview behavior while preserving full synthetic input on load.

## What Tests Do Not Prove / 測試未宣稱事項

The tests do not prove production security effectiveness. They do not prove real-world exploit prevention, real firewall blocking, real EDR containment, real account action, real cloud enforcement, or SIEM/SOAR remediation.

They prove the prototype behavior and safety boundaries expected by this demo implementation.

## Manual Smoke Evidence / 手動驗證證據

Manual demo checks are documented in:

- [USER_OPERATION_GUIDE.md](USER_OPERATION_GUIDE.md)
- [final_demo_smoke_checklist.md](final_demo_smoke_checklist.md)
- [v2.7_manual_smoke_report.md](v2.7_manual_smoke_report.md)
- [screenshots/README.md](screenshots/README.md)

The refreshed v2.8-D screenshot set records the main UI states, including Fast command-injection analysis, AI Analyst Brief, Evidence Gap Analyzer, Knowledge Q&A, Similar Cases, Relationship Graph, Case Draft/Export, HTTP/2 Resource Exhaustion safe demo, and optional Full AI-assisted mode.

## Conclusion / 結論

The current validation evidence supports the demo-ready claim: deterministic security authority remains intact, advisory AI/RAG features are bounded, and the user-facing documentation and screenshots now match the current console workflow.

