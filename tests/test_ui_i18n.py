import sys
from pathlib import Path

from modules.ui.i18n import (
    CORE_UI_KEYS,
    DEFAULT_LANGUAGE,
    language_display_name,
    language_display_options,
    language_from_display_name,
    normalize_language,
    t,
)


def test_default_language_is_traditional_chinese() -> None:
    assert DEFAULT_LANGUAGE == "zh-TW"


def test_normalize_language_defaults_for_none_or_unknown() -> None:
    assert normalize_language(None) == DEFAULT_LANGUAGE
    assert normalize_language("unknown") == DEFAULT_LANGUAGE


def test_language_display_names() -> None:
    assert language_display_name("zh-TW") == "繁體中文"
    assert language_display_name("en") == "English"
    assert language_display_name("bilingual") == "中英雙語"


def test_language_display_options_are_ordered() -> None:
    assert language_display_options() == ("繁體中文", "English", "中英雙語")


def test_language_from_display_name() -> None:
    assert language_from_display_name("繁體中文") == "zh-TW"
    assert language_from_display_name("English") == "en"
    assert language_from_display_name("中英雙語") == "bilingual"


def test_translates_run_input_for_each_language_mode() -> None:
    assert t("run_input", "zh-TW") == "執行輸入"
    assert t("run_input", "en") == "Run input"
    assert t("run_input", "bilingual") == "執行輸入 / Run input"


def test_missing_key_returns_safe_fallback() -> None:
    assert t("missing.translation.key", "en") == "missing.translation.key"


def test_core_ui_keys_exist_for_major_areas() -> None:
    for key in CORE_UI_KEYS:
        assert t(key, "zh-TW") != key
        assert t(key, "en") != key
        assert t(key, "bilingual") != key


def test_i18n_helper_does_not_import_streamlit() -> None:
    source = Path("modules/ui/i18n.py").read_text(encoding="utf-8")

    assert "streamlit" not in source.lower()
    assert "streamlit" not in sys.modules


def test_i18n_helper_does_not_contain_display_name_mojibake_markers() -> None:
    source = Path("modules/ui/i18n.py").read_text(encoding="utf-8")

    for marker in ("蝜", "銝", "", ""):
        assert marker not in source
