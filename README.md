# CLYDEX V2

Windows-first personal AI assistant. Active code is in `src/clydex/`; the original V1 release is preserved independently in `v1-old/`.

Phase 03 adds modular local voice, controlled follow-up conversation, interrupt/mute/lock privacy, native activation adapters and nine personality profiles through **Voice & Personality** in the existing desktop UI. Microphone/background activation starts off; speech models require separate reviewed preparation. SAPI remains the local fallback. No validated Hey CLYDEX model or approved cinematic neural voice is bundled. See [voice setup and limitations](docs/VOICE_CONFIGURATION.md) and the [Phase 03 checkpoint](docs/PHASE_03_COMPLETION_REPORT.md).

Multi-provider routing, encrypted conversations and consented memory remain available through **AI & Memory**. Codex remains the default; new providers are disabled, chats start temporary, and automatic memory suggestions are off. See [provider setup and privacy](docs/PROVIDER_CONFIGURATION.md). Live hardware/provider and production acceptance remain pending.

From the checkout root:

```powershell
python -m pip install -r deployment/windows/requirements.txt
python scripts/windows/clydex_widget.pyw
python scripts/windows/clydex_voice_agent.pyw
```

Windows shortcuts and the build command are in [scripts/windows](scripts/windows/). The widget's Agent button opens active V2. Existing installed EXE names are unchanged.

| Folder | Contents |
|---|---|
| `src/clydex/` | Active V2 Python packages |
| `frontend/legacy/` | Current static desktop UI and bundled fonts/icons |
| `assets/` | Active artwork and future approved production assets |
| `config/` | Non-secret configuration examples |
| `tests/` | V2 automated tests |
| `scripts/` | Launch, setup, build and verification utilities |
| `installer/` | PyInstaller specifications and Windows installer definition |
| `deployment/windows/` | Desktop dependencies and ignored build artifacts |
| `docs/` | Official specifications, setup and development records |
| `v1-old/` | Standalone original V1 source, UI, assets and launchers |

See [setup](docs/README_SETUP.txt), [actual and target structure](docs/architecture/PROJECT_STRUCTURE.md), and [testing evidence](docs/TESTING_AND_ACCEPTANCE.md). User data belongs outside the checkout under `%LOCALAPPDATA%\CLYDEX\`.

Check changes with `python -m unittest discover -v`, `python -m ruff check --no-cache src tests`, and `python scripts/verify_windows_smoke.py --webview`.
