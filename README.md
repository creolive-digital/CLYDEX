# CLYDEX V2

Phase 06 adds supervised local operating tools, the React Automation Studio, disabled/versioned workflows and routines, explicit feeds/monitoring, local reviewed plugins and controlled MCP/service codecs. See [Phase 06 report](docs/PHASE_06_COMPLETION_REPORT.md) for actual verification and partial/live acceptance boundaries. No automatic schedules, polling, plugin execution or cloud activation follows installation. Local checks: `scripts/verify_phase06.ps1 -CloudPython <isolated-cloud-python>`.

Phase 05 adds the optional personal cloud account and Knowledge Vault on `v2`. Cloud is disabled by default; local chat/voice/memory continue independently. See [Phase 05 checkpoint](docs/PHASE_05_COMPLETION_REPORT.md), [cloud architecture](docs/CLOUD_ARCHITECTURE.md) and [private deployment/recovery guide](docs/CLOUD_DEPLOYMENT_GUIDE.md). Native SQL Server/Linux/embedding/production acceptance and earlier acoustic/3D asset gates remain pending. The owner-removed automatic GitHub Actions workflow stays removed; use `scripts/verify_phase05.ps1` for local checks. No public deployment or paid/private activation follows from installation.

Windows-first personal AI assistant. Active code is in `src/clydex/`; the original V1 release is preserved independently in `v1-old/`.

Phase 04 adds the local React cinematic HUD with functional management screens, six display modes, exact approvals and the approved reference avatar presentation. A production facial/full-body rig remains pending. Build the frontend before launching:

```powershell
npm --prefix frontend ci
npm --prefix frontend run build
python scripts/windows/clydex_voice_agent.pyw
```

Use `--legacy` for the preserved static interface, `--silent` for quiet startup or `--reduced-motion`. See [Phase 04 evidence and limitations](docs/PHASE_04_COMPLETION_REPORT.md) and [frontend architecture](docs/FRONTEND_ARCHITECTURE.md). No new provider, microphone or model is enabled by the HUD.

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
| `frontend/src/`, `frontend/tests/` | React/TypeScript HUD and deterministic frontend tests |
| `frontend/legacy/` | Preserved static desktop fallback and bundled fonts/icons |
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

Frontend checks: `npm --prefix frontend test` and `npm --prefix frontend run build`. Native HUD verification: `python scripts/verify_hud_smoke.py --output "$env:LOCALAPPDATA/CLYDEX/tmp/hud-verification"` (PowerShell; disposable profile, no microphone/provider/weather calls).
