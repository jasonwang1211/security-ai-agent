# Human-Approved Knowledge Capture Spec

Version: v3.5 foundation

## Purpose

Human-approved Knowledge Capture lets analysts preserve useful Event-Aware Q&A answers, analyst notes, or advisory context without automatically trusting AI output. The system creates candidate notes first. A human must review, edit, approve, or reject them before they can be exported for future RAG or Knowledge Graph use.

## Concepts

### CandidateKnowledgeNote

A pending note proposed from a user question, analyst note, or AI advisory answer. It has provenance and safety flags, but is not trusted for RAG or graph use until approved.

### ApprovedKnowledgeNote

A human-approved note. It preserves the original candidate provenance plus approval metadata. It can be exported as advisory RAG markdown or graph node/edge candidates.

### RejectedKnowledgeNote

A human-rejected note. It preserves provenance and rejection reason for review, but cannot be exported.

### KnowledgeCaptureProvenance

Structured metadata describing where the note came from. Provenance must include source event, question/answer context, cited evidence/rule/gap/RAG/case/graph IDs, timestamps, actor fields, status, confidence label, and safety flags.

### GraphNodeCandidate

An advisory graph node candidate derived from an approved note. It is not a detection source and must not be inserted into official graph facts automatically.

### GraphEdgeCandidate

An advisory graph edge candidate derived from an approved note. It must label its relation as advisory context and not proof.

### RagIngestionCandidate

A markdown-ready advisory snippet derived from an approved note. It is eligible for future reviewed RAG ingestion, but v3.5 does not run Chroma/embedding ingest.

## Pipeline

```text
User question / analyst note / AI advisory answer
-> candidate extraction
-> safety filtering
-> pending review queue
-> user review/edit/reject/approve
-> approved knowledge store
-> optional RAG markdown export
-> optional graph candidate export
```

## Required Provenance Fields

- `source_event_id`
- `source_question`
- `source_answer_summary`
- `source_evidence_ids`
- `source_rule_ids`
- `source_gap_ids`
- `source_rag_ids`
- `source_case_ids`
- `source_graph_ids`
- `official_risk_level`
- `official_decision`
- `created_at`
- `created_by`
- `approved_at`
- `approved_by`
- `status`
- `confidence_label`
- `safety_flags`

## Safety Boundaries

- No auto-approve.
- No auto-ingest of unreviewed notes.
- No unsafe content.
- Deterministic safety checks include English and zh-TW unsafe wording patterns.
- No exploit, PoC, traffic generation, load testing, or offensive automation.
- No PII or secret capture.
- No claim that captured notes prove compromise.
- Similar Cases remain advisory comparisons only.
- Graph remains advisory-only and is not a detection source.
- RAG remains advisory-only.
- Official Risk Level and Decision remain deterministic and cannot be changed by captured notes.
- Human review is required.

## Storage

v3.5 uses local JSONL files:

```text
data/knowledge_capture/pending_notes.jsonl
data/knowledge_capture/approved_notes.jsonl
data/knowledge_capture/rejected_notes.jsonl
```

Each line is one JSON object. Tests should use temporary directories. Do not commit real user/private content to these files.

If example data is needed, use synthetic examples under:

```text
docs/examples/knowledge_capture/
```

## Candidate Extraction Rules

A candidate may be created only when it has:

- non-empty note text;
- non-empty source event ID;
- at least one provenance reference from rule/evidence/gap/RAG/case/graph IDs;
- official Risk Level and Decision copied from deterministic context;
- safety flags computed deterministically.

The extractor must not call live LLM providers. It may summarize only provided strings in a deterministic way.

## Review Rules

- Pending notes are not exportable.
- Approved notes are exportable.
- Rejected notes are not exportable.
- Approval requires non-empty `approved_by` and `approved_at`.
- If an approver edits note body text during approval, the edited text is revalidated before the pending note is moved.
- Approval-time revalidation preserves the original provenance and copied official Risk Level / Decision.
- If approval-time validation fails, the candidate remains pending and no approved note is written.
- Rejection requires `rejected_by`, `rejected_at`, and a reason.
- Safety flags must be preserved and block approval/export.

## RAG Export Rules

- Export only approved notes.
- Include an advisory-only warning.
- Include provenance header fields.
- Include official Risk Level / Decision as copied context, not as editable conclusions.
- Run final deterministic safety validation before export so manually constructed unsafe approved objects cannot be exported.
- Do not run ingestion, Chroma, embeddings, or network calls.

## Graph Export Rules

- Export only approved notes.
- Nodes/edges must be marked `advisory_only: true`.
- Nodes/edges must be marked `not_detection_source: true`.
- Similar Case references must be marked `not_proof: true`.
- Run final deterministic safety validation before export so manually constructed unsafe approved objects cannot be exported.
- Exports are candidates only and are not official graph facts.

## v3.5 Non-Goals

- No Streamlit review UI unless separately approved.
- No live LLM extraction or summarization.
- No automatic RAG ingestion.
- No automatic graph mutation.
- No production knowledge governance workflow.
- No real enforcement or response action.
