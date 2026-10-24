"""Provider interface and common conversation types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from PIL import Image


@dataclass
class Message:
    """One conversational turn."""

    role: str
    content: str


class BaseProvider(ABC):
    """Abstract asynchronous interface implemented by vision providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        image: Image.Image | None = None,
        history: list[Message] | None = None,
    ) -> str:
        """Generate a response using optional screenshot and prior turns."""

    @abstractmethod
    async def close(self) -> None:
        """Release provider resources."""
