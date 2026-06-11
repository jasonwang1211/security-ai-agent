import importlib
import subprocess
import sys

from modules.output_language import (
    OUTPUT_LANGUAGE_BILINGUAL,
    OUTPUT_LANGUAGE_EN,
    OUTPUT_LANGUAGE_ZH_TW,
    normalize_output_language,
    output_language_instruction,
    output_language_profile,
)

FORBIDDEN_HEAVY_MODULES = (
    "chromadb",
    "sentence_transformers",
    "torch",
    "langchain",
    "langchain_community",
    "ollama",
    "streamlit",
    "modules.rag_qa",
)


def test_normalize_output_language_accepts_ui_values_and_display_names() -> None:
    assert normalize_output_language("zh-TW") == OUTPUT_LANGUAGE_ZH_TW
    assert normalize_output_language("繁體中文") == OUTPUT_LANGUAGE_ZH_TW
    assert normalize_output_language("English") == OUTPUT_LANGUAGE_EN
    assert normalize_output_language("en") == OUTPUT_LANGUAGE_EN
    assert normalize_output_language("bilingual") == OUTPUT_LANGUAGE_BILINGUAL
    assert normalize_output_language("中英雙語") == OUTPUT_LANGUAGE_BILINGUAL
    assert normalize_output_language(None) == OUTPUT_LANGUAGE_ZH_TW


def test_output_language_instructions_match_expected_policy() -> None:
    zh = output_language_instruction("zh-TW")
    en = output_language_instruction("en")
    bilingual = output_language_instruction("bilingual")

    assert "繁體中文為主" in zh
    assert "Risk Level" in zh and "Decision" in zh
    assert "Answer in English" in en
    assert "Traditional Chinese first" in bilingual
    assert "compact" in bilingual


def test_output_language_profile_is_pure_value_object() -> None:
    profile = output_language_profile("English")

    assert profile.language == "en"
    assert profile.short_label == "English"
    assert "SOC analyst" in profile.instruction


def test_output_language_import_stays_lightweight() -> None:
    code = f"""
import importlib
import json
import sys

forbidden = {FORBIDDEN_HEAVY_MODULES!r}
importlib.import_module("modules.output_language")
loaded = [
    name for name in forbidden
    if name in sys.modules or any(module.startswith(name + ".") for module in sys.modules)
]
print(json.dumps(loaded))
raise SystemExit(1 if loaded else 0)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert importlib.import_module("modules.output_language") is not None
