# ADR-0002: followup_handler vs report_followup Boundary

## Status

Accepted

## Context

The project has two follow-up paths with different responsibilities.

`followup_handler` supports point and context follow-up in the conversational agent flow. `report_followup` supports report-aware questions, including EV/F-ID lookup and report-specific explanations.

## Decision

Keep `followup_handler` and `report_followup` separate.

`followup_handler` owns point and context conversational follow-up. `report_followup` owns report-aware EV/F-ID and report-specific follow-up, including protected report/rule explanation helpers.

Future Smart Router or Workflow Plan work may route by question type, but this ADR does not wire runtime routing.

## Consequences

The current boundary stays explicit and avoids merging different follow-up models too early.

Future consolidation can use this decision as the baseline for tests and migration planning.

## Non-Goals

- No module merge in this ADR.
- No import path changes.
- No Smart Router runtime wiring.
- No Workflow Plan execution.
- No change to report, risk, or decision behavior.
