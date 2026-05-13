from pathlib import Path

import yaml
from pydantic import ValidationError

from modules.detection_rules import DetectionRule


def load_detection_rule(path: str | Path) -> DetectionRule:
    rule_path = Path(path)

    try:
        raw_rule = yaml.safe_load(rule_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"could not read detection rule file: {rule_path}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML in detection rule file: {rule_path}") from exc

    if not isinstance(raw_rule, dict):
        raise ValueError(f"detection rule file must contain a YAML mapping: {rule_path}")

    raw_rule["source_path"] = rule_path.as_posix()

    try:
        return DetectionRule.model_validate(raw_rule)
    except ValidationError as exc:
        raise ValueError(f"invalid detection rule schema in file: {rule_path}") from exc


def load_detection_rules(directory: str | Path) -> list[DetectionRule]:
    rule_directory = Path(directory)
    if not rule_directory.exists():
        return []

    rule_paths = _iter_rule_files(rule_directory) if rule_directory.is_dir() else [rule_directory]
    rules: list[DetectionRule] = []

    for rule_path in rule_paths:
        rule = load_detection_rule(rule_path)
        if rule.enabled:
            rules.append(rule)

    return rules


def collect_matches(text: str, rules: list[DetectionRule]) -> dict[str, list[str]]:
    matches_by_attack_type: dict[str, list[str]] = {}

    for rule in rules:
        for pattern in rule.matches(text):
            attack_matches = matches_by_attack_type.setdefault(rule.attack_type, [])
            if pattern not in attack_matches:
                attack_matches.append(pattern)

    return matches_by_attack_type


def _iter_rule_files(directory: Path) -> list[Path]:
    return sorted(
        path
        for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in {".yml", ".yaml"}
    )
