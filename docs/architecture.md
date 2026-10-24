# Architecture

`app.py` wires the PySide6 tray lifecycle to the asyncio loop supplied by
qasync. The pynput listener runs in its own hook thread and emits a Qt signal,
so widget work stays on the GUI thread. `SelectionOverlay` provides a
virtual-desktop rectangle; `capture.py` uses mss to read that global rectangle
and returns a PIL image. Capture runs in a worker thread.

`ChatWindow` owns an `Orchestrator`, which sends the immutable captured image
with every prompt and stores prior turns. `providers.base.BaseProvider`
specifies async generation. Ollama, Gemini, and OpenRouter use httpx async
clients; the registry gets API keys from the OS keyring. Configuration is
validated by pydantic-settings and persisted in TOML.

`tts.base.BaseTTS` defines speech synthesis. Piper runs as a local CLI process;
edge-tts streams online MP3 audio. pygame is used for playback because its
mixer handles both Piper WAV and edge-tts MP3 on Windows and Linux without a
second platform-specific audio adapter. All filesystem settings and log
locations are centralized by platform-specific helpers.

The current MVP targets Windows and Linux/X11. Wayland portal capture and
global shortcut support have not been implemented.
