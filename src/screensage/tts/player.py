"""Play synthesized audio without blocking the GUI."""

from __future__ import annotations

import asyncio
import os
from io import BytesIO
from threading import Lock

_state_lock = Lock()
_audio_paused = False
_audio_active = False


def set_audio_paused(paused: bool) -> None:
    """Pause or resume current and upcoming audio playback."""
    global _audio_paused
    with _state_lock:
        _audio_paused = paused
        active = _audio_active
    if not active:
        return
    try:
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        import pygame
    except ImportError as exc:
        raise RuntimeError("Install pygame to control audio playback") from exc
    if paused:
        pygame.mixer.music.pause()
    else:
        pygame.mixer.music.unpause()


def is_audio_paused() -> bool:
    """Return whether speech playback is currently paused."""
    with _state_lock:
        return _audio_paused


async def play_audio(audio: bytes) -> None:
    """Play MP3/WAV bytes using pygame's cross-platform mixer."""

    # pygame provides one backend for Piper WAV and edge-tts MP3 on both OSes.
    def play() -> None:
        global _audio_active
        try:
            os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
            import pygame
        except ImportError as exc:
            raise RuntimeError("Install pygame to enable audio playback") from exc
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(BytesIO(audio))
        pygame.mixer.music.play()
        with _state_lock:
            _audio_active = True
            paused = _audio_paused
        if paused:
            pygame.mixer.music.pause()
        try:
            while True:
                with _state_lock:
                    paused = _audio_paused
                if not paused and not pygame.mixer.music.get_busy():
                    break
                pygame.time.wait(50)
        finally:
            with _state_lock:
                _audio_active = False

    await asyncio.to_thread(play)
