"""Discovery of installed local vision models served by Ollama."""

from __future__ import annotations

import httpx
from loguru import logger

VISION_MODEL_FAMILIES = (
    "qwen3.5",
    "qwen2.5vl",
    "qwen2.5-vl",
    "llava",
    "moondream",
    "bakllava",
    "minicpm-v",
    "qwen2-vl",
    "llama3.2-vision",
    "gemma3",
)
PREFERRED_MODEL = "qwen3.5:2b"


async def discover_local_model(base_url: str) -> str | None:
    """Return the preferred installed Ollama vision model, if available.

    Args:
        base_url: Base URL of the local Ollama server.

    Raises:
        RuntimeError: If the Ollama server cannot be reached or returns invalid data.
    """
    url = f"{base_url.rstrip('/')}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.info("Ollama model discovery unavailable: {}", exc)
        raise RuntimeError(
            "Не удалось подключиться к Ollama. Запустите Ollama и повторите попытку."
        ) from exc

    models = data.get("models")
    if not isinstance(models, list):
        raise RuntimeError("Ollama вернула неожиданный список моделей")

    installed: list[str] = []
    for entry in models:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if isinstance(name, str) and name.strip():
            installed.append(name.strip())

    def priority(name: str) -> tuple[int, str]:
        lowered = name.lower()
        if lowered == PREFERRED_MODEL:
            return -1, lowered
        for index, family in enumerate(VISION_MODEL_FAMILIES):
            if family in lowered:
                return index, lowered
        return len(VISION_MODEL_FAMILIES), lowered

    supported = [
        name
        for name in installed
        if priority(name)[0] < len(VISION_MODEL_FAMILIES)
    ]
    return min(supported, key=priority) if supported else None
