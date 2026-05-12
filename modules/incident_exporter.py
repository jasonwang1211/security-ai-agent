from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from modules.types import Incident

REQUIRED_INCIDENT_EXPORT_KEYS = {
    "id",
    "title",
    "status",
    "risk_level",
    "decision",
    "findings",
    "evidence_bundle",
    "generated_with",
}


def incident_to_json_dict(incident: Incident) -> dict[str, Any]:
    return incident.to_json_dict()


def incident_to_json_string(incident: Incident, *, indent: int = 2) -> str:
    return json.dumps(
        incident_to_json_dict(incident),
        ensure_ascii=False,
        indent=indent,
        sort_keys=True,
    )


def write_incident_json(incident: Incident, path: str | Path) -> Path:
    export_path = Path(path)
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(incident_to_json_string(incident), encoding="utf-8")
    return export_path


def incident_summary_for_export(incident: Incident) -> dict[str, Any]:
    generated_at = incident.generated_with.generated_at
    mitre_techniques = sorted(
        {
            technique
            for finding in incident.findings
            for technique in finding.mitre_techniques
        }
    )

    return {
        "id": incident.id,
        "title": incident.title,
        "status": incident.status,
        "risk_level": incident.risk_level,
        "decision": incident.decision,
        "attack_type": incident.attack_type,
        "finding_count": len(incident.findings),
        "evidence_count": len(incident.evidence_bundle.items),
        "generated_at": generated_at.isoformat(),
        "mitre_techniques": mitre_techniques,
        "simulation_notice": incident.simulation_notice,
    }


def validate_incident_json_dict(data: dict[str, Any]) -> bool:
    if not isinstance(data, dict):
        return False

    return REQUIRED_INCIDENT_EXPORT_KEYS.issubset(data)
