# Repository Guidelines

Publication record: after the Phase 04 engineering handoff, the owner explicitly requested committing and pushing that completed checkpoint to GitHub on `v2`. This supersedes the phase's historical no-push restriction for this publication only. It does not authorize merging main, tagging, releasing, activating providers or starting another phase.

## Project Structure & Module Organization

CLYDEX is a Windows-first desktop assistant undergoing incremental V2 migration. Read both official specifications in `docs/` and `docs/architecture/PROJECT_STRUCTURE.md` before product or architectural changes. Product decisions in the supplied documents take precedence over legacy implementation choices. Do not overwrite those specifications.

New business logic belongs under `src/clydex/`, never the repository root. Phase 03 adds modular `voice` and `personality` services and desktop activation/settings to the existing Phase 02 conversations, memory, providers and Core queue. Create other target packages only when implementing their approved phase. The owner explicitly requested removal of leftover root files: launchers retain their filenames under `scripts/windows/`; obsolete root Python import facades are retired. Import active `clydex` package modules directly.

The Phase 04 React/TypeScript frontend is under `frontend/src/` with tests under `frontend/tests/`. `frontend/legacy/` (including fonts/icons) remains the working fallback. Use the minimal typed HUD bridge and existing services; no duplicate AI/voice/data engine. Approved owner references are under `assets/branding/` and `assets/avatars/`; the avatar is a labeled reference until a matching production rig is supplied. Preserve `assets/legacy/`. PyInstaller specs belong in `installer/pyinstaller/`, Inno Setup and notes in `installer/windows/`, Windows requirements in `deployment/windows/`, and setup documentation in `docs/`. Keep root files limited to project metadata, AGENTS.md and README.md. Generated build output belongs in ignored deployment artifact directories or outside source, never loose at the root.

The owner-requested `v1-old/` contains the standalone original e65fe46 release, including its own launchers, modules, UI, assets, setup scripts and four tests. Keep archived original files unchanged. V2 must not import code or resources from this archive. Original V1 voice regression cases are also maintained for V2 in `tests/test_voice_routing.py`. Run archived tests separately from `v1-old/` in a fresh Python process.

Use `v2` for development. Keep main stable and preserve uncommitted user changes. Do not push without explicit owner approval. Stop at each phase checkpoint; do not activate later-phase features or introduce placeholders presented as complete.

## Build, Test, and Development Commands

Run commands from the repository directory in Windows CMD or PowerShell:

- `python -m pip install -r deployment/windows/requirements.txt` installs the voice assistant dependencies.
- `python -m pip install -e .` installs the headless package; `python -m pip install -e ".[dev]"` also installs lint tooling. The desktop requires dependencies from `deployment/windows/requirements.txt`.
- `python -m unittest discover -v` runs baseline and foundation unit/security/regression tests.
- `python -m ruff check --no-cache src tests` lints the new package and tests; the largely unchanged legacy orchestrator is excluded from style lint during migration.
- `python scripts/verify_windows_smoke.py --webview` checks real Tk/WebView2 startup and local controls with network/audio/private integrations disabled.
- `npm --prefix frontend ci`, `npm --prefix frontend test` and `npm --prefix frontend run build` verify/build the local HUD (Node 24 build baseline).
- `python scripts/verify_hud_smoke.py --output <outside-source-directory>` checks actual WebView2 HUD, native modes/review/privacy, shared tools, rendering suspension/fallback and joined shutdown with a disposable profile. It captures only the application client area.
- `python scripts/verify_voice_native.py` enumerates devices/voices, synthesizes a fixed SAPI phrase to RAM and checks joined native hotkey/tray registration; it opens no microphone or speaker.
- `python scripts/windows/clydex_widget.pyw` launches the widget (standard library only).
- `python scripts/windows/clydex_voice_agent.pyw` launches the voice assistant with console output for troubleshooting.
- `scripts/windows/START_CLYDEX.bat` starts the packaged app using the repository's intended launcher.

Build with specs under `installer/pyinstaller/` and `installer/windows/installer.iss`, or `scripts/windows/build_installer.bat`. The owner removed the GitHub Actions build workflow from `v2`; run local tests/lint and build checks before publication. The voice assistant requires Windows 10/11, Python 3.10+, audio devices, and a logged-in Codex CLI; consult `docs/README_SETUP.txt`. Verify the interpreter: this workstation's default `py` currently points at a missing 3.14 installation, while `python` runs 3.13.14. Do not change the user's Python installation without authorization.

## Coding Style & Naming Conventions

Use descriptive `snake_case` names, four-space indentation, type hints for new public contracts, standard library first, and explicit module boundaries. Keep widget and voice-assistant changes in their relevant packages. Preserve Windows `.pyw` launch behavior and update packaging, imports, tests and documentation when moving modules. Avoid circular imports and destructive repository-wide restructures.

## Testing Guidelines

Use unittest and mock effectful Windows/provider operations. Run the existing four voice cases along with `tests/` before and after refactoring. Record actual results and distinguish baseline failures from regressions. For changes, also run the affected `.pyw` entry point on Windows. UI, audio, weather, browser and mailbox acceptance remain platform/account/device dependent; automated startup or mocked tests do not establish live integration correctness. Never perform real sends, destructive tasks or paid calls solely to satisfy a test.

## Commit & Pull Request Guidelines

Use small, reversible commits with a short imperative subject (for example, `Fix widget weather refresh`). Pull requests should describe user-visible behavior, actual test/manual verification and Windows environment, dependency/configuration changes, migration/rollback and unresolved risks; include screenshots for visual changes. No remote push without owner approval. Maintain requirement/task IDs and evidence in the development-management documents under `docs/`.

## Security & Configuration Tips

Do not commit credentials, transcripts, or local configuration secrets. The voice assistant sends prompts to the Codex service; follow the privacy notes in `docs/README_SETUP.txt` and avoid dictating sensitive information.

Persistent user data belongs under `%LOCALAPPDATA%\CLYDEX\` (data, memory, cache, models, logs, backups, settings, plugins, tmp), outside source. Use Credential Manager/DPAPI for secrets; no plaintext fallback or credentials in SQLite/config/logs. Non-secret examples belong in `.env.example` and `config/`. Owner-authorized Phase 02 adds DPAPI-encrypted conversation titles/text and personal memories to schema 3, preserving settings/audit. Temporary sessions are default. Persistence and automatic memory suggestions require consent; each suggested memory requires review. Never save raw audio, credentials or sensitive tool/mail turns.

All assistant action pathways must use the central executor. Risk/scope comes from installed trusted adapters, never model/web/mail/plugin output. Preserve one-time exact-action approvals, expiry, cancellation, private-context transfer reviews and local privacy policy. Do not add a public operating-system control endpoint, elevate privileges or treat Python-level checks as an OS sandbox.

Preserve Cyber Cyan, Intelligence Core and Digital Wireframe branding. The standalone approved references are supplied at `assets/branding/clydex_logo_reference.png` and `assets/avatars/clydex_avatar_reference.png`; preserve their exact bytes and do not claim a reference image is a production rig. Do not replace the legacy artwork or approved face. The latest owner instruction authorizes Phase 04 cinematic HUD engineering after foundation admission; stop at the Phase 04 owner review checkpoint. All new providers stay disabled/unconfigured until explicitly enabled. Microphone/wake/background/continuous/hotkey/tray start off; models never download implicitly. No paid requests, real credentials, private data transmission, automatic memory activation, cloud deployment, push, merge, tag or release is authorized by this phase. Consult `docs/PROVIDER_CONFIGURATION.md`, `docs/VOICE_CONFIGURATION.md`, `docs/FRONTEND_ARCHITECTURE.md` and the Phase 04 acceptance report. Material changes outside this scope require owner approval.
