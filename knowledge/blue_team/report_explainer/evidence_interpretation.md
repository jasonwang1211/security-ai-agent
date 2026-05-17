---
doc_id: report.evidence_interpretation
doc_type: report_explainer
applies_to:
  - Security Triage Report
  - Evidence
  - EV-ID
related_tools:
  - report_followup
  - rag_security_qa
attack_types:
  - Possible Account Compromise
  - Brute Force
severity:
  - MEDIUM
  - HIGH
rule_ids: []
mitre_techniques: []
keywords:
  - evidence
  - EV-ID
  - EV-003
  - success_after_failures
  - report evidence
---

# Evidence Interpretation

Evidence items are concrete observations used to support a Finding. Each item has a stable EV-ID, such as EV-001, EV-002, or EV-003, so a reviewer can ask about it directly.

Examples:

- EV-001 failed_count: how many failed authentication events were observed.
- EV-002 time_window: the time range where the pattern occurred.
- EV-003 success_after_failures: a successful login happened after repeated failures.

EV-003 is important for possible_account_compromise because the sequence suggests that repeated attempts may have eventually reached a successful authentication. This is suspicious, especially when source_ip, user, and target are consistent across the failures and the success.

Evidence explains why the report reached the current Finding, but evidence does not automatically prove confirmed compromise. A successful login after failures may still require analyst review, context from identity logs, session records, endpoint telemetry, and normal user behavior.

Report-aware RAG should explain evidence that already exists in the current Incident. It should not invent new EV-IDs, add unsupported facts, or change the final Risk Level or Decision.
