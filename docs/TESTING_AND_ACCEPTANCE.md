# Testing and acceptance

## Phase 02 foundation admission

Baseline 0c0213d: 76 tests passed, lint and safe Windows UI smoke passed. GitHub Actions [45795129836](https://github.com/creolive-digital/CLYDEX/actions/runs/45795129836) passed Python 3.11 checks, both EXE builds and Inno Setup compilation/artifact upload (no release). CI evidence resolves the earlier unknown compiler/build gate; clean interactive installation is still unverified.

H-01/H-02: fixed early instance-lock release. Non-daemon shutdown finalization now waits for the actual queue, browser and model-load completion; failures retain ownership. Windows child processes start suspended, enter an owned kill-on-close job, then resume; cancellation/deadline cleanup waits for the job to empty. stdin and combined output are bounded; generated Codex answer files are watched. Fixed Windows helpers use the same bounded runner. Concurrent speech model loads are rejected rather than orphaned.

Hardening evidence: **80 tests passed** (4.975 s), lint and real Tk/WebView2 smoke passed. New tests exercise unfinished native work/replacement-instance rejection, stdout flooding, child timeout and answer-file overflow. Existing migration rollback/reopen/newer-version guard and exact-approval tests remain green. Engineering blockers H-01–03 are resolved; proceed with authorized Phase 02. Live audio/account behavior, clean-install UX, signed release, long-run native cancellation and agreed hardware budgets remain external acceptance gates, not claims of successful live validation.

## Baseline

Windows, Python 3.13.14, baseline e65fe46: `python -m unittest discover -v`, **4 passed** (0.003 s). No existing automated failures. `py` default launcher is broken (OI-08); not a new source regression.

## Phase 01 acceptance plan

| Gate | Acceptance evidence needed |
|---|---|
| T1 Contracts/config | Invalid inputs rejected; deterministic immutable action digests; runtime paths outside source; old registry preference preserved. |
| T2 Authorization | Deny unknown/unscoped tools; reject replay, changed args/target/identity, expiry; decline/cancel/stop has no effect; concurrent consume succeeds at most once. |
| T3 Data/logging | SQLite migrations transactional/reopen/schema guard; safe settings/audit only; secrets never written into config/logs/DB; Credential Manager round-trip with mock plus Windows validation if available. |
| T4 Execution | Bounded serial queue and events, timeout/cancel, shutdown; exceptions mapped; no unsafe retry; provider privacy enforced. |
| T5 Regression | Original four tests; local app routing, planner tools, approval bridge and widget time/weather with mocks; no actual mailbox mutation or shell tasks. |
| T6 Packaging | Editable package import, legacy root import, PyInstaller analysis/build if available, JS syntax, lint and full suite; CI configuration inspected. |
| T7 Windows manual | Widget, clock/time tools, weather, WebView startup/audio/Codex, window/control, Chrome/Edge, Outlook draft, approval expiry and emergency stop. Report individually verified vs unverified. |
| T8 Performance/security | Queue limits and prompt/data boundary tests; no added public listener. No fabricated latency/RAM/GPU targets; reference hardware gate remains open. |

Unit/security checks do not prove live hardware/integration or production acceptance. Do not send messages, run destructive commands, fetch private mailbox content or call paid providers to test without explicit scope. Foundation checkpoint report must list actual results and remaining manual checks.

## Executed Phase 01 evidence — 2026-11-26

Environment: Windows 10 kernel 10.0.19045, Python 3.13.14, Intel Core i7-7500U, approximately 19.9 GiB installed RAM reported, Intel HD Graphics 620 and NVIDIA GeForce 930MX. This is the observed workstation, not an owner-approved performance target. Tools installed for verification: Ruff 0.17.6, setuptools 84.2.1, wheel 0.48.0, PyInstaller 6.22.3 and hooks-contrib 2026.10. CI remains Python 3.11 and has not been run remotely for this change.

| Check | Actual result |
|---|---|
| `python -m unittest discover -q` | **75 passed**, 0 failures/errors/skips; final recorded run 2.381 s. Includes original four tests. No coverage percentage claimed. |
| `python -m ruff check src tests` | Passed. Largely unchanged `legacy_engine.py` excluded from style lint; not a whole-repository lint claim. |
| `python -m compileall -q src tests scripts clydex_voice_agent.pyw clydex_widget.pyw` | Passed. |
| `node --check studio_ui/studio.js` | Passed. |
| `python scripts/verify_windows_smoke.py --webview` | Passed: real Tk startup, clock, compact/full, timer start/pause/resume/expiry, alarm arm/cancel, stopwatch/lap/reset; hidden WebView2 startup, local assets, actual bridge export, Stop control and exact-action details. Weather mocked, no mic or cloud request. |
| `python scripts/verify_windows_smoke.py --credentials` | Passed: native Credential Manager synthetic write/read/delete; absence checked after deletion. Also reruns widget smoke. No real credentials inspected. |
| Editable package install | Passed with regular build isolation. Initial no-isolation attempt failed because setuptools was absent; resolved tooling gap. |
| Wheel/resource/isolated import | Passed: built wheel contains migration SQL, both PS1 helpers and Studio; `python -I` imported extracted wheel from a temporary directory outside the checkout. |
| PyInstaller widget and voice-agent specs | Both built successfully. Agent rebuilt after final runtime fixes. SQL and PS1 files verified under frozen `_internal/clydex/`; no relevant missing-clydex/msal/playwright/win32cred/sqlite warnings found. Builds stored outside source under `%LOCALAPPDATA%\CLYDEX\tmp\phase01-verification\`. |
| Original documents | SHA256 unchanged against intake values. |

One native credential integration error was found and fixed (Unicode argument required by CredWrite). A test cleanup connection leak and a mock return-type mismatch were corrected during development; final suite is green. These were development issues, distinct from the green four-test baseline.

## Remaining acceptance gates

- **Unverified live integrations:** actual microphone/speaker/SAPI sound quality, local Whisper inference/download/English-accent accuracy, Codex service/login and offline behavior, real Chrome/Edge interaction/tab reading, real window focus/accessibility operations and Outlook/Graph inbox/draft behavior. Existing implementations remain, but mocks and imports are not live acceptance.
- **Unverified human UX:** accessibility/keyboard/DPI, approval review usability for large payloads, cancellation responsiveness during actual STT/COM/browser calls, long idle/gaming/lock privacy. UI smoke does not establish these.
- **Unverified release:** compiled EXE interactive flows, Inno Setup compilation (tool absent), fresh install/uninstall on clean Windows, signing, updates/recovery and CI 3.11 execution. Successful EXE builds do not establish installation correctness.
- **Performance:** deterministic queue/event bounds tested; local script/build/suite timings observed. No CPU/GPU/RAM/voice-latency regression budget established or claimed. Numeric thresholds require reference-hardware approval and profiling.
- **Security boundary:** trusted in-process adapters + user-reviewed scripts, not hostile plugin isolation or OS sandboxing. Existing WebView asset serving remains loopback; no new public control API. Future clients need authenticated transport and scoped ownership tests before activation.

Phase 01 engineering implementation is ready for review. Overall product and live release acceptance are pending; do not advance to Phase 02 automatically.

## V1 archive relocation verification

- Before moving files: active V2 suite **75 passed**. After relocation and an added regression for the widget Agent button: **76 passed** (2.505 s), proving the button targets the active root V2 launcher rather than V1.
- Independently from `v1-old/`: original **4 tests passed**. Original Tk widget/assets and Studio READY startup smoke passed in a separate process, with weather/audio/cloud access disabled.
- Active V2 real Tk/WebView2 smoke passed after module/resource relocation. Ruff and Python compilation passed. An unused inherited theme import was removed to satisfy lint.
- Both active PyInstaller builds passed using the updated asset/helper paths. Verification artifacts are under `%LOCALAPPDATA%\CLYDEX\tmp\v1-archive-verification\`.
- All **43 original archived files** match `git archive e65fe46` byte-for-byte. Relocated active PNGs match their original bytes. Official product document hashes are unchanged. Active V2 code and build scripts contain no dependencies on `v1-old/`.
- Fresh installation and live audio/provider/browser/mail acceptance remain unverified, as at the Phase 01 checkpoint. No new product phase or remote push was performed.

## Root cleanup verification

- Active V2: **76 tests passed** (2.390 s); standalone V1: **4 passed** (0.002 s). No permission, voice, tool, storage or provider behavior was rewritten.
- Lint without repository cache, Python compilation, JS syntax and real Tk/WebView2 smoke all passed after the launcher/frontend moves.
- Both PyInstaller builds passed from their new `installer/pyinstaller/` locations. Build outputs stayed outside source under `%LOCALAPPDATA%/CLYDEX/tmp/organized-layout-verification/`. Inno Setup compilation/fresh installation remains unverified locally because that compiler is unavailable; its relative paths and CI commands were updated.
- Root file allowlist passed: exactly `.env.example`, `.gitattributes`, `.gitignore`, `AGENTS.md`, `README.md` and `pyproject.toml`. Launchers, source facades, build/setup definitions, requirements and generated remnants are absent from root.
- All 43 original V1 archive files and both original product document hashes remain unchanged. Relocated V2 resources resolve to frontend/legacy; the widget Agent-button regression targets scripts/windows/clydex_voice_agent.pyw.
