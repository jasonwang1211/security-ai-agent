# ADR-0001: Deterministic ControllerAgent

## Status

Accepted

## Context

The project has typed controller infrastructure for registered local tools. The security model requires deterministic detector and policy output to remain the final authority.

Future orchestration work needs a clear boundary before any workflow planning or tool permission contract is added.

## Decision

ControllerAgent is a deterministic typed dispatcher and workflow boundary.

It may dispatch by explicit route or registered tool name. It must not choose tools through an LLM, judge attacks, override Risk Level or Decision, execute real defense actions, or become an autonomous agent loop.

Future workflow integration must be constrained by Tool Permission and Workflow Plan contracts.

## Consequences

ControllerAgent can remain useful as orchestration infrastructure without changing the final security authority.

Any future runtime wiring must prove explicit routing, registered tools, permission checks, and no auto-execution behavior.

## Non-Goals

- No LLM-based tool selection.
- No AI attack determination.
- No Risk Level or Decision override.
- No real firewall, WAF, SIEM, SOAR, cloud, or endpoint enforcement.
- No ControllerAgent auto-execution in this ADR.
