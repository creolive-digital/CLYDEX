# Repository Guidelines

## Project Structure & Module Organization

CLYDEX is a Windows-first desktop assistant undergoing incremental V2 migration. Read both official specifications in `docs/` and `docs/architecture/PROJECT_STRUCTURE.md` before product or architectural changes. Product decisions in the supplied documents take precedence over legacy implementation choices. Do not overwrite those specifications.

New business logic belongs under `src/clydex/`, never the repository root. Phase 01 implements `core`, `providers`, `voice`, `tools`, `integrations`, `security`, `automation`, `database` and `desktop`. Create other target packages only when implementing their approved phase. Preserve the existing `.pyw` entry points and root compatibility imports. `clydex_widget.pyw` remains the working Tk widget. `clydex_voice_agent.pyw` launches the packaged Studio bridge. `studio_ui/` remains the legacy frontend until the separately approved React/TypeScript phase.

Use `v2` for development. Keep main stable and preserve uncommitted user changes. Do not push without explicit owner approval. Stop at each phase checkpoint; do not activate later-phase features or introduce placeholders presented as complete.

## Build, Test, and Development Commands

Run commands from the repository directory in Windows CMD or PowerShell:

- `py -m pip install -r requirements.txt` installs the voice assistant dependencies.
- `python -m pip install -e .` installs the headless package; `python -m pip install -e ".[dev]"` also installs lint tooling. The desktop requires dependencies from `requirements.txt`.
- `python -m unittest discover -v` runs baseline and foundation unit/security/regression tests.
- `python -m ruff check src tests` lints the new package and tests; the largely unchanged legacy orchestrator is excluded from style lint during migration.
- `python scripts/verify_windows_smoke.py --webview` checks real Tk/WebView2 startup and local controls with network/audio/private integrations disabled.
- `py clydex_widget.pyw` launches the widget (standard library only).
- `py clydex_voice_agent.pyw` launches the voice assistant with console output for troubleshooting.
- `START_CLYDEX.bat` starts the packaged app using the repository's intended launcher.

Build with the two existing PyInstaller specs and `installer.iss`, or `build_installer.bat`. CI runs tests/lint before building. The voice assistant requires Windows 10/11, Python 3.10+, audio devices, and a logged-in Codex CLI; consult `README_SETUP.txt`. Verify the interpreter: this workstation's default `py` currently points at a missing 3.14 installation, while `python` runs 3.13.14. Do not change the user's Python installation without authorization.

## Coding Style & Naming Conventions

Use descriptive `snake_case` names, four-space indentation, type hints for new public contracts, standard library first, and explicit module boundaries. Keep widget and voice-assistant changes in their relevant packages. Preserve Windows `.pyw` launch behavior and update packaging, imports, tests and documentation when moving modules. Avoid circular imports and destructive repository-wide restructures.

## Testing Guidelines

Use unittest and mock effectful Windows/provider operations. Run the existing four voice cases along with `tests/` before and after refactoring. Record actual results and distinguish baseline failures from regressions. For changes, also run the affected `.pyw` entry point on Windows. UI, audio, weather, browser and mailbox acceptance remain platform/account/device dependent; automated startup or mocked tests do not establish live integration correctness. Never perform real sends, destructive tasks or paid calls solely to satisfy a test.

## Commit & Pull Request Guidelines

Use small, reversible commits with a short imperative subject (for example, `Fix widget weather refresh`). Pull requests should describe user-visible behavior, actual test/manual verification and Windows environment, dependency/configuration changes, migration/rollback and unresolved risks; include screenshots for visual changes. No remote push without owner approval. Maintain requirement/task IDs and evidence in the development-management documents under `docs/`.

## Security & Configuration Tips

Do not commit credentials, transcripts, or local configuration secrets. The voice assistant sends prompts to the Codex service; follow the privacy notes in `README_SETUP.txt` and avoid dictating sensitive information.

Persistent user data belongs under `%LOCALAPPDATA%\CLYDEX\` (data, memory, cache, models, logs, backups, settings, plugins, tmp), outside source. Use Credential Manager/DPAPI for secrets; no plaintext fallback or credentials in SQLite/config/logs. Non-secret examples belong in `.env.example` and `config/`. SQLite currently stores only allowlisted voice preferences and redacted audit metadata; do not silently add conversations, memory or sensitive caches.

All assistant action pathways must use the central executor. Risk/scope comes from installed trusted adapters, never model/web/mail/plugin output. Preserve one-time exact-action approvals, expiry, cancellation, private-context transfer reviews and local privacy policy. Do not add a public operating-system control endpoint, elevate privileges or treat Python-level checks as an OS sandbox.

Preserve Cyber Cyan, Intelligence Core and Digital Wireframe branding. The standalone approved references are expected at `assets/branding/clydex_logo_reference.png` and `assets/avatars/clydex_avatar_reference.png`; record missing assets rather than invent replacements. Do not replace the legacy artwork during foundation work. Product/branding/architecture/privacy/security-policy/database/cost changes require owner approval; routine implementation within approved Phase 01 does not require repeated approval.
