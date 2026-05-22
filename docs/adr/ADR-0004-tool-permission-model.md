# ADR-0004: Tool Permission Model Rationale

## Status

Accepted

## Context

Future orchestration may expose more local tools through controller or workflow boundaries.

Without an explicit permission model, read-only helpers, draft writers, simulated actions, and forbidden real-world actions can become unclear.

## Decision

Future tools should use explicit permission levels:

- `READ_ONLY`
- `WRITE_DRAFT`
- `WRITE_REVIEW_REQUIRED`
- `SIMULATED_ACTION`
- `FORBIDDEN`

Unknown tools default to `FORBIDDEN`.

AI agents must not auto-execute high-risk, write, deployment, real enforcement, or verdict-changing actions.

## Consequences

Tool permissions create a reviewable boundary before any orchestration implementation.

Future Tool Permission implementation must be schema-first and tested before runtime enforcement is considered.

## Non-Goals

- No `modules/tool_policy.py` implementation in this ADR.
- No runtime enforcement.
- No automatic rule activation.
- No real firewall, WAF, SIEM, SOAR, cloud, or endpoint action.
- No LLM permission escalation.
