"""Validated application settings and platform-specific persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import tomli_w
from loguru import logger
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from screensage.platform_utils import config_dir, shortcut_display

ProviderName = Literal["ollama", "gemini", "openrouter"]


def config_path() -> Path:
    """Return the user configuration file path for this platform."""
    return config_dir() / "config.toml"


class AppConfig(BaseSettings):
    """User-configurable application options."""

    model_config = SettingsConfigDict(extra="ignore", validate_assignment=True)

    provider: ProviderName = "ollama"
    model: str = "qwen3.5:2b"
    ollama_url: str = "http://localhost:11434"
    openrouter_url: str = "https://openrouter.ai/api/v1"
    tts_engine: Literal["piper", "edge-tts"] = "piper"
    tts_voice: str = ""
    tts_speed: float = Field(default=1.0, ge=0.5, le=2.0)
    tts_language: Literal["auto", "ru", "en"] = "auto"
    hotkey: str = Field(default_factory=shortcut_display)
    speech_enabled: bool = True
    start_minimized: bool = True

    @classmethod
    def load(cls, path: Path | None = None) -> AppConfig:
        """Load settings from TOML, falling back to defaults if unavailable."""
        import tomllib

        target = path or config_path()
        if not target.exists():
            return cls()
        try:
            with target.open("rb") as stream:
                data = tomllib.load(stream)
            return cls.model_validate(data)
        except (OSError, ValueError) as exc:
            logger.warning("Could not load config {}: {}", target, exc)
            return cls()

    def save(self, path: Path | None = None) -> None:
        """Validate and persist options as TOML."""
        target = path or config_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = self.model_dump(mode="json")
        with target.open("wb") as stream:
            tomli_w.dump(payload, stream)
        logger.info("Saved configuration to {}", target)
