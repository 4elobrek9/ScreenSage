"""Tests for asking about a selected image without an automatic first request."""

import os
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import QApplication

from screensage.config import AppConfig
from screensage.providers.base import BaseProvider, Message
from screensage.ui.chat_window import ChatWindow
from screensage.ui.theme import apply_glass_theme, screensage_icon


class RecordingProvider(BaseProvider):
    """Provider that records requests without making network calls."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    async def generate(
        self,
        prompt: str,
        image: Image.Image | None = None,
        history: list[Message] | None = None,
    ) -> str:
        self.prompts.append(prompt)
        return "test response"

    async def close(self) -> None:
        return None


def test_chat_waits_for_user_question(monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    apply_glass_theme(app)
    provider = RecordingProvider()
    monkeypatch.setattr(
        "screensage.ui.chat_window.create_provider", lambda config: provider
    )

    window = ChatWindow(
        Image.new("RGB", (4, 4)),
        AppConfig(speech_enabled=False),
        (0, 0, 4, 4),
    )
    app.processEvents()

    assert window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    assert "glassSurface" in app.styleSheet()
    assert not screensage_icon().isNull()
    assert window.input.isEnabled()
    assert window.input.hasFocus()
    assert window.transcript.toPlainText() == ""
    assert provider.prompts == []
    assert window.search_button.text() == "Search image"

    opened_urls: list[str] = []
    with patch.object(
        QDesktopServices,
        "openUrl",
        side_effect=lambda url: opened_urls.append(url.toString()) or True,
    ):
        window.search_button.click()

    clipboard_image = QGuiApplication.clipboard().image()
    assert clipboard_image.size().width() == 4
    assert clipboard_image.size().height() == 4
    assert opened_urls == ["https://lens.google.com/"]
    window.hide()
