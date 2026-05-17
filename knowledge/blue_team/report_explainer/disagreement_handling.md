---
doc_id: report.disagreement_handling
doc_type: report_explainer
applies_to:
  - Security Triage Report
  - AI Assist
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
  - disagreement
  - AI Assist
  - deterministic verdict
  - final decision
  - evidence references
---

# Disagreement Handling

Sometimes AI Assist may differ from the deterministic final verdict. When that happens, Final Decision prevails.

AI Assist is supporting context. A disagreement is something to review, not an authority to follow automatically.

Example:

- The deterministic finding says HIGH / MONITOR.
- LLMAssist suggests BLOCK.
- The report keeps MONITOR as the final Decision.
- The disagreement can be shown as cautionary advisory context.

This matters because deterministic policy controls the final Risk Level and Decision. LLMAssist may lack operational context, may overstate confidence, or may cite evidence incorrectly. Guardrails help detect those problems.

When reviewing a disagreement:

- Check which EV-IDs the AI cited.
- Confirm that those EV-IDs exist in the EvidenceBundle.
- Compare the AI suggestion to the Finding and policy rationale.
- Review the Simulation Notice before taking any real-world action.

If the AI suggestion reveals a useful concern, record it as analyst context and investigate further. Do not treat it as final enforcement authority.
