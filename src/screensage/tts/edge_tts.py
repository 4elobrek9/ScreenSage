"""Microsoft Edge online text-to-speech backend."""

from __future__ import annotations

import edge_tts

from screensage.tts.base import BaseTTS


class EdgeTTS(BaseTTS):
    """Synthesize MP3 bytes using edge-tts."""

    def __init__(self, voice: str = "", speed: float = 1.0) -> None:
        self.voice, self.speed = voice, speed

    async def synthesize(self, text: str, language: str = "en") -> bytes:
        """Return speech audio as MP3 bytes."""
        voice = self.voice or (
            "ru-RU-SvetlanaNeural" if language == "ru" else "en-US-JennyNeural"
        )
        rate_percent = round((self.speed - 1.0) * 100)
        rate = f"{rate_percent:+d}%"
        communicator = edge_tts.Communicate(text, voice, rate=rate)
        chunks = [
            chunk["data"]
            async for chunk in communicator.stream()
            if chunk["type"] == "audio"
        ]
        return b"".join(chunks)
