"""Ollama local vision model integration."""

from __future__ import annotations

import time

import httpx
from loguru import logger
from PIL import Image

from screensage.capture import image_to_base64
from screensage.providers.base import BaseProvider, Message


class OllamaProvider(BaseProvider):
    """Generate answers through Ollama's /api/generate endpoint."""

    def __init__(self, base_url: str, model: str, timeout: float = 180.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.AsyncClient(timeout=timeout)

    async def generate(
        self,
        prompt: str,
        image: Image.Image | None = None,
        history: list[Message] | None = None,
    ) -> str:
        transcript = "\n".join(
            f"{item.role}: {item.content}" for item in (history or [])
        )
        combined = f"{transcript}\nuser: {prompt}".strip()
        payload: dict[str, object] = {
            "model": self.model,
            "prompt": combined,
            "stream": False,
        }
        if image is not None:
            payload["images"] = [image_to_base64(image)]
        started = time.perf_counter()
        logger.info(
            "Sending Ollama request | model={} | image={} | history_turns={}",
            self.model,
            image.size if image is not None else None,
            len(history or []),
        )
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate", json=payload
            )
            response.raise_for_status()
            result = response.json().get("response")
            if not isinstance(result, str) or not result.strip():
                raise ValueError("Ollama returned an empty response")
            logger.info(
                "Ollama request succeeded | model={} | response_chars={} | "
                "elapsed={:.2f}s",
                self.model,
                len(result),
                time.perf_counter() - started,
            )
            return result.strip()
        except (httpx.HTTPError, ValueError) as exc:
            logger.error(
                "Ollama request failed | model={} | elapsed={:.2f}s | error={}",
                self.model,
                time.perf_counter() - started,
                exc,
            )
            logger.exception("Ollama request failed")
            raise RuntimeError(f"Ollama request failed: {exc}") from exc

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
