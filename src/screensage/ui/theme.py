"""Shared translucent glass styling for ScreenSage windows."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

GLASS_STYLESHEET = """
QWidget {
    color: #f4f6ff;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 10pt;
}

QWidget#glassSurface {
    background-color: rgba(23, 28, 46, 238);
    border: 1px solid rgba(255, 255, 255, 42);
    border-radius: 22px;
}

QLabel {
    background: transparent;
}

QTextBrowser {
    background-color: rgba(9, 13, 27, 155);
    border: 1px solid rgba(255, 255, 255, 28);
    border-radius: 16px;
    padding: 12px;
    selection-background-color: rgba(110, 150, 255, 170);
}

QLineEdit, QComboBox {
    background-color: rgba(255, 255, 255, 17);
    border: 1px solid rgba(255, 255, 255, 48);
    border-radius: 12px;
    padding: 9px 12px;
    min-height: 22px;
    selection-background-color: rgba(110, 150, 255, 170);
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid rgba(153, 190, 255, 210);
    background-color: rgba(255, 255, 255, 25);
}

QComboBox::drop-down {
    border: 0;
    width: 26px;
}

QComboBox QAbstractItemView {
    color: #f4f6ff;
    background-color: #202740;
    selection-background-color: #526aa5;
    border: 1px solid rgba(255, 255, 255, 42);
    outline: 0;
}

QPushButton {
    background-color: rgba(255, 255, 255, 20);
    border: 1px solid rgba(255, 255, 255, 48);
    border-radius: 12px;
    padding: 8px 13px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: rgba(255, 255, 255, 38);
    border-color: rgba(255, 255, 255, 90);
}

QPushButton:pressed {
    background-color: rgba(140, 165, 230, 70);
}

QPushButton#primaryButton {
    color: white;
    font-weight: 600;
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 rgba(108, 145, 255, 220),
        stop: 1 rgba(151, 111, 240, 220)
    );
    border: 1px solid rgba(207, 218, 255, 100);
}

QPushButton#primaryButton:hover {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 rgba(129, 163, 255, 245),
        stop: 1 rgba(170, 132, 255, 245)
    );
}

QCheckBox {
    spacing: 9px;
}

QCheckBox::indicator {
    width: 17px;
    height: 17px;
    border: 1px solid rgba(255, 255, 255, 80);
    border-radius: 5px;
    background-color: rgba(255, 255, 255, 18);
}

QCheckBox::indicator:checked {
    background-color: #829cff;
    border-color: #aebdff;
}

QDialogButtonBox QPushButton {
    min-width: 82px;
}

QScrollBar:vertical {
    width: 8px;
    background: transparent;
    margin: 4px 1px;
}

QScrollBar::handle:vertical {
    background: rgba(220, 227, 255, 80);
    border-radius: 4px;
    min-height: 24px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
"""


def apply_glass_theme(app: QApplication) -> None:
    """Apply the shared liquid-glass-inspired palette to the application."""
    app.setStyleSheet(GLASS_STYLESHEET)


def screensage_icon() -> QIcon:
    """Load the branded application icon from package assets."""
    asset = Path(__file__).parent.parent / "assets" / "screensage.svg"
    icon = QIcon(str(asset))
    if icon.isNull():
        raise RuntimeError(f"ScreenSage icon asset could not be loaded: {asset}")
    return icon
