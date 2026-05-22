# ADR-0003: RAGQA and RAG v2 Helper Coexistence

## Status

Accepted

## Context

The existing `RAGQA` path is the active general security knowledge QA runtime.

RAG v2 helper modules provide source-cited report and rule explanation foundations. They support more structured answers but are not a replacement for the active general QA runtime.

## Decision

Keep `RAGQA` as the active general knowledge QA runtime.

Keep RAG v2 modules as helper infrastructure for source-cited report/rule explanation paths. v1.9 does not replace `RAGQA`.

Future Graph RAG should first augment context and retrieval. It must not directly replace `RAGQA`, become a detector, or make final security decisions.

## Consequences

The project can improve explanation quality without destabilizing the current QA runtime.

Future retrieval work must preserve deterministic detector and policy authority and avoid treating RAG as a detection source.

## Non-Goals

- No RAGQA replacement.
- No Graph RAG implementation.
- No new RAG runtime package.
- No RAG-based attack determination.
- No Risk Level or Decision override.
