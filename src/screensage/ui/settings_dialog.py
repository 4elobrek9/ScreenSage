"""Settings dialog with API credentials stored only in the system keyring."""

from __future__ import annotations

from loguru import logger
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from screensage.config import AppConfig
from screensage.platform_utils import shortcut_display
from screensage.providers.ollama_manager import pull_model
from screensage.providers.registry import store_api_key
from screensage.ui.theme import screensage_icon


class ModelPullWorker(QThread):
    """Download an Ollama model without blocking the Qt interface."""

    progress = Signal(str, int)
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, base_url: str, model: str, parent: QWidget) -> None:
        super().__init__(parent)
        self.base_url = base_url
        self.model = model

    def run(self) -> None:
        """Stream an Ollama model download in the worker thread."""
        try:
            pull_model(self.base_url, self.model, self.progress.emit)
        except Exception as exc:
            logger.exception("Ollama model download failed | model={}", self.model)
            self.failed.emit(str(exc))
        else:
            self.succeeded.emit(self.model)


class SettingsDialog(QDialog):
    """Edit application preferences and securely save provider credentials."""

    def __init__(self, config: AppConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("glassSurface")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowIcon(screensage_icon())
        self.config = config
        self.setWindowTitle("ScreenSage settings")
        form = QFormLayout(self)
        self.provider = QComboBox()
        self.provider.addItems(["ollama", "gemini", "openrouter"])
        self.provider.setCurrentText(config.provider)
        self.model = QLineEdit(config.model)
        self.provider.currentTextChanged.connect(self._provider_changed)
        self.model_download_button = QPushButton("Download model")
        self.model_download_button.clicked.connect(self._download_model)
        model_row = QWidget(self)
        model_layout = QHBoxLayout(model_row)
        model_layout.setContentsMargins(0, 0, 0, 0)
        model_layout.addWidget(self.model, 1)
        model_layout.addWidget(self.model_download_button)
        self.download_status = QLabel()
        self.download_progress = QProgressBar()
        self.download_progress.setRange(0, 100)
        self.download_progress.setValue(0)
        self.download_progress.setVisible(False)
        download_row = QVBoxLayout()
        download_row.setContentsMargins(0, 0, 0, 0)
        download_row.addWidget(model_row)
        download_row.addWidget(self.download_status)
        download_row.addWidget(self.download_progress)
        download_widget = QWidget(self)
        download_widget.setLayout(download_row)
        self.download_widget = download_widget
        self._pull_worker: ModelPullWorker | None = None
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText("Leave blank to keep existing key")
        self.tts_engine = QComboBox()
        self.tts_engine.addItems(["edge-tts", "piper"])
        self.tts_engine.setCurrentText(config.tts_engine)
        self.tts_voice = QLineEdit(config.tts_voice)
        self.tts_speed = QLineEdit(str(config.tts_speed))
        self.tts_language = QComboBox()
        self.tts_language.addItems(["auto", "ru", "en"])
        self.tts_language.setCurrentText(config.tts_language)
        self.hotkey = QLineEdit(shortcut_display())
        self.hotkey.setReadOnly(True)
        self.speech = QCheckBox("Speak answers automatically")
        self.speech.setChecked(config.speech_enabled)
        self.minimized = QCheckBox("Start minimized to tray")
        self.minimized.setChecked(config.start_minimized)
        form.addRow("Provider", self.provider)
        form.addRow("Model", self.download_widget)
        form.addRow("API key (keyring)", self.api_key)
        form.addRow(
            QLabel(
                "Privacy: Gemini and OpenRouter send the selected screenshot "
                "to their online service."
            )
        )
        form.addRow("Speech engine", self.tts_engine)
        form.addRow("Piper model file / Edge voice", self.tts_voice)
        form.addRow("Speech speed (0.5–2.0)", self.tts_speed)
        form.addRow("Speech language", self.tts_language)
        form.addRow("Global shortcut (display only)", self.hotkey)
        form.addRow(self.speech)
        form.addRow(self.minimized)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.save_button = buttons.button(QDialogButtonBox.StandardButton.Save)
        self.cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)
        self._update_model_download_visibility(config.provider)

    def _provider_changed(self, provider: str) -> None:
        self._update_model_download_visibility(provider)
        defaults = {
            "ollama": "qwen3.5:2b",
            "gemini": "gemini-2.0-flash",
            "openrouter": "qwen/qwen2.5-vl-3b-instruct:free",
        }
        if not self.model.text().strip() or self.model.text() in {
            "qwen3.5:2b",
            "qwen2.5vl:7b",
            "llava:latest",
            "gemini-2.0-flash",
            "qwen/qwen2.5-vl-3b-instruct:free",
        }:
            self.model.setText(defaults[provider])

    def _update_model_download_visibility(self, provider: str) -> None:
        """Show Ollama model download controls only for the local provider."""
        self.model_download_button.setVisible(provider == "ollama")

    def _download_model(self) -> None:
        """Start an asynchronous Ollama model download from the settings UI."""
        if self.provider.currentText() != "ollama":
            return
        model = self.model.text().strip()
        if not model:
            QMessageBox.warning(self, "Model required", "Enter an Ollama model name.")
            return
        self.download_progress.setVisible(True)
        self.download_progress.setRange(0, 0)
        self.download_status.setText(f"Starting download of {model}…")
        self.model_download_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        worker = ModelPullWorker(self.config.ollama_url, model, self)
        worker.progress.connect(self._show_download_progress)
        worker.succeeded.connect(self._model_downloaded)
        worker.failed.connect(self._model_download_failed)
        worker.finished.connect(self._model_download_finished)
        self._pull_worker = worker
        logger.info("Starting model download from settings | model={}", model)
        worker.start()

    def _show_download_progress(self, status: str, percent: int) -> None:
        """Display the latest Ollama model download status."""
        self.download_status.setText(f"{status} — {percent}%")
        self.download_progress.setRange(0, 100)
        self.download_progress.setValue(percent)

    def _model_downloaded(self, model: str) -> None:
        """Select the downloaded model for use when settings are saved."""
        self.model.setText(model)
        self.download_status.setText(f"{model} downloaded. Save settings to use it.")
        self.download_progress.setRange(0, 100)
        self.download_progress.setValue(100)

    def _model_download_failed(self, error: str) -> None:
        """Show a clear error when Ollama cannot download the model."""
        self.download_status.setText(f"Download failed: {error}")
        self.download_progress.setRange(0, 100)
        logger.error("Model download failed from settings: {}", error)

    def _model_download_finished(self) -> None:
        """Restore settings controls after the worker thread exits."""
        self.model_download_button.setEnabled(self.provider.currentText() == "ollama")
        self.save_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        self._pull_worker = None

    def reject(self) -> None:
        """Keep the dialog alive while a worker is accessing its controls."""
        if self._pull_worker is not None and self._pull_worker.isRunning():
            self.download_status.setText(
                "Wait for the model download to finish before closing settings."
            )
            return
        super().reject()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Prevent destroying the dialog while its model worker is running."""
        if self._pull_worker is not None and self._pull_worker.isRunning():
            self.download_status.setText(
                "Wait for the model download to finish before closing settings."
            )
            event.ignore()
            return
        super().closeEvent(event)

    def _save(self) -> None:
        if self._pull_worker is not None and self._pull_worker.isRunning():
            return
        try:
            self.config.provider = self.provider.currentText()  # type: ignore[assignment]
            self.config.model = self.model.text().strip()
            self.config.tts_engine = self.tts_engine.currentText()  # type: ignore[assignment]
            self.config.tts_voice = self.tts_voice.text().strip()
            self.config.tts_speed = float(self.tts_speed.text())
            self.config.tts_language = self.tts_language.currentText()  # type: ignore[assignment]
            self.config.speech_enabled = self.speech.isChecked()
            self.config.start_minimized = self.minimized.isChecked()
            key = self.api_key.text().strip()
            if key:
                store_api_key(self.config.provider, key)
            self.config.save()
        except Exception as exc:
            QMessageBox.critical(self, "Settings error", str(exc))
            return
        self.accept()
