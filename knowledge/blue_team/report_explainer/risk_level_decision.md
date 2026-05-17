---
doc_id: report.risk_level_decision
doc_type: report_explainer
applies_to:
  - Security Triage Report
  - Risk Level
  - Decision
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
  - risk level
  - decision
  - monitor
  - allow
  - block
---

# Risk Level and Decision

Risk Level and Decision are related but not identical.

Risk Level describes how concerning the observed behavior is. Decision describes the simulated action recommendation for the training report.

HIGH does not always mean BLOCK. For possible_account_compromise or Possible Account Compromise, the evidence can be suspicious while still requiring analyst review before containment. MONITOR is appropriate when repeated authentication failures are followed by a success, but the prototype has not confirmed malicious access.

ALLOW, MONITOR, and BLOCK are simulated training decisions. They are not real enforcement actions.

If AI Assist disagrees with the deterministic verdict, the deterministic Risk Level and Decision prevail. AI Assist is advisory and should be reviewed as supporting context only.
