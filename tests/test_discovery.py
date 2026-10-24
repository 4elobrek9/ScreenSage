"""Tests for automatic local vision-model selection."""

import httpx
import pytest
import respx

from screensage.providers.discovery import discover_local_model


@pytest.mark.asyncio
@respx.mock
async def test_discovery_prefers_installed_vision_model() -> None:
    respx.get("http://localhost:11434/api/tags").mock(
        return_value=httpx.Response(
            200,
            json={
                "models": [
                    {"name": "llama3.1:8b"},
                    {"name": "moondream:latest"},
                    {"name": "llava:7b"},
                    {"name": "qwen2.5vl:7b"},
                    {"name": "qwen3.5:2b"},
                ]
            },
        )
    )

    assert await discover_local_model("http://localhost:11434") == "qwen3.5:2b"


@pytest.mark.asyncio
@respx.mock
async def test_discovery_returns_none_without_vision_models() -> None:
    respx.get("http://localhost:11434/api/tags").mock(
        return_value=httpx.Response(
            200, json={"models": [{"name": "llama3.1:8b"}]}
        )
    )

    assert await discover_local_model("http://localhost:11434") is None


@pytest.mark.asyncio
@respx.mock
async def test_discovery_explains_when_ollama_is_unavailable() -> None:
    respx.get("http://localhost:11434/api/tags").mock(side_effect=httpx.ConnectError)

    with pytest.raises(RuntimeError, match="подключиться к Ollama"):
        await discover_local_model("http://localhost:11434")
