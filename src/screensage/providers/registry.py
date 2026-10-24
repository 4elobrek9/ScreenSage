"""Provider construction and secure credential lookup."""

from __future__ import annotations

import keyring

from screensage.config import AppConfig
from screensage.providers.base import BaseProvider
from screensage.providers.gemini_provider import GeminiProvider
from screensage.providers.ollama_provider import OllamaProvider
from screensage.providers.openrouter_provider import OpenRouterProvider

SERVICE_NAME = "ScreenSage"


def store_api_key(provider: str, api_key: str) -> None:
    """Store a provider API key in the operating-system keyring."""
    keyring.set_password(SERVICE_NAME, provider, api_key)


def create_provider(config: AppConfig) -> BaseProvider:
    """Create a provider, retrieving online credentials from keyring only."""
    if config.provider == "ollama":
        return OllamaProvider(config.ollama_url, config.model)
    key = keyring.get_password(SERVICE_NAME, config.provider) or ""
    if config.provider == "gemini":
        return GeminiProvider(key, config.model or "gemini-2.0-flash")
    return OpenRouterProvider(
        key, config.model or "qwen/qwen2.5-vl-3b-instruct:free", config.openrouter_url
    )
