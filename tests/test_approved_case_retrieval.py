from pathlib import Path

from modules.controller.approved_case_retrieval import (
    AUTH_COMPROMISE_BOUNDARY,
    SIMILAR_CASE_BOUNDARY,
    ApprovedCaseSeed,
    format_similar_case_output,
    load_approved_case_seeds,
    build_case_relationship_explanation,
    retrieve_approved_similar_cases,
)
from modules.event_followup import ActiveEventContext
from modules.incident_followup import build_active_auth_incident_context
from modules.types import EvidenceBundle, EvidenceItem, Finding, Incident
from modules.ui.report_sections import parse_report_sections


def _event_context(
    *,
    attack_types: tuple[str, ...] = ("Command Injection",),
    rule_ids: tuple[str, ...] = ("CMD-001",),
) -> ActiveEventContext:
    return ActiveEventContext(
        original_input="test; rm -rf /tmp/test",
        attack_types=attack_types,
        matched_signatures={"Command Injection": (";", "rm ")},
        rule_ids=rule_ids,
        rule_sources=("detections/blue_team/command_injection_basic.yml",),
        risk_level="HIGH",
        decision="BLOCK",
        simulation_notice="Simulated BLOCK only.",
        rendered_report="Mode 1 report",
    )


def _auth_context():
    incident = Incident(
        id="INC-20260605-001",
        title="Possible Account Compromise",
        status="ALERT",
        risk_level="HIGH",
        decision="MONITOR",
        attack_type="Possible Account Compromise",
        findings=[
            Finding(
                id="F-001",
                finding_type="possible_account_compromise",
                title="Successful login after failures",
                status="ALERT",
                risk_level="HIGH",
                decision="MONITOR",
                evidence_ids=["EV-001", "EV-003"],
            )
        ],
        evidence_bundle=EvidenceBundle(
            incident_id="INC-20260605-001",
            items=[
                EvidenceItem(
                    id="EV-001",
                    type="auth_failure_sequence",
                    description="Repeated failed login attempts",
                    value={"source_ip": "10.0.0.5", "user": "admin"},
                ),
                EvidenceItem(
                    id="EV-003",
                    type="success_after_failures",
                    description="Successful login after failures",
                    value={"source_ip": "10.0.0.5", "user": "admin"},
                ),
            ],
        ),
    )
    return build_active_auth_incident_context(incident)


def test_loads_only_approved_seed_files_from_default_corpus() -> None:
    seeds = load_approved_case_seeds()

    assert [seed.case_id for seed in seeds] == [
        "CASE-SEED-001",
        "CASE-SEED-002",
        "CASE-SEED-003",
    ]
    assert all(seed.review_status == "approved_for_similarity_demo" for seed in seeds)
    assert all(seed.approved_for_retrieval is True for seed in seeds)


def test_invalid_unapproved_and_runtime_draft_seed_files_are_ignored(tmp_path: Path) -> None:
    (tmp_path / "unapproved.yml").write_text(
        """
schema_version: v2.5-approved-case1
case_id: CASE-SEED-X
title: Unapproved
review_status: draft
approved_for_retrieval: false
case_type: payload_event
risk_level: HIGH
decision: BLOCK
simulated_decision: true
summary: draft
analyst_conclusion: draft
outcome: draft
source_provenance: manually_curated_seed
current_event_authority: advisory_only_no_override
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "invalid.yml").write_text("not: [valid", encoding="utf-8")

    seeds = load_approved_case_seeds(tmp_path)

    assert seeds == []


def test_command_injection_active_event_returns_case_seed_001_as_top_match() -> None:
    result = retrieve_approved_similar_cases(_event_context(), load_approved_case_seeds())

    assert result.matches[0].seed.case_id == "CASE-SEED-001"
    assert "matched attack_types: Command Injection" in result.matches[0].reasons
    assert "matched rule_ids: CMD-001" in result.matches[0].reasons


def test_authentication_incident_returns_case_seed_002_as_top_match() -> None:
    result = retrieve_approved_similar_cases(_auth_context(), load_approved_case_seeds())

    assert result.matches[0].seed.case_id == "CASE-SEED-002"
    assert "matched finding_types: possible_account_compromise" in result.matches[0].reasons
    assert "matched evidence_types: auth_failure_sequence, success_after_failures" in result.matches[0].reasons


def test_risk_and_decision_only_matches_are_excluded() -> None:
    event_result = retrieve_approved_similar_cases(_event_context(), load_approved_case_seeds())
    auth_result = retrieve_approved_similar_cases(_auth_context(), load_approved_case_seeds())

    assert [match.seed.case_id for match in event_result.matches] == ["CASE-SEED-001"]
    assert [match.seed.case_id for match in auth_result.matches] == ["CASE-SEED-002"]


def test_sql_injection_seed_exists_as_comparison_candidate() -> None:
    seeds = load_approved_case_seeds()
    sql_seed = next(seed for seed in seeds if seed.case_id == "CASE-SEED-003")

    assert sql_seed.attack_types == ["SQL Injection"]
    assert sql_seed.rule_ids == ["SQLI-001"]
    assert sql_seed.evidence_types == ["sql_injection_payload"]


def test_output_includes_reasons_differences_and_boundaries() -> None:
    result = retrieve_approved_similar_cases(_auth_context(), load_approved_case_seeds())

    output = format_similar_case_output(result)

    assert "CASE-SEED-002" in output
    assert "Similarity reasons:" in output
    assert "Key differences / missing evidence to check:" in output
    assert SIMILAR_CASE_BOUNDARY in output
    assert AUTH_COMPROMISE_BOUNDARY in output
    assert "do not override" in output
    assert "do not prove account compromise" in output


def test_command_injection_output_includes_graph_grounded_relationship_lines() -> None:
    result = retrieve_approved_similar_cases(_event_context(), load_approved_case_seeds())

    output = format_similar_case_output(result)

    assert "Graph-Grounded Relationship Explanation:" in output
    assert "Current context shares attack type Command Injection with CASE-SEED-001." in output
    assert "Current context shares rule ID CMD-001 with CASE-SEED-001." in output
    assert "Current context shares evidence type shell_metacharacter_payload with CASE-SEED-001." in output
    assert "Historical simulated BLOCK does not prove current command execution." in output
    assert SIMILAR_CASE_BOUNDARY in output


def test_auth_incident_output_includes_graph_grounded_relationship_lines() -> None:
    result = retrieve_approved_similar_cases(_auth_context(), load_approved_case_seeds())

    output = format_similar_case_output(result)

    assert "Graph-Grounded Relationship Explanation:" in output
    assert "Current incident shares attack type Possible Account Compromise with CASE-SEED-002." in output
    assert "Current incident shares finding type possible_account_compromise with CASE-SEED-002." in output
    assert "Current incident shares evidence type success_after_failures with CASE-SEED-002." in output
    assert "Current incident shares simulated Decision MONITOR with CASE-SEED-002." in output
    assert AUTH_COMPROMISE_BOUNDARY in output


def test_relationship_explanation_is_omitted_when_no_approved_case_matches() -> None:
    result = retrieve_approved_similar_cases(
        _event_context(attack_types=("Unknown Attack",), rule_ids=("UNKNOWN-001",)),
        load_approved_case_seeds(),
    )

    output = format_similar_case_output(result)

    assert result.matches == ()
    assert "No approved similar cases matched the current structured facts." in output
    assert "Graph-Grounded Relationship Explanation:" not in output


def test_relationship_explanation_helper_uses_structured_match_fields() -> None:
    result = retrieve_approved_similar_cases(_event_context(), load_approved_case_seeds())

    explanation = build_case_relationship_explanation(result.current, result.matches[0])

    assert explanation.shared_relationships == (
        "Current context shares attack type Command Injection with CASE-SEED-001.",
        "Current context shares rule ID CMD-001 with CASE-SEED-001.",
        "Current context shares evidence type shell_metacharacter_payload with CASE-SEED-001.",
        "Current context shares simulated Decision BLOCK with CASE-SEED-001.",
    )
    assert "Historical simulated BLOCK does not prove current command execution." in explanation.difference_relationships
    assert explanation.boundary == SIMILAR_CASE_BOUNDARY


def test_approved_case_seed_model_rejects_non_advisory_seed() -> None:
    raw = load_approved_case_seeds()[0].model_dump()
    raw["current_event_authority"] = "can_override"

    try:
        ApprovedCaseSeed.model_validate(raw)
    except ValueError as exc:
        assert "advisory only" in str(exc)
    else:
        raise AssertionError("non-advisory approved case seed was accepted")


def test_approved_case_retrieval_has_no_heavy_runtime_dependencies() -> None:
    source = Path("modules/controller/approved_case_retrieval.py").read_text(encoding="utf-8")

    forbidden = [
        "chromadb",
        "ollama",
        "langchain",
        "ingest_knowledge",
        "workbench/case_drafts",
        "modules.graph",
        "modules.rag",
    ]
    assert all(item not in source for item in forbidden)


# --- v2.6-S language-aware similar-case output ------------------------------


def _command_injection_output(language: str | None = None) -> str:
    result = retrieve_approved_similar_cases(_event_context(), load_approved_case_seeds())
    return format_similar_case_output(result, language)


def test_english_similar_case_output_remains_existing_wording() -> None:
    output = _command_injection_output("en")

    assert "[Approved Similar Cases]" in output
    assert "Current Risk Level: HIGH" in output
    assert "Current Decision: BLOCK" in output
    assert "Similarity reasons:" in output
    assert "Graph-Grounded Relationship Explanation:" in output
    assert "CASE-SEED-001" in output


def test_default_language_similar_case_output_matches_explicit_english() -> None:
    result = retrieve_approved_similar_cases(_event_context(), load_approved_case_seeds())

    assert format_similar_case_output(result) == format_similar_case_output(result, "en")


def test_zh_tw_similar_case_output_uses_chinese_labels_and_keeps_dynamic_values() -> None:
    output = _command_injection_output("zh-TW")

    assert "[核准相似案例]" in output
    assert "目前風險等級：HIGH" in output
    assert "目前決策：BLOCK" in output
    assert "相似原因：" in output
    assert "圖形關係說明：" in output
    assert "目前脈絡與 CASE-SEED-001 共享攻擊類型：Command Injection。" in output
    assert "目前脈絡與 CASE-SEED-001 共享規則 ID：CMD-001。" in output
    assert "目前脈絡與 CASE-SEED-001 共享證據類型：shell_metacharacter_payload。" in output
    # dynamic / domain values are never translated.
    for token in ("CASE-SEED-001", "Command Injection", "CMD-001", "shell_metacharacter_payload"):
        assert token in output
    # English fixed labels must not leak in zh-TW mode.
    assert "Current Risk Level:" not in output
    assert "Graph-Grounded Relationship Explanation:" not in output
    # the deterministic reason content stays English (produced by scoring).
    assert "matched attack_types: Command Injection" in output


def test_bilingual_similar_case_output_uses_compact_bilingual_labels() -> None:
    output = _command_injection_output("bilingual")

    assert "[核准相似案例 / Approved Similar Cases]" in output
    assert "目前風險等級 / Current Risk Level：HIGH" in output
    assert "相似原因 / Similarity reasons：" in output
    assert "圖形關係說明 / Graph-Grounded Relationship Explanation：" in output
    # bilingual keeps both halves of relationship sentences; dynamic values intact.
    assert "Current context shares attack type Command Injection with CASE-SEED-001." in output
    assert "目前脈絡與 CASE-SEED-001 共享攻擊類型：Command Injection。" in output


def test_unsupported_similar_case_language_falls_back_to_english() -> None:
    output = _command_injection_output("fr")

    assert "[Approved Similar Cases]" in output
    assert "[核准相似案例]" not in output


def test_similar_case_scoring_and_matching_unchanged_across_languages() -> None:
    seeds = load_approved_case_seeds()
    base = retrieve_approved_similar_cases(_event_context(), seeds)

    # language is a render-only argument; ranking, scores, and reasons are
    # computed before formatting and never depend on it.
    for language in ("en", "zh-TW", "bilingual", "fr"):
        format_similar_case_output(base, language)
    assert [match.seed.case_id for match in base.matches] == ["CASE-SEED-001"]
    assert base.matches[0].score == retrieve_approved_similar_cases(
        _event_context(), seeds
    ).matches[0].score
    assert "matched attack_types: Command Injection" in base.matches[0].reasons


def test_zh_tw_relationship_helper_keeps_seed_differences_and_localizes_boundary() -> None:
    result = retrieve_approved_similar_cases(_event_context(), load_approved_case_seeds())

    explanation = build_case_relationship_explanation(result.current, result.matches[0], "zh-TW")

    assert explanation.shared_relationships[0].startswith("目前脈絡與 CASE-SEED-001 共享攻擊類型")
    # seed-derived differences are dynamic content and stay unchanged (English).
    assert "Historical simulated BLOCK does not prove current command execution." in (
        explanation.difference_relationships
    )
    assert explanation.boundary.startswith("歷史核准案例僅供參考")


def test_zh_tw_real_output_parses_into_localized_report_sections() -> None:
    # End-to-end guard: the real localized renderer output must still split into
    # the approved-similar-case and graph-relationship sections by the parser.
    output = _command_injection_output("zh-TW")

    sections = parse_report_sections(output)

    assert sections.approved_similar_cases.startswith("[核准相似案例]")
    assert "CASE-SEED-001" in sections.approved_similar_cases
    assert sections.graph_relationship_explanation.startswith("圖形關係說明：")
    assert "共享攻擊類型：Command Injection" in sections.graph_relationship_explanation
    # localized analyst-conclusion field closes the graph block.
    assert "分析師結論" not in sections.graph_relationship_explanation
