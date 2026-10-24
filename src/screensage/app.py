"""Qt system-tray application bootstrap and event coordination."""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

from loguru import logger
from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon
from qasync import QEventLoop

from screensage.capture import capture_region
from screensage.config import AppConfig
from screensage.hotkey import HotkeyListener
from screensage.platform_utils import (
    platform_support_message,
    state_dir,
)
from screensage.providers.discovery import discover_local_model
from screensage.ui.chat_window import ChatWindow
from screensage.ui.overlay import SelectionOverlay
from screensage.ui.settings_dialog import SettingsDialog
from screensage.ui.theme import apply_glass_theme, screensage_icon


class UiSignals(QObject):
    """Cross-thread signals from the keyboard hook to Qt."""

    toggle_overlay = Signal()


class ScreenSageApp:
    """Own tray, hotkey, and screenshot-selection lifecycle."""

    def __init__(self, app: QApplication) -> None:
        self.app = app
        self._setup_logging()
        self.config = AppConfig.load()
        self.overlay: SelectionOverlay | None = None
        self.windows: list[ChatWindow] = []
        self.signals = UiSignals()
        self.signals.toggle_overlay.connect(self.toggle_overlay)
        self.tray = self._create_tray()
        logger.info(
            "Starting ScreenSage | platform={} | Python={} | executable={} | PID={}",
            sys.platform,
            sys.version.split()[0],
            sys.executable,
            os.getpid(),
        )
        logger.info(
            "Settings loaded | provider={} | model={} | hotkey={} | speech={}",
            self.config.provider,
            self.config.model,
            self.config.hotkey,
            self.config.speech_enabled,
        )
        self.listener: HotkeyListener | None = None
        hotkey_error: str | None = None
        message = platform_support_message()
        if message:
            logger.warning(message)
            hotkey_error = message
        else:
            try:
                self.listener = HotkeyListener(self._hotkey_triggered)
                self.listener.start()
            except Exception as exc:
                logger.exception("Global shortcut could not be started")
                hotkey_error = (
                    f"Не удалось включить глобальное сочетание клавиш: {exc}"
                )
        if QSystemTrayIcon.isSystemTrayAvailable():
            shortcut_status = (
                hotkey_error
                or f"Нажмите {self.config.hotkey} или выберите "
                "«Выделить область экрана» в меню значка ScreenSage."
            )
            self.tray.showMessage(
                "ScreenSage запущен",
                f"{shortcut_status}\nЗатем зажмите левую кнопку мыши, "
                "обведите область и отпустите кнопку.\n"
                f"Логи: {self._log_folder()}",
                QSystemTrayIcon.MessageIcon.Information,
                12000,
            )
        elif hotkey_error:
            QMessageBox.warning(None, "ScreenSage", hotkey_error)
        if (
            not self.config.start_minimized
            or not QSystemTrayIcon.isSystemTrayAvailable()
        ):
            self.show_settings()

    def _setup_logging(self) -> None:
        folder = self._log_folder()
        folder.mkdir(parents=True, exist_ok=True)
        logger.add(
            folder / "screensage.log",
            level="DEBUG",
            rotation="5 MB",
            retention=5,
            encoding="utf-8",
            backtrace=True,
            diagnose=False,
        )
        logger.info("Detailed log file: {}", folder / "screensage.log")

    @staticmethod
    def _log_folder() -> Path:
        """Return the application's log directory."""
        return state_dir() / "logs"

    def _create_tray(self) -> QSystemTrayIcon:
        tray = QSystemTrayIcon()
        tray.setIcon(self.app.windowIcon())
        tray.setToolTip("ScreenSage")
        menu = QMenu()
        select = QAction("Выделить область экрана", menu)
        select.triggered.connect(self.toggle_overlay)
        menu.addAction(select)
        settings = QAction("Settings", menu)
        settings.triggered.connect(self.show_settings)
        menu.addAction(settings)
        open_logs = QAction("Open logs folder", menu)
        open_logs.triggered.connect(
            lambda: QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(self._log_folder()))
            )
        )
        menu.addAction(open_logs)
        providers = menu.addMenu("Switch provider")
        for provider in ("ollama", "gemini", "openrouter"):
            action = QAction(provider, providers)
            action.triggered.connect(
                lambda checked=False, value=provider: self.switch_provider(value)
            )
            providers.addAction(action)
        exit_action = QAction("Exit", menu)
        exit_action.triggered.connect(self.quit)
        menu.addAction(exit_action)
        tray.setContextMenu(menu)
        tray.activated.connect(self._tray_activated)
        tray.show()
        return tray

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_settings()

    def _hotkey_triggered(self) -> None:
        """Forward hotkey activation to Qt's main thread."""
        logger.info("Global shortcut detected; forwarding to Qt event loop")
        self.signals.toggle_overlay.emit()

    def toggle_overlay(self) -> None:
        """Open the selection overlay or cancel the current one."""
        if self.overlay is not None and self.overlay.isVisible():
            logger.info("Selection overlay cancelled by shortcut/menu")
            self.overlay.close()
            self.overlay = None
            return
        logger.info("Opening screen selection overlay")
        self.overlay = SelectionOverlay(self._capture, self._cancel_overlay)
        self.overlay.start()

    async def detect_local_ai(self) -> None:
        """Select an installed local vision model and explain missing setup."""
        if self.config.provider != "ollama":
            return
        try:
            model = await discover_local_model(self.config.ollama_url)
        except RuntimeError as exc:
            logger.warning("Local model detection failed: {}", exc)
            self.tray.showMessage(
                "Ollama не запущена",
                "Установите Ollama, запустите её и установите vision-модель "
                "командой `ollama pull qwen3.5:2b`.",
                QSystemTrayIcon.MessageIcon.Warning,
                10000,
            )
            return
        if model is None:
            self.tray.showMessage(
                "Vision-модель не найдена",
                "В Ollama нет установленной vision-модели. Установите её командой "
                "`ollama pull qwen3.5:2b` или выберите Gemini/OpenRouter "
                "в настройках.",
                QSystemTrayIcon.MessageIcon.Warning,
                10000,
            )
            return
        changed = self.config.model != model
        self.config.model = model
        if changed:
            try:
                self.config.save()
            except OSError as exc:
                logger.exception("Could not save detected local model")
                self.tray.showMessage(
                    "Не удалось сохранить настройки",
                    str(exc),
                    QSystemTrayIcon.MessageIcon.Warning,
                    7000,
                )
        logger.info("Selected installed local vision model: {}", model)
        self.tray.showMessage(
            "Локальная модель найдена",
            f"Будет использоваться {model}. Снимки экрана останутся на компьютере.",
            QSystemTrayIcon.MessageIcon.Information,
            7000,
        )

    def _cancel_overlay(self) -> None:
        logger.info("Selection overlay cancelled by user")
        self.overlay = None

    def _capture(self, left: int, top: int, width: int, height: int) -> None:
        """Capture selected pixels on a worker thread, then open chat."""
        self.overlay = None
        logger.info(
            "Capturing selected screen region | x={} y={} width={} height={}",
            left,
            top,
            width,
            height,
        )

        async def capture_and_show() -> None:
            started = time.perf_counter()
            try:
                image = await asyncio.to_thread(
                    capture_region, left, top, width, height
                )
                logger.info(
                    "Screen capture succeeded | image={}x{} | elapsed={:.2f}s",
                    image.width,
                    image.height,
                    time.perf_counter() - started,
                )
                window = ChatWindow(image, self.config, (left, top, width, height))
                self.windows.append(window)
                window.destroyed.connect(
                    lambda: (
                        self.windows.remove(window) if window in self.windows else None
                    )
                )
            except Exception as exc:
                logger.error(
                    "Screen capture failed after {:.2f}s: {}",
                    time.perf_counter() - started,
                    exc,
                )
                logger.exception("Screen capture failed")
                QMessageBox.critical(None, "ScreenSage capture error", str(exc))

        asyncio.create_task(capture_and_show())

    def show_settings(self) -> None:
        logger.debug("Opening settings dialog")
        dialog = SettingsDialog(self.config)
        if dialog.exec():
            logger.info(
                "Settings updated | provider={} | model={} | speech={} | "
                "tts_engine={} | tts_language={}",
                self.config.provider,
                self.config.model,
                self.config.speech_enabled,
                self.config.tts_engine,
                self.config.tts_language,
            )

    def switch_provider(self, provider: str) -> None:
        defaults = {
            "ollama": "qwen3.5:2b",
            "gemini": "gemini-2.0-flash",
            "openrouter": "qwen/qwen2.5-vl-3b-instruct:free",
        }
        if self.config.provider != provider and self.config.model in {
            *defaults.values(),
            "qwen2.5vl:7b",
            "llava:latest",
        }:
            self.config.model = defaults[provider]
        self.config.provider = provider  # type: ignore[assignment]
        self.config.save()
        logger.info("Default provider set to {}", provider)

    def quit(self) -> None:
        if self.listener:
            self.listener.stop()
        self.tray.hide()
        self.app.quit()


def run() -> int:
    """Start the Qt/qasync application event loop."""
    QApplication.setQuitOnLastWindowClosed(False)
    app = QApplication(sys.argv)
    apply_glass_theme(app)
    app.setWindowIcon(screensage_icon())
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    controller = ScreenSageApp(app)
    loop.create_task(controller.detect_local_ai())
    with loop:
        result = loop.run_forever()
    del controller
    return result or 0
