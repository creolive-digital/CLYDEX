# Project structure and public interfaces

## Phase 05 actual extension (2026-11-28)

- `cloud/`: independent `clydex-cloud` package, API/core/auth/devices/sync/vault/storage/workers/repositories/tests, runtime lock and generated OpenAPI.
- `cloud/src/clydex_cloud/repositories/migrations/`: canonical packaged SQL Server DDL/reverse migration; `database/mssql/README.md` links this single source.
- `src/clydex/cloud`, `knowledge`, `synchronization`: desktop client/workspace, shared format/citation contracts, DPAPI queue/cache and existing-coordinator RAG.
- `src/clydex/database/migrations/004_cloud.sql`: additive local schema 4; imports/mappings share one transaction.
- `frontend/src/features/{cloud,knowledge,devices,synchronization}`: four functional React screens using the existing three-method HUD bridge.
- `deployment/{docker,linux,nginx}`: private templates/scripts only, no deployed service or SQL image.
- `scripts/verify_phase05.ps1`, `verify_cloud_native.py`, `verify_phase05_package.py`, `verify_frozen_startup.py`, schema/OpenAPI generation scripts: local verification without GitHub Actions.
- `docs/evidence/phase05`: synthetic/native screenshots and concise verification manifests; runtime builds/data remain outside source.

The automatic workflow remains removed. Historical inventories below describe earlier checkpoints; no current `.github/workflows` build is provided. Existing legacy/widget/archive and branding paths remain unchanged. New business logic never lives at repository root.

## Phase 04 extension

The current primary frontend is `frontend/src/` (React/TypeScript), with `app`, `components`, `features`, `hooks`, `services`, `stores`, `themes` and `styles`. `frontend/tests/` contains deterministic Vitest/jsdom tests. Package/lock/TS/Vite configuration stays under `frontend/`. Vite emits to ignored `deployment/windows/artifacts/frontend/`; it never mixes generated files into source. Fonts/license notices are bundled; expected owner logo/face references are supplied under `assets/branding/` and `assets/avatars/` and remain unchanged. No unnecessary model/texture/sound placeholder directories were created.

New active desktop modules are `hud.py` (validated minimal facade and single event collector), `hud_contract.json`, `display.py`, `preferences.py`, `notifications.py`, `system_info.py` and `widget_service.py` (one owned adapter to existing Tk time tools). Launcher defaults to the built HUD, retaining `--legacy`. `scripts/verify_hud_smoke.py` verifies the production bundle in native Windows WebView2. CI and installer builds include npm tests/build and package both frontends plus local licenses/contract resources. The directory inventory below remains the historical Phase 03 baseline; its "no UI redesign" description is superseded by this authorized extension. See FRONTEND_ARCHITECTURE for contracts and ownership.

Current Phase 03 structure after incremental voice/personality extraction. Target follows the owner's mandatory layout; only functional packages exist. Source launchers remain under scripts/windows and the supplied specifications/archive remain unchanged.

## Actual structure

```text
CLYDEX/
  .github/workflows/              CI and release configuration
  .env.example                    non-secret environment examples
  .gitattributes, .gitignore       repository metadata
  AGENTS.md, README.md             repository instructions and entry guide
  pyproject.toml                  src packaging and development tooling
  src/clydex/
    core/                         headless application, contracts, config, events,
                                  safe logging/errors, processes, legacy orchestrator
    providers/                    Codex + six HTTP codecs, transport, registry, router
    conversations/                encrypted owned sessions/messages and retention
    memory/                       encrypted provenance, consent, suggestions, retrieval
    voice/                        typed contracts, config/artifacts, input/output,
                                  Whisper, SAPI/Piper, VAD, wake, lifecycle,
                                  devices/privacy/events and real PCM/FFT spectrum
    personality/                  nine presentation profiles, response policy,
                                  encrypted optional personal addressing
    tools/                        Windows, browser, PowerShell adapters and PS1 resources
    integrations/                 existing Outlook integration
    security/                     exact approvals, outbound policy, Credential Manager,
                                  DPAPI encryption and private persistence filter
    automation/                   bounded queue, cancellation and tool execution
    database/                     SQLite metadata and schema 1–3 embedded migrations
    desktop/                      Studio/voice/settings bridge, native hotkey/tray
                                  activation ownership, widget, Tk theme/helpers
  frontend/legacy/                existing HTML/CSS/JS desktop frontend, bundled
                                  fonts/icons/licenses; no UI redesign
  assets/legacy/                  unchanged active PNG artwork
  config/                         non-secret settings template
  tests/                          all active V2 tests, including voice regressions
  scripts/
    verify_windows_smoke.py        safe native UI/credential verification
    verify_voice_native.py         device/voice metadata, SAPI-to-RAM and owned
                                  native activation check; no mic/speaker
    windows/
      clydex_widget.pyw            V2 widget launcher
      clydex_voice_agent.pyw       V2 Studio launcher
      START_CLYDEX.bat             Windows widget shortcut
      INSTALL_REQUIREMENTS.bat     Windows dependency setup
      build_installer.bat          Windows build shortcut
  installer/
    pyinstaller/                  widget and voice-agent .spec files
    windows/                      Inno Setup script and installer notes
  deployment/windows/
    requirements.txt              editable core plus existing desktop dependencies
    artifacts/                    ignored local build outputs, created on demand
  docs/                           original specifications, setup and management docs
    architecture/                 actual/target structure
  v1-old/                         independent exact e65fe46 release and archive notes
```

There are no loose Python modules, launchers, batch files, .spec files, installer definitions, setup notes or desktop requirements at the root. Runtime/cache/build remnants previously left at the root were preserved outside the checkout under `%LOCALAPPDATA%/CLYDEX/tmp/repository-cleanup-20261126-150704/`. No future-phase placeholder folders were added.

## Target structure (planned packages are not empty placeholders)

| Location | Responsibility | Current / introduction gate |
|---|---|---|
| `src/clydex/core/` | Application services and orchestration | Implemented foundation; legacy orchestration retained incrementally |
| `providers/` | Seven model adapters/routing | Implemented Phase 02; six new adapters disabled, live validation pending |
| `voice/` | STT/TTS/activation/audio | Phase 03 services implemented; gated local custom wake/neural assets; live acoustic acceptance open |
| `conversations/`, `memory/` | Session persistence and consented personal memory | Implemented Phase 02; encryption, owner-bound repositories and local retrieval |
| `personality/` | Adaptive presentation | Phase 03 nine profiles/configured tone/length/language; no permission authority |
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
| `frontend/` | React/TypeScript HUD/avatar | Phase 4; current `frontend/legacy/` retained |
| `assets/` | Approved branding/avatar/fonts/sounds | Existing V2 artwork under legacy/; approved reference files still missing OI-01 |
| `cloud/` | Independently deployable cloud gateway/sync | Phase 5 after owner infra approval |
| `database/` (root) | SQLite/MSSQL deployment schemas/scripts | Add deployment SQL when needed; current embedded local migration is package data |

## Phase 03 public boundaries and runtime ownership

`voice/contracts.py` defines AudioInput, AudioOutput, SpeechRecognizer, SpeechSynthesizer, ActivityDetector, WakeDetector, ConversationLifecycle and InterruptibleVoice, plus AudioBuffer/PCMChunk/Transcript. `devices.py` defines DeviceManager/AudioDevice. `events.py` defines VoiceState, VoiceEvent and optional SpeechTiming; sinks remain transport-independent and bridge tuple compatibility is retained. `spectrum.py` remains the single real FFT implementation.

CoreApplication owns VoiceRuntime and PersonalityService. VoiceEngine delegates capture/recognition/synthesis to these services while the same IntelligenceCoordinator, ToolExecutor, permissions, conversation/memory services and supervised queue handle every request. `desktop/activations.py` owns native hotkey/tray lifecycles registered with Core. The Core lock is released only after queue/model/wake/privacy/native cleanup. The background worker detects wake only and submits to the same queue; it never plans tools.

Voice preferences and encrypted optional addressing live in runtime `settings/voice.json` and `settings/personality.json`; downloaded models/manifests/binaries belong under runtime `models/`, outside source. No schema-4 migration, raw audio file, frontend-specific headless dependency, empty placeholder package or approved-brand replacement was added. `docs/VOICE_CONFIGURATION.md` is included by the Windows installer. Optional wake code is collected by PyInstaller only when explicitly installed for that build; no wake/neural assets are bundled. React/HUD/production humanoid remains Phase 04.
| `config/` | Non-secret templates | Implemented |
| `tests/` | Unit/integration/regression/security/perf/e2e | Functional foundation tests now, later categories incrementally |
| `deployment/`, `installer/` | Windows/Linux/Docker/proxy and setup wizard | Later migration; working scripts/specs under scripts/ and installer/ |
| `scripts/`, `tools/` (root) | Maintenance/build scripts and standalone dev utilities | UI smoke script now; no empty utility folders |
| `docs/` | Source specifications and development records | Implemented, continuously maintained |

## Dependency direction and runtime behavior

Desktop → CoreApplication → VoiceEngine adapter → provider/tool adapters → OS/services. Contracts/events/errors are UI-independent; no provider imports WebView or authorizes its own action. ToolExecutor accepts only installed ToolSpec entries. The model returns a validated plan; the service constructs typed actions and consumes exact approvals before invoking effects. Window/control and inbox identities are revalidated at the effect boundary.

Public interfaces: `CoreApplication.submit/stop/close`; `VoiceEngine.chat_reply/text_worker/record_worker/pending_review/decide/cancel/close`; `AIProvider.respond(ProviderRequest, Cancellation)`; `ToolExecutor.execute(ActionRequest, operation, review, token)`; `LocalStore.get_setting/set_setting/audit`; `CredentialStore.get/set/delete`. Direct legacy helpers are trusted internal adapters, not remotely callable APIs or a security sandbox. Obsolete root import facades are retired by the owner's explicit cleanup request; active callers import the package directly. Only `Studio` is exported to the existing trusted WebView bridge.

Runtime storage: `%LOCALAPPDATA%\CLYDEX\{data,memory,cache,models,logs,backups,settings,plugins,tmp}`. SQLite schema 3 contains settings/audit plus explicitly retained DPAPI-encrypted conversation/memory payloads. Default conversations remain temporary. Provider/routing JSON is non-secret under settings; keys remain in Credential Manager. Logs are capped at 1 MiB × 4 files; no raw prompts, payloads or exception text. Model files use models; Codex temporary files use tmp and are cleaned after the call. PyWebView retains its existing loopback asset server; no new public core/OS endpoint is introduced.

## Migration and rollback

Install from the checkout root with `python -m pip install -r deployment/windows/requirements.txt`, or install only the core with `python -m pip install -e .`. Launch V2 using `python scripts/windows/clydex_widget.pyw` or `python scripts/windows/clydex_voice_agent.pyw`. Original launcher filenames are preserved in scripts/windows; root compatibility imports were removed at the owner's request.

PyInstaller specs resolve source paths relative to their own installer/pyinstaller location. They include the active frontend at frontend/legacy and packaged SQL/PS1 resources. Inno Setup resolves relative paths from installer/windows; local/CI build outputs use deployment/windows/artifacts. Installed widget/agent EXE names and sibling layout are unchanged. The widget's Agent button targets the relocated V2 launcher in development and the existing sibling EXE when installed.

All 43 original V1 files under v1-old remain byte-for-byte equal to the reviewed V2 intake 0c0213d. Compared with original e65fe46 Git blobs, 31 text files have preexisting CRLF-only differences (OI-24); older raw-byte provenance claims are qualified by this finding. Its launchers, UI, artwork, requirements and build scripts remain independent; V2 never imports archive code. README_ARCHIVE.md is unchanged archive documentation.

The organization cleanup did not change user schemas. Phase 02 now adds transactional 1→3 migrations; settings/audit are preserved, failures roll back and downgrades are refused. Only isolated synthetic profiles were migrated during verification. See PROVIDER_CONFIGURATION.md for backup/restore guidance; never downgrade a real schema-3 database in place.

## Phase 02 module interfaces

`core/orchestrator.IntelligenceCoordinator.respond/check_provider` serves model requests inside the existing VoiceEngine/ToolExecutor, not a separate agent loop. `core/context.ContextBundle` separates six context compartments and enforces local-only provenance on derived history. `core/data_actions.OwnedDataActions` constructs exact current-user local data operations; model plan enums do not expose memory/settings mutation.

`providers/base` defines immutable validated configuration/capabilities and safe failures. `registry.ProviderRegistry.configure/configure_routing/build/check/snapshot` owns non-secret settings, credential lookup and observed health. `router.ProviderRouter.select` is deterministic trusted policy. Six named provider adapters share actual protocol codecs in `http_provider` and bounded TLS/loopback transport in `transport`; Codex retains the existing child-process path. No provider imports UI/database or grants permissions.

`conversations/models`, `repository.ConversationRepository` and `service.ConversationService` implement owned session CRUD, safe pair persistence, resume/search/export/retention and temporary defaults. `memory/models`, `repository.MemoryRepository`, `service.MemoryService` and `retrieval.retrieve` implement owned encrypted records, revisions/provenance, consent/category policy, RAM proposals and bounded lexical retrieval. Repositories depend on LocalStore and an injected cipher; production uses `security/encryption.LocalCipher` with Windows DPAPI only. These local record/provenance/tombstone boundaries support a future synchronization adapter; no cloud transport or conflict engine is implemented.

`desktop/intelligence.IntelligenceControls` extends Studio using the same serial queue and existing approval dialog. Static controls live in `frontend/legacy/intelligence.js` plus the existing index/CSS; external strings use text nodes. UI never calls provider HTTP directly. Package SQL migrations remain under `src/clydex/database/migrations/`; there is no duplicate root database directory or unnecessary future module.
