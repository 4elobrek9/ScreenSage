# Providers and privacy

## Ollama

Install Ollama and start its local service. ScreenSage prefers
`qwen3.5:2b`; install it with `ollama pull qwen3.5:2b` if it is not already
present. Alternatively, enter a model tag in Settings and click **Download
model** to install it from the running Ollama service. The Ollama library lists
this model at about 3.1 GB on disk; active
VRAM use varies with quantization, image size, and context length. ScreenSage
checks the model names reported by `http://localhost:11434/api/tags` and selects
this exact model when available. Otherwise it picks an installed supported
vision model. Supported families include Qwen3.5, Qwen2.5-VL, LLaVA, Moondream,
BakLLaVA, MiniCPM-V, Qwen2-VL/Qwen3-VL, Llama 3.2 Vision, and Gemma 3. It will
not automatically upload screenshots to an online provider if local detection
fails. Configure an alternate Ollama server URL in `config.toml`.

## Gemini

Create a Google AI Studio API key, select Gemini in Settings, and enter the key
there. It is stored in the operating-system keyring. Default model:
`gemini-2.0-flash`.

## OpenRouter

Create an OpenRouter key, select OpenRouter, and enter the key in Settings.
Default model is `qwen/qwen2.5-vl-3b-instruct:free`; model availability and
vision support can change, and a different vision model can be specified in
Settings. OpenRouter model requests include the screenshot.

Gemini and OpenRouter receive captured screen content over the network. Do not
select private material unless you are comfortable with the selected service's
data handling. API keys are never written to TOML or application logs.
