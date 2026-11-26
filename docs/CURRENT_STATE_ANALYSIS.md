# Current state analysis

Audit date: 2026-11-26. Specification: full 26-page Blueprint v1.1 and Codex master instructions v1.1. Implementation baseline: `e65fe46e19e554066a43926f4a0e5335843096c8`. Dedicated branch: `v2`. At intake only the owner-supplied `docs/` directory was untracked; no source changes were present. Original documents must remain byte-for-byte unchanged.

## Baseline evidence

- Windows, Python 3.13.14: `python -m unittest discover -v`: **4 passed**, 0.003 s; no observed baseline automated failure.
- `py` launcher points by default at a missing Python 3.14 executable; use `python` or a verified installed interpreter. Packaging CI selects 3.11. Reference hardware and performance budgets remain unapproved.
- Source inspection establishes implementation presence, not successful live behavior. Audio, Codex service, UI accessibility, weather service, browser, mailbox and installer have not yet been manually accepted for V2.
- Product PDF SHA256: `258831e9659dc66145c80d2759c5bc6857be7798d6400f0b5ae876586ec45d2c`; master instructions: `6bd06df66c55d714b708984bfd72349a8ef2e503deb410a84abb284e7c470680`.
- PDF text extracted using installed pypdf. Font-map warnings affect a few decorative glyphs; all pages were extracted and the logo/avatar embedded reference images were inspected. Standalone approved `assets/branding/clydex_logo_reference.png` and `assets/avatars/clydex_avatar_reference.png` are absent (OI-01); embedded screenshots are not shipping assets.

## Repository inventory and dependencies

| Component | Observed behavior / limitations |
|---|---|
| `clydex_engine.py` | VoiceEngine mixes recording/STT, command parsing, planning, history, Windows tools, approvals and SAPI. Model prompts separate tool results from instructions in wording only. |
| `clydex_voice_agent.pyw` | PyWebView Studio bridge; RLock/busy flag; per-request daemon threads; polls tuple events and real spectrum. Recognition mode in HKCU registry. |
| `clydex_apps.py`, `app_controls.ps1` | Start/window matching, focus/minimize/maximize/restore/close, accessibility inspection, approved button activation and append. Rechecks HWND/PID/title/control identity. |
| `clydex_desktop.py`, `read_browser_tab.ps1` | PowerShell helper (120 s timeout, entire user authority); Playwright own visible browser on one executor; existing tab text through Windows accessibility. Output caps apply after capture. |
| `clydex_outlook.py` | Classic COM and Graph/MSAL; up to 12 inbox messages and native unsent replies. Tokens in process memory; Mail.ReadWrite broader than reading alone. |
| `clydex_widget.pyw` | Tkinter clock/weather/timer/alarm/stopwatch, snooze/laps, compact/full, topmost, assistant launch. Timers monotonic; alarms wall clock; UI-thread weather delivery. Settings/time tools mostly in memory. |
| `studio_ui/` | Bundled static HTML/CSS/JS and licensed fonts/icons; canvas face, FFT/waveform and task review dialog. No React/TS build, reduced-motion or hidden-window animation throttling. User/model messages inserted with textContent. |
| `clydex_spectrum.py` | Locked fixed audio ring, calibrated 36 bands; numpy loaded lazily. |
| `clydex_theme.py`, `clydex_hologram.py` | Tk skins and older hologram rendering helpers. No production approved 3D avatar. |
| Packaging | Two PyInstaller specs, Inno Setup, three Windows batch entry/build scripts, main/tag GitHub Actions build and tag release. Dependencies have broad ranges; no lock, signing or updater. |
| Tests | Four unittest voice routing/confidence tests only; Windows imports prevent portable collection without mocks. |

Runtime dependency inventory: Pillow, numpy, sounddevice/PortAudio, faster-whisper/ctranslate2, av<19, pywebview/WebView2, playwright plus installed Chrome/Edge, pywin32/COM, msal and requests. Standard libraries include Tkinter, sqlite3 (available but unused at baseline), urllib, subprocess and threading. Codex CLI is an external logged-in executable. No backend API server, SQL Server client, cloud account or public listener exists.

## Assessment

- **Maintainability:** large mixed orchestration module and UI-coupled state. Extract behind compatibility adapters rather than rewrite tool implementations.
- **Security:** approvals are ephemeral booleans with no expiry or payload/user/device digest. Browser/mail/window reads and drafts lack centralized scopes. No central audit, credential API or local-only/cloud policy. PowerShell is not an OS sandbox; arbitrary approved scripts inherit all user rights. This must remain explicit.
- **AI orchestration:** Codex only; structured response schema passed to CLI but returned JSON not locally validated; no provider interface, cancellation or retry policy. Prompt text alone cannot enforce authorization.
- **Voice:** bounded 30 s capture, VAD/confidence retry, lazy model load, local SAPI PCM. No wake word, continuous/hotkey/tray activation or guaranteed male/language voice. Stop-recording currently continues to transcription; distinct task cancellation needed.
- **Configuration:** scattered constants, registry preference, Outlook client ID environment variable; no central validation or per-user runtime directory.
- **Errors:** raw exceptions reach UI, no structured safe error categories/logging. Tool receipts preserve partial completion on summarization failure.
- **Concurrency:** UI busy flag generally serializes requests, but direct engine access bypasses it. Unbounded event queue; indefinitely blocked approval waits. Browser kept on one thread; spectrum protected. Close does not cancel subprocesses or model load. Shared mutable histories/inbox expect one request at a time.
- **Performance:** CPU STT and first model downloads; WebView render loop always active; captured subprocess output can grow before truncation. No reference-hardware timings/idle or memory profile.
- **Database/cloud:** no DB/schema/migrations, sync or authenticated gateway. Introduce SQLite metadata only now; sensitive memory/vault caching and MSSQL/vector feasibility are later gates.
- **Devices/plugins:** no remote device or SDK surfaces. Define local request identity and authorization contracts now; do not expose Windows control or execute third-party code.
- **Testing:** substantial gaps in action approvals, failure paths, widget time behavior, UI bridge and packaging. Add offline mocks before moving behavior; no live sends, file mutation, login or cloud deployment during audit.

See REQUIREMENTS_TRACEABILITY, OPEN_ISSUES and ARCHITECTURE_DECISIONS for requirement mapping, conflicts and resolutions. Phase 01 implementation and acceptance evidence are tracked separately from this preserved baseline.
