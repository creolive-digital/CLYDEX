# Changelog

## V2 Phase 03 — engineering checkpoint (2026-11-27)

- Extracted bounded local audio, Whisper, SAPI/Piper, VAD, wake, devices, lifecycle, privacy and real spectrum events behind typed headless contracts; existing Core/coordinator/tools remain the authority.
- Added opt-in microphone, distinct finish/cancel, half-duplex follow-ups, independent languages, lock watcher, mute/Stop, foreground cancellation and owned native shutdown.
- Added configurable native hotkey/tray and a local custom-wake adapter. No trained Hey CLYDEX model, cinematic neural voice, raw recording, cloud TTS or automatic model download is bundled/enabled.
- Added nine isolated personality modes, concise spoken/full-screen answers, encrypted optional addressing and functional legacy settings/status/error controls.
- Preserved intake user changes and fixed the synthetic model-loader startup/cleanup failure, muted activation rejection and headless lock/action checks. Added deterministic/native/visual verification, optional-runtime packaging, setup/licensing documentation and the Phase 03 checkpoint.
- Main, archive, official specifications and artwork remain protected. Live speech/language/quality/provider/hardware acceptance and asset choices are open; stop before Phase 04, with no push/merge/release.

## V2 Phase 02 — engineering checkpoint (2026-11-26)

- Hardened shutdown ownership and Windows child jobs, including failed assignment cleanup, bounded combined output/generated files and descendant termination.
- Added the existing Codex default plus disabled OpenAI/Claude/Gemini/Ollama/OpenRouter/custom adapters, immutable registry/configuration, capability routing, health/status, JSON schema validation and supported HTTP streaming.
- Added common outbound privacy/cost/consent policy, separate context compartments, reviewed retry/fallback and local-only derived-history protection. Existing Windows privileges unchanged.
- Added transactional SQLite schema 1→3, consented DPAPI-encrypted conversations, temporary defaults, history search/resume/export/retention/archive/delete and owner-scoped personal memory/provenance/revisions.
- Added explicit memory commands, six categories, local retrieval and opt-in literal suggestions reviewed before saving. No automatic collection or new account enabled.
- Extended the existing frontend/desktop bridge with functional settings/history/memory controls and same supervised queue/approval UI; no artwork redesign or React/voice/cloud expansion.
- Expanded deterministic/security/native verification, CI compilation/JS checks and all development/architecture/configuration documentation. Exact final evidence and limitations are in TESTING_AND_ACCEPTANCE and DEVELOPMENT_PROGRESS.
- Main, the independent V1 archive and original product specifications remain unchanged. No remote push/merge/release or paid/private live provider call.

## V2 Phase 01 — in development (2026-11-26)

- Established `v2` branch from e65fe46; preserved original specifications and existing source baseline.
- Added baseline audit, conflicts/decisions, phase roadmap, progress and acceptance documents.
- No remote push, cloud deployment, branding replacement, provider activation or user-data migration.

### Foundation implementation

- Introduced src packaging, central CoreApplication, typed immutable contracts/events and compatible root launch/import adapters.
- Added validated configuration, per-user runtime folders, SQLite metadata migrations/preferences, Credential Manager storage and safe rotating diagnostics/audit.
- Added scope-aware exact-action approvals with identity/digest/expiry/replay checks, separate private-context transfer consent, bounded queue/events, per-user core lock and cancellation/Stop.
- Extracted existing Codex CLI provider with cancellation and local response validation; preserved Windows/browser/Outlook/speech/spectrum/widget capabilities incrementally.
- Updated packaging resources and CI tests/lint; added 71 foundation/regression checks alongside the original four (75 total).
- Verified real Tk/WebView2 startup and native synthetic credential storage, wheel contents/isolated import and both PyInstaller EXE builds. Live accounts/audio, fresh installer, performance budgets and owner acceptance remain open.
- Fixed the credential adapter's native Unicode-write contract after a real integration check exposed a mismatch missed by the initial mock.

No Phase 02 features implemented. Original product document hashes unchanged. See DEVELOPMENT_PROGRESS for checkpoint/handoff and TESTING_AND_ACCEPTANCE for evidence.

### V1 archive organization

- Preserved standalone original release in `v1-old/` at the owner's request.
- Migrated active shared Tk implementations into `src/clydex/desktop/`, retained root compatibility launchers/imports, moved legacy V2 artwork into `assets/legacy/` and voice regression cases into `tests/`.
- Updated build resource paths; removed redundant root Windows helper copies. Active V2 remains independent of the archive.
- Verified 76 active V2 tests, four independent V1 tests, safe UI startup for both versions and both updated V2 EXE builds.

### Root cleanup requested by owner

- Retired root import shims and moved launch/setup/build files into scripts, installer, deployment and docs folders.
- Relocated active static UI to frontend/legacy with unchanged behavior and artwork. Updated resource paths, CI and packaging.
- Preserved generated root remnants outside source; added root README with current commands. Original V1 remains isolated in v1-old.
