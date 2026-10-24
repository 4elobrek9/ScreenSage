"""Fullscreen translucent region-selection overlay."""

from __future__ import annotations

from collections.abc import Callable

from loguru import logger
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import (
    QColor,
    QKeyEvent,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import QApplication, QWidget


class SelectionOverlay(QWidget):
    """Select a desktop region with mouse, Enter, or Escape."""

    def __init__(
        self,
        on_capture: Callable[[int, int, int, int], None],
        on_cancel: Callable[[], None],
    ) -> None:
        super().__init__(
            None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.on_capture, self.on_cancel = on_capture, on_cancel
        self.origin: QPoint | None = None
        self.selection = QRect()
        geometry = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(geometry)
        self.setWindowOpacity(1.0)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        logger.debug("Selection overlay initialized | desktop_geometry={}", geometry)

    def start(self) -> None:
        """Show the overlay over the virtual desktop."""
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()
        logger.info("Selection overlay shown; drag with left mouse button to select")

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor(17, 23, 44, 150))
        gradient.setColorAt(0.5, QColor(25, 34, 61, 135))
        gradient.setColorAt(1.0, QColor(45, 29, 68, 145))
        painter.fillRect(self.rect(), gradient)
        if not self.selection.isNull():
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(self.selection, Qt.GlobalColor.transparent)
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOver
            )
            painter.setPen(QPen(QColor("#a8c5ff"), 2))
            painter.drawRect(self.selection)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.globalPosition().toPoint()
            logger.debug(
                "Selection drag started | x={} y={}", self.origin.x(), self.origin.y()
            )
            self.selection = QRect(
                self.mapFromGlobal(self.origin), self.mapFromGlobal(self.origin)
            )
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.origin is not None:
            self.selection = QRect(
                self.mapFromGlobal(self.origin),
                self.mapFromGlobal(event.globalPosition().toPoint()),
            ).normalized()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.origin is not None:
            self.mouseMoveEvent(event)
            logger.debug("Selection drag finished | rect={}", self.selection)
            self._confirm()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            logger.info("Escape pressed; cancelling selection overlay")
            self.on_cancel()
            self.close()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            logger.info("Enter pressed; confirming selection overlay")
            self._confirm()

    def _confirm(self) -> None:
        if self.selection.width() < 2 or self.selection.height() < 2:
            logger.warning(
                "Ignoring selection smaller than 2 pixels | rect={}", self.selection
            )
            return
        rect = self.selection
        top_left = self.mapToGlobal(rect.topLeft())
        self.hide()
        self.on_capture(top_left.x(), top_left.y(), rect.width(), rect.height())
        self.close()
