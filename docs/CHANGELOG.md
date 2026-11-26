# Changelog

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
