# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

Run from the repository root in CMD or PowerShell:

```
py -m pip install -r requirements.txt   # install dependencies
py clydex_widget.pyw                    # run the clock/weather widget (console output visible)
py clydex_voice_agent.pyw               # run the voice agent with console output for debugging
START_CLYDEX.bat                        # production launcher (uses pythonw, no console window)
```

There is no build step and no test suite. Manual end-to-end testing on Windows is the only verification path. Before running the voice agent, confirm `codex --version` and `codex login status` succeed in a terminal.

## Architecture

**Two independent entry points, one shared engine:**

- `clydex_widget.pyw` — Tkinter flip-clock and weather widget. Uses only the standard library plus `clydex_theme.py`. Runs fully standalone; launches `clydex_voice_agent.pyw` as a subprocess when the user clicks Agent.

- `clydex_voice_agent.pyw` — WebView2-hosted voice assistant. `pywebview` loads `studio_ui/index.html` with Edge Chromium as the renderer. The `Studio` class is the JS API bridge: JavaScript calls `window.pywebview.api.<method>()` to trigger recording, text submission, settings changes, etc. `Studio` owns a `VoiceEngine` and delegates all heavy work to it on daemon threads.

**Core modules:**

- `clydex_engine.py` (`VoiceEngine`) — All blocking I/O: microphone recording via `sounddevice`, offline transcription via `faster-whisper` (Whisper `base`, CPU int8), Codex CLI subprocess calls, and Windows SAPI TTS synthesized to a temp WAV then played back through `sounddevice`. Worker threads push typed `(kind, value)` tuples onto `VoiceEngine.events` (a `queue.Queue`); the UI polls this queue with `Studio.snapshot()` from JavaScript's render loop.

- `clydex_spectrum.py` (`SpectrumStream`) — Thread-safe rolling PCM ring buffer. The audio callback (or TTS playback loop) calls `push()` from a worker thread; the display thread calls `read_display()` to compute the FFT and 36 log-frequency bands on demand. No FFT work happens on the audio thread.

- `clydex_hologram.py` — Tkinter Canvas animations: `Hologram` (a twisted-strip 3-D ribbon driven by spectrum bands) and `SpectrumMeter` (bar graph with floating peak markers). Both call `draw()` on a timer.

- `clydex_theme.py` (`StudioSkin`) — Generates nine-slice `PhotoImage` capsule tiles for ttk buttons and frames, giving them smooth rounded corners without external image files.

**Codex integration (`clydex_engine.py:chat_reply`):** Codex is invoked via `subprocess.run` with `codex exec --sandbox read-only --skip-git-repo-check`. A JSON schema (`response.schema.json`) constrains the reply to `{action, app, message}`. The model's last message is captured to a file via `--output-last-message`. When `action == "open_app"`, `launch_installed_app` resolves the name against `Get-StartApps` via PowerShell and calls `os.startfile`.

**Weather:** `ClydexWidget.fetch_weather` hits open-meteo.com geocoding then forecast APIs from a daemon thread; results are queued and consumed by a 250 ms `after` poll (`check_results`).

## Key Constraints

- Windows 10/11 only: `os.startfile`, `System.Speech`, PowerShell `Get-StartApps`, `CREATE_NO_WINDOW`, and `edgechromium` WebView2 are all Windows-specific.
- `clydex_widget.pyw` must remain importable with the standard library only (no pip dependencies). `clydex_theme` is the sole intra-package import.
- The `.pyw` extension suppresses the console window in production; always test changes via `py <file>.pyw` to see tracebacks.
- `SpectrumStream` FFT is intentionally deferred to the display thread — do not call `read_display()` from the audio callback.
- TTS text is capped at 1 300 characters in `speak_with_audio_meter` to keep synthesis latency manageable.
