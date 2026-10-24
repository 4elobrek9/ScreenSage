"""Google Gemini REST API provider."""

from __future__ import annotations

from io import BytesIO

import httpx
from loguru import logger
from PIL import Image

from screensage.providers.base import BaseProvider, Message


class GeminiProvider(BaseProvider):
    """Call the Gemini generateContent REST endpoint."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        if not api_key:
            raise ValueError("Gemini API key is missing; add it in Settings")
        self.api_key, self.model = api_key, model
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate(
        self,
        prompt: str,
        image: Image.Image | None = None,
        history: list[Message] | None = None,
    ) -> str:
        parts: list[dict[str, object]] = []
        if history:
            parts.extend({"text": f"{item.role}: {item.content}"} for item in history)
        parts.append({"text": prompt})
        if image is not None:
            buffer = BytesIO()
            image.save(buffer, format="JPEG")
            import base64

            parts.append(
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": base64.b64encode(buffer.getvalue()).decode("ascii"),
                    }
                }
            )
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        try:
            response = await self.client.post(
                url,
                headers={"x-goog-api-key": self.api_key},
                json={"contents": [{"role": "user", "parts": parts}]},
            )
            response.raise_for_status()
            data = response.json()
            answer = data["candidates"][0]["content"]["parts"][0]["text"]
            return str(answer).strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
            logger.exception("Gemini request failed")
            raise RuntimeError(f"Gemini request failed: {exc}") from exc

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
