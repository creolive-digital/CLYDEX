# Phase 03 — Voice Intelligence and Adaptive Personality

Date: 2026-11-27. Branch: `v2`. Reviewed Phase 02 checkpoint: `6b8c4524353c3b7f613c068c5757dfe693b494f4`. Actual continuation HEAD: `aa084d453e41152c6c007a90a1b05c892fd72cf4`, with preexisting uncommitted Phase 03 work preserved and completed.

**Phase 03 engineering is delivered in the scope below. Acoustic/hardware, model, language and production acceptance remain pending.** No validated Hey CLYDEX model or owner-approved cinematic neural voice is supplied. The working compatibility option is installed local SAPI. Stop here before Phase 04. No push, merge, release, paid provider activation, real credentials, private-content test, microphone recording or speaker playback was performed.

## Foundation admission and changes preserved

Read AGENTS, both official specifications (all 26 PDF pages and the master instructions), all development-management records, provider setup, Phase 02 completion and project structure. Original specification hashes still match the recorded intake. The continuation working tree already contained voice/personality/Core/desktop/frontend changes; these were backed up under `%LOCALAPPDATA%/CLYDEX/tmp/phase03-verification/` and retained. No reset/checkout overwrote them.

The exact reviewed Phase 02 CI [run 45807025777](https://github.com/creolive-digital/CLYDEX/actions/runs/45807025777) succeeded: Python 3.11 tests/lint/compilation, both EXEs, Inno compilation and installer artifact upload; release skipped. This is historical CI evidence, not CI for the unpushed Phase 03 tree.

An isolated archive of committed HEAD passed **135 tests in 9.805 s**. The current-tree intake ran **178 tests**, with one intermittent synthetic model-loader wait failure and a subsequent temporary-directory cleanup error. Injected loaders still imported heavy Whisper dependencies before entering the test factory, and failed assertions did not always release/join the fixture. Lazy injected imports and unconditional cleanup corrected this; ownership/security behavior is covered in the passing final suite. The committed provider socket-cancellation hardening after the reviewed checkpoint is retained; native DNS remains a declared limitation.

Reviewed OI-07/09/12/14/18–30: permissions, model/native shutdown ownership, provider privacy, implicit Whisper downloads, local voice/wake availability, multilingual synthesis and microphone/lock/background risk. Engineering blockers were resolved before final verification. External owner/device/account gates are listed below, not counted as successful live validation.

## Completed task IDs

| Task | Engineering outcome |
|---|---|
| P3-01 | Repository/specification/CI audit and repeated foundation admission; preserve actual working changes and reviewed main/archive bytes. |
| P3-02 | Typed headless audio/device/STT/VAD/event services, bounded transient capture, silence/confidence/language rejection and reviewed local model preparation/cache closure. |
| P3-03 | Configurable local synthesis/output boundaries, async literal SAPI/purge, actual PCM metering and optional fingerprinted owner-supplied Piper CLI. Cinematic asset selection remains open. |
| P3-04 | Controlled conversation states, half duplex/cooldown/follow-ups/inactivity, distinct finish/cancel, foreground/native ownership, Stop/mute, headless lock watcher and action-time privacy checks. |
| P3-05 | Manual, continuous, configurable Windows hotkey/tray and gated custom local wake routing. No trained Hey CLYDEX detector or acoustic wake result claimed. |
| P3-06 | Nine presentation profiles, configurable tone/length/languages, concise speech/full screen text, encrypted optional addressing and permission/privacy isolation. |
| P3-07 | Existing Core/coordinator/provider/memory/conversation/executor integration; functional frontend/legacy settings/status/errors/Stop and native window visibility handling. |
| P3-08 | Deterministic/synthetic regressions, safe real Windows UI/launcher/native SAPI/registration checks, syntax/lint, visual check and packaging verification. External audio/model acceptance remains pending. |
| P3-09 | Current setup, technology/license evaluation, language matrix, all development documents, architecture/decisions/traceability and this checkpoint/file manifest. |

## Architecture and actual behavior

CoreApplication owns VoiceRuntime and PersonalityService alongside the existing IntelligenceCoordinator, ProviderRegistry, ConversationService, MemoryService, ToolExecutor and supervised queue. VoiceEngine delegates audio responsibilities and retains its established tool/request adapter. No second AI engine, frontend-dependent voice core or public OS endpoint was introduced.

`voice/contracts.py` defines AudioInput, AudioOutput, SpeechRecognizer, SpeechSynthesizer, ActivityDetector, WakeDetector, ConversationLifecycle and InterruptibleVoice with AudioBuffer, PCMChunk and Transcript. Devices have AudioDevice/DeviceManager contracts. Functional services separate capture, output, Faster Whisper, SAPI/Piper, energy/silence VAD, optional local wake, lifecycle, privacy and real spectrum/events. Dependencies load lazily; text chat does not need a microphone/model. Runtime settings/models stay outside source; no new database migration beyond existing schema 3.

The state machine includes standby, wake detected, listening, transcribing, thinking, waiting for approval, speaking, interrupted, sleeping and error. Recovery permits new settings reviews after Stop/sleep/error; completed settings return to standby. Continuous mode uses the same queue task, a bounded follow-up window and inactivity limit. Silence sleeps instead of issuing another request. Local Stop/sleep phrases do not authorize tools.

Capture has noise-aware energy gating plus Whisper/Silero VAD, configurable silence/sustained speech/duration and overflow rejection. Low/nonfinite segment confidence, excessive no-speech probability and uncertain/missing auto-language confidence are rejected before dispatch. English fast/accurate and explicit/auto language settings are retained; English-only presets select their multilingual equivalent for other languages. Missing model/tokenizer/config/vocabulary files never trigger an implicit download. Preparation is a separate exact reviewed action identifying model, public network source and runtime storage, without auth tokens or private audio upload.

Default operation is **half duplex**, not AEC/full duplex: capture/wake streams close before transcription, thinking, approvals, synthesis and playback. A configurable acoustic-tail delay precedes re-listening. Stop cancels active/pending/follow-up work and revokes approvals; runtime Stop also cancels its owned foreground tokens. Native inference/download/COM/driver cleanup may take time to return; the queue/instance stays owned until completion. Already completed external effects are not undone.

## Activation status

| Method | Implemented / verified | Remaining acceptance |
|---|---|---|
| Manual push-to-talk | Start/finish controls and separate cancel/mute; opt-in/unmute checks and synthetic capture/closure tests. | Real microphone/audio flow untested. |
| Continuous | Configurable follow-up/silence/inactivity lifecycle and safe half-duplex routing. | Real dialog comfort, acoustic tail/echo and long-session behavior untested. |
| Global shortcut | Configurable RegisterHotKey adapter; default CTRL+ALT+SPACE, busy activation interrupts, reserved/occupied keys rejected. Temporary native CTRL+ALT+F24 registration and cleanup verified. | No actual key press/activation or frozen UX acceptance. |
| Tray | Native Open/Talk/interrupt/mute/unmute/Stop/Exit, independent status refresh and joined ownership. Native registration/cleanup verified. | No real menu interaction/long-idle/frozen UX acceptance. Uses neutral OS fallback icon, no invented branding asset. |
| Hey CLYDEX | Optional openWakeWord ONNX adapter; exact local artifacts, phrase/license/hash attestation, bounded transient frames, reviewed arming and same Core routing. Synthetic detector/routing/privacy tests pass. | **No actual validated Hey CLYDEX model supplied or tested.** No generic model substituted, default wake remains off. |

Microphone permission, background/wake/continuous/hotkey/tray start off; microphone starts muted. Wake configuration and arming are distinct. Stop/mute/lock disarms, and unlock/restart never automatically unmutes/rearms. Hidden capture/output additionally requires explicit background policy and a trusted active tray/indicator with reachable Stop/mute. A headless consumer must explicitly provide an equivalent trusted indicator predicate.

## Speech technologies, licenses and selected voice

Retained Faster Whisper (MIT), CPU/int8/two threads/one worker, with complete local-cache enforcement. Windows SAPI remains installed-voice compatibility. SAPI uses literal asynchronous synthesis to memory, purge on cancellation and our separate selected-device PCM output. It prefers matching male voice metadata; it is not certified cinematic quality.

Actual installed metadata: **Microsoft David Desktop — male, English**; Microsoft Zira Desktop — female, English. No personal addressing was invented. No owner voice preference/model was activated. Only fixed synthetic English speech to RAM was verified; the owner must audition and select an original deep/calm/masculine voice.

Optional Piper uses an owner-supplied local executable, ONNX model and config with reviewed rights/provenance/fingerprints; no binary or voice is bundled. The required CLI emits mono int16 PCM; builds with other raw formats are incompatible. Current OHF Piper code is GPLv3, with separate voice/data terms. This adapter buffers bounded phrases and reloads the CLI per phrase; upstream streaming capability is not a claim of CLYDEX streaming synthesis latency. No cloud TTS fallback.

Optional openWakeWord code is Apache-2.0; upstream pretrained models have CC-BY-NC-SA-4.0 terms, and custom training/feature rights need review. Porcupine was evaluated but not added because Console/AccessKey/account/usage terms require owner selection. Coqui/XTTS and Meta MMS Tamil were evaluated without installation: separate weight licenses/language limitations and deployment costs do not establish an approved original cinematic multilingual voice. Candidate CPU/RAM/GPU/disk/streaming/redistribution considerations and current official source links are recorded in [VOICE_CONFIGURATION.md](VOICE_CONFIGURATION.md). No voice model, training dataset, optional runtime, paid dependency or actor imitation was introduced.

## Language support matrix

| Language | Recognition configuration | Text/response behavior | Actual local synthesis / validation |
|---|---|---|---|
| English | Explicit en; fast base / accurate small.en or configurable supported model | Existing provider plus presentation policy | SAPI English metadata and synthetic RAM PCM verified; microphone, speaker/accent/quality unverified. |
| Sinhala | Explicit si or auto with multilingual equivalent | Unicode/provider-dependent response preference | No installed Sinhala voice/model. Visible text-only or explicit English notice; STT/pronunciation unverified. |
| Tamil | Explicit ta or auto with multilingual equivalent | Unicode/provider-dependent response preference | No installed Tamil voice/model. Same honest fallback; STT/pronunciation unverified. |
| Singlish/mixed | Auto/en/si, no dedicated Singlish recognition model | Mixed-language text and configurable Singlish preference | No validated Singlish synthesis. Latin-script auto uses English pronunciation, not claimed Singlish quality. |
| Additional | Actual Whisper-supported language code | Provider-dependent | Matching installed metadata or approved model required; otherwise visible fallback. |

Recognition, response and synthesis settings are independent. Auto TTS script routing is limited; explicit language selection is needed for other Latin languages. An AI model emitting a script does not establish local STT/TTS quality. Unsupported local speech leaves the full answer on screen and emits a visible warning; an optional English notice never pretends to speak/translate the unsupported answer.

## Personality, memory and security verification

Personal, professional, developer, technical support, study, focus, gaming, privacy and custom modes affect tone/length/presentation. Focus/gaming suppress speech unless explicitly allowed. Spoken output removes code/URLs and truncates concisely while preserving the complete screen/history answer. No personality fields grant tool scopes, permit paid/cloud services, change approvals or activate memory. Privacy mode can further restrict outbound cloud access.

Optional addressing is DPAPI-encrypted under the Windows owner in personality settings and inserted as reviewed private context, never trusted instructions or automatic memory. Existing temporary-session defaults, consented saved conversations, sensitive-turn exclusions, local-only history/memory protection and reviewed suggestions remain intact. All requests and effects use the established coordinator/executor policy.

Native lock/secure-desktop/disconnection/probe-failure handling mutes and cancels; an owned watcher works without UI polling. Action/approval-time checks prevent a locked session from approving the next effect. The UI hides private payloads and shows the privacy shield; no automatic unlock reactivation. Wake/recognized voice is not authentication. No raw audio files or private voice diagnostic content are saved. Buffers are bounded/transient, not claimed securely erased or protected against malicious same-user native code.

Transport-independent lifecycle events cover listening, recognition stages, thinking, synthesis/playback, genuine amplitude/spectrum, interruption, approval waiting, warnings/errors and sleep/wake. Playback reports frame counts. Optional SpeechTiming accepts future phoneme/viseme data; **no validated phoneme/viseme synchronization or Phase 04 avatar renderer is implemented**.

## Verification evidence

| Check | Actual result |
|---|---|
| Full V2 suite | **185 passed**, zero failures/errors/skips; final run 16.088 s on Windows/Python 3.13.14. Includes 50 new service/personality/activation integration tests and all four original voice cases. |
| Separate original archive | **4 passed**, 0.004 s in a fresh process from v1-old. No archive edits. |
| Static checks | Ruff no-cache, Python compilation and studio/intelligence/voice JS syntax passed. Existing legacy-engine style exclusion retained; its syntax/regressions are checked. |
| Synthetic coverage | PCM capture/closure/privacy, silence/VAD/confidence, model preparation/cache, detector/artifact routing, lifecycle/follow-ups, STT/playback cancellation, literal SAPI and Piper contracts, real binary subprocess bytes, Core/provider/memory/privacy integration, exact reviews, native ownership and recovery after interruption. |
| Safe real Windows UI | Updated Tk/WebView2 smoke passed, including legacy controls, seven providers, encrypted synthetic session, reviewed voice settings, nine profiles and simulated lock privacy shield. Network/audio/private services disabled. |
| Actual voice .pyw launcher | Hidden real WebView2 under isolated temporary profile, main-entry execution, voice controls/native window bindings and joined close passed. Audio/cloud/speech disabled. |
| Safe native speech/activation | Device/voice enumeration, fixed SAPI-to-RAM synthesis, native shortcut/tray registration, independent tray status callback and joined cleanup passed. No actual activation input or audio device stream. |
| Actual audio tests | **Microphone: not opened. Speakers: not opened. Local Whisper inference: not run. Wake inference: not run. Neural voice audition: not run.** Synthetic/memory evidence does not establish acoustic acceptance. |
| Native sample measurements | Most recent fixed English SAPI sample: **0.2272 s wall, 0.1719 s process CPU; 227,278 PCM bytes / 5.154 s mono int16 at 22,050 Hz**. Measures this synthetic memory-synthesis sample only, not voice-request latency. No CPU-load/RAM/GPU/idle/STT/wake budget measured or claimed. |
| Visual | Isolated headless Edge with network blocked, local frontend/isolated profile bridge: panel and nine options, no JS page errors; screenshot captured/reviewed. Human DPI/accessibility unverified. |
| Wheel/frozen/installer | Both PyInstaller specs pass. Final agent built with `--clean` in a fresh work/dist directory; embedded final confidence bytecode, voice/personality/native/UI/migration resources verified, with no missing active clydex modules. Final wheel contains the updated code and imports in isolation. Optional wake runtime absent/gated. Local Inno compiler absent; current installer/fresh installation remains unverified. |
| Integrity | 48 protected archive/assets/specification paths byte-match reviewed 6b8c452; main still e65fe46; v2 active; root has exactly six permitted files. |

Local artifacts/logs/screenshot: `%LOCALAPPDATA%/CLYDEX/tmp/phase03-verification/`. Nothing was uploaded. Screenshot: `voice-settings.png`. Final agent is under `dist-final-clean/clydex_voice_agent/`; widget under `dist/clydex_widget/`; final wheel under `wheels-final/`. An incremental rebuild retained stale PYZ code despite reanalysis; direct embedded-code inspection caught it. The clean rebuild/fresh directory resolved the finding, and the final bytecode explicitly contains the new rejection branch. Existing CI/build shortcuts already use clean builds.

Final SHA256 values (also in local `packaging-final.json`):

```text
agent EXE: f19041b97671affaa601ff8794230a719b375ca1ea9895036a8bc52f7464ec95
widget EXE: ad09f30646458776ecf54185456667a0500e0f4c588cff925080a727c10f19e4
wheel: 458fa6f3e57ee0cb87de0badd214b6a3f592e91adbdd7eb73083f790f278c9d9
```

No current remote CI, clean-install, live-provider or production-readiness claim.

Publication authorization: after reviewing this local checkpoint, the owner explicitly requested a GitHub push on 2026-11-27. This authorizes publishing the `v2` commits only; it does not authorize merging to main, tagging or releasing. The local verification and live-acceptance limits above remain unchanged. Current GitHub Actions results must be assessed separately after publication.

## Remaining owner decisions and Phase 04 readiness

- Select/license/train/validate the actual Hey CLYDEX model and measure false activations/rejections on target hardware; explicitly authorize any data generation/training/download.
- Select and audition the legally available original cinematic voice and its complete Windows runtime bundle; confirm raw PCM, redistribution terms, installation size and actual Sinhala/Tamil/Singlish quality or accept text/English-notice fallback.
- Authorize real microphone/speaker and local-model acceptance with nonprivate phrases. Test language/accent/noise, acoustic tail, interruptions, continuous/idle behavior, native menu/key use, lock/disconnect/minimize and human accessibility/DPI. No such consent or results are inferred here.
- Approve reference CPU/RAM/GPU/disk/latency targets and benchmark selected models. Validate optional frozen runtime, current installer/clean installation/uninstall and frozen interactive flows before release.
- Existing provider accounts/models/prices/privacy/retention, native DNS/COM limits, audit retention/recovery and missing approved standalone branding assets remain open as described in OPEN_ISSUES.

Phase 04 can consume the actual voice/lifecycle/spectrum and optional timing contracts. Full cinematic React HUD and production humanoid assets/rendering require their own authorization, licensed approved assets and performance/accessibility acceptance. No cloud/plugin/mobile/robot work was added. **Stop at the Phase 03 engineering checkpoint.**

Rollback: preserve runtime settings/data/models in the owner's protected backup, close Core fully and review/shelve the Phase 03 working changes before returning to a prior V2 checkout. Do not discard intake changes, downgrade schema 3 or delete user runtime data. New voice/personality JSON has no destructive migration. Main and the independent archive remain available unchanged.

## Created and modified files

Manifest is relative to reviewed Phase 02 commit `6b8c452`, including the preserved post-checkpoint transport fix and intake Phase 03 work. Generated builds/runtime/model data are excluded.

Created (29):

```text
docs/PHASE_03_COMPLETION_REPORT.md
docs/VOICE_CONFIGURATION.md
frontend/legacy/voice.js
scripts/verify_voice_native.py
src/clydex/core/settings.py
src/clydex/desktop/activations.py
src/clydex/desktop/hotkeys.py
src/clydex/desktop/tray.py
src/clydex/desktop/voice_settings.py
src/clydex/personality/__init__.py
src/clydex/personality/policy.py
src/clydex/personality/profiles.py
src/clydex/personality/service.py
src/clydex/voice/artifacts.py
src/clydex/voice/audio_input.py
src/clydex/voice/audio_output.py
src/clydex/voice/config.py
src/clydex/voice/contracts.py
src/clydex/voice/conversation.py
src/clydex/voice/devices.py
src/clydex/voice/events.py
src/clydex/voice/privacy.py
src/clydex/voice/service.py
src/clydex/voice/speech_to_text.py
src/clydex/voice/text_to_speech.py
src/clydex/voice/vad.py
src/clydex/voice/wake_word.py
tests/test_voice_integration.py
tests/test_voice_services.py
```

Modified (38):

```text
.github/workflows/build.yml
AGENTS.md
README.md
deployment/windows/requirements.txt
docs/ARCHITECTURE_DECISIONS.md
docs/CHANGELOG.md
docs/CURRENT_STATE_ANALYSIS.md
docs/DEVELOPMENT_PROGRESS.md
docs/DEVELOPMENT_ROADMAP.md
docs/OPEN_ISSUES.md
docs/PROVIDER_CONFIGURATION.md
docs/README_SETUP.txt
docs/REQUIREMENTS_TRACEABILITY.md
docs/TESTING_AND_ACCEPTANCE.md
docs/architecture/PROJECT_STRUCTURE.md
frontend/legacy/desktop.css
frontend/legacy/index.html
frontend/legacy/intelligence.js
frontend/legacy/studio.js
installer/pyinstaller/clydex_voice_agent.spec
installer/windows/INSTALLER_NOTES.txt
installer/windows/installer.iss
pyproject.toml
scripts/verify_windows_smoke.py
scripts/windows/clydex_voice_agent.pyw
src/clydex/automation/executor.py
src/clydex/automation/tasks.py
src/clydex/core/application.py
src/clydex/core/events.py
src/clydex/core/legacy_engine.py
src/clydex/core/orchestrator.py
src/clydex/core/processes.py
src/clydex/desktop/intelligence.py
src/clydex/desktop/studio.py
src/clydex/providers/transport.py
src/clydex/security/permissions.py
tests/test_provider_transport.py
tests/test_regression.py
```
