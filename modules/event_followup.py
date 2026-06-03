from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ActiveEventContext:
    """Structured facts retained from the latest Mode 1 payload analysis."""

    original_input: str
    attack_types: tuple[str, ...]
    matched_signatures: dict[str, tuple[str, ...]]
    rule_ids: tuple[str, ...]
    rule_sources: tuple[str, ...]
    risk_level: str
    decision: str
    simulation_notice: str
    rendered_report: str


def build_active_event_context(
    *,
    detector_result: dict[str, Any],
    risk_result: dict[str, Any],
    decision_result: dict[str, Any],
    defense_result: dict[str, Any],
    rendered_report: str,
) -> ActiveEventContext:
    metadata = detector_result.get("metadata") or {}
    return ActiveEventContext(
        original_input=str(detector_result.get("original_input") or ""),
        attack_types=tuple(_dedupe_text(detector_result.get("attack_types") or [])),
        matched_signatures=_matched_signatures(detector_result.get("matched_signatures") or {}),
        rule_ids=tuple(_dedupe_text(metadata.get("rule_ids") or [])),
        rule_sources=tuple(_dedupe_text(metadata.get("rule_sources") or [])),
        risk_level=str(risk_result.get("risk_level") or "LOW"),
        decision=str(decision_result.get("decision") or "ALLOW"),
        simulation_notice=str(defense_result.get("summary") or ""),
        rendered_report=str(rendered_report or ""),
    )


def answer_event_followup(
    question: str,
    context: ActiveEventContext | None,
) -> str | None:
    if context is None:
        return None

    intent = classify_event_followup_intent(question)
    if intent == "classification":
        return _classification_answer(context)
    if intent == "evidence_rule":
        return _evidence_rule_answer(context)
    if intent == "simulation_boundary":
        return _simulation_boundary_answer(context)
    if intent == "execution_uncertainty":
        return _execution_uncertainty_answer(context)
    if intent == "investigation_remediation":
        return _investigation_answer(context)
    return None


def classify_event_followup_intent(question: str) -> str | None:
    text = str(question or "").casefold()
    if not text.strip():
        return None

    if _contains_any(
        text,
        [
            "成功執行",
            "執行成功",
            "真的執行",
            "已經執行",
            "命令已經",
            "成功了嗎",
            "prove",
            "executed",
            "exploitation",
            "compromise",
            "遭入侵",
        ],
    ):
        return "execution_uncertainty"

    if _contains_any(
        text,
        [
            "真的已經封鎖",
            "真的封鎖",
            "真實封鎖",
            "實際封鎖",
            "real blocking",
            "real enforcement",
            "simulated",
            "模擬",
            "block 是",
            "monitor 是",
            "allow 是",
        ],
    ):
        return "simulation_boundary"

    if _contains_any(
        text,
        [
            "哪條規則",
            "命中了哪",
            "有什麼證據",
            "證據",
            "規則",
            "rule",
            "signature",
            "matched",
            "indicator",
        ],
    ):
        return "evidence_rule"

    if _contains_any(
        text,
        [
            "調查",
            "修補",
            "處理",
            "先做",
            "下一步",
            "next",
            "investigate",
            "remediate",
            "mitigate",
        ],
    ):
        return "investigation_remediation"

    if _contains_any(
        text,
        [
            "為什麼",
            "怎麼判斷",
            "為何",
            "判定",
            "分類",
            "classified",
            "why",
        ],
    ):
        return "classification"

    return None


def _classification_answer(context: ActiveEventContext) -> str:
    attack_text = _join_or_none(context.attack_types)
    signature_text = _format_matched_signatures(context)
    rule_text = _format_rule_ids(context)
    return (
        f"這筆事件目前由 Mode 1 deterministic detector 判定為 {attack_text}。"
        f"判定依據是目前輸入中的已知攻擊指標：{signature_text}。"
        f"{rule_text}"
        f"目前 Risk Level 為 {context.risk_level}，Decision 為 {context.decision}。"
        "此 Decision 為模擬決策，不代表已執行真實封鎖、監控部署或其他實際處置。"
        "這個回答只解釋目前事件的偵測事實，不新增任何 evidence、finding 或 incident stable ID。"
    )


def _evidence_rule_answer(context: ActiveEventContext) -> str:
    return (
        f"此事件保留的規則 ID：{_join_or_none(context.rule_ids)}。"
        f"此事件保留的 matched signature / evidence：{_format_matched_signatures(context)}。"
        f"原始輸入：{context.original_input}。"
        "這些是目前 Mode 1 實際產生的事件事實；沒有額外建立 evidence、finding 或 incident stable ID。"
    )


def _simulation_boundary_answer(context: ActiveEventContext) -> str:
    return (
        f"{context.decision} 是本專案的模擬決策，不代表已執行真實封鎖、"
        "真實監控部署、防火牆/WAF/EDR 設定變更或帳號處置。"
        "BLOCK、MONITOR 與 ALLOW 都只表示目前 deterministic policy 的訓練/展示用決策。"
        f"目前事件的 simulation notice：{context.simulation_notice}"
    )


def _execution_uncertainty_answer(context: ActiveEventContext) -> str:
    checks = _execution_checks(context.attack_types)
    return (
        "不代表。命中 payload、signature 或 rule 只能表示此輸入符合攻擊模式，"
        "不能證明命令已成功執行、資料已外洩、系統已遭入侵或 compromise 已確認。"
        f"建議用目前事件的脈絡進一步確認：{checks}"
    )


def _investigation_answer(context: ActiveEventContext) -> str:
    guidance = _investigation_guidance(context.attack_types)
    return (
        "建議先依目前事件事實進行人工複核與防禦性調查，"
        "但不要把模擬決策視為已執行的處置。"
        f"目前事件類型：{_join_or_none(context.attack_types)}。"
        f"建議調查與修補重點：{guidance}"
        f"目前 simulation notice：{context.simulation_notice}"
    )


def _execution_checks(attack_types: tuple[str, ...]) -> str:
    if "Command Injection" in attack_types:
        return (
            "檢查應用程式是否真的呼叫 shell 或 command execution sink、process/audit logs、"
            "檔案變更、權限變更、異常 outbound connections，以及相關主機/容器日誌。"
        )
    if "SQL Injection" in attack_types:
        return "檢查 SQL error、異常查詢結果、資料庫 audit log、auth bypass 或資料外洩跡象。"
    if "XSS" in attack_types:
        return "檢查 payload 是否被反射或儲存到頁面、瀏覽器 console、response body 與 CSP 報告。"
    if "Path Traversal" in attack_types:
        return "檢查檔案存取日誌、是否讀取敏感檔案、路徑 normalization 與應用程式錯誤回應。"
    return "檢查相關應用程式日誌、主機日誌、帳號活動與後續安全告警。"


def _investigation_guidance(attack_types: tuple[str, ...]) -> str:
    if "Command Injection" in attack_types:
        return (
            "保留原始請求與參數；檢查 shell metacharacters、管線或命令串接符號；"
            "盤點 command execution sinks；用安全 API 或 allowlist 取代直接 shell 呼叫。"
        )
    if "SQL Injection" in attack_types:
        return (
            "確認 endpoint 與參數；檢查 SQL error、異常查詢結果與資料庫 audit log；"
            "改用 parameterized queries 或 prepared statements。"
        )
    if "XSS" in attack_types:
        return (
            "確認輸出點與 template context；檢查 response body 是否反射 payload；"
            "套用正確 output encoding 並檢查 CSP。"
        )
    if "Path Traversal" in attack_types:
        return (
            "確認受影響路徑參數；檢查檔案存取日誌；套用路徑 normalization 與 allowlist。"
        )
    return "保留原始輸入、時間、來源與相關日誌，確認是否有後續異常活動。"


def _format_matched_signatures(context: ActiveEventContext) -> str:
    parts = []
    for attack_type, signatures in context.matched_signatures.items():
        parts.append(f"{attack_type}: {', '.join(signatures)}")
    return "; ".join(parts) if parts else "None"


def _format_rule_ids(context: ActiveEventContext) -> str:
    if not context.rule_ids:
        return "目前沒有可顯示的 YAML rule ID；此結果可能來自 hardcoded signature。"
    return f"命中規則 ID：{', '.join(context.rule_ids)}。"


def _matched_signatures(raw: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    output: dict[str, tuple[str, ...]] = {}
    for attack_type, signatures in raw.items():
        if isinstance(signatures, list):
            output[str(attack_type)] = tuple(_dedupe_text(signatures))
    return output


def _dedupe_text(values: list[Any]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in deduped:
            deduped.append(text)
    return deduped


def _join_or_none(values: tuple[str, ...]) -> str:
    return ", ".join(values) if values else "None"


def _contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)
