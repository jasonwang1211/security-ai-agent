# Streamlit Analyst Console Walkthrough

This walkthrough explains the main UI path for the Sentinel Project demo. The console is the primary showcase surface for the project.

## Launch

```powershell
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
```

The UI entry point is `ui/streamlit_app.py`.

## What Reviewers Should Notice First

- The home console shows language and analysis-mode controls.
- Demo scenario cards make the project inspectable without live systems.
- The HTTP/2 Resource Exhaustion card is explicitly safe and synthetic.
- The input area and Run input action make the workflow easy to follow.
- The status area keeps simulated decisions and safety boundaries visible.

## Main Demo Path

1. Select Fast deterministic mode.
2. Load Command Injection demo.
3. Click Run input.
4. Review the deterministic classification, Risk Level, and simulated Decision.
5. Open AI Analyst Brief.
6. Open Evidence Gap Analyzer.
7. Ask a defensive Knowledge Q&A / RAG question.
8. Review Approved Similar Cases and Relationship Graph.
9. Review Case Draft and Markdown Export.
10. Load HTTP/2 Resource Exhaustion safe demo to show the safe synthetic scenario boundary.

## Feature Areas

| Feature area | What it shows | Screenshot |
|---|---|---|
| Console home | Scenario cards, mode controls, input area, and safety framing. | [01_console_home.png](screenshots/en/01_console_home.png) |
| AI Analyst Brief | Advisory event summary and deterministic boundary. | [03_ai_analyst_brief.png](screenshots/en/03_ai_analyst_brief.png) |
| Evidence Gap Analyzer | Confirmed facts, missing evidence, review tasks, unsafe assumptions. | [04_evidence_gap_analyzer.png](screenshots/en/04_evidence_gap_analyzer.png) |
| Knowledge Q&A / RAG | Defensive knowledge answer with advisory framing. | [05_knowledge_qa_rag.png](screenshots/en/05_knowledge_qa_rag.png) |
| Similar Cases | Approved historical comparison without override authority. | [06_similar_cases.png](screenshots/en/06_similar_cases.png) |
| Relationship Graph | Read-only visual context for event, rule, risk, decision, and case links. | [07_relationship_graph.png](screenshots/en/07_relationship_graph.png) |
| Case Draft / Export | Reviewable draft and Markdown export material. | [08_case_draft_export.png](screenshots/en/08_case_draft_export.png) |
| HTTP/2 safe demo | Synthetic incident summary with no traffic generation. | [09_http2_resource_exhaustion_demo.png](screenshots/en/09_http2_resource_exhaustion_demo.png) |

## Safety Boundary

- Rule-Based Detector is the detection authority.
- Risk Level / Decision are deterministic.
- BLOCK / MONITOR / ALLOW are simulated.
- RAG / LLM / AI Analyst Brief / Evidence Gap are advisory only.
- No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action is performed.
- No exploit / PoC / traffic generation is provided.
- Human review is required.
