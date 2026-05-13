# Technical Notes

This document summarizes the main technical ideas behind the project. It is intended for project review, future maintenance, and study notes.

The project is defensive and academic. Final detection and decision logic remains deterministic. LLM and RAG features are used for explanation and advisory context, not as final authority.

## Rule-Based Detection

Rule-based detection uses explicit signatures or patterns to identify known suspicious inputs. Because the rules are written directly and evaluated predictably, this approach is deterministic and easier to test than probabilistic detection.

In this project, `modules/detector.py` supports rule-based detection for:

- XSS
- SQL Injection
- Path Traversal
- Command Injection

This is suitable for known payload patterns, such as common XSS tags, SQL Injection fragments, path traversal strings, and command injection operators. The main weakness is that rule-based detection may miss novel, heavily obfuscated, or previously unseen attack patterns.

## Detection-as-Code

Detection-as-Code means storing detection rules as structured files instead of hard-coding all signatures in Python. In v1.4, this project uses YAML rules under `detections/blue_team/`.

YAML rules are easier to review, update, test, and attach metadata to. This is still deterministic rule-based detection, not ML detection.

Project usage includes:

- `detections/blue_team/`
- `modules/detection_rules.py`
- `modules/rule_loader.py`
- `DetectionRule`

Rule metadata includes:

- `id`
- `title`
- `attack_type`
- `severity`
- `confidence`
- `patterns`
- MITRE techniques
- references

Hard-coded signatures remain as a conservative fallback so the detector keeps known behavior even if external rule loading is unavailable.

Example YAML rule:

```yaml
id: XSS-001
title: Basic XSS Script Indicators
attack_type: XSS
severity: MEDIUM
confidence: 0.8
patterns:
  - "<script>"
  - "alert("
match_mode: substring
case_sensitive: false
enabled: true
```

## ControllerAgent and Tool Registry

v1.5 adds typed agent infrastructure without making the system autonomous. `ToolSpec` defines each tool contract, including input model, output model, safety level, RAG/LLM flags, and allowed input kinds. `ToolRegistry` stores the allowed tools, while the Skill Catalog defines exactly six v1.5 wrapper skills:

- `payload_triage`
- `raw_log_translate`
- `log_file_ingest`
- `rag_security_qa`
- `report_followup`
- `incident_json_export`

Skill wrappers expose existing local capabilities as typed local tools. `ControllerAgent` validates input, calls the registered handler, validates output, and returns a `ControllerOutput`.

Dispatch is deterministic by explicit route or tool name. This is agent infrastructure, not autonomous LLM routing. Auto Route, Smart Router, and LLM-driven tool selection are deferred.

## YAML and Schema Validation

YAML is a human-readable data format. This project uses PyYAML to read YAML rule files, then uses Pydantic to validate that each rule has the required fields and valid values.

Schema validation prevents broken or incomplete rule files from silently entering the detector. For example:

- invalid severity values are rejected
- `confidence` must be between `0.0` and `1.0`
- `patterns` must not be empty
- disabled rules are ignored

This helps keep detection behavior predictable and testable.

Simplified Pydantic-style example, not the full production class:

```python
class DetectionRule(BaseModel):
    id: str
    attack_type: str
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    confidence: float
    patterns: list[str]
```

## Evidence and Incident Model

v1.3 introduced incident-style evidence handling. Evidence items use stable `EV-ID` references, findings use stable `F-ID` references, and incidents group evidence and findings into structured reportable objects.

Project models include:

- `EvidenceItem`
- `EvidenceBundle`
- `Finding`
- `Incident`
- `GenerationMetadata`

This matters because report follow-up can answer questions like "EV-003 是什麼意思？" and JSON Incident Report export becomes possible. Stable evidence references also help prevent ungrounded explanations because generated text can be checked against known evidence IDs.

Compact example:

```text
EV-003: success_after_failures
F-001: possible_account_compromise
Risk Level: HIGH
Decision: MONITOR
```

## Time-Window and Sequence Correlation

Single events may not be enough to determine suspicious behavior. Multiple related events within a time window can create stronger evidence.

In v1.3 Scenario A, the project detects repeated authentication failures followed by a successful login. This can produce a `possible_account_compromise` finding with `HIGH / MONITOR`.

This means the behavior is suspicious but not a confirmed compromise. Analyst review is still required before making operational conclusions.

Project module:

- `modules/evidence_correlator.py`

## LLM Guardrails

LLMs can hallucinate, so this project does not allow LLM output to make final decisions. `LLMAssist` is advisory only, and `LLMGuardrails` validates advisory output before it is trusted as context.

Guardrail checks include:

- evidence reference validation
- no downgrade of deterministic verdict
- no unilateral `BLOCK` authority
- allowed attack type validation
- confidence sanity checks
- fallback to deterministic result if unsafe

Project modules:

- `modules/llm_assist.py`
- `modules/llm_guardrails.py`

Why not let the LLM decide?

Because final security decisions must be reproducible, testable, and bounded by deterministic policy.

Pseudo-rule:

```text
If LLMAssist cites EV-999 but EV-999 does not exist in the EvidenceBundle,
LLMGuardrails rejects the advisory result and falls back to deterministic output.
```

## RAG and Report-aware Follow-up

RAG is used for explanation and security knowledge, not primary detection. Report-aware follow-up explains existing reports, evidence IDs, risk levels, and decisions. It must not re-judge the final verdict.

Project modules and knowledge paths include:

- `modules/rag_query_planner.py`
- `modules/rag_qa.py`
- `modules/report_followup.py`
- `knowledge/blue_team/report_explainer/`

Example follow-up questions:

- "EV-003 是什麼意思？"
- "為什麼是 MONITOR？"
- "我接下來要查什麼？"

## Testing Strategy

The project uses several testing layers:

- Unit tests: test individual models and functions
- Golden tests: protect known payload behavior from regression
- Integration tests: verify an end-to-end scenario such as Scenario A
- Lint and type checks: `ruff` and `mypy`

Current quality gate:

- `python -m pytest` -> `240 passed`
- `python -m ruff check .`
- `python -m mypy app.py modules tests`

Deterministic tests do not require Ollama, Chroma, embeddings, Torch, ChatOllama, or app startup.

Compact examples:

```text
Golden payload test:
known XSS / SQLi / Path Traversal / Command Injection payloads should keep their expected behavior.

Scenario A integration test:
mixed auth log -> Incident -> EV-ID follow-up -> LLMAssist guardrails.
```

## MITRE ATT&CK Metadata

MITRE ATT&CK provides standard technique IDs. This project uses MITRE technique IDs as metadata in YAML rules so local rules can connect to broader security terminology.

Examples include:

- `T1059` for command/scripting-related behavior
- `T1190` for exploit public-facing application style references
- `T1083` for file/directory discovery style references

Mappings in this prototype are lightweight educational metadata, not a complete ATT&CK evaluation.

## What This Project Is Not

This project is:

- not a production SIEM
- not a SOAR system
- not a WAF
- not an offensive tool
- not an ML anomaly detector
- not an LLM-based final decision engine

It is a defensive, local-first academic prototype.

## Study Checklist

- YAML syntax
- PyYAML `safe_load`
- Pydantic validators
- rule-based detection
- Detection-as-Code
- false positive / false negative
- MITRE ATT&CK basics
- LLM hallucination and guardrails
- RAG basics
- unit / golden / integration testing
