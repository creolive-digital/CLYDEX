# Phase 03 voice and personality

## Phase 06 boundary (2026-11-28)

Phase 06 recognizes explicit create-workflow/create-routine and exact saved-name run requests after existing transcript confidence/privacy handling. Drafting uses the same coordinator, then validates/reviews a disabled save. Running needs an enabled local version and normal tool approvals. Voice/wake is not authentication; no new acoustic/model/language acceptance is claimed.

## Phase 05 privacy boundary (2026-11-28)

Cloud synchronization and the offline knowledge cache exclude ambient/raw microphone recordings and sensitive voice-derived history. No voice engine or cloud STT path is added. An owner can separately select an existing PCM WAV file as a reviewed document upload; it receives metadata/storage and `needs_transcription`, not an invented transcription. Current local voice/wake/language/asset/acoustic limitations remain unchanged; cloud accounts do not authenticate spoken commands or bypass action approval.

The local voice runtime feeds the existing CoreApplication queue, IntelligenceCoordinator, conversations, memory and exact-action executor. Text chat still works without a microphone or speech model. Engineering verification and external acceptance are distinguished in [PHASE_03_COMPLETION_REPORT.md](PHASE_03_COMPLETION_REPORT.md).

## First use

1. Open **Voice & Personality**. Select input/output devices, recognition mode/language, installed SAPI voice, speech speed/volume and personality. **Review voice settings** uses the existing exact-action approval dialog.
2. Microphone permission starts **off**. Review permission, then explicitly **Unmute this session**. Restarting or locking mutes again. Checking a device enumerates metadata; **Test microphone** deliberately opens it for up to five seconds. **Play local test phrase** deliberately opens the selected output.
3. Review model preparation separately. The approval identifies the supported model and `%LOCALAPPDATA%\CLYDEX\models` directory, public Hugging Face download and potentially several GiB of storage/network use. No prompt/audio or authentication token is uploaded. Dependencies do not download a model. Missing model/tokenizer/config/vocabulary files fail closed during inference.
4. Click **Use Live Mic** to start a bounded voice turn. Click it again to finish the recording and transcribe. **Stop / interrupt**, **Stop task** or **Mute mic** cancels the current work, pending approvals and follow-up capture. Finishing a recording and canceling are different controls.

Always review operating actions in the existing approval dialog. A recognized voice or wake word is not authentication. Uncertain speech is rejected before dispatch. Environmental speech can still be misrecognized; sensitive/model-generated actions retain their reviews.

## Activation and conversation

| Method | Behavior / gate |
|---|---|
| Manual | Start/finish the microphone button; requires reviewed opt-in and per-session unmute. |
| Continuous | Enable follow-ups. The same serial task listens again after the answer; a silent follow-up expires to sleep. |
| Global shortcut | Enable a configurable shortcut, default `CTRL+ALT+SPACE`. A busy shortcut interrupts instead of queueing another request. Windows-key combinations, F12, duplicate modifiers and occupied shortcuts are rejected. |
| System tray | Enable native Open, Talk/interrupt, mute, per-session unmute, Stop and Exit controls. Closing the window exits; minimizing can retain an explicitly permitted background session. |
| Hey CLYDEX | Local custom openWakeWord adapter is implemented, **but no validated Hey CLYDEX model is supplied**. Configure reviewed assets, permit background capture, unmute, then review **Arm local wake listening**. No generic model is relabeled. |

Wake, background listening, continuous, hotkey and tray are off by default. Saving wake configuration does not arm it, and arming does not survive restart/Stop/mute/lock. Hidden-window capture/output requires background permission and a functioning native tray indicator with reachable Stop/mute. A headless client must supply its own trusted indicator predicate before hidden background capture is permitted. Tray status refreshes independently of frontend polling.

The state machine exposes standby, wake detected, listening, transcribing, thinking, waiting for approval, speaking, interrupted, sleeping and error. Initial operation is **half duplex**: microphone/wake capture closes before transcription, thinking, approvals, synthesis or playback. A configurable 600 ms default acoustic-tail delay precedes follow-up/wake capture. No acoustic echo cancellation, full duplex or spoken barge-in during playback is claimed; use the UI, shortcut or tray to interrupt.

Default capture: 30 s maximum (configurable 1–60), 5 s initial silence, 850 ms trailing silence, 240 ms sustained energy, six-second follow-up window, 60 s inactivity limit. An adaptive energy gate precedes local Whisper/Silero VAD and confidence rejection. This is not certified noise suppression. Background input uses six 80 ms frames maximum; foreground callback queue is 25 blocks of 20 ms, with bounded pre-roll and a 16 MiB retained-sample ceiling. Overflow discards the recording. No raw audio files are created; consumed recognition arrays and transient references are discarded. This is not a secure-memory-erasure guarantee.

## Speech and language capabilities

Recognition, response and synthesis languages are independent. `en`, `si`, `ta`, `auto` and additional engine-supported codes can be selected; mixed text can be sent through existing provider policy. Response language is a presentation preference, never proof of speech support.

| Language | Local recognition implementation | Text response | Actual local synthesis / acceptance |
|---|---|---|---|
| English | Fast `base`, accurate `small.en`; configurable supported Whisper models | Provider-dependent | Installed SAPI English voices; native synthetic PCM verified. Human quality, speaker output and accent accuracy unverified. |
| Sinhala | Multilingual Whisper, explicit `si` or auto | Provider-dependent Unicode text | No Sinhala SAPI voice on this workstation, no selected neural model; visible text-only fallback. Recognition/pronunciation unverified. |
| Tamil | Multilingual Whisper, explicit `ta` or auto | Provider-dependent Unicode text | No Tamil SAPI voice on this workstation, no selected neural model; visible text-only fallback. Recognition/pronunciation unverified. |
| Singlish / mixed | Choose auto/English/Sinhala; no distinct Singlish recognition model | Configurable `singlish` response preference | No validated Singlish voice. Latin-script auto synthesis uses English pronunciation; not a Singlish quality claim. |
| Additional | Explicit engine-supported language; `.en` presets switch to multilingual equivalents for non-English/auto input | Provider-dependent | Requires matching installed SAPI metadata or a licensed selected neural model. Otherwise text-only. |

Auto synthesis detects Sinhala/Tamil scripts, mixed scripts and Latin text; it is not a general language detector. Select the actual synthesis language for other Latin languages. Missing/unsupported voices produce a visible warning with the full answer retained on screen. The optional English fallback speaks only an English notice that the answer is on screen; it does not pretend to pronounce or translate the unsupported answer. There is no cloud TTS fallback.

SAPI prefers male metadata among matching installed voices; this does not establish a deep cinematic voice. Microsoft David Desktop and Zira Desktop report English here; only synthetic in-memory SAPI output was verified. The owner still chooses and auditions the original cinematic voice.

## Technology evaluation and licensing

Official documentation was checked on 2026-11-27. No models, training data, voice assets or optional runtimes were downloaded during verification. Statements below describe upstream capabilities, not measured CLYDEX quality/resource usage.

| Candidate | Evaluation and decision |
|---|---|
| Faster Whisper | Retained local CPU/int8 adapter, two threads/one worker, owned model loading and segment-boundary cancellation. CPU execution avoids requiring CUDA; larger models need more disk/RAM and profiling. Code is MIT. [Official repository](https://github.com/SYSTRAN/faster-whisper), [license](https://github.com/SYSTRAN/faster-whisper/blob/master/LICENSE), [Whisper language registry](https://github.com/openai/whisper/blob/main/whisper/tokenizer.py). |
| openWakeWord | Optional adapter selected: local Windows ONNX, 16 kHz PCM, custom phrase training. Code Apache-2.0; supplied upstream pretrained models have CC-BY-NC-SA-4.0 restrictions. Custom training/data/feature-model rights need separate review. CPU/ONNX dependencies, actual memory/latency and custom phrase accuracy require target-PC validation. No upstream performance numbers are treated as ours. [Official usage, training and license](https://github.com/dscripka/openWakeWord). |
| Porcupine | Evaluated alternative: local Windows inference and custom platform-specific wake files, with Console/AccessKey and account/usage terms. No credential, subscription or runtime added. Select only after owner account/licensing review. [Official introduction](https://picovoice.ai/docs/porcupine/), [terms](https://picovoice.ai/docs/terms-of-use/). |
| Windows SAPI | Working installed-voice compatibility path, asynchronous literal-text synthesis into RAM, purge on cancellation, PCM playback under our device/output boundary. Uses OS-installed licensed voices; no Microsoft voice assets redistributed. [Microsoft speech flags](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ms720892(v=vs.85)). |
| Piper | Optional separately supplied local executable/model/config adapter; fixed arguments/stdin, CPU default, cancellation via owned process. Upstream offers raw output/streaming, but this adapter buffers each bounded phrase before playback and reloads the CLI per phrase. Current OHF code is GPLv3; model/dataset terms are separate. Windows bundle/dependencies and voice size depend on the chosen build/model. No model, GPU package or executable is bundled, no redistribution clearance or cinematic quality claimed. [Official project/license](https://github.com/OHF-Voice/piper1-gpl), [CLI](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md), [Windows build](https://github.com/OHF-Voice/piper1-gpl/blob/main/libpiper/README.md). |
| Coqui / XTTS | Evaluated, not installed. Heavier PyTorch/model deployment; upstream streaming capability does not establish latency here. Code MPL-2.0, XTTS weights under a separate Coqui Public Model License; documented XTTS languages do not establish Sinhala/Tamil support. Voice cloning and actor imitation are not enabled. [Maintained project](https://github.com/idiap/coqui-ai-TTS), [XTTS model documentation](https://github.com/coqui-ai/TTS/blob/dev/docs/source/models/xtts.md). |
| Meta MMS Tamil | Evaluated language-specific possibility, not installed or integrated. Official Tamil VITS checkpoint is CC-BY-NC-4.0; commercial redistribution/use is not assumed. RAM/quality/size/streaming on this PC unmeasured; not an approved cinematic/multilingual solution. [Official model card](https://huggingface.co/facebook/mms-tts-tam). |

The [Piper voice catalog](https://huggingface.co/rhasspy/piper-voices/blob/main/README.md) does not list Sinhala/Tamil. A catalog or model generating English does not establish those languages. Review each actual voice model card and dataset provenance. Installation size, CPU/RAM/GPU use and perceived voice quality remain selection/benchmark gates; there is no defensible single measurement without selected assets.

## Supplying optional local assets

Source deployments may explicitly install `python -m pip install -e ".[voice-wake]"` after choosing the optional openWakeWord runtime. This installs code dependencies, not models. Standard/frozen builds omit that runtime unless it is explicitly installed in the build environment; PyInstaller conditionally collects its code/native dependencies. Rebuilding a frozen app is required to add it. Do not install into another interpreter and assume the frozen app can import it. SAPI/manual/text paths remain available.

Place owner-selected artifacts and manifests under `%LOCALAPPDATA%\CLYDEX\models`, outside the repository. The Piper executable must implement the reviewed CLI contract: `--model`, `--config`, `--output-raw`, `--length-scale`, `--volume`, text on stdin, **mono signed little-endian int16 PCM** on stdout at the model config sample rate. Not every native build's raw format is identical. Confirm it before approval; float output is incompatible. Keep the complete trusted runtime/DLL/data bundle together. Only declared executable/model/config files are fingerprinted; this is not isolation from malicious same-user/native code.

Each manifest is at most 64 KiB, contains no credentials, and declares:

| Fields | Required value |
|---|---|
| `kind` | `piper` or `openwakeword` |
| `rights_confirmed`, `license`, `provenance` | `true`, actual applicable terms, and source/model/training-rights evidence |
| `languages` | Nonempty array of actual language codes |
| `files` | Piper: `executable`, `model`, `config`; wake: `model`, `melspec`, `embedding` |
| Each file entry | Exactly `path` relative to runtime models and `sha256` of the actual file (64 lowercase hex characters) |
| Piper fields | `original_voice: true`, nonempty `voice_name`; actual `.exe`, `.onnx` and JSON config containing `audio.sample_rate` |
| Wake fields | `phrase: "Hey CLYDEX"`, `phrase_validated: true`; optional `output_key`, and actual ONNX files |

Compute hashes with `Get-FileHash -Algorithm SHA256 <selected-file>`. Attest only after actual licensing review and phrase testing; setting a boolean does not train or validate a model. Trusted code supplies the manifest fingerprint in the exact configuration review and rechecks hashes before use. Changed/outside/missing artifacts fail closed. There is no shipped manifest containing fake production hashes or an alleged validated model.

## Personality, storage, privacy and recovery

Nine presentation modes: personal, professional, developer, technical support, study, focus, gaming, privacy and custom. Tone, screen detail, response language, spoken length and focus/gaming speech are configurable. Focus/gaming suppress speech unless explicitly allowed. Spoken answers omit code/URLs and are short; complete original text remains on screen and in consented history. Privacy mode adds a cloud restriction; no mode can grant permissions, bypass exact approvals, enable automatic memory or change tool scopes.

No personal name is inferred. Optional personal addressing is DPAPI-encrypted in `settings/personality.json`, scoped to the Windows owner. It enters a private data compartment with existing outbound review, never trusted system instructions. It is not an automatic memory. Other voice/presentation settings are atomic bounded JSON under `settings/voice.json` and `settings/personality.json`. Existing recognition/speak preferences migrate without changing schema 3 or deleting HKCU entries. Temporary conversation and reviewed memory policies are unchanged.

A native desktop/session probe fails closed on lock, secure desktop, disconnected session or probe failure. A Core-owned watcher requests stop/revokes approvals even if the UI stops polling; recording/playback and each next operating action recheck policy. Unlock never automatically unmutes/rearms. Native drivers, model loading/decoding, DNS, model downloads or COM cleanup can take time to return. Ownership stays held until completion. Cancellation cannot undo completed external effects.

Diagnostic events/logs contain status/codes, not transcripts or raw audio. Phase 04 receives typed lifecycle events, real amplitude/spectrum and playback frame counts. Optional `SpeechTiming` fields allow future phoneme/viseme timing; no engine currently supplies validated phoneme synchronization and no humanoid renderer was added.

Before rollback, close CLYDEX and preserve its runtime settings/data in the owner's protected backup location. Phase 03 adds no database migration. Keep new voice/personality JSON when running an earlier V2 commit; do not downgrade schema 3 or delete downloaded models/user data. Main and the independent V1 archive remain unchanged. Further phases, release, push and paid/private live tests need separate authorization.
# Phase 04 navigation note

The current HUD separates **Voice** (devices/models/languages/activation) and **Personality** into their own navigation pages. Talk/Finish recording, Stop and Unmute/Mute use the same existing services and reviews described below. The legacy **Voice & Personality** interface remains available with `--legacy`. No acoustic/model/language capability is upgraded merely by the new visual interface. See PHASE_04_COMPLETION_REPORT for native UI evidence.
