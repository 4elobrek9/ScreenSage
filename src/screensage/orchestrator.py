"""Coordinates screenshot analysis and conversational follow-ups."""

from __future__ import annotations

from PIL import Image

from screensage.prompts import SHORT_ANSWER_INSTRUCTION
from screensage.providers.base import BaseProvider, Message


class Orchestrator:
    """Keep screenshot and conversation context for a single chat."""

    def __init__(self, provider: BaseProvider, image: Image.Image) -> None:
        self.provider, self.image = provider, image
        self.history: list[Message] = []

    async def first_answer(self) -> str:
        """Analyze the screenshot with the built-in concise instruction."""
        return await self.ask("Опиши изображение.")

    async def ask(self, prompt: str) -> str:
        """Ask a follow-up while retaining the screenshot and prior turns."""
        model_prompt = f"{SHORT_ANSWER_INSTRUCTION}\n\nВопрос: {prompt}"
        answer = await self.provider.generate(
            model_prompt, self.image, list(self.history)
        )
        self.history.extend((Message("user", prompt), Message("assistant", answer)))
        return answer

    async def close(self) -> None:
        """Release the underlying provider client."""
        await self.provider.close()
