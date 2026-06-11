"""Deterministic Evidence Gap Analyzer for the v2.7-A AI advisory layer.

Pure, LLM-free, side-effect-free analysis. Given already-computed deterministic
facts, it produces advisory analyst context: what is confirmed, what evidence is
still missing, what to check next, and which assumptions would be unsafe.

It never calls an LLM, RAG, or Ollama; never reads files or crawls knowledge;
never infers new graph facts; and never changes the Risk Level or Decision. The
output is purely advisory and is safe to render alongside, but subordinate to,
the deterministic verdict.
"""

from modules.output_language import (
    OUTPUT_LANGUAGE_BILINGUAL,
    OUTPUT_LANGUAGE_EN,
    OUTPUT_LANGUAGE_ZH_TW,
    normalize_output_language,
)

from .types import ADVISORY_BOUNDARY, AIAdvisoryInput, EvidenceGapAnalysis

ADVISORY_BOUNDARY_ZH_TW = (
    "確定性 AI 建議分析內容，未使用 LLM 或 RAG。這不會變更、取代或覆蓋"
    "規則式 Risk Level 或 Decision；BLOCK / MONITOR / ALLOW 仍為模擬決策。"
    "不寫入偵測規則、即時知識、圖譜事實或任何真實防護狀態；不執行真實 firewall、"
    "WAF、EDR、account、cloud、SIEM 或 SOAR action；不提供 exploit、PoC 或 traffic generation；"
    "所有處置都需要人工審查。"
)

ADVISORY_BOUNDARY_BILINGUAL = (
    f"{ADVISORY_BOUNDARY_ZH_TW} / Deterministic advisory context only; no LLM or RAG. "
    "It does not override rule-based Risk Level or Decision; no real enforcement, exploit, "
    "PoC, or traffic generation is provided; human review is required."
)


def _line(zh: str, en: str, language: str) -> str:
    if language == OUTPUT_LANGUAGE_ZH_TW:
        return zh
    if language == OUTPUT_LANGUAGE_BILINGUAL:
        return f"{zh} / {en}"
    return en


def _boundary(language: str) -> str:
    if language == OUTPUT_LANGUAGE_ZH_TW:
        return ADVISORY_BOUNDARY_ZH_TW
    if language == OUTPUT_LANGUAGE_BILINGUAL:
        return ADVISORY_BOUNDARY_BILINGUAL
    return ADVISORY_BOUNDARY


def _common_confirmed_facts(ai: AIAdvisoryInput, language: str) -> list[str]:
    """Facts that are true regardless of scenario, built from structured input."""
    facts: list[str] = []
    if ai.matched_rule_ids:
        rule_ids = ", ".join(ai.matched_rule_ids)
        facts.append(
            _line(
                f"確定性規則命中：{rule_ids}。",
                f"Deterministic rule match: {rule_ids}.",
                language,
            )
        )
    if ai.matched_signatures:
        signatures = ", ".join(ai.matched_signatures)
        facts.append(
            _line(
                f"命中的特徵：{signatures}。",
                f"Matched signature(s): {signatures}.",
                language,
            )
        )
    if ai.evidence_labels:
        labels = ", ".join(ai.evidence_labels)
        facts.append(
            _line(
                f"已記錄的證據標籤：{labels}。",
                f"Evidence label(s) recorded: {labels}.",
                language,
            )
        )
    if ai.risk_label:
        facts.append(
            _line(
                f"確定性 Risk Level（規則式權威來源）：{ai.risk_label}。",
                f"Deterministic Risk Level (rule-based, authoritative): {ai.risk_label}.",
                language,
            )
        )
    if ai.decision_label:
        facts.append(
            _line(
                f"確定性 Decision（規則式、模擬）：{ai.decision_label}。",
                f"Deterministic Decision (rule-based, simulated): {ai.decision_label}.",
                language,
            )
        )
    facts.append(
        _line(
            f"偵測來源：{ai.detection_source}（rule-based，不是 AI）。",
            f"Detection source: {ai.detection_source} (rule-based, not AI).",
            language,
        )
    )
    if ai.incident_id:
        facts.append(
            _line(
                f"關聯 incident id：{ai.incident_id}。",
                f"Associated incident id: {ai.incident_id}.",
                language,
            )
        )
    if ai.source_label:
        facts.append(
            _line(
                f"來源標籤：{ai.source_label}。",
                f"Source label: {ai.source_label}.",
                language,
            )
        )
    return facts


def _command_injection_sections(
    ai: AIAdvisoryInput, language: str
) -> tuple[list[str], list[str], list[str], list[str]]:
    confirmed = [
        _line(
            "輸入命中 Command Injection 偵測模式。",
            "Input matched the Command Injection detection pattern.",
            language,
        ),
        _line(
            "命中 payload、rule 或 signature 不代表命令已成功執行。",
            "Matching a payload, rule, or signature does not prove command execution.",
            language,
        ),
    ]
    missing = [
        _line(
            "程序執行證據（是否真的啟動 shell、child process 或 command execution sink）。",
            "Process execution evidence (whether a shell or command actually ran).",
            language,
        ),
        _line(
            "伺服器 / runtime telemetry，確認請求前後是否有異常資源或錯誤訊號。",
            "Server / runtime telemetry around the request.",
            language,
        ),
        _line(
            "受影響主機上的檔案修改證據。",
            "File modification evidence on the affected host.",
            language,
        ),
        _line(
            "主機或 container 的外連 DNS / HTTP connection evidence。",
            "Outbound connection evidence from the host or container.",
            language,
        ),
    ]
    checks = [
        _line(
            "檢查請求時間前後的 Web server logs。",
            "Web server logs around the request timestamp.",
            language,
        ),
        _line(
            "檢查 process creation logs（例如新的 shell 或 child process）。",
            "Process creation logs (e.g., new shell or child processes).",
            language,
        ),
        _line(
            "檢查受影響主機或 container 的 EDR telemetry。",
            "EDR telemetry for the affected host or container.",
            language,
        ),
        _line(
            "檢查 file integrity / file change logs。",
            "File integrity / file change logs.",
            language,
        ),
        _line(
            "檢查 outbound DNS / HTTP connection logs。",
            "Outbound DNS / HTTP connection logs.",
            language,
        ),
    ]
    unsafe = [
        _line(
            "不要只根據 payload、rule 或 signature match 就宣稱命令已執行。",
            "Do not claim a command was executed based on a payload, rule, or signature match alone.",
            language,
        ),
        _line(
            "不要只根據模式命中就宣稱 host 或 system compromise。",
            "Do not claim host or system compromise from a pattern match alone.",
            language,
        ),
    ]
    return confirmed, missing, checks, unsafe


def _sql_injection_sections(
    ai: AIAdvisoryInput, language: str
) -> tuple[list[str], list[str], list[str], list[str]]:
    confirmed = [
        _line(
            "輸入命中 SQL Injection 偵測模式。",
            "Input matched the SQL Injection detection pattern.",
            language,
        ),
        _line(
            "命中 SQLi payload 或 rule 不代表資料已被讀取、修改或外洩。",
            "Matching a SQLi payload or rule does not prove that data was read, "
            "modified, or exfiltrated.",
            language,
        ),
    ]
    missing = [
        _line("對應請求的 database error logs。", "Database error logs corresponding to the request.", language),
        _line(
            "Query execution evidence（注入查詢是否真的執行）。",
            "Query execution evidence (whether the injected query actually ran).",
            language,
        ),
        _line("未授權資料存取證據。", "Unauthorized data access evidence.", language),
        _line(
            "Data exfiltration evidence（任何資料外洩量與目的地）。",
            "Data exfiltration evidence (volume and destination of any extracted data).",
            language,
        ),
    ]
    checks = [
        _line("檢查請求時間前後的 application logs。", "Application logs around the request timestamp.", language),
        _line("檢查 database audit logs。", "Database audit logs.", language),
        _line("檢查 query traces / statement logs。", "Query traces / statement logs.", language),
        _line("檢查 database and application error logs。", "Database and application error logs.", language),
        _line("檢查異常或大量 data-access patterns。", "Unusual or large data-access patterns.", language),
    ]
    unsafe = [
        _line(
            "不要只根據 payload match 就宣稱 data exfiltration。",
            "Do not claim data exfiltration from a payload match alone.",
            language,
        ),
        _line(
            "不要只根據 SQLi pattern 就宣稱 database compromise。",
            "Do not claim database compromise from the SQLi pattern alone.",
            language,
        ),
    ]
    return confirmed, missing, checks, unsafe


def _account_compromise_sections(
    ai: AIAdvisoryInput, language: str
) -> tuple[list[str], list[str], list[str], list[str]]:
    confirmed: list[str] = []
    if ai.matched_rule_ids or ai.matched_signatures or ai.evidence_labels:
        confirmed.append(
            _line(
                "觀察到 authentication sequence：多次 failed login attempts 後出現 successful login。",
                "Observed authentication sequence: failed login attempts followed by "
                "a successful login.",
                language,
            )
        )
    confirmed.append(
        _line(
            "命中 authentication-anomaly pattern 不代表 confirmed account compromise。",
            "A matched authentication-anomaly pattern does not prove a confirmed "
            "account compromise.",
            language,
        )
    )
    missing = [
        _line("successful login 的 MFA status。", "MFA status for the successful login.", language),
        _line(
            "Impossible-travel / geo-velocity assessment。",
            "Impossible-travel / geo-velocity assessment.",
            language,
        ),
        _line("該登入的 device and session telemetry。", "Device and session telemetry for the login.", language),
        _line(
            "使用者確認該活動是否符合預期。",
            "User confirmation of whether the activity was expected.",
            language,
        ),
        _line(
            "successful login 後是否有 privileged action evidence。",
            "Privileged action evidence after the successful login.",
            language,
        ),
    ]
    checks = [
        _line("檢查 Identity provider (IdP) sign-in logs。", "Identity provider (IdP) sign-in logs.", language),
        _line("檢查 MFA / second-factor logs。", "MFA / second-factor logs.", language),
        _line("檢查 session and device logs。", "Session and device logs.", language),
        _line("檢查帳號的 Geo / IP history。", "Geo / IP history for the account.", language),
        _line(
            "檢查 account activity and privileged-action audit logs。",
            "Account activity and privileged-action audit logs.",
            language,
        ),
    ]
    unsafe = [
        _line(
            "不要只根據 authentication sequence 就宣稱 confirmed account compromise。",
            "Do not claim a confirmed account compromise from the authentication "
            "sequence alone.",
            language,
        ),
        _line(
            "沒有 corroborating evidence 前，不要宣稱該帳號已執行惡意行為。",
            "Do not claim the account performed malicious actions without "
            "corroborating evidence.",
            language,
        ),
    ]
    return confirmed, missing, checks, unsafe


def _generic_sections(
    ai: AIAdvisoryInput, language: str
) -> tuple[list[str], list[str], list[str], list[str]]:
    confirmed = [
        _line(
            "規則式偵測產生此 finding。",
            "A rule-based detection produced this finding.",
            language,
        ),
        _line(
            "Rule 或 signature match 只代表模式相似，不證明真實影響或 compromise。",
            "A rule or signature match indicates pattern resemblance only; it does "
            "not prove real impact or compromise.",
            language,
        ),
    ]
    missing = [
        _line("活動造成真實影響的直接證據。", "Direct evidence that the activity caused real impact.", language),
        _line("事件前後的 runtime / system telemetry。", "Runtime / system telemetry around the event.", language),
        _line("受影響系統的 corroborating logs。", "Corroborating logs from the affected systems.", language),
        _line(
            "確認命中模式是否代表 genuine malicious activity。",
            "Confirmation that the matched pattern reflects genuine malicious activity.",
            language,
        ),
    ]
    checks = [
        _line("相關 application and system logs。", "Relevant application and system logs.", language),
        _line("Authentication and access logs。", "Authentication and access logs.", language),
        _line("Host / endpoint telemetry。", "Host / endpoint telemetry.", language),
        _line("Network and outbound connection logs。", "Network and outbound connection logs.", language),
    ]
    unsafe = [
        _line(
            "不要把 rule 或 signature match 當成 confirmed impact 或 compromise。",
            "Do not treat a rule or signature match as confirmed impact or compromise.",
            language,
        ),
        _line(
            "不要把 simulated decision 當成 real enforcement action。",
            "Do not treat the simulated decision as a real enforcement action.",
            language,
        ),
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


def analyze_evidence_gap(
    advisory_input: AIAdvisoryInput, language: str | None = OUTPUT_LANGUAGE_EN
) -> EvidenceGapAnalysis:
    """Produce a deterministic, advisory-only evidence gap analysis.

    Reads ``advisory_input`` without mutating it and returns a fresh
    ``EvidenceGapAnalysis``. No LLM, RAG, file, or network access is performed.
    The result never overrides the deterministic Risk Level or Decision.
    """
    output_language = normalize_output_language(language)
    scenario = _classify_scenario(advisory_input)
    builder = _SCENARIO_BUILDERS.get(scenario, _generic_sections)
    extra_confirmed, missing, checks, unsafe = builder(advisory_input, output_language)

    confirmed_facts = _common_confirmed_facts(advisory_input, output_language) + list(
        extra_confirmed
    )

    return EvidenceGapAnalysis(
        confirmed_facts=confirmed_facts,
        missing_evidence=list(missing),
        recommended_checks=list(checks),
        unsafe_assumptions=list(unsafe),
        advisory_boundary=_boundary(output_language),
        llm_status="not_used",
        source="deterministic_ai_advisory",
    )
