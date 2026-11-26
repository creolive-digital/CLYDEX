# Project structure and public interfaces

Phase 01 incremental structure, followed by the owner-requested V1 archive relocation. Target follows the owner's mandatory layout; only functional packages exist. Root compatibility launchers, build/install entry points and supplied documents are retained.

## Actual structure

```text
CLYDEX/
  pyproject.toml              setuptools src package; Python >=3.10; dev lint extra
  requirements.txt           editable core + existing desktop dependencies
  .env.example               non-secret environment examples, not auto-loaded
  config/clydex.example.json non-secret core policy/config template
  src/clydex/
    core/
      application.py         CoreApplication lifecycle, one per-user queue, settings
      instance.py            OS lock released on exit/crash; prevents competing cores
      contracts.py           frozen RequestContext, ActionRequest, ToolSpec, AIProvider
      commands.py            existing deterministic parser and response schemas
      config.py              validated AppConfig and RuntimePaths
      events.py              CoreEvent and bounded tuple-compatible EventChannel
      errors.py              safe Failure mapping; no raw provider exceptions to UI
      logging.py             rotating allowlisted JSON diagnostics
      processes.py           cancellable, timed child-process execution
      legacy_engine.py       migrated VoiceEngine compatibility orchestrator
    providers/codex.py       actual existing Codex CLI adapter; local response validation
    voice/spectrum.py        unchanged real PCM/FFT visualization implementation
    tools/
      windows_apps.py        existing Win32/accessibility adapters + execution gate
      desktop.py             existing Playwright/tab/PowerShell helpers
      app_controls.ps1       packaged accessibility helper
      read_browser_tab.ps1   packaged existing-tab reader
    integrations/outlook.py  existing COM/Graph inbox and unsent drafts
    security/
      permissions.py         installed scopes/risk and expiring one-use grants
      credentials.py         Windows Credential Manager (no file fallback)
    automation/
      tasks.py               serial bounded queue, task handles and cancellation
      executor.py            trusted tool registry, schema/scope/approval/outcome gate
    database/
      store.py               transactional LocalStore, non-secret preferences/audit
      migrations/001_foundation.sql
    desktop/
      studio.py             existing PyWebView bridge adapted to CoreApplication
      widget.py             shared Tk clock/weather/time tools, migrated from root
      theme.py              Tk skins used by the active widget
      hologram.py           preserved older Tk hologram helper
  tests/                     application, execution, config/database, provider,
                             approval security and legacy/widget regressions
  scripts/verify_windows_smoke.py
  docs/                      two original specifications + eight management docs
    architecture/PROJECT_STRUCTURE.md
  studio_ui/                 preserved static HTML/CSS/JS/fonts/icons
  clydex_voice_agent.pyw      original launch path, now thin package launcher
  clydex_widget.pyw           thin compatible launcher for desktop/widget.py
  clydex_{engine,apps,desktop,outlook,spectrum}.py
                             root import compatibility facades
  clydex_theme.py, clydex_hologram.py
                             root compatibility imports for desktop helpers
  assets/legacy/             active legacy PNG artwork; approved references still missing
  v1-old/                    standalone exact e65fe46 release, original UI/artwork/
                             launchers/tests/setup; never imported by active V2
  clydex_*.spec, installer.iss, *.bat
                             preserved build/install commands, src-aware packaging
  .github/workflows/build.yml
                             local tests/lint before Windows main/v2 build
```

## Target structure (planned packages are not empty placeholders)

| Location | Responsibility | Current / introduction gate |
|---|---|---|
| `src/clydex/core/` | Application services and orchestration | Implemented foundation; legacy orchestration retained incrementally |
| `providers/` | Seven model adapters/routing | Codex adapter now; remaining adapters Phase 2 |
| `voice/` | STT/TTS/activation/audio | Spectrum now; existing engine STT/SAPI retained until Phase 3 |
| `memory/`, `personality/` | Memory/history, adaptive behavior | Phase 2–3 |
| `tools/`, `automation/` | OS/developer adapters and supervised execution/workflows | Existing tools/queue now; expanded tools/studio Phase 6 |
| `knowledge/` | Ingestion/retrieval | Phase 5 |
| `security/` | Permissions/credentials/audit/auth | Local consent/secret foundation now; cloud/device auth later |
| `plugins/` | Manager/registry/SDK | Phase 6 |
| `integrations/` | External accounts/MCP | Existing Outlook now; other integrations Phase 6 |
| `monitoring/`, `notifications/` | Health/feeds/notifications | Phases 4,6 |
| `devices/` | Pairing/revocation/capabilities | Phase 8; no hardware implementation |
| `api/` | Authenticated FastAPI/WebSocket transport | Deferred transport extraction; no new core HTTP control API in Phase 1 |
| `database/` (package) | Data access/repositories | SQLite metadata now |
| `desktop/` | Windows application lifecycle and shell | Studio, shared widget, Tk skins and older hologram helper |
| `frontend/` | React/TypeScript HUD/avatar | Phase 4; current `studio_ui/` retained |
| `assets/` | Approved branding/avatar/fonts/sounds | Existing V2 artwork under legacy/; approved reference files still missing OI-01 |
| `cloud/` | Independently deployable cloud gateway/sync | Phase 5 after owner infra approval |
| `database/` (root) | SQLite/MSSQL deployment schemas/scripts | Add deployment SQL when needed; current embedded local migration is package data |
| `config/` | Non-secret templates | Implemented |
| `tests/` | Unit/integration/regression/security/perf/e2e | Functional foundation tests now, later categories incrementally |
| `deployment/`, `installer/` | Windows/Linux/Docker/proxy and setup wizard | Later migration; root working build/installer retained |
| `scripts/`, `tools/` (root) | Maintenance/build scripts and standalone dev utilities | UI smoke script now; no empty utility folders |
| `docs/` | Source specifications and development records | Implemented, continuously maintained |

## Dependency direction and runtime behavior

Desktop → CoreApplication → VoiceEngine adapter → provider/tool adapters → OS/services. Contracts/events/errors are UI-independent; no provider imports WebView or authorizes its own action. ToolExecutor accepts only installed ToolSpec entries. The model returns a validated plan; the service constructs typed actions and consumes exact approvals before invoking effects. Window/control and inbox identities are revalidated at the effect boundary.

Public interfaces: `CoreApplication.submit/stop/close`; `VoiceEngine.chat_reply/text_worker/record_worker/pending_review/decide/cancel/close`; `AIProvider.respond(ProviderRequest, Cancellation)`; `ToolExecutor.execute(ActionRequest, operation, review, token)`; `LocalStore.get_setting/set_setting/audit`; `CredentialStore.get/set/delete`. Direct legacy helpers are trusted internal adapters, not remotely callable APIs or a security sandbox. Root facades retain existing Python import paths. Only `Studio` is exported to the existing trusted WebView bridge.

Runtime storage: `%LOCALAPPDATA%\CLYDEX\{data,memory,cache,models,logs,backups,settings,plugins,tmp}`. Directories are created for the approved runtime organization; memory/cache/plugins directories do not indicate implemented features. SQLite contains preferences/audit metadata only. Logs are capped at 1 MiB × 4 files; no raw prompts, payloads or exception text. Model files use the models directory; Codex temporary files use tmp and are cleaned after the call. PyWebView may run its existing loopback asset server; no new public core/OS endpoint is introduced.

## Migration and rollback

Install with `python -m pip install -r requirements.txt`, or the dependency-free core with `python -m pip install -e .`. Root launchers can locate local `src/` without an editable install. PyInstaller includes `src` and package SQL/PS1 resources. The install folder keeps widget/agent siblings as before.

The original release is now directly runnable from `v1-old/`, without switching branches. Its 43 original tracked files are byte-for-byte copies of the Git baseline; README_ARCHIVE.md is the only added archive documentation. No user data or .git directory is archived. V2's active packaged Windows helper scripts are solely under `src/clydex/tools/`; their root duplicate copies were removed. The archive has its own original helpers.

The root `.pyw` commands still launch V2. Widget development resources resolve from the checkout root and frozen resources from `sys._MEIPASS`; its Agent button targets the active root agent launcher (or installed sibling EXE), not the archive. PyInstaller specifications use `assets/legacy/` and packaged PS1 resources. Root tests moved to `tests/test_voice_routing.py`; the independent archive retains its original test filename.

Save V2 work and switch to `main` if a complete baseline checkout is preferred. No user data is deleted, registry setting overwritten, or DB downgrade attempted. Future schema changes require migrations and restore tests. Active V2 shares no imports or resource lookups with `v1-old/`.
