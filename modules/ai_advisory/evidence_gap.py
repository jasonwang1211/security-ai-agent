"""Deterministic Evidence Gap Analyzer for the v2.7-A AI advisory layer.

Pure, LLM-free, side-effect-free analysis. Given already-computed deterministic
facts, it produces advisory analyst context: what is confirmed, what evidence is
still missing, what to check next, and which assumptions would be unsafe.

It never calls an LLM, RAG, or Ollama; never reads files or crawls knowledge;
never infers new graph facts; and never changes the Risk Level or Decision. The
output is purely advisory and is safe to render alongside, but subordinate to,
the deterministic verdict.
"""

from .types import ADVISORY_BOUNDARY, AIAdvisoryInput, EvidenceGapAnalysis


def _common_confirmed_facts(ai: AIAdvisoryInput) -> list[str]:
    """Facts that are true regardless of scenario, built from structured input."""
    facts: list[str] = []
    if ai.matched_rule_ids:
        facts.append(f"Deterministic rule match: {', '.join(ai.matched_rule_ids)}.")
    if ai.matched_signatures:
        facts.append(f"Matched signature(s): {', '.join(ai.matched_signatures)}.")
    if ai.evidence_labels:
        facts.append(f"Evidence label(s) recorded: {', '.join(ai.evidence_labels)}.")
    if ai.risk_label:
        facts.append(
            f"Deterministic Risk Level (rule-based, authoritative): {ai.risk_label}."
        )
    if ai.decision_label:
        facts.append(
            f"Deterministic Decision (rule-based, simulated): {ai.decision_label}."
        )
    facts.append(f"Detection source: {ai.detection_source} (rule-based, not AI).")
    if ai.incident_id:
        facts.append(f"Associated incident id: {ai.incident_id}.")
    if ai.source_label:
        facts.append(f"Source label: {ai.source_label}.")
    return facts


def _command_injection_sections(ai: AIAdvisoryInput) -> tuple[list[str], list[str], list[str], list[str]]:
    confirmed = [
        "Input matched the Command Injection detection pattern.",
        "Matching a payload, rule, or signature does not prove command execution.",
    ]
    missing = [
        "Process execution evidence (whether a shell or command actually ran).",
        "Server / runtime telemetry around the request.",
        "File modification evidence on the affected host.",
        "Outbound connection evidence from the host or container.",
    ]
    checks = [
        "Web server logs around the request timestamp.",
        "Process creation logs (e.g., new shell or child processes).",
        "EDR telemetry for the affected host or container.",
        "File integrity / file change logs.",
        "Outbound DNS / HTTP connection logs.",
    ]
    unsafe = [
        "Do not claim a command was executed based on a payload, rule, or signature match alone.",
        "Do not claim host or system compromise from a pattern match alone.",
    ]
    return confirmed, missing, checks, unsafe


def _sql_injection_sections(ai: AIAdvisoryInput) -> tuple[list[str], list[str], list[str], list[str]]:
    confirmed = [
        "Input matched the SQL Injection detection pattern.",
        "Matching a SQLi payload or rule does not prove that data was read, "
        "modified, or exfiltrated.",
    ]
    missing = [
        "Database error logs corresponding to the request.",
        "Query execution evidence (whether the injected query actually ran).",
        "Unauthorized data access evidence.",
        "Data exfiltration evidence (volume and destination of any extracted data).",
    ]
    checks = [
        "Application logs around the request timestamp.",
        "Database audit logs.",
        "Query traces / statement logs.",
        "Database and application error logs.",
        "Unusual or large data-access patterns.",
    ]
    unsafe = [
        "Do not claim data exfiltration from a payload match alone.",
        "Do not claim database compromise from the SQLi pattern alone.",
    ]
    return confirmed, missing, checks, unsafe


def _account_compromise_sections(ai: AIAdvisoryInput) -> tuple[list[str], list[str], list[str], list[str]]:
    confirmed: list[str] = []
    if ai.matched_rule_ids or ai.matched_signatures or ai.evidence_labels:
        confirmed.append(
            "Observed authentication sequence: failed login attempts followed by "
            "a successful login."
        )
    confirmed.append(
        "A matched authentication-anomaly pattern does not prove a confirmed "
        "account compromise."
    )
    missing = [
        "MFA status for the successful login.",
        "Impossible-travel / geo-velocity assessment.",
        "Device and session telemetry for the login.",
        "User confirmation of whether the activity was expected.",
        "Privileged action evidence after the successful login.",
    ]
    checks = [
        "Identity provider (IdP) sign-in logs.",
        "MFA / second-factor logs.",
        "Session and device logs.",
        "Geo / IP history for the account.",
        "Account activity and privileged-action audit logs.",
    ]
    unsafe = [
        "Do not claim a confirmed account compromise from the authentication "
        "sequence alone.",
        "Do not claim the account performed malicious actions without "
        "corroborating evidence.",
    ]
    return confirmed, missing, checks, unsafe


def _generic_sections(ai: AIAdvisoryInput) -> tuple[list[str], list[str], list[str], list[str]]:
    confirmed = [
        "A rule-based detection produced this finding.",
        "A rule or signature match indicates pattern resemblance only; it does "
        "not prove real impact or compromise.",
    ]
    missing = [
        "Direct evidence that the activity caused real impact.",
        "Runtime / system telemetry around the event.",
        "Corroborating logs from the affected systems.",
        "Confirmation that the matched pattern reflects genuine malicious activity.",
    ]
    checks = [
        "Relevant application and system logs.",
        "Authentication and access logs.",
        "Host / endpoint telemetry.",
        "Network and outbound connection logs.",
    ]
    unsafe = [
        "Do not treat a rule or signature match as confirmed impact or compromise.",
        "Do not treat the simulated decision as a real enforcement action.",
    ]
    return confirmed, missing, checks, unsafe


def _classify_scenario(ai: AIAdvisoryInput) -> str:
    """Deterministically pick a scenario from structured facts only."""
    haystack = " ".join(
        part for part in (ai.attack_type, ai.finding_type, ai.event_kind) if part
    ).lower()
    rule_ids = [r.strip().upper() for r in ai.matched_rule_ids]

    if "command injection" in haystack or any(r.startswith("CMD-") for r in rule_ids):
        return "command_injection"
    if "sql injection" in haystack or any(r.startswith("SQLI-") for r in rule_ids):
        return "sql_injection"
    if (
        "account compromise" in haystack
        or "authentication" in haystack
        or "auth_" in haystack
        or any(r.startswith("AUTH-") for r in rule_ids)
    ):
        return "account_compromise"
    return "generic"


# Dispatch table keeps analyze_evidence_gap small and the routing explicit.
_SCENARIO_BUILDERS = {
    "command_injection": _command_injection_sections,
    "sql_injection": _sql_injection_sections,
    "account_compromise": _account_compromise_sections,
    "generic": _generic_sections,
}


def analyze_evidence_gap(advisory_input: AIAdvisoryInput) -> EvidenceGapAnalysis:
    """Produce a deterministic, advisory-only evidence gap analysis.

    Reads ``advisory_input`` without mutating it and returns a fresh
    ``EvidenceGapAnalysis``. No LLM, RAG, file, or network access is performed.
    The result never overrides the deterministic Risk Level or Decision.
    """
    scenario = _classify_scenario(advisory_input)
    builder = _SCENARIO_BUILDERS.get(scenario, _generic_sections)
    extra_confirmed, missing, checks, unsafe = builder(advisory_input)

    confirmed_facts = _common_confirmed_facts(advisory_input) + list(extra_confirmed)

    return EvidenceGapAnalysis(
        confirmed_facts=confirmed_facts,
        missing_evidence=list(missing),
        recommended_checks=list(checks),
        unsafe_assumptions=list(unsafe),
        advisory_boundary=ADVISORY_BOUNDARY,
        llm_status="not_used",
        source="deterministic_ai_advisory",
    )
