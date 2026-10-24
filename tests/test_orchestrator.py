"""Tests for concise image-question prompts."""

import pytest
from PIL import Image

from screensage.orchestrator import Orchestrator
from screensage.providers.base import BaseProvider, Message


class RecordingProvider(BaseProvider):
    """Provider that records calls for prompt tests."""

    def __init__(self) -> None:
        self.prompt = ""

    async def generate(
        self,
        prompt: str,
        image: Image.Image | None = None,
        history: list[Message] | None = None,
    ) -> str:
        self.prompt = prompt
        assert image is not None
        return "Ответ."

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_orchestrator_requests_very_short_answer() -> None:
    provider = RecordingProvider()
    orchestrator = Orchestrator(provider, Image.new("RGB", (1, 1)))

    answer = await orchestrator.ask("Что это за предмет?")

    assert answer == "Ответ."
    assert "до 15 слов" in provider.prompt
    assert "Что это за предмет?" in provider.prompt
    assert orchestrator.history[0].content == "Что это за предмет?"
