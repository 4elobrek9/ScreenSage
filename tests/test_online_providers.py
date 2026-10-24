"""HTTP contract tests for online vision providers."""

import httpx
import pytest
import respx
from PIL import Image

from screensage.providers.gemini_provider import GeminiProvider
from screensage.providers.openrouter_provider import OpenRouterProvider


@pytest.mark.asyncio
@respx.mock
async def test_gemini_sends_prompt_and_image() -> None:
    route = respx.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    ).mock(
        return_value=httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "A window."}]}}]},
        )
    )
    provider = GeminiProvider("test-key")
    try:
        answer = await provider.generate("Describe", Image.new("RGB", (2, 2)))
        assert answer == "A window."
        request = route.calls[0].request
        assert b"image/jpeg" in request.content
        assert request.headers["x-goog-api-key"] == "test-key"
        assert "test-key" not in str(request.url)
    finally:
        await provider.close()


@pytest.mark.asyncio
@respx.mock
async def test_openrouter_sends_authorization_and_image() -> None:
    route = respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=httpx.Response(
            200, json={"choices": [{"message": {"content": "A graph."}}]}
        )
    )
    provider = OpenRouterProvider("test-key")
    try:
        answer = await provider.generate("Describe", Image.new("RGB", (2, 2)))
        assert answer == "A graph."
        request = route.calls[0].request
        assert request.headers["Authorization"] == "Bearer test-key"
        assert b"image_url" in request.content
    finally:
        await provider.close()
