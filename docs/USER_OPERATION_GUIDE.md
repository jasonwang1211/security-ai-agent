# User Operation Guide

This guide covers setup, launch, operating modes, and troubleshooting. For a step-by-step UI demo path, use [UI_WALKTHROUGH.md](UI_WALKTHROUGH.md).

## Environment Assumptions

Recommended local environment:

- Windows PowerShell or a compatible shell;
- Python virtual environment;
- dependencies installed from requirements.txt;
- optional local AI/RAG services only when testing Full AI-assisted or Knowledge Q&A paths.

The project can demonstrate the primary workflow in Fast deterministic mode without relying on optional LLM/RAG warm-up.

## Install and Activate

~~~powershell
git clone https://github.com/jasonwang1211/security-ai-agent.git
cd security-ai-agent
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
~~~

## Streamlit Launch

~~~powershell
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
~~~

Use --server.fileWatcherType none if the Streamlit file watcher causes slow startup or noisy reload behavior.

## CLI Launch

~~~powershell
python app.py
~~~

CLI mode is useful for direct input testing. The Streamlit console is the recommended public demo surface.

## Analysis Modes

### Fast Deterministic Mode

Use this for the main demo.

Expected behavior:

- rule-based detection runs;
- Risk Level and Decision are deterministic;
- BLOCK / MONITOR / ALLOW are simulated;
- optional AI/RAG explanation warm-up is skipped;
- startup is faster after the v2.8 Lazy RAG refactor.

### Full AI-Assisted Mode

Use this only when optional AI/RAG services are available and you want to demonstrate the extended explanation path.

Expected behavior:

- deterministic detection remains authoritative;
- AI/RAG output is advisory only;
- first run can be slower while local models or retrieval dependencies warm up;
- unavailable AI/RAG components should not change the deterministic result.

## Lazy RAG Startup Behavior

v2.8 keeps heavy RAG and embedding-related dependencies out of the fastest deterministic startup path. Knowledge Q&A and Full AI-assisted features may initialize RAG-related components only when those paths are used.

This design improves demo startup while preserving the same safety boundary.

## If RAG / Ollama / Chroma / Embedding Is Unavailable

Expected safe behavior:

- deterministic analysis should still work;
- Risk Level and Decision should not change;
- advisory panels should degrade gracefully or show that optional context is unavailable;
- no fallback should claim proof of exploitation or perform enforcement.

Suggested checks:

1. Confirm Fast deterministic mode works first.
2. Confirm the input is a supported demo scenario.
3. Confirm optional local AI/RAG services are running only if you intend to use them.
4. Treat unavailable RAG/LLM output as a demo environment issue, not a detection failure.

## If Streamlit Is Slow or Reloads Repeatedly

Use:

~~~powershell
python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
~~~

Also check:

- the virtual environment is active;
- dependencies are installed;
- no stale Streamlit process is occupying the expected port;
- the browser is pointed at the URL printed by Streamlit.

## Pre-Demo Checklist

Before a live demo:

- open the Streamlit console;
- set Interface Language as needed;
- select Fast deterministic mode for the primary path;
- load Command Injection Demo once;
- verify Risk Level HIGH and Decision BLOCK appear as simulated labels;
- click Find Similar Cases and confirm approved cases appear;
- check AI Analyst Brief and Evidence Gap Analyzer;
- load HTTP/2 Resource Exhaustion Suspicion and confirm the old active context clears;
- keep the safety boundary visible.

## Common Problems and Expected Behavior

| Situation | Expected behavior |
|---|---|
| Optional RAG/LLM is unavailable | Deterministic analysis still works; advisory context may be unavailable. |
| Similar cases not requested yet | Similar-case panel may show no approved similar cases until the button is clicked. |
| HTTP/2 scenario loaded but not run | Textarea contains synthetic input; active context should remain empty/pending. |
| Full AI-assisted first run is slow | Local AI/RAG warm-up can take time. |
| BLOCK appears in UI | It is simulated only; no real enforcement occurs. |

## Safety Reminders

- Rule-Based Detector is the detection authority.
- Risk Level / Decision are deterministic.
- BLOCK / MONITOR / ALLOW are simulated decisions only.
- RAG / LLM / AI Analyst Brief / Evidence Gap Analyzer / Similar Cases / Relationship Graph provide advisory context only.
- No real firewall / WAF / EDR / account / cloud / SIEM / SOAR action is performed.
- No exploit code, PoC generation, traffic generation, or offensive automation is provided.
- Human review is required.
