"""Settings UI model installation tests."""

import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from screensage.config import AppConfig
from screensage.ui.settings_dialog import SettingsDialog


def test_model_download_runs_in_worker_and_updates_settings(monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    received: list[tuple[str, str]] = []

    def fake_pull_model(base_url: str, model: str, on_progress) -> None:
        received.append((base_url, model))
        on_progress("downloading", 50)

    monkeypatch.setattr("screensage.ui.settings_dialog.pull_model", fake_pull_model)
    config = AppConfig(model="qwen3.5:2b")
    dialog = SettingsDialog(config)
    dialog.model.setText("qwen3.5:4b")
    dialog.model_download_button.click()

    deadline = time.monotonic() + 2
    while dialog._pull_worker is not None and time.monotonic() < deadline:
        app.processEvents()
        QTest.qWait(10)

    app.processEvents()
    assert received == [("http://localhost:11434", "qwen3.5:4b")]
    assert dialog.model.text() == "qwen3.5:4b"
    assert "downloaded" in dialog.download_status.text()
    assert dialog.download_progress.value() == 100
    assert dialog.model_download_button.isEnabled()
    dialog.close()
