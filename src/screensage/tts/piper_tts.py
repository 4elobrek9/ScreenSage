"""Local Piper CLI speech synthesis backend."""

from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path

from screensage.tts.base import BaseTTS


class PiperTTS(BaseTTS):
    """Synthesize WAV audio with a configured Piper model."""

    def __init__(self, model: str = "", speed: float = 1.0) -> None:
        self.model, self.speed = model, speed

    async def synthesize(self, text: str, language: str = "en") -> bytes:
        """Run Piper without blocking the Qt event loop."""
        executable = shutil.which("piper")
        if not executable:
            raise RuntimeError("Piper executable is not installed")
        if not self.model or not Path(self.model).is_file():
            raise RuntimeError("Choose a valid local Piper model file in Settings")
        return await asyncio.to_thread(self._synthesize_sync, executable, text)

    def _synthesize_sync(self, executable: str, text: str) -> bytes:
        """Synthesize to a short-lived WAV file and return its contents."""
        import subprocess

        with tempfile.TemporaryDirectory(prefix="screensage-") as directory:
            output = Path(directory) / "speech.wav"
            result = subprocess.run(
                [
                    executable,
                    "--model",
                    self.model,
                    "--output_file",
                    str(output),
                    "--length_scale",
                    str(1 / self.speed),
                ],
                input=text,
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or "Piper synthesis failed")
            return output.read_bytes()
