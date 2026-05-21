import subprocess
import sys

import pytest
from pydantic import ValidationError

from modules.eval_cases import load_router_cases
from modules.smart_router import SmartRouterDecision, SmartRouterPreview, preview_route, route_user_input


def _assert_route(user_input: str, expected_input_kind: str, expected_route: str) -> SmartRouterDecision:
    decision = route_user_input(user_input)

    assert decision.input_kind == expected_input_kind
    assert decision.route == expected_route
    return decision


def test_blank_input_routes_to_unknown_clarification():
    decision = _assert_route("  ", "unknown", "clarification_required")

    assert decision.confidence == "HIGH"
    assert decision.requires_clarification


def test_xss_payload_routes_to_payload_triage():
    _assert_route("<script>alert(1)</script>", "payload_or_event", "payload_triage")


def test_command_injection_payload_routes_to_payload_triage():
    _assert_route("127.0.0.1; cat /etc/passwd", "payload_or_event", "payload_triage")


def test_raw_auth_log_line_routes_to_raw_log_translate():
    _assert_route(
        "May 12 10:15:44 host sshd[123]: Failed password for invalid user admin "
        "from 203.0.113.10 port 51234 ssh2",
        "raw_log_line",
        "raw_log_translate",
    )


def test_log_file_path_routes_to_log_file_ingest():
    _assert_route(r"C:\logs\auth.log", "log_file_path", "log_file_ingest")


def test_general_security_question_routes_to_rag_security_qa():
    _assert_route(
        "What is SQL injection and how should analysts triage it?",
        "security_knowledge_question",
        "rag_security_qa",
    )


def test_xss_question_routes_to_rag_security_qa_not_payload_triage():
    _assert_route("XSS 是什麼？", "security_knowledge_question", "rag_security_qa")


def test_ev_id_report_followup_routes_to_report_followup():
    _assert_route("EV-003 是什麼意思？", "report_followup", "report_followup")


def test_monitor_question_routes_to_report_followup():
    _assert_route("為什麼是 MONITOR？", "report_followup", "report_followup")


def test_incident_export_request_routes_to_incident_json_export():
    _assert_route("Export this incident as JSON", "incident_export", "incident_json_export")


def test_unrelated_unclear_text_routes_to_unknown_clarification():
    decision = _assert_route("please handle this thing somehow", "unknown", "clarification_required")

    assert decision.requires_clarification


def test_unknown_decision_requires_clarification():
    with pytest.raises(ValidationError):
        SmartRouterDecision(
            input_kind="unknown",
            route="clarification_required",
            reason="Needs clarification.",
            requires_clarification=False,
        )


def test_route_user_input_does_not_execute_tools():
    decision = route_user_input("<script>alert(1)</script>")

    assert decision.route == "payload_triage"
    assert isinstance(decision, SmartRouterDecision)


def test_preview_route_returns_smart_router_preview():
    preview = preview_route("<script>alert(1)</script>")

    assert isinstance(preview, SmartRouterPreview)
    assert isinstance(preview.decision, SmartRouterDecision)


def test_preview_route_never_executes_tools():
    preview = preview_route("<script>alert(1)</script>")

    assert not preview.would_execute


def test_preview_route_has_would_execute_false():
    preview = preview_route("EV-003 是什麼意思？")

    assert preview.would_execute is False


def test_preview_route_payload_text_includes_route_and_no_execution_wording():
    preview = preview_route("<script>alert(1)</script>")

    assert preview.decision.route == "payload_triage"
    assert "payload_triage" in preview.preview_text
    assert "不會執行工具" in preview.preview_text
    assert "不會改變風險等級或決策" in preview.preview_text


def test_preview_route_report_followup_text_includes_route_and_no_execution_wording():
    preview = preview_route("EV-003 ?臭?暻潭???")

    assert preview.decision.route == "report_followup"
    assert "report_followup" in preview.preview_text
    assert "不會執行工具" in preview.preview_text


def test_preview_route_unknown_input_asks_for_clarification():
    preview = preview_route("please handle this thing somehow")

    assert preview.decision.route == "clarification_required"
    assert preview.decision.requires_clarification
    assert "補充資訊" in preview.preview_text
    assert "不會執行任何工具" in preview.preview_text


def test_preview_route_preserves_route_user_input_decision():
    user_input = "Export this incident as JSON"

    preview = preview_route(user_input)
    decision = route_user_input(user_input)

    assert preview.decision == decision


def test_smart_router_preview_rejects_blank_preview_text():
    decision = route_user_input("<script>alert(1)</script>")

    with pytest.raises(ValidationError):
        SmartRouterPreview(decision=decision, preview_text=" ")


def test_smart_router_preview_does_not_allow_would_execute_true():
    decision = route_user_input("<script>alert(1)</script>")

    with pytest.raises(ValidationError):
        SmartRouterPreview(decision=decision, preview_text="Preview only.", would_execute=True)


def test_bundled_router_cases_match_route_user_input():
    cases = load_router_cases("eval_cases/router_cases.jsonl")

    for case in cases:
        decision = route_user_input(case.user_input)
        assert decision.input_kind == case.expected_input_kind, case.id
        assert decision.route == case.expected_route, case.id


def test_smart_router_decision_rejects_blank_reason():
    with pytest.raises(ValidationError):
        SmartRouterDecision(input_kind="payload_or_event", route="payload_triage", reason=" ")


def test_smart_router_decision_enforces_unknown_to_clarification_required():
    with pytest.raises(ValidationError):
        SmartRouterDecision(
            input_kind="unknown",
            route="payload_triage",
            reason="Invalid route.",
            requires_clarification=True,
        )


def test_smart_router_module_does_not_import_runtime_heavy_modules():
    code = (
        "import sys; "
        "import modules.smart_router; "
        "forbidden={'app','modules.detector','modules.rag_qa','chromadb','ollama','langchain','torch'}; "
        "present=forbidden.intersection(sys.modules); "
        "raise SystemExit(1 if present else 0)"
    )

    result = subprocess.run([sys.executable, "-c", code], check=False)

    assert result.returncode == 0
