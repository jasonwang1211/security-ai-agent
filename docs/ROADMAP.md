# Roadmap

Current baseline: v2.8 demo-ready.

Sentinel Project is currently focused on a defensible blue-team demonstration workflow: deterministic detection and decision logic first, advisory AI and retrieval context second.

## Completed

- v2.7 AI advisory layer and safe HTTP/2 Resource Exhaustion synthetic demo.
- v2.8 Lazy RAG startup so deterministic analysis can start without loading heavy retrieval dependencies.
- Language-aware output policy for analyst-facing advisory text.
- Public documentation cleanup for README, project report, user guide, validation evidence, and screenshot gallery.
- Screenshot gallery refresh covering the current Streamlit analyst console.

## Next

- Public documentation polish and link hygiene.
- Packaging and release polish for a cleaner GitHub handoff.
- Additional defensive synthetic scenarios for analyst triage practice.
- Analyst timeline and event replay views.
- Read-only graph and approved-case memory improvements.

## Non-Goals

- No real firewall, WAF, EDR, account, cloud, SIEM, or SOAR action.
- No exploit, proof-of-concept, or traffic generation.
- No AI final verdict and no AI override of deterministic Risk Level or Decision.

## Safety Boundary

- Rule-Based Detector remains the detection authority.
- Risk Level and Decision remain deterministic.
- BLOCK, MONITOR, and ALLOW remain simulated decisions.
- RAG, LLM, AI Analyst Brief, and Evidence Gap Analyzer provide advisory context only.
- Human review is required before any operational action.
