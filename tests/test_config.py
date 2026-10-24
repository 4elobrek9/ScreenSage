"""Configuration validation and persistence tests."""

import pytest

from screensage.config import AppConfig


def test_config_round_trip(tmp_path) -> None:
    path = tmp_path / "settings.toml"
    config = AppConfig(
        provider="gemini", model="gemini-2.0-flash", speech_enabled=False
    )
    config.save(path)
    restored = AppConfig.load(path)
    assert restored.provider == "gemini"
    assert restored.model == "gemini-2.0-flash"
    assert restored.speech_enabled is False


def test_speed_validation() -> None:
    with pytest.raises(ValueError):
        AppConfig(tts_speed=3.0)


def test_invalid_toml_uses_defaults(tmp_path) -> None:
    path = tmp_path / "bad.toml"
    path.write_text("provider = [", encoding="utf-8")
    assert AppConfig.load(path).provider == "ollama"
