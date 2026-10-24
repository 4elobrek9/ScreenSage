# ScreenSage

ScreenSage is a Windows and Linux/X11 system-tray assistant for understanding a
selected screen region. Press **Ctrl+Win+A** (Windows) or **Ctrl+Super+A**
(Linux/X11), drag a region, and continue asking questions in the small chat.

## Requirements and installation

- Python 3.11+, a desktop session, and an audio output device for speech.
- Linux needs X11 (Wayland global shortcuts/capture are not supported yet).
- Windows: double-click `run_screensage.bat`; it creates `.venv`, installs the
  package, and starts it. Or install manually:

  ```powershell
  py -3.11 -m venv .venv
  .venv\Scripts\Activate.ps1
  python -m pip install -e .
  python -m screensage
  ```

- Linux: `python3 -m venv .venv && . .venv/bin/activate`, then
  `pip install -e .` and `python -m screensage`. Install system audio/X11
  development libraries as needed by PySide6, pygame, and pynput.
- Development: `pip install -e ".[dev]"`, then `pytest`, `ruff check .`,
  `mypy`.

The default provider is **Ollama** at `http://localhost:11434`, with the newer,
compact vision model `qwen3.5:2b` preferred. Open Settings, enter a model name,
and click **Download model** to install it from Ollama without blocking the UI.
The download requires the Ollama service and internet access. At startup,
ScreenSage checks the models installed in Ollama and selects it when present;
otherwise it picks another supported vision model (`qwen2.5vl`, `llava`,
`moondream`, `bakllava`, `minicpm-v`, `qwen2-vl`, `qwen3-vl`,
`llama3.2-vision`, or `gemma3`). It does not silently switch to an online
provider. If no local vision model is found, install Ollama, start it, then run
`ollama pull qwen3.5:2b`; ScreenSage will show a tray notification with the
status. The Ollama library currently lists the model at about 3.1 GB on disk;
actual VRAM use is higher and depends on image size, context, and quantization.
Gemini and OpenRouter need API keys configured in Settings; keys are stored in
the operating-system keyring, never in `config.toml`. Selecting either online
provider sends the selected screenshot and follow-up context to that service.
Review each provider's privacy and pricing terms before use.

Answers are prompted to be one short phrase of at most 15 words, unless you ask
for more detail. The chat's **Pause speech** button pauses/resumes voice output.

Speech uses Piper with a local model when configured; if Piper or its model is
unavailable, ScreenSage falls back to Edge TTS and warns that answer text is
sent to Microsoft's service. Audio playback uses pygame. Speech can be disabled in Settings. For Piper, install a compatible `.onnx`
voice model and enter its file path in Settings. The standalone PyInstaller
build also needs the Piper executable installed separately; Edge TTS can also
be selected explicitly.

## Use

On startup, ScreenSage shows a notification explaining whether the global
shortcut is ready and which local model it selected. It then stays in the
system tray; if the tray icon is hidden, check the Windows notification-area
overflow (the `^` icon). Press **Ctrl+Win+A**, drag over the screen area, and
release the mouse button to open the chat. **Escape** cancels, and **Enter**
confirms the current selection. After capture, type a question in the chat and
press Enter or **Send**; the app does not start by analyzing the image without
your question. Use **Search image** to copy the exact selection and open Google
Lens, then press Ctrl+V in the browser. Alternatively, right-click the
ScreenSage tray icon and choose **Выделить область экрана**. If the shortcut
still does not respond, use this menu item and check `screensage.log` from
**Open logs folder**. The detailed log records keyboard-hook events and errors
but does not record screenshots, questions, model responses, or API keys.

The tray menu opens Settings, switches providers, or exits. Settings include
provider/model, speech engine/voice/speed/language, displayed shortcut, speech
toggle, and start-minimized toggle. Drag and release captures immediately;
Escape cancels and Enter confirms the selection. Every submitted question is
sent with the selected image and prior chat context.

ScreenSage uses the supplied gradient eye icon in the tray, window, and
Windows executable/taskbar. Configuration is stored at
`%APPDATA%\\ScreenSage\\config.toml` on Windows and
`~/.config/screensage/config.toml` on Linux. Rotating logs are kept under the
platform's user state directory: `%LOCALAPPDATA%\\ScreenSage\\logs` on Windows
and `~/.local/state/screensage/logs` on Linux. Unsupported desktop facilities
are reported in the UI/log rather than preventing import of the rest of the app.

## Limitations and roadmap

This MVP supports screen capture and global shortcuts on Windows and X11 only.
Wayland portals, voice input, OCR-specific workflows, and plugin support are
not implemented. Provider output quality and supported image formats depend on
the selected vision model. Global shortcut availability may be affected by
other applications or desktop permissions. Online providers receive captured
screen content; Piper is local, while edge-tts is online.

## Contributing and license

See [CONTRIBUTING.md](CONTRIBUTING.md). ScreenSage is MIT-licensed; see
[LICENSE](LICENSE).
