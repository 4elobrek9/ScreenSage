"""Provider abstraction and orchestration tests."""

import pytest
from PIL import Image

from screensage.orchestrator import Orchestrator
from screensage.providers.base import BaseProvider, Message


def test_provider_is_abstract() -> None:
    with pytest.raises(TypeError):
        BaseProvider()  # type: ignore[abstract]


@pytest.mark.asyncio
async def test_orchestrator_retains_image_and_history(mocker: object) -> None:
    provider = mocker.AsyncMock()  # type: ignore[attr-defined]
    provider.generate.return_value = "answer"
    image = Image.new("RGB", (1, 1))
    chat = Orchestrator(provider, image)
    assert await chat.ask("question") == "answer"
    args = provider.generate.await_args
    assert "до 15 слов" in args.args[0]
    assert "question" in args.args[0]
    assert args.args[1] is image
    assert chat.history == [Message("user", "question"), Message("assistant", "answer")]
