"""Speech selection and backend tests."""

from types import SimpleNamespace

import pytest

from screensage.tts import player
from screensage.tts.base import BaseTTS
from screensage.tts.edge_tts import EdgeTTS
from screensage.ui.chat_window import speech_language


def test_language_auto_detection() -> None:
    assert speech_language("Привет, мир!", "auto") == "ru"
    assert speech_language("Hello world", "auto") == "en"
    assert speech_language("Привет", "en") == "en"


def test_tts_is_abstract() -> None:
    with pytest.raises(TypeError):
        BaseTTS()  # type: ignore[abstract]


@pytest.mark.asyncio
async def test_edge_tts_uses_configured_voice_and_speed(mocker) -> None:
    class MockCommunicate:
        def __init__(self, text: str, voice: str, rate: str) -> None:
            assert text == "hello"
            assert voice == "en-GB-LibbyNeural"
            assert rate == "+25%"

        async def stream(self):
            yield {"type": "audio", "data": b"audio"}

    mocker.patch("screensage.tts.edge_tts.edge_tts.Communicate", MockCommunicate)
    audio = await EdgeTTS("en-GB-LibbyNeural", 1.25).synthesize("hello")
    assert audio == b"audio"


def test_speech_pause_controls_current_playback(monkeypatch) -> None:
    calls: list[str] = []
    fake_pygame = SimpleNamespace(
        mixer=SimpleNamespace(
            music=SimpleNamespace(
                pause=lambda: calls.append("pause"),
                unpause=lambda: calls.append("unpause"),
            )
        )
    )
    monkeypatch.setitem(__import__("sys").modules, "pygame", fake_pygame)
    monkeypatch.setattr(player, "_audio_active", True)

    player.set_audio_paused(True)
    assert player.is_audio_paused()
    player.set_audio_paused(False)

    assert not player.is_audio_paused()
    assert calls == ["pause", "unpause"]
    monkeypatch.setattr(player, "_audio_active", False)
