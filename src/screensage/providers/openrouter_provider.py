"""OpenRouter OpenAI-compatible vision provider."""

from __future__ import annotations

import httpx
from loguru import logger
from PIL import Image

from screensage.capture import image_to_base64
from screensage.providers.base import BaseProvider, Message


class OpenRouterProvider(BaseProvider):
    """Call OpenRouter's chat completions API."""

    def __init__(
        self,
        api_key: str,
        model: str = "qwen/qwen2.5-vl-3b-instruct:free",
        base_url: str = "https://openrouter.ai/api/v1",
    ) -> None:
        if not api_key:
            raise ValueError("OpenRouter API key is missing; add it in Settings")
        self.api_key, self.model = api_key, model
        self.client = httpx.AsyncClient(timeout=120.0)
        self.url = f"{base_url.rstrip('/')}/chat/completions"

    async def generate(
        self,
        prompt: str,
        image: Image.Image | None = None,
        history: list[Message] | None = None,
    ) -> str:
        messages: list[dict[str, object]] = [
            {
                "role": item.role if item.role in ("user", "assistant") else "user",
                "content": item.content,
            }
            for item in (history or [])
        ]
        if image is not None:
            content: list[dict[str, object]] = [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_to_base64(image)}"
                    },
                },
            ]
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": prompt})
        try:
            response = await self.client.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://github.com/screensage",
                },
                json={"model": self.model, "messages": messages},
            )
            response.raise_for_status()
            answer = response.json()["choices"][0]["message"]["content"]
            if isinstance(answer, list):
                answer = "\n".join(
                    str(part.get("text", ""))
                    for part in answer
                    if isinstance(part, dict)
                )
            return str(answer).strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
            logger.exception("OpenRouter request failed")
            raise RuntimeError(f"OpenRouter request failed: {exc}") from exc

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
