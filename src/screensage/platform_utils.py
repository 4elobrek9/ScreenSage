"""Small centralized helpers for platform-dependent behavior."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def state_dir() -> Path:
    """Return a writable per-user state directory."""
    if sys.platform == "win32":
        return (
            Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
            / "ScreenSage"
        )
    return (
        Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
        / "screensage"
    )


def config_dir() -> Path:
    """Return the user configuration directory for this platform."""
    if sys.platform == "win32":
        return (
            Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
            / "ScreenSage"
        )
    return (
        Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "screensage"
    )


def configure_dpi_awareness() -> None:
    """Request per-monitor DPI awareness on Windows before creating Qt windows."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        try:
            import ctypes

            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            return


def shortcut_display() -> str:
    """Return the platform's default shortcut label."""
    if sys.platform == "win32":
        return "Ctrl+Win+A"
    if sys.platform.startswith("linux"):
        return "Ctrl+Super+A"
    return "Unavailable"


def platform_support_message() -> str | None:
    """Return an explanation when global shortcuts are unsupported."""
    if sys.platform.startswith("linux") and os.environ.get("WAYLAND_DISPLAY"):
        return "Global shortcuts are not supported on Wayland yet; use an X11 session."
    if sys.platform not in ("win32", "linux"):
        return f"Global shortcuts are not supported on {sys.platform}."
    return None
