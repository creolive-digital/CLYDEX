# Testing and acceptance

## Phase 04 local owner review verification (2026-11-27)

Reviewed `5258c8f` admission: 185 tests in 16.772 s; successful exact-checkpoint CI [45954460043](https://github.com/creolive-digital/CLYDEX/actions/runs/45954460043). New work remains local, so no new remote CI result is claimed. Detailed results, actual screenshots and limits are in PHASE_04_COMPLETION_REPORT and `docs/evidence/phase04/`.

| Check | Actual evidence |
|---|---|
| V2 regressions/security/unit | **201 passed, 26.385 s**; includes 16 HUD cases and original four voice regressions. Ruff/compileall/legacy JS checks passed. |
| Fresh archive Python process | **4 passed, 0.004 s**; no archive source changes. |
| Frontend mocked/component/lifecycle | **16 passed, 16.84 s**, Vitest/jsdom; TS compile and Vite production build passed (2.46 s final build). Chunk-size advisory remains for lazy Three.js. |
| Native Windows HUD | Actual production bundle/bridge, loaded providers/voice settings, encrypted synthetic memory add/delete/UI refresh, six modes, running shared timer, two-monitor moves, native approval/Cancel focus/tray restoration, synthetic lock, context-loss fallback and joined native resources passed. Widget Stop is visibly fixed while scrolling. No mic/speaker/network/provider calls. |
| Rendering/resource sample | 27 frames/2 s idle (15 FPS cap); 0/1 s minimized and reduced motion after final static redraw; Python working set 105,263,104 bytes before widget startup. This excludes WebView/GPU. System CPU90.4%/RAM65% are machine-wide, not attributable app utilization. Raw values retained. |
| Retained native fallback | Tk clock/timer/alarm/stopwatch plus legacy WebView2 providers/history/personality/voice reviews/privacy smoke passed on serial rerun; weather mocked. |
| `.pyw` main path | Isolated Studio factory, actual Windows launcher path and silent/reduced flags, three bridge methods/Stop/muted defaults and joined shutdown passed. |
| Packaging | Clean widget/agent PyInstaller builds and headless wheel with versioned HUD contract verified; all 14 final packaged frontend files match the production bundle and embedded native dispatch/restore/Tk modules were checked. Actual frozen agent native window/quiet startup/clean exit passed in a disposable profile; no frozen DOM/audio/provider certification. Inno is absent locally; updated CI/install definition is not a successful new installer execution. |

Fixed native findings include the registry JavaScript MIME mapping, startup timer reset, native initial focus and a cross-thread TopMost hang (ADR-047). One concurrent full-suite run hit temporary-directory sharing after existing process assertions; isolated six hardening tests and later complete suites passed without test weakening. One concurrent legacy smoke assertion failed; serial native fallback passed. These failures are recorded separately from final passing results.

External acceptance remains: production rig/rights, articulated facial/full-body/phoneme features, physical lock/disconnect, mixed DPI/work-area/long-run/accessibility, audible cues, actual language/model/wake/voice/provider performance, fresh install/Inno and current remote CI when explicitly authorized. Browser/jsdom and synthetic lock tests do not establish native/audio production correctness. Do not activate later phases, paid services or large optional assets to close these gates.

## Phase 03 final engineering verification (2026-11-27)

Windows 10 / Python 3.13.14, `v2` at committed `aa084d4` plus preserved Phase 03 working changes. Reviewed Phase 02 checkpoint remains `6b8c452`; GitHub Actions [45807025777](https://github.com/creolive-digital/CLYDEX/actions/runs/45807025777) is confirmed successful at that SHA, including Python 3.11 checks, both EXEs, Inno compilation and artifact upload (release skipped). No Phase 03 changes were pushed, so no current remote CI result is claimed.

| Check | Actual result / limits |
|---|---|
| Repeated foundation admission | Isolated committed HEAD: **135 passed**, 9.805 s. Current intake: 178 tests, one intermittent injected-model-load wait failure plus consequent temporary-directory cleanup error. Corrected lazy dependency injection/guaranteed cleanup; not a failure of the isolated committed foundation. |
| Final V2 suite | `python -m unittest discover -q`: **185 passed**, no failures/errors/skips, 16.088 s. Fifty new service/personality/activation integration cases plus existing foundation/security/data/provider and four original voice cases. |
| Voice audio/lifecycle | Synthetic PCM, callback copy/stream closure, cancellation before native open, finite/confidence/language rejection, VAD/silence/max bounds, follow-ups/sleep, real sample-based output spectrum, PCM byte preservation and cancellation between recognition/playback segments. No uncertain transcript dispatch. |
| Consent/security/integration | No implicit model/tokenizer download, denied preparation/config makes no network/native call, artifact/hash mutation rejection, background wake pauses for Core, Stop/mute revokes actions, headless lock watcher and approval-time rejection, hidden indicator policy, instance/model/native ownership, recovery from Stop/sleep/error, personality isolation/private addressing and full screen vs spoken text. |
| Separate archive | Fresh process from `v1-old/`: **4 passed**, 0.004 s. Archive code untouched. |
| Lint/syntax | Ruff `--no-cache src tests`, compileall for src/tests/scripts and node checks for studio/intelligence/voice JS passed. Inherited legacy-engine style exclusion remains; syntax and regression tests include it. |
| Safe native UI | Updated `verify_windows_smoke.py --webview` passed: real Tk controls and hidden WebView2, seven providers, encrypted synthetic session, nine personality modes, exact reviewed voice settings, muted/disabled defaults and simulated lock privacy shield. Audio/network/weather/private integrations disabled. |
| Actual `.pyw` entry | Executed voice-agent launcher as `__main__` in an isolated temporary profile with hidden real WebView2; loaded voice UI, native event bindings and joined shutdown passed. Audio/cloud/speech disabled. This is startup/ownership evidence, not acoustic acceptance. |
| Native local speech/activation | `verify_voice_native.py` passed: device/voice enumeration, fixed SAPI phrase to RAM, temporary `CTRL+ALT+F24` registration, native tray status refreshing without frontend polling, and joined cleanup. No key press/menu action or microphone/speaker stream. |
| Native sample measurements | Most recent fixed SAPI sample: 0.2272 s wall, 0.1719 s process CPU, 227,278 PCM bytes / 5.154 s generated mono int16 audio at 22,050 Hz. Not microphone-to-answer latency or voice quality; CPU load/RAM/GPU/long-run/STT/wake performance not measured. |
| Installed synthesis metadata | Microsoft David Desktop: male/en; Microsoft Zira Desktop: female/en. 15 input / 18 output enumeration entries include host duplicates and are not physical-device counts. No installed Sinhala/Tamil voice and no neural voice/model audition. |
| Visual check | Isolated headless Edge, network blocked, real local frontend + synthetic profile/bridge: voice panel opens, nine profiles and no JS page errors; screenshot reviewed at `%LOCALAPPDATA%/CLYDEX/tmp/phase03-verification/voice-settings.png`. Human accessibility/DPI acceptance still open. |
| Packaging | Final wheel and isolated headless imports pass. Both PyInstaller specs build. Incremental agent rebuild retained stale PYZ bytecode; a clean rebuild in a fresh directory passed, and the embedded final confidence code plus voice/personality/native/UI/migration resources were verified. No active clydex modules missing. Optional openWakeWord is absent in the standard build, correctly gated. Inno compiler remains absent locally; current installer/fresh installation unverified. |
| Integrity | 48 protected archive/assets/specification paths match reviewed `6b8c452` bytes; main remains `e65fe46`; active branch `v2`; exactly six root files. All intake changes preserved; generated wheel/build evidence outside source. |

Final packaging hashes/logs and complete file manifest are in PHASE_03_COMPLETION_REPORT and `%LOCALAPPDATA%/CLYDEX/tmp/phase03-verification/`. Later sections are historical checkpoint evidence and do not supersede this current status.

External gates: real microphone/speaker flow, local Whisper/model preparation/inference, English/Sinhala/Tamil/Singlish accuracy, acoustic echo/false wake and voice-quality tests; actual Hey CLYDEX model/license/training validation; original cinematic voice selection and redistribution terms; real hotkey/menu use, human secure-lock/disconnect/minimize/privacy and accessibility; reference CPU/RAM/GPU/latency/long-idle benchmarks; optional frozen wake runtime/model/Piper bundle; current Inno/fresh install/uninstall/frozen interaction; live provider accounts/billing/retention and private-data authorization. No paid call, real key, private user content or ambient recording was used to fill these gates. Stop at Phase 03; production acceptance and Phase 04 authorization remain pending.

## Phase 02 final verification (2026-11-26)

Baseline: clean reviewed V2 `0c0213d`, **76 passing tests**. Engineering admission after hardening `3d38311`: **80 passing**. Additional native job-descendant/assignment-failure tests and Phase 02 contracts bring the final suite to **132 passed**, no failures/errors/skips (recorded run 8.023 s, Windows/Python 3.13.14). No coverage percentage or successful live-provider inference is claimed.

| Check | Actual evidence |
|---|---|
| Full unit/regression suite | `python -m unittest discover -q`: 132 passed. Original voice/tool/security/queue/database cases retained. |
| Provider contracts | Six HTTP request/response/header/schema and SSE/NDJSON adapters; malformed/incomplete/refused responses, missing/bad credentials, bounded bodies, errors and safe metadata. Codex existing mock contract/process tests retained. |
| Policy and routing | Manual/all four profiles, capability/health/context/price filtering, offline/privacy across every provider, no unauthorized cloud fallback, fresh review on explicit retry/fallback, no tool side effect replay, local-only memory excluded and derived-history leakage prevented. |
| Real synthetic HTTP boundary | Local ephemeral `127.0.0.1` server: actual Ollama wire format, redirect refusal, 401/403/404/429/500 normalization, stream/size limits, stalled socket deadline/cancel and cancellation during connection. No external AI service contacted. |
| Conversations/memory | Temporary no-SQL default, consented persistence/resume/metadata/search/export, rename/archive/delete/retention, parameterized SQL, cross-owner rejection, memory provenance/revisions/categories/consent/suggestions/retrieval/disabling and known-secret filters. |
| Migration/rollback | Schema-1 fixture with settings and audit rows upgrades to 3; failed third migration rolls second back and retains schema 1/data; idempotent reopen and newer-schema refusal. No real owner profile migrated for testing. |
| Native encryption/credential | Actual DPAPI round-trip of synthetic data, wrong-owner entropy rejection, encrypted SQLite bytes; native Credential Manager dummy write/read/delete and absence check. No real credential inspected/used. |
| Native process/shutdown | Noncooperative task retains instance lock, timeout/flood/generated-file caps, descendants terminated before runner returns and failed Windows job assignment cleans suspended child. |
| Functional bridge | Actual exact reviews for denied/approved provider settings, credential exclusion, queued history creation/resume/export, manual memory policy/delete and routing privacy; Core queue remains single authority. |
| Lint/syntax | Ruff `--no-cache src tests`, Python compileall, `node --check frontend/legacy/{studio,intelligence}.js` passed. Legacy engine retains existing style-lint exclusion; syntax/regressions run. |
| Safe native UI | `python scripts/verify_windows_smoke.py --webview --credentials` passed: Tk clock/timer/alarm/stopwatch controls; WebView2/Stop/review, seven provider controls, temporary defaults and reviewed DPAPI session creation. Network/audio/weather/private services disabled or mocked. |
| Wheel | Build passed without new dependencies; schema 3/modules present, isolated `python -I` headless imports passed. Wheel SHA256 `5fb102b33ddf717311a723517895751b325365deefa31acac237aa8a32b4e009`. |
| Frozen packaging | Both final PyInstaller EXEs built successfully from current source. Archive/module checks confirm coordinator, registry/codecs, conversations/memory, encryption and controls; DPAPI extension and all three migrations/frontend JS present. Artifacts/logs under `%LOCALAPPDATA%/CLYDEX/tmp/phase02-verification/`. |
| CI | Reviewed [baseline run 45795129836](https://github.com/creolive-digital/CLYDEX/actions/runs/45795129836) passed Python 3.11, EXEs and Inno/artifact upload. Current workflow adds Python compilation and JS syntax checks. Current changes not pushed, so no new remote CI result. |
| Integrity/organization | Original specification hashes unchanged; main ref unchanged; 43 original archived files match reviewed intake byte-for-byte; assets untouched; exactly six root files. Generated wheel build directory preserved outside source. Preexisting archive CRLF provenance discrepancy recorded as OI-24. |

Development defects corrected: annotation shadowing by repository `list`, fixture SQLite connection cleanup, HTTP/1.0 socket ownership preventing prompt cancellation, arbitrary usage keys, local-only context leaking through history, native job assignment failure cleanup and current Claude version/auth/workspace shape. These were introduced/discovered during development, distinct from the passing 76-test baseline. Final tests pass.

Remaining gates: actual Codex login/model and all six HTTP providers, real local Ollama isolation/inference, paid/private transfer approvals, human UI/accessibility/DPI, audio/STT/TTS, Windows apps/browser/Outlook live behavior, current Inno compilation/fresh install/uninstall/frozen interaction, reference-hardware performance/long-run profiling, OS DNS interruption, provider billing/retention agreements, audit retention and cross-account recovery. No real credentials, private email, destructive operation or production resource was used to fill these gaps. No Phase 03 readiness or release certification is inferred from synthetic tests.

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
