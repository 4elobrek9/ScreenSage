"""Ollama model installation helpers."""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx
from loguru import logger


def pull_model(
    base_url: str,
    model: str,
    on_progress: Callable[[str, int], None],
) -> None:
    """Download a model from Ollama while reporting streamed progress.

    Args:
        base_url: Base URL of the Ollama service.
        model: Ollama model name or tag.
        on_progress: Callback receiving a status message and percent complete.

    Raises:
        ValueError: If the model name is empty or the stream is invalid.
        RuntimeError: If Ollama reports a model download failure.
        httpx.HTTPError: If the Ollama service cannot be reached.
    """
    model_name = model.strip()
    if not model_name:
        raise ValueError("Укажите имя модели Ollama, например qwen3.5:2b.")
    url = f"{base_url.rstrip('/')}/api/pull"
    logger.info("Starting Ollama model download | model={}", model_name)

    timeout = httpx.Timeout(None, connect=15.0)
    with httpx.Client(timeout=timeout) as client:
        with client.stream(
            "POST", url, json={"name": model_name, "stream": True}
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        "Ollama вернула некорректный статус загрузки."
                    ) from exc
                if not isinstance(event, dict):
                    raise ValueError("Ollama вернула неожиданный статус загрузки.")
                error = event.get("error")
                if error:
                    raise RuntimeError(f"Не удалось скачать модель: {error}")
                status = str(event.get("status", "Загрузка модели"))
                total = event.get("total")
                completed = event.get("completed")
                percent = (
                    min(100, int(completed * 100 / total))
                    if isinstance(total, (int, float))
                    and total > 0
                    and isinstance(completed, (int, float))
                    else 0
                )
                on_progress(status, percent)
                logger.debug(
                    "Ollama pull progress | model={} | status={} | "
                    "completed={} | total={} | percent={}",
                    model_name,
                    status,
                    completed,
                    total,
                    percent,
                )
    logger.info("Ollama model download completed | model={}", model_name)
