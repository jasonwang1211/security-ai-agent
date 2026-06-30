# v3.7 Manual Smoke Checklist

This checklist is for the post-final v3.7 integration branch after the Knowledge Capture stack import. It is intentionally manual because Streamlit rerun behavior and local runtime state are easiest to verify in the browser.

## Setup

1. Start the Streamlit console:

   ```powershell
   python -m streamlit run ui/streamlit_app.py --server.fileWatcherType none
   ```

2. Open the local Streamlit URL shown by the command.
3. Confirm the final presentation package is not open for editing and is not part of this smoke test.

## Knowledge Capture Review UI

- [ ] App starts without import errors.
- [ ] AI Analyst tab opens normally.
- [ ] Knowledge Capture Review UI is visible as an optional/collapsed review area and does not disrupt the existing AI Analyst flow.
- [ ] Default store path is `.tmp/knowledge_capture_ui/capture_store`.
- [ ] Empty state is readable and explains that there are no pending notes.
- [ ] zh-TW labels are readable when Interface Language is set to Traditional Chinese.
- [ ] Approve/reject controls appear only for reviewable pending notes.
- [ ] Approve/reject actions may require Streamlit rerun/refresh to visually reflect state.
- [ ] UI copy states advisory-only review boundaries.
- [ ] UI copy states notes are not a detection source and not proof of compromise.
- [ ] UI copy states no real enforcement occurs.

## Optional Synthetic Demo Data

1. Generate synthetic demo notes only:

   ```powershell
   python scripts/demo_knowledge_capture.py --output-dir .tmp/knowledge_capture_ui --clean
   ```

2. Refresh Streamlit.
3. Confirm pending/approved/rejected synthetic notes are visible according to their state.
4. Approve a safe pending note if available.
5. Reject a pending note if available.
6. Preview RAG markdown export.
7. Preview Graph candidate JSON.

## Safety Checks

- [ ] No real `data/knowledge_capture` path is modified by default.
- [ ] No auto-approval occurs.
- [ ] No auto-ingest into runtime RAG occurs.
- [ ] No runtime Graph mutation occurs.
- [ ] Official Risk Level / Decision are not changed.
- [ ] No live LLM, API, Chroma ingest, embedding execution, or network call is required by the review UI.
- [ ] No exploit, PoC, traffic generation, load testing, or offensive automation is introduced.
- [ ] Final presentation package remains untouched.

## Status

Manual smoke status for this branch: **pending** until performed locally after the final docs commit.
