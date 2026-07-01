# v3.5 PR Description Draft

## Summary

Adds a human-approved knowledge capture foundation for future RAG and Knowledge Graph workflows. The implementation creates explicit candidate, approved, and rejected note contracts, deterministic safety checks, local JSONL review storage, approved-only export candidates, synthetic examples, and an offline demo script.

## Motivation

The project already produces deterministic analysis, AI advisory summaries, Evidence Gap output, RAG answers, Similar Cases, and Graph context. v3.5 starts a safe path for preserving analyst-reviewed knowledge without automatically trusting AI output or mutating runtime knowledge stores.

## What Changed

- Added `modules/knowledge_capture/` contracts and helpers.
- Added deterministic candidate extraction and safety flagging.
- Added zh-TW safety wording coverage for common unsafe or overclaiming requests.
- Added local JSONL pending/approved/rejected store.
- Added approval-time edited-body revalidation.
- Added approved-only RAG markdown export candidate.
- Added approved-only Graph node/edge export candidate.
- Added export-time final safety validation.
- Added synthetic examples under `docs/examples/knowledge_capture/`.
- Added offline demo script: `scripts/demo_knowledge_capture.py`.
- Added focused tests for storage, approval, export, demo script, and sample artifact validation.

## What Did Not Change

- No detector changes.
- No risk scoring changes.
- No deterministic decision policy changes.
- No RAG runtime behavior changes.
- No Graph runtime behavior changes.
- No Streamlit UI changes.
- No case draft behavior changes.
- No ToolPolicy changes.
- No live LLM, API, Chroma, embeddings, or network dependency.
- No real user/private captured content.

## Safety Boundaries

- Rule-Based Detector remains detection authority.
- Official Risk Level / Decision remain deterministic.
- BLOCK / MONITOR / ALLOW remain simulated only.
- Captured knowledge is advisory-only.
- Similar Cases are not proof of compromise.
- Graph context is not a detection source.
- Approved exports do not authorize real enforcement.
- No exploit, PoC, traffic generation, load testing, or offensive automation.
- Human review is required before approval/export.

## Tests

Added/updated tests cover:

- Candidate provenance requirements.
- Unsafe content rejection.
- Verdict override rejection.
- zh-TW unsafe and overclaiming pattern coverage.
- Approval-time edited body revalidation.
- Pending notes remaining pending after failed approval.
- Approved-only RAG/Graph export.
- Final export safety validation for manually constructed unsafe approved notes.
- Offline demo script output.
- Synthetic example JSON/model validation.

## Validation

Run before merge:

```powershell
python -m pytest
python -m ruff check .
python -m mypy app.py modules tests
git diff --check
git status --short --untracked-files=all
```

## Screenshots

N/A. This is not a Streamlit UI change and does not update README showcase images.

## Rollback

Revert the v3.5 commits or remove the isolated worktree/branch. Since no runtime RAG, Graph, UI, detector, risk, or decision behavior is wired to this foundation automatically, rollback risk is low.
