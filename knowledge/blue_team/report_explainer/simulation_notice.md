---
doc_id: report.simulation_notice
doc_type: report_explainer
applies_to:
  - Security Triage Report
  - Simulation Notice
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
  - simulation notice
  - simulated decision
  - monitor
  - block
  - enforcement
---

# Simulation Notice

All decisions in this prototype are simulated training decisions.

Decision meanings:

- ALLOW: the prototype did not identify enough concern for action.
- MONITOR: the prototype found suspicious behavior that should be reviewed or tracked.
- BLOCK: the prototype recommends a simulated blocking response for training purposes.

The prototype does not control a firewall, WAF, EDR, SIEM, SOAR platform, identity provider, or production enforcement system. It does not revoke sessions, reset passwords, block IPs, disable accounts, or quarantine hosts.

MONITOR means an analyst should review the case, inspect related logs, preserve evidence, and decide whether escalation is needed. It is not a passive dismissal; it is a review path.

BLOCK means the report recommends a simulated blocking action. Real blocking should only occur through approved operational processes, with analyst review and change-control expectations appropriate to the environment.

When reading a Security Triage Report, keep the Simulation Notice in mind. The report is useful for learning, triage explanation, and structured testing, but it is not an enforcement engine.
