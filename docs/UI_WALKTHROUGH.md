# Streamlit UI Walkthrough

This walkthrough guides an evaluator through the Streamlit analyst console. It assumes the environment is already installed. For setup and troubleshooting, use [USER_OPERATION_GUIDE.md](USER_OPERATION_GUIDE.md).

## Step 1: Launch Streamlit

~~~powershell
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
~~~

Open the local Streamlit URL shown by the command. The console should display scenario cards, language and analysis-mode controls, and the safety boundary.

Reference: [Console home screenshot](screenshots/en/01_console_home.png)

## Step 2: Choose Fast Deterministic Mode

Select Fast deterministic mode for the primary demo path. This mode uses rule-based detection and deterministic policy while skipping optional AI/RAG warm-up.

Expected behavior:

- Risk Level and Decision remain deterministic.
- BLOCK / MONITOR / ALLOW remain simulated.
- No real enforcement is executed.

## Step 3: Load or Enter the Command Injection Demo Input

Use the Command Injection Demo scenario card or manually enter:

~~~text
test; rm -rf /tmp/test
~~~

Click Run input.

## Step 4: Review Deterministic Detection / Risk / Decision

The active context should show:

- attack type: Command Injection;
- rule evidence such as CMD-001;
- Risk Level: HIGH;
- Decision: BLOCK;
- simulated decision warning.

Reference: [Fast deterministic analysis screenshot](screenshots/en/02_fast_command_injection_analysis.png)

## Step 5: Review AI Analyst Brief

Open the AI Analyst tab and review AI Analyst Brief.

What to look for:

- what happened;
- why it matters;
- deterministic verdict context;
- advisory summary;
- evidence gap summary;
- recommended next steps;
- unsafe assumptions.

The panel should state that it is deterministic advisory context and does not use LLM authority.

Reference: [AI Analyst Brief screenshot](screenshots/en/03_ai_analyst_brief.png)

## Step 6: Review Evidence Gap Analyzer

Scroll to Evidence Gap Analyzer in the AI Analyst tab.

What to look for:

- confirmed facts;
- missing evidence;
- recommended checks;
- unsafe assumptions;
- advisory/no-override boundary.

Reference: [Evidence Gap Analyzer screenshot](screenshots/en/04_evidence_gap_analyzer.png)

## Step 7: Review Knowledge Q&A / RAG If Available

Continue to Knowledge Q&A.

Safe expected behavior:

- answers are defensive and advisory;
- answers follow the selected UI language;
- RAG is not proof of current exploitation;
- unavailable Ollama, Chroma, or embedding components should not change deterministic results.

Reference: [Knowledge Q&A screenshot](screenshots/en/05_knowledge_qa_rag.png)

## Step 8: Review Approved Similar Cases

Click Find Similar Cases, then open Case Intelligence.

What to look for:

- approved similar case IDs such as CASE-SEED-001;
- deterministic similarity reasons;
- key differences and missing evidence;
- advisory boundary stating historical cases do not override the current event.

Reference: [Approved Similar Cases screenshot](screenshots/en/06_similar_cases.png)

## Step 9: Review Relationship Graph

In Case Intelligence, scroll to Graph Relations.

What to look for:

- current event / incident node;
- Risk Level and Decision nodes;
- shared fields such as rule ID or attack type;
- approved-case relationship context;
- advisory-only graph boundary.

Reference: [Relationship Graph screenshot](screenshots/en/07_relationship_graph.png)

## Step 10: Review Case Draft / Markdown Export

Open Draft / Export.

What to look for:

- draft approval gate;
- human review requirement;
- Markdown export preview;
- safety notes stating that the report is not live remediation proof.

Reference: [Case Draft / Export screenshot](screenshots/en/08_case_draft_export.png)

## Step 11: Load the HTTP/2 Resource Exhaustion Safe Synthetic Demo

Return to the scenario launcher and load HTTP/2 Resource Exhaustion Suspicion.

Expected behavior before clicking Run input:

- the textarea contains the full synthetic incident summary;
- the launcher card uses short preview rows;
- old Command Injection active context is cleared;
- the UI shows no active context / pending input state;
- wording remains defensive: no traffic generated, no real enforcement, human review required.

Reference: [HTTP/2 safe demo screenshot](screenshots/en/09_http2_resource_exhaustion_demo.png)

## Step 12: Explain What the Screenshots Prove

The screenshot set demonstrates the public v2.8 demo surface:

- the UI is understandable as a SOC analyst console;
- deterministic detection and simulated decision outputs are visible;
- AI advisory panels provide context without taking authority;
- RAG, similar cases, and graph views remain advisory;
- case draft and export remain human-review material;
- the HTTP/2 scenario is safe and synthetic.

Optional mode reference: [Full AI-assisted mode screenshot](screenshots/en/10_full_ai_assisted_optional.png)
