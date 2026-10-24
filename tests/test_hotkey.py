"""Tests for global shortcut combination registration."""

import ctypes
import sys
from ctypes import wintypes

import pytest
import shiboken6
from pynput import keyboard

from screensage import hotkey
from screensage.hotkey import HotkeyListener


def test_hotkey_uses_canonical_ctrl_win_a(monkeypatch) -> None:
    activations: list[str] = []
    captured: dict[str, object] = {}

    class FakeListener:
        def __init__(self, on_press, on_release) -> None:
            captured["on_press"] = on_press
            captured["on_release"] = on_release

        def canonical(self, key):
            if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                return keyboard.Key.ctrl
            if key in (keyboard.Key.cmd_l, keyboard.Key.cmd_r):
                return keyboard.Key.cmd
            if isinstance(key, keyboard.KeyCode) and key.char is not None:
                return keyboard.KeyCode.from_char(key.char.lower())
            return key

        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None

    monkeypatch.setattr("screensage.hotkey.sys.platform", "linux")
    monkeypatch.setattr(keyboard, "Listener", FakeListener)
    listener = HotkeyListener(lambda: activations.append("activated"))
    listener.start()

    press = captured["on_press"]
    release = captured["on_release"]
    assert callable(press)
    assert callable(release)
    for key in (
        keyboard.Key.ctrl_l,
        keyboard.Key.cmd_l,
        keyboard.KeyCode.from_char("a"),
    ):
        press(key)

    assert activations == ["activated"]

    release(keyboard.KeyCode.from_char("a"))
    release(keyboard.Key.cmd_l)
    release(keyboard.Key.ctrl_l)
    listener.stop()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows native hotkey event")
def test_windows_hotkey_filter_dispatches_registered_shortcut() -> None:
    activations: list[str] = []
    event_filter = hotkey._WindowsHotkeyFilter(
        42, lambda: activations.append("activated")
    )
    message = wintypes.MSG()
    message.message = 0x0312
    message.wParam = 42

    handled, result = event_filter.nativeEventFilter(
        b"windows_generic_MSG",
        shiboken6.VoidPtr(ctypes.addressof(message), False),
    )

    assert handled is True
    assert result == 0
    assert activations == ["activated"]
