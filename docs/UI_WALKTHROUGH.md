# Streamlit UI Walkthrough

This walkthrough is the step-by-step demo path for the Streamlit analyst console. It is not a setup or troubleshooting guide; use [USER_OPERATION_GUIDE.md](USER_OPERATION_GUIDE.md) for environment and operational details. For a presenter narrative — timed 5-minute and 8–10-minute versions, per-panel talking points, reviewer Q&A, and a failure-recovery path — use the [v3.0 demo script](v3.0_demo_script.md).

## Step 1: Launch Streamlit

~~~powershell
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
~~~

| Item | Detail |
|---|---|
| User action | Open the local Streamlit URL shown by the command. |
| What appears | Security AI Agent Console with scenario cards, language/mode controls, and safety framing. |
| What to say | This is the main analyst-facing UI, not a backend-only API. |
| Safety note | The console does not execute real enforcement actions. |

Reference: [Console home screenshot](screenshots/en/01_console_home.png)

## Step 2: Confirm UI Language

| Item | Detail |
|---|---|
| User action | Set Interface Language to English for the English public demo, or Traditional Chinese for zh-TW materials. |
| What appears | Fixed UI labels and advisory panels follow the selected UI language. |
| What to say | English docs use English screenshots; Traditional Chinese docs keep separate zh-TW screenshots. |
| Safety note | Language changes presentation only; detection and decision logic do not change. |

## Step 3: Select Fast Deterministic Mode

| Item | Detail |
|---|---|
| User action | Select Fast deterministic mode. |
| What appears | Mode badge shows Fast deterministic. |
| What to say | This is the primary demo path because it avoids optional AI/RAG warm-up. |
| Safety note | Risk Level and Decision remain deterministic. |

## Step 4: Load The Command Injection Demo

| Item | Detail |
|---|---|
| User action | Click Load Scenario on Command Injection Demo, or enter test; rm -rf /tmp/test. |
| What appears | The input area contains the command-injection payload. |
| What to say | The payload is a safe text input used for deterministic rule matching. |
| Safety note | The app does not execute the payload. |

## Step 5: Run Input

| Item | Detail |
|---|---|
| User action | Click Run input. |
| What appears | Active context updates to Command Injection, HIGH, BLOCK, with rule evidence such as CMD-001. |
| What to say | The verdict path is rule-based and deterministic. |
| Safety note | BLOCK is simulated; no firewall, WAF, EDR, account, cloud, SIEM, or SOAR action occurs. |

Reference: [Fast deterministic analysis screenshot](screenshots/en/02_fast_command_injection_analysis.png)

## Step 6: Explain The Deterministic Result

| Item | Detail |
|---|---|
| User action | Review Active Context and Analysis Report. |
| What appears | Attack type, Risk Level, Decision, rule/evidence fields, and safety boundary. |
| What to say | The current event's deterministic result is the authority path. |
| Safety note | Advisory panels later in the demo cannot override this result. |

## Step 7: Open AI Analyst Brief

| Item | Detail |
|---|---|
| User action | Open the AI Analyst tab and review AI Analyst Brief. |
| What appears | What happened, why it matters, deterministic verdict context, next steps, and unsafe assumptions. |
| What to say | The brief translates deterministic findings into analyst language. |
| Safety note | It is advisory context and does not use AI as final authority. |

Reference: [AI Analyst Brief screenshot](screenshots/en/03_ai_analyst_brief.png)

### Step 7 (v2.9 branch): Review The Evidence-Grounded AI Brief

| Item | Detail |
|---|---|
| User action | At the top of the AI Analyst tab, review the Evidence-Grounded AI Brief panel. |
| What appears | Official Verdict (Risk Level / Decision), supporting evidence with citations such as rule-001 and ev-001, an evidence-gap summary, advisory context, citations, and a Safety / Human Review Boundary. The panel shows `llm_status: not_used_deterministic_fallback`. |
| What to say | The brief is grounded in the deterministic evidence and is cited; it is advisory analyst context, not an AI verdict. |
| Safety note | Official Risk Level and Decision are copied from deterministic policy and cannot be overridden by the brief. No live LLM client is wired on this branch. |

Reference: [Evidence-Grounded AI Brief screenshot](screenshots/en/11_evidence_grounded_ai_brief.png) (v2.9 branch; panel render)


### v3.2 Development Branch Note: Full AI-Assisted Advisory Result

On `v3.2-full-ai-assisted-showcase`, the AI Analyst tab also includes a Full AI-Assisted Advisory Result panel above the Evidence-Grounded AI Brief, plus an Event-Aware Q&A panel below Evidence Gap Analyzer. These panels use the current EvidenceGroundingBundle and default to provider-disabled deterministic fallback. They do not prove compromise, do not treat Graph as a detection source, and do not change the official Risk Level or Decision. Screenshot refresh is intentionally deferred.

## Step 8: Open Evidence Gap Analyzer

| Item | Detail |
|---|---|
| User action | Scroll to Evidence Gap Analyzer. |
| What appears | Confirmed facts, missing evidence, recommended checks, and unsafe assumptions. |
| What to say | The panel helps an analyst avoid overclaiming. |
| Safety note | Missing evidence requires human review; it does not change Risk Level or Decision. |

Reference: [Evidence Gap Analyzer screenshot](screenshots/en/04_evidence_gap_analyzer.png)

## Step 9: Open Knowledge Q&A / RAG

| Item | Detail |
|---|---|
| User action | Review the Knowledge Q&A panel, or ask a defensive knowledge question if RAG is available. |
| What appears | Defensive knowledge context with advisory framing. |
| What to say | RAG helps explain defensive concepts, but it is not proof of current exploitation. |
| Safety note | If Ollama, Chroma, or embedding dependencies are unavailable, deterministic analysis still stands. |

Reference: [Knowledge Q&A screenshot](screenshots/en/05_knowledge_qa_rag.png)

## Step 10: Click Find Similar Cases

| Item | Detail |
|---|---|
| User action | Click Find Similar Cases, then open Case Intelligence. |
| What appears | Approved Similar Cases with deterministic similarity reasons and key differences. |
| What to say | Similar cases are manually approved references for comparison. |
| Safety note | Historical cases do not prove compromise or successful execution in the current event. |

Reference: [Approved Similar Cases screenshot](screenshots/en/06_similar_cases.png)

Observation (v2.9 branch): after Find Similar Cases, re-open the Evidence-Grounded
AI Brief from Step 7. Its Advisory Context now cites `case-001` (approved similar
case — comparison context only, not proof of current compromise) and `graph-001`
(relationship context — not a detection source). These are derived from the
already-computed structured similar-case result, not from parsed display text.

Reference: [Structured Similar Cases / Graph context screenshot](screenshots/en/12_structured_similar_case_graph_context.png)

## Step 11: Review Relationship Graph

| Item | Detail |
|---|---|
| User action | Scroll to Graph Relations in Case Intelligence. |
| What appears | Event, rule, risk, decision, shared fields, and approved case relationship context. |
| What to say | The graph is a read-only explanation surface. |
| Safety note | Graph context does not perform graph-based detection or override deterministic policy. |

Reference: [Relationship Graph screenshot](screenshots/en/07_relationship_graph.png)

## Step 12: Review Case Draft / Markdown Export

| Item | Detail |
|---|---|
| User action | Open Draft / Export. |
| What appears | Case Draft controls, approval status, safety notes, and Markdown export preview. |
| What to say | Draft and export material is for human review. |
| Safety note | Export output is not live remediation proof and does not write to live knowledge. |

Reference: [Case Draft / Export screenshot](screenshots/en/08_case_draft_export.png)

## Step 13: Load HTTP/2 Resource Exhaustion Safe Demo

| Item | Detail |
|---|---|
| User action | Return to the scenario launcher and load HTTP/2 Resource Exhaustion Suspicion. |
| What appears | Textarea contains a synthetic incident summary; active context is empty until Run input is clicked, after which it shows the deterministic verdict HTTP/2 Resource Exhaustion Suspicion / MEDIUM / MONITOR. |
| What to say | This demonstrates resource-exhaustion triage without generating traffic. |
| Safety note | The scenario provides no exploit, PoC, traffic generation, or real enforcement. |

Reference: [HTTP/2 safe demo screenshot](screenshots/en/09_http2_resource_exhaustion_demo.png)

## Step 14: Explain Why The Demo Is Safe And Synthetic

| Item | Detail |
|---|---|
| User action | Point to the HTTP/2 card preview, loaded synthetic input, no-active-context state, and safety wording. |
| What appears | No traffic generated / no real enforcement / human review required wording. |
| What to say | The demo models defensive triage signals, not offensive behavior. |
| Safety note | Human review remains required before any real operational action outside the demo. |

Optional mode reference: [Full AI-assisted mode screenshot](screenshots/en/10_full_ai_assisted_optional.png)

## v2.9 Screenshots

The v2.9 Evidence-Grounded AI Brief panel images are captured under
`docs/screenshots/en/`, rendered from the live panel markup and console CSS:

- `11_evidence_grounded_ai_brief.png` — Official Verdict, rule-001 / ev-001 citations, deterministic-fallback status.
- `12_structured_similar_case_graph_context.png` — case-001 / graph-001 advisory context after Find Similar Cases.
- `13_evidence_grounded_markdown_export.png` — the Markdown export brief section.

Full-window app captures (with the Streamlit chrome) are now available too:
`en/14`–`16` (English) and `zh-TW/17` (Traditional Chinese chrome with the
English brief panel). See the [screenshot gallery](screenshots/README.md).
