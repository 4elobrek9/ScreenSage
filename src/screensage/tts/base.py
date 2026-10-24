"""Speech synthesis interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseTTS(ABC):
    """Asynchronous speech synthesis contract."""

    @abstractmethod
    async def synthesize(self, text: str, language: str = "en") -> bytes:
        """Return playable audio bytes."""
