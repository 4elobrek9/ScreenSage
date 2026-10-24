"""Tests for streamed Ollama model installation."""

import httpx
import pytest
import respx

from screensage.providers.ollama_manager import pull_model


@respx.mock
def test_pull_model_reports_download_progress() -> None:
    route = respx.post("http://localhost:11434/api/pull").mock(
        return_value=httpx.Response(
            200,
            content=(
                b'{"status":"pulling manifest"}\n'
                b'{"status":"downloading","completed":25,"total":100}\n'
                b'{"status":"success"}\n'
            ),
        )
    )
    updates: list[tuple[str, int]] = []

    pull_model(
        "http://localhost:11434",
        "qwen3.5:2b",
        lambda *args: updates.append(args),
    )

    assert updates == [
        ("pulling manifest", 0),
        ("downloading", 25),
        ("success", 0),
    ]
    assert route.calls[0].request.read()


@respx.mock
def test_pull_model_reports_server_errors() -> None:
    respx.post("http://localhost:11434/api/pull").mock(
        return_value=httpx.Response(200, json={"error": "model not found"})
    )

    with pytest.raises(RuntimeError, match="model not found"):
        pull_model("http://localhost:11434", "missing", lambda *_: None)


def test_pull_model_requires_model_name() -> None:
    with pytest.raises(ValueError, match="имя модели"):
        pull_model("http://localhost:11434", "  ", lambda *_: None)
