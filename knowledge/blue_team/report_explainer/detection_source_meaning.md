---
doc_id: report.detection_source_meaning
doc_type: report_explainer
applies_to:
  - Security Triage Report
  - Detection Source
  - AI Assist
  - Triage Policy
related_tools:
  - report_followup
  - rag_security_qa
attack_types:
  - Possible Account Compromise
  - Brute Force
severity:
  - LOW
  - MEDIUM
  - HIGH
rule_ids: []
mitre_techniques: []
keywords:
  - detection source
  - rule_based_detector
  - log_pipeline
  - triage_policy
  - report_aware_rag
---

# Detection Source Meaning

Detection source labels help explain which part of the prototype contributed to a report.

Common sources:

- rule_based_detector: deterministic signature or rule logic for direct indicators.
- log_pipeline: parsing and normalization of raw logs into structured events.
- rule_based_correlator: deterministic grouping, time-window checks, and sequence correlation.
- triage_policy: the policy-controlled logic that determines final Risk Level and Decision.
- llm_assist: advisory analysis that may summarize or suggest, but does not control the final verdict.
- report_aware_rag: report-focused explanation after the report is produced.

Rule-based detector, log pipeline, correlator, and triage policy components are deterministic. Their outputs should be reproducible for the same input.

LLMAssist is advisory only. It can suggest reasoning or highlight concerns, but guardrails must validate that it cites real Evidence IDs and does not improperly downgrade deterministic severity.

Report-aware RAG is explanatory. It helps a reviewer understand EV-IDs, F-IDs, Risk Level, Decision, and next steps. It should not re-judge the Incident or create new evidence.

TriagePolicy remains the authority for final risk and decision.
