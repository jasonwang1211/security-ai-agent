# v3.5 Human-Approved Knowledge Capture Review Summary

Branch: `v3.5-human-approved-knowledge-capture`

## Purpose

v3.5 adds a low-risk foundation for human-approved knowledge capture. The branch lets the project preserve reviewed analyst notes as local, advisory-only artifacts for future RAG and Knowledge Graph workflows without changing current detector, RAG runtime, graph runtime, or Streamlit behavior.

## Commits Included So Far

- `4e32a2d docs: add knowledge capture design spec`
- `88dfdb3 feat: add human-approved knowledge capture foundation`
- `70266e9 test: add knowledge capture safety regressions`
- `a10090c test: harden knowledge capture approval and export safety`
- Current demo/review artifact commit: this document, synthetic examples, demo script, and artifact tests.

## Modules Added

- `modules/knowledge_capture/types.py`
- `modules/knowledge_capture/extractor.py`
- `modules/knowledge_capture/store.py`
- `modules/knowledge_capture/rag_export.py`
- `modules/knowledge_capture/graph_export.py`

## Behavior Changed

No runtime RAG, runtime Graph, Streamlit UI, detector, risk scoring, decision policy, ToolPolicy, or case-draft behavior is changed by this branch.

The new behavior is limited to explicit knowledge-capture APIs, synthetic examples, and an offline demo script.

## Implemented

- Candidate, approved, and rejected knowledge note contracts.
- Deterministic safety checks for missing provenance, unsafe content, verdict override attempts, Similar Cases-as-proof claims, Graph-as-detection-source claims, and secret/PII risk.
- zh-TW safety wording coverage for common unsafe or overclaiming phrases.
- Local JSONL pending/approved/rejected store.
- Approval-time edited body revalidation.
- Approved-only RAG markdown export candidate.
- Approved-only Graph node/edge export candidate.
- Export-time final safety validation.
- Synthetic sample artifacts under `docs/examples/knowledge_capture/`.
- Offline demo script at `scripts/demo_knowledge_capture.py`.

## Deferred

- Streamlit review queue UI.
- Runtime RAG ingestion into Chroma or embeddings.
- Runtime graph mutation or graph fact promotion.
- Live LLM-assisted note extraction.
- Production audit workflow.
- Real user/private captured content.

## Validation Status

The branch includes focused regression tests for the knowledge capture foundation and demo artifacts. Before review or merge, run:

```powershell
python -m pytest
python -m ruff check .
python -m mypy app.py modules tests
git diff --check
git status --short --untracked-files=all
```

The validation result should be recorded in the PR or review handoff. These tests verify bounded demo behavior and safety-boundary regressions; they do not prove production IDS/IPS effectiveness or live-provider quality.

## Reviewer Checklist

- Confirm examples are synthetic and contain no private user data.
- Confirm pending notes cannot export.
- Confirm approval-time edited text is revalidated.
- Confirm unsafe manually constructed approved notes cannot export.
- Confirm RAG export is markdown-only and does not call Chroma, embeddings, network, or runtime RAG ingest.
- Confirm Graph export emits advisory candidates only and does not mutate graph facts.
- Confirm official Risk Level / Decision remain copied deterministic context only.
- Confirm Similar Cases are not represented as proof of compromise.
- Confirm Graph is not represented as a detection source.

## Merge Risk

Low. The branch adds isolated modules, tests, docs, examples, and an offline demo script. No existing runtime call path imports or invokes knowledge capture automatically.

Primary review risk is semantic: future UI/RAG/Graph integration must preserve human approval and advisory-only boundaries.

## Rollback Plan

If this branch becomes risky, remove the isolated worktree and delete the branch:

```powershell
git worktree remove <knowledge-capture-worktree>
git branch -D v3.5-human-approved-knowledge-capture
```

Do not remove or modify the final presentation package as part of rollback.
