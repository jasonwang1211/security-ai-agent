# v3.7 Manual Streamlit Smoke Result

## Branch And HEAD

- Branch: `v3.7-post-final-runtime-truth`
- HEAD at time of smoke-result documentation: `98fc2d5 docs: finalize v3.7 runtime and integration notes`

## Working Launch Command

The working Streamlit launch command on Windows was run from the repository root with the repository path added to `PYTHONPATH`:

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m streamlit run .\ui\streamlit_app.py
```

This command successfully launched the Streamlit analyst console.

## Failed Launch Attempts

### Attempt 1: `streamlit run app.py`

Result: not the correct UI smoke command.

Observed behavior:

- The browser page opened blank.
- `app.py` entered the CLI agent input loop instead of the Streamlit UI.
- Terminal output included:
  - `Security AI ready. RAG initializes on first knowledge question.`
  - `Agent input (...):`

Explanation: `app.py` is the CLI-oriented entrypoint, not the Streamlit analyst console entrypoint.

### Attempt 2: `streamlit run ui/streamlit_app.py`

Result: found the Streamlit UI entrypoint, but failed with:

```text
ModuleNotFoundError: No module named 'modules'
```

Explanation: the repository root was not on Python import path for that launch attempt.

## Manual Smoke Checklist Result

Manual Streamlit smoke passed for UI launch, main advisory flow, Knowledge Capture draft request and approval flow, readable zh-TW labels, no observed auto-approval, no observed auto-ingest, and no observed real enforcement.

Observed UI results:

- Streamlit UI rendered successfully.
- Main Security AI Agent Console opened successfully.
- Demo scenario launcher rendered successfully.
- Full AI-Assisted advisory result rendered successfully.
- Provider-disabled / deterministic fallback status was visible.
- Official Risk Level / Decision remained deterministic and visible.
- Evidence Gap Analyzer rendered successfully.
- Unsafe assumptions and grounded citations rendered successfully.
- Safety / Human Review Boundary rendered successfully.
- Draft / Export / Knowledge Capture related section was visible.
- Export report / markdown preview rendered.
- zh-TW labels were readable; no obvious mojibake was observed.
- No real firewall / WAF / EDR / SIEM / SOAR enforcement was observed.
- Final presentation package was untouched.

## Knowledge Capture / Case Draft Flow Result

Observed flow:

1. Initial state showed no pending draft.
2. Clicking `Request Draft` changed status to `pending approval`.
3. `Pending Approval` changed to `yes`.
4. At the pending-approval stage, the UI showed no draft file path.
5. Clicking `Approve Draft` changed status to `draft created`.
6. `Pending Approval` changed back to `no`.
7. A draft path was created under:

   ```text
   workbench/case_drafts/active_event-high-block-....md
   ```

8. `Active Context` remained `yes`.

Observed safety boundary wording in the UI:

- Draft files are isolated under `workbench/case_drafts/`.
- Draft files are not live knowledge.
- Draft files are not ingested.
- Draft files are not approved for promotion.
- Human review is required before any draft is trusted or promoted.
- `safety_reviewed` is false by default.
- No real firewall, WAF, EDR, account, password reset, monitoring deployment, or enforcement action is executed.

## Safety Confirmations

- No auto-approval observed.
- No auto-ingest observed.
- No real enforcement observed.
- Knowledge Capture remains human-review oriented.
- AI advisory does not modify official Risk Level / Decision.
- Similar Cases remain advisory, not proof.
- Graph remains context, not detection source.
- Final presentation package untouched.
- No code, tests, or runtime behavior were changed by this documentation task.
- No push, tag, release, merge, rebase, or reset was performed.

## Caveats And Remaining Risks

- Cancel/reject path was not fully exercised and remains a minor follow-up smoke item.
- Screenshot evidence confirms draft output under `workbench/case_drafts/`.
- The `.tmp/knowledge_capture_ui/capture_store` default-store safety check is covered by automated tests/docs rather than directly proven by screenshot.
- UI launch on Windows should use the repository-root `PYTHONPATH` command shown above.

## PR / Merge Readiness

v3.7 is ready for PR / human merge review after this smoke result is recorded, with one minor follow-up item: exercise the cancel/reject path in a later manual smoke pass.

The manual smoke evidence supports the current v3.7 safety boundary: deterministic official verdict authority remains intact, advisory panels remain non-authoritative, Knowledge Capture remains human-review oriented, and no real enforcement or runtime RAG/Graph mutation was observed.
