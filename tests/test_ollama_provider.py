"""Ollama HTTP contract tests."""

import httpx
import pytest
import respx
from PIL import Image

from screensage.providers.ollama_provider import OllamaProvider


@pytest.mark.asyncio
@respx.mock
async def test_ollama_sends_image_and_returns_text() -> None:
    route = respx.post("http://localhost:11434/api/generate").mock(
        return_value=httpx.Response(200, json={"response": "A page."})
    )
    provider = OllamaProvider("http://localhost:11434", "llava")
    try:
        result = await provider.generate("describe", Image.new("RGB", (2, 2)))
        assert result == "A page."
        assert route.calls[0].request.read()
    finally:
        await provider.close()
