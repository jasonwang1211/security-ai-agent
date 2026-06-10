"""Focused corpus audit for the v2.7-B Resource Exhaustion knowledge pack.

These tests verify the new reviewed, defensive, blue-team docs exist, parse as
retrieval-only metadata (no detector/graph-seed coupling), carry the required
advisory safety boundary, contain mitigation / evidence-gap language, and do NOT
contain offensive exploit-enablement phrases.
"""

from pathlib import Path

import pytest

from modules.rag.metadata import load_knowledge_metadata

DOC_DIR = Path("knowledge/blue_team/report_explainer")

DOCS: dict[str, str] = {
    "http2_resource_exhaustion.md": "report.http2_resource_exhaustion",
    "http2_bomb_triage.md": "report.http2_bomb_triage",
    "resource_exhaustion_evidence_gap.md": "report.resource_exhaustion_evidence_gap",
    "cve_context_boundary.md": "report.cve_context_boundary",
    "http2_dos_mitigation.md": "report.http2_dos_mitigation",
}

# Phrases that must appear verbatim in every doc's safety boundary block.
REQUIRED_SAFETY_SUBSTRINGS = [
    "advisory only",
    "不會覆蓋",
    "Risk Level 或 Decision",
    "BLOCK / MONITOR / ALLOW",
    "模擬決策",
    "未執行任何真實",
    "人工審查",
    "不提供任何攻擊 PoC",
    "流量產生",
]

# Offensive exploit-enablement phrases that must never appear (case-insensitive).
FORBIDDEN_PHRASES = [
    "run this exploit",
    "attack a real server",
    "send traffic to target",
    "amplify against public target",
    "working poc",
]


def _read(name: str) -> str:
    return (DOC_DIR / name).read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Existence + metadata
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("name", list(DOCS))
def test_doc_exists(name: str) -> None:
    assert (DOC_DIR / name).is_file()


@pytest.mark.parametrize("name,doc_id", list(DOCS.items()))
def test_frontmatter_parses_as_retrieval_only(name: str, doc_id: str) -> None:
    metadata = load_knowledge_metadata(DOC_DIR / name)
    assert metadata is not None
    assert metadata.doc_id == doc_id
    assert metadata.doc_type == "report_explainer"
    assert metadata.review_status == "approved_for_runtime_promotion"
    # Retrieval-only: no attack_types / rule_ids so no graph seed or detector
    # coupling is created (there is no Resource-Exhaustion detection rule).
    assert metadata.attack_types == []
    assert metadata.rule_ids == []


# --------------------------------------------------------------------------- #
# Safety boundary + no offensive content
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("name", list(DOCS))
def test_safety_boundary_phrases_present(name: str) -> None:
    text = _read(name)
    for phrase in REQUIRED_SAFETY_SUBSTRINGS:
        assert phrase in text, f"{name} is missing required safety phrase: {phrase}"


@pytest.mark.parametrize("name", list(DOCS))
def test_advisory_and_no_enforcement_language(name: str) -> None:
    low = _read(name).lower()
    assert "advisory only" in low
    assert "no real enforcement" in low
    assert "simulated" in low
    assert "human review required" in low


@pytest.mark.parametrize("name", list(DOCS))
def test_no_forbidden_exploit_phrases(name: str) -> None:
    low = _read(name).lower()
    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in low, f"{name} contains forbidden phrase: {phrase}"


# --------------------------------------------------------------------------- #
# Per-doc content requirements
# --------------------------------------------------------------------------- #
def test_resource_exhaustion_doc_explains_asymmetric_non_signature() -> None:
    text = _read("http2_resource_exhaustion.md")
    assert "Resource Exhaustion" in text
    assert "HTTP/2" in text
    assert "不對稱" in text  # low inbound -> high server cost (asymmetric)
    assert "signature" in text  # not a normal payload-signature problem


def test_bomb_triage_doc_focuses_on_logs_telemetry_metrics() -> None:
    text = _read("http2_bomb_triage.md")
    assert "telemetry" in text
    assert "metrics" in text
    assert "可以下的結論" in text  # what can be concluded
    assert "不能下的結論" in text  # what cannot be concluded


def test_evidence_gap_doc_lists_required_signals_and_unsafe_assumptions() -> None:
    text = _read("resource_exhaustion_evidence_gap.md")
    for term in (
        "memory pressure",
        "stream count",
        "connection duration",
        "flow-control",
        "server/proxy logs",
        "process metrics",
    ):
        assert term in text, f"evidence-gap doc missing: {term}"
    assert "不安全的假設" in text  # unsafe assumptions


def test_cve_context_doc_requires_asset_facts_and_not_proof() -> None:
    text = _read("cve_context_boundary.md")
    for term in (
        "asset version",
        "configuration",
        "exposure",
        "patch status",
        "reachability",
        "observed behavior",
    ):
        assert term in text, f"CVE context doc missing: {term}"
    assert "背景情報" in text
    assert "不是當前資產已被利用" in text or "不得被當成" in text


def test_mitigation_doc_includes_defensive_controls() -> None:
    text = _read("http2_dos_mitigation.md")
    low = text.lower()
    for term in ("patch", "concurrent streams", "timeout", "rate limit", "reverse proxy"):
        assert term in low, f"mitigation doc missing: {term}"
    assert "升級" in text  # patch / upgrade
    assert "monitoring" in low  # memory / per-connection monitoring
