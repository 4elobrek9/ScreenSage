"""Global shortcut listener, imported lazily for OS-specific compatibility."""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any

from loguru import logger

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    from PySide6.QtCore import QAbstractNativeEventFilter


    class _WindowsHotkeyFilter(QAbstractNativeEventFilter):
        """Dispatch a RegisterHotKey message from Qt's Windows event loop."""

        def __init__(self, hotkey_id: int, callback: Callable[[], None]) -> None:
            super().__init__()
            self.hotkey_id = hotkey_id
            self.callback = callback

        def nativeEventFilter(
            self, event_type: bytes, message: int
        ) -> tuple[bool, int]:
            if event_type not in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
                return False, 0
            msg = ctypes.cast(int(message), ctypes.POINTER(wintypes.MSG)).contents
            if msg.message == 0x0312 and msg.wParam == self.hotkey_id:
                logger.info("Windows registered shortcut Ctrl+Win+A detected")
                self.callback()
                return True, 0
            return False, 0


class HotkeyListener:
    """Listen for Ctrl+Win/Super+A and dispatch callbacks."""

    def __init__(self, callback: Callable[[], None]) -> None:
        self.callback = callback
        self._listener: Any | None = None

    def start(self) -> None:
        """Start the pynput listener, raising a clear platform error."""
        if sys.platform == "win32":
            self._start_windows()
            return

        from pynput import keyboard

        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse("<ctrl>+<cmd>+a"), self.callback
        )

        def on_press(key: object) -> None:
            if self._listener is not None:
                normalized = self._listener.canonical(key)
                if normalized in (
                    keyboard.Key.ctrl,
                    keyboard.Key.cmd,
                    keyboard.KeyCode.from_char("a"),
                ):
                    logger.debug("Keyboard hook pressed key: {}", normalized)
                hotkey.press(normalized)

        def on_release(key: object) -> None:
            if self._listener is not None:
                normalized = self._listener.canonical(key)
                if normalized in (
                    keyboard.Key.ctrl,
                    keyboard.Key.cmd,
                    keyboard.KeyCode.from_char("a"),
                ):
                    logger.debug("Keyboard hook released key: {}", normalized)
                hotkey.release(normalized)

        logger.info("Registering global shortcut Ctrl+Win/Super+A")
        self._listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._listener.start()
        logger.info("Global keyboard listener started")

    def _start_windows(self) -> None:
        """Register Ctrl+Win+A with Windows and receive it through Qt."""
        from PySide6.QtWidgets import QApplication

        hotkey_id = 0x5A31
        modifiers = 0x0002 | 0x0008 | 0x4000
        if not ctypes.windll.user32.RegisterHotKey(None, hotkey_id, modifiers, 0x41):
            error = ctypes.get_last_error()
            raise OSError(
                error,
                "Windows не зарегистрировала Ctrl+Win+A. Возможно, это сочетание "
                "уже занято другой программой.",
            )
        event_filter = _WindowsHotkeyFilter(hotkey_id, self.callback)
        app = QApplication.instance()
        if app is None:
            ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)
            raise RuntimeError("Qt application must exist before registering hotkey")
        app.installNativeEventFilter(event_filter)
        self._listener = (hotkey_id, event_filter, app)
        logger.info("Windows global shortcut Ctrl+Win+A registered")

    def stop(self) -> None:
        """Stop the listener if it was started."""
        if self._listener is not None:
            if sys.platform == "win32":
                hotkey_id, event_filter, app = self._listener
                app.removeNativeEventFilter(event_filter)
                ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)
                logger.info("Windows global shortcut unregistered")
            else:
                self._listener.stop()
                logger.info("Global keyboard listener stopped")
