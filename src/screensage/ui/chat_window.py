"""Compact screenshot conversation window."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Coroutine
from typing import Any

from loguru import logger
from PIL import Image
from PySide6.QtCore import QPoint, Qt, QTimer, QUrl
from PySide6.QtGui import QCursor, QDesktopServices, QGuiApplication, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from screensage.config import AppConfig
from screensage.orchestrator import Orchestrator
from screensage.providers.registry import create_provider
from screensage.tts.edge_tts import EdgeTTS
from screensage.tts.piper_tts import PiperTTS
from screensage.tts.player import play_audio, set_audio_paused
from screensage.ui.theme import screensage_icon


def image_to_pixmap(image: Image.Image) -> QPixmap:
    """Convert a PIL image into a detached Qt pixmap."""
    rgb = image.convert("RGB")
    qimage = QImage(
        rgb.tobytes(), rgb.width, rgb.height, rgb.width * 3, QImage.Format.Format_RGB888
    ).copy()
    return QPixmap.fromImage(qimage)


def speech_language(text: str, preference: str) -> str:
    """Choose Russian when Cyrillic letters exceed 30 percent."""
    if preference in ("ru", "en"):
        return preference
    letters = [char for char in text if char.isalpha()]
    return (
        "ru"
        if letters
        and sum("а" <= char.lower() <= "я" or char.lower() == "ё" for char in letters)
        / len(letters)
        > 0.3
        else "en"
    )


class ChatWindow(QWidget):
    """A small chat tied to one immutable screenshot."""

    def __init__(
        self,
        image: Image.Image,
        config: AppConfig,
        selection: tuple[int, int, int, int],
    ) -> None:
        super().__init__(
            None, Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setObjectName("glassSurface")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowIcon(screensage_icon())
        self.image, self.config = image, config
        self.orchestrator = Orchestrator(create_provider(config), image)
        self._request_lock = asyncio.Lock()
        self._speech_warning_shown = False
        self.setWindowTitle("ScreenSage")
        self.resize(420, 520)
        self.setMinimumSize(320, 360)
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMaximumHeight(110)
        pix = image_to_pixmap(image)
        self.preview.setPixmap(
            pix.scaled(
                300,
                100,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        header.addWidget(self.preview, 1)
        self.provider_picker = QComboBox()
        self.provider_picker.addItems(["ollama", "gemini", "openrouter"])
        self.provider_picker.setCurrentText(config.provider)
        self.provider_picker.currentTextChanged.connect(self._switch_provider)
        header.addWidget(self.provider_picker)
        layout.addLayout(header)
        self.transcript = QTextBrowser()
        layout.addWidget(self.transcript, 1)
        controls = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask a follow-up…")
        self.input.returnPressed.connect(self._submit)
        controls.addWidget(self.input, 1)
        send = QPushButton("Send")
        send.setObjectName("primaryButton")
        send.clicked.connect(self._submit)
        controls.addWidget(send)
        layout.addLayout(controls)
        actions = QHBoxLayout()
        repeat = QPushButton("Speak again")
        repeat.clicked.connect(self._repeat)
        self.pause_speech_button = QPushButton("⏸ Pause speech")
        self.pause_speech_button.clicked.connect(self._toggle_speech_pause)
        search = QPushButton("Search image")
        search.setToolTip(
            "Copy the selected image and open Google Lens; paste it there with Ctrl+V."
        )
        search.clicked.connect(self._search_image)
        self.search_button = search
        copy = QPushButton("Copy")
        copy.clicked.connect(self._copy)
        close = QPushButton("Close")
        close.clicked.connect(self.close)
        actions.addWidget(repeat)
        actions.addWidget(self.pause_speech_button)
        actions.addWidget(search)
        actions.addWidget(copy)
        actions.addStretch()
        actions.addWidget(close)
        layout.addLayout(actions)
        self._place(selection)
        self.show()
        self.raise_()
        self.activateWindow()
        self.input.setPlaceholderText("Введите вопрос по выделенному изображению…")
        QTimer.singleShot(0, self.input.setFocus)

    def _place(self, selection: tuple[int, int, int, int]) -> None:
        x, y, width, height = selection
        screen = QGuiApplication.screenAt(QPoint(x, y)) or QApplication.primaryScreen()
        avail = screen.availableGeometry()
        target_x = x + width + 12
        target_y = y
        if target_x + self.width() > avail.right():
            target_x = x - self.width() - 12
        if target_x < avail.left() or target_x + self.width() > avail.right():
            cursor = QCursor.pos()
            screen = QGuiApplication.screenAt(cursor) or screen
            avail = screen.availableGeometry()
            target_x = cursor.x() + 16
            target_y = cursor.y() + 16
            if target_x + self.width() > avail.right():
                target_x = cursor.x() - self.width() - 16
        if target_y + self.height() > avail.bottom():
            target_y = avail.bottom() - self.height()
        target_x = min(max(avail.left(), target_x), avail.right() - self.width() + 1)
        target_y = min(max(avail.top(), target_y), avail.bottom() - self.height() + 1)
        self.move(target_x, target_y)

    def _submit(self) -> None:
        prompt = self.input.text().strip()
        if not prompt:
            return
        self.input.clear()
        self._append("You", prompt)
        asyncio.create_task(self._run(self.orchestrator.ask(prompt)))

    async def _run(self, operation: Coroutine[Any, Any, str]) -> None:
        async with self._request_lock:
            started = time.perf_counter()
            logger.info(
                "Chat request started | provider={} | model={}",
                self.config.provider,
                self.config.model,
            )
            try:
                answer = await operation
                logger.info(
                    "Chat request completed | provider={} | model={} | "
                    "response_chars={} | elapsed={:.2f}s",
                    self.config.provider,
                    self.config.model,
                    len(answer),
                    time.perf_counter() - started,
                )
                self._append("ScreenSage", answer)
                if self.config.speech_enabled:
                    await self._speak(answer)
            except Exception as exc:
                logger.error(
                    "Chat request failed | provider={} | model={} | "
                    "elapsed={:.2f}s | error={}",
                    self.config.provider,
                    self.config.model,
                    time.perf_counter() - started,
                    exc,
                )
                logger.exception("Chat operation failed")
                self._append("Error", str(exc))
            finally:
                self.input.setFocus()

    def _append(self, speaker: str, text: str) -> None:
        self.transcript.append(f"<b>{speaker}</b>: {text}")

    async def _speak(self, text: str) -> None:
        language = speech_language(text, self.config.tts_language)
        logger.info(
            "Speech synthesis started | engine={} | language={} | chars={}",
            self.config.tts_engine,
            language,
            len(text),
        )
        audio: bytes | None = None
        if self.config.tts_engine == "piper":
            try:
                audio = await PiperTTS(
                    self.config.tts_voice, self.config.tts_speed
                ).synthesize(text, language)
            except Exception as exc:
                logger.warning("Piper unavailable; falling back to Edge TTS: {}", exc)
        if audio is None:
            if not self._speech_warning_shown:
                self._append(
                    "Speech privacy",
                    "Edge TTS sends answer text to Microsoft for speech synthesis.",
                )
                self._speech_warning_shown = True
            audio = await EdgeTTS(
                self.config.tts_voice, self.config.tts_speed
            ).synthesize(text, language)
        await play_audio(audio)

    def _repeat(self) -> None:
        text = self.transcript.toPlainText().split("ScreenSage:")[-1].strip()
        if text:
            asyncio.create_task(self._repeat_speech(text))

    async def _repeat_speech(self, text: str) -> None:
        try:
            await self._speak(text)
        except Exception as exc:
            self._append("Error", str(exc))
            logger.exception("Speech playback failed")

    def _copy(self) -> None:
        QGuiApplication.clipboard().setText(self.transcript.toPlainText())
        logger.info("Chat transcript copied to clipboard")

    def _toggle_speech_pause(self) -> None:
        """Toggle speech playback pause state."""
        paused = self.pause_speech_button.text().startswith("⏸")
        try:
            set_audio_paused(paused)
        except RuntimeError as exc:
            logger.warning("Could not change speech playback state: {}", exc)
            self._append("Error", str(exc))
            return
        self.pause_speech_button.setText(
            "▶ Resume speech" if paused else "⏸ Pause speech"
        )
        logger.info("Speech playback {}", "paused" if paused else "resumed")

    def _search_image(self) -> None:
        """Copy the captured screenshot and open Google Lens in a browser."""
        rgb = self.image.convert("RGB")
        qimage = QImage(
            rgb.tobytes(),
            rgb.width,
            rgb.height,
            rgb.width * 3,
            QImage.Format.Format_RGB888,
        ).copy()
        QGuiApplication.clipboard().setImage(qimage)
        opened = QDesktopServices.openUrl(QUrl("https://lens.google.com/"))
        if not opened:
            self._append(
                "Поиск изображения",
                "Не удалось открыть браузер. Изображение уже скопировано: "
                "откройте https://lens.google.com/ и нажмите Ctrl+V.",
            )
            logger.error("Could not open browser for Google Lens")
            return
        self._append(
            "Поиск изображения",
            "Изображение скопировано в буфер обмена. В Google Lens нажмите Ctrl+V, "
            "чтобы найти именно выделенную картинку.",
        )
        logger.info(
            "Google Lens opened with selected image copied to clipboard | image={}x{}",
            self.image.width,
            self.image.height,
        )

    def _switch_provider(self, name: str) -> None:
        asyncio.create_task(self._replace_provider(name))

    async def _replace_provider(self, name: str) -> None:
        try:
            logger.info("Switching chat provider | target={}", name)
            await self.orchestrator.close()
            history = list(self.orchestrator.history)
            defaults = {
                "ollama": "qwen3.5:2b",
                "gemini": "gemini-2.0-flash",
                "openrouter": "qwen/qwen2.5-vl-3b-instruct:free",
            }
            if self.config.provider != name and self.config.model in {
                *defaults.values(),
                "qwen2.5vl:7b",
                "llava:latest",
            }:
                self.config.model = defaults[name]
            self.config.provider = name  # type: ignore[assignment]
            self.config.save()
            self.orchestrator = Orchestrator(create_provider(self.config), self.image)
            self.orchestrator.history = history
            self._append(
                "ScreenSage", f"Provider switched to {name}; screenshot retained."
            )
            if name in ("gemini", "openrouter"):
                self._append(
                    "Privacy warning",
                    "This online provider receives the selected screenshot.",
                )
        except Exception as exc:
            self._append("Error", str(exc))
            logger.exception("Could not switch provider")

    def closeEvent(self, event: object) -> None:
        asyncio.create_task(self.orchestrator.close())
        super().closeEvent(event)  # type: ignore[arg-type]
