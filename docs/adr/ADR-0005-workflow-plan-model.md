# ADR-0005: Workflow Plan Model Rationale

## Status

Accepted

## Context

Future orchestration may describe analyst workflows, route choices, dependencies, and required confirmations.

The project needs a contract for workflow planning before any runtime execution is considered.

## Decision

Workflow plans are future orchestration contracts, not auto-execution.

Workflow execution modes should include:

- `PREVIEW_ONLY`
- `READ_ONLY`
- `HUMAN_APPROVAL_REQUIRED`
- `SIMULATED_ONLY`
- `FORBIDDEN`

Workflow plans must not bypass detector, policy, guardrails, Tool Permission boundaries, or human approval where required.

## Consequences

The project can describe multi-step analyst workflows without implying autonomous execution.

Future Workflow Plan implementation must remain schema-first and must prove that forbidden and approval-required actions cannot run silently.

## Non-Goals

- No `modules/workflow_types.py` implementation in this ADR.
- No workflow auto-execution.
- No hidden tool calls.
- No Smart Router runtime execution.
- No Risk Level or Decision override.
