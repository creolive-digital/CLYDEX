# Development progress

## Phase 02 intake and Phase 01 hardening (2026-11-26)

Owner authorizes Phase 02 only after foundation blockers are resolved. Baseline is clean `v2` at `0c0213d5a7637ecb944eddde9a4d049f9f91e1f7`; main and v1-old are protected. All required product/management documents were reread. No remote push/merge/release is authorized for this phase.

- H-01: fix shutdown ordering so the per-user lock stays held until queue/native browser/model workers finish; test noncooperative work and replacement-instance rejection.
- H-02: bound child stdin/stdout/stderr and generated answer files, enforce timeouts/cancellation and terminate owned child processes; test output flooding, timeout and cancellation with harmless local processes.
- H-03: verify existing transactional migrations, all 76 regressions and safe Tk/WebView2 smoke. Initial results: 76 passed (2.572 s), lint passed, UI smoke passed.
- CI evidence: [run 45795129836](https://github.com/creolive-digital/CLYDEX/actions/runs/45795129836), reviewed baseline SHA, successful Python 3.11 tests/lint, both EXE builds, Inno Setup compilation and installer artifact upload. Clean installation, actual audio/accounts and reference hardware budgets remain external acceptance gates.

After H-01–03: P2-01 provider/context contracts and trusted outbound policy; P2-02 six HTTP adapters plus existing Codex, registry/config/health/streaming; P2-03 explicit routing profiles/privacy/cost/fallback; P2-04 additive SQLite migration and owner-scoped conversations; P2-05 manual/opt-in memory with provenance and bounded local retrieval; P2-06 existing engine/queue/desktop UI integration; P2-07 mocked and local HTTP boundary/security/regression tests, packaging and documentation checkpoint. Dependencies follow this order; no duplicate tool orchestrator.

Planned touched paths: core/application, processes, contracts, config, context and a provider coordinator; automation/tasks, security policy/specs, database/store and additive migrations; providers/, conversations/, memory/; desktop/studio and frontend/legacy functional controls; tests/, config templates, existing management/architecture docs. No branding, voice redesign, cloud infrastructure or archive changes.

Engineering defaults: retain Codex as the only enabled provider; never contact any provider while configuring/listing; new accounts/models blank and disabled; paid use requires explicit configuration and per-request consent; automatic memory off; temporary conversation by default. Persistent sessions/manual memories require explicit UI action. Credentials stay in Credential Manager. Tests use synthetic context and deterministic fixtures only. Specific decisions and official API sources will be recorded before activation.

H-01–03 engineering admission completed: 80 tests, lint and safe native UI smoke passed. Shutdown ownership now waits for actual native completion; owned Windows jobs and bounded child I/O close the known process gaps. SQLite baseline rollback tests remain green. Proceed to P2-01; external human/device/account acceptance remains explicitly open.

## 2026-11-26 — baseline and plan

- P0-01 complete: read all 26 PDF pages and entire master instructions; inspected embedded approved reference images.
- P0-02 complete (static): repository, dependency, concurrency, security and packaging inventory; gaps/conflicts recorded before source edits.
- P0-03 complete: verified exact e65fe46 baseline; existing four tests pass; created `v2`; preserved untracked owner documents. No pushes authorized.
- P0-04 open: live integration baseline/reference hardware/benchmark acceptance.
- P1-01 through P1-08 planned: see architecture decisions for touched files, sequence, risks and rollback.

No later-phase implementation is authorized by this record. Tests and final checkpoint will be appended with actual evidence.

## Phase 01 checkpoint — implementation delivered for owner review

Objective: establish an incremental, secure, testable core while retaining the working Windows entry points and current visual identity.

| Task | Result |
|---|---|
| P1-01 | Implemented `src/clydex` package, immutable contracts, typed events, compatibility structure and pyproject. |
| P1-02 | Implemented central validated config, runtime directory organization, transactional SQLite metadata schema and preference migration fallback. |
| P1-03 | Implemented safe error mapping, rotating structured diagnostics, allowlisted audit metadata and native Windows credential storage. |
| P1-04 | Implemented granular installed scopes, optional scope disable, exact expiring/revocable one-time approvals and private context transfer guards. |
| P1-05 | Implemented bounded serial queue/events, per-user runtime lock, cancellation and Stop control. Native interruption/rollback limits documented. |
| P1-06 | Migrated existing engine/Windows/browser/Outlook/spectrum/Studio behind adapters and root compatibility paths; extracted Codex provider. Existing widget retained. |
| P1-07 | 75 tests passed, lint/syntax checks passed, real safe UI and credential smoke passed, wheel/resources/import passed, both EXEs built. Live integration, installer and reference-hardware acceptance remain open. |
| P1-08 | All eight requested management documents, actual/target structure and AGENTS updated. Original specifications preserved. |

### Files created

- `src/clydex/{core,providers,voice,tools,integrations,security,automation,database,desktop}/` functional modules, package markers and SQL/PS1 resources; responsibilities/public APIs in architecture/PROJECT_STRUCTURE.
- `tests/test_application.py`, `test_execution.py`, `test_foundation.py`, `test_provider.py`, `test_regression.py`, `test_security.py` and package marker.
- `pyproject.toml`, `.env.example`, `.gitattributes`, `config/clydex.example.json`, `scripts/verify_windows_smoke.py`.
- Eight development-management documents and `docs/architecture/PROJECT_STRUCTURE.md`. Owner-supplied original documents added to version control unchanged.

### Files modified

- Root `clydex_engine.py`, `clydex_apps.py`, `clydex_desktop.py`, `clydex_outlook.py`, `clydex_spectrum.py` now compatibility imports; original implementation is retained in the package.
- `clydex_voice_agent.pyw` thin Studio launcher; both PyInstaller specs and `requirements.txt` updated for src/package resources.
- `studio_ui/index.html`, `studio_ui/studio.js`: exact-action review details, approve-once wording, task Stop control. No branding or avatar redesign.
- `.github/workflows/build.yml`, `.gitignore`, `AGENTS.md`, `README_SETUP.txt`.
- `clydex_widget.pyw`, original root helper PS1 scripts, themes, fonts, artwork, existing voice test file, batch launcher and Inno Setup layout retained.

### Decisions, security and performance

ADR-001–015 record branch protection, compatibility migration, trusted policy boundary, safe storage/logging, single queue/instance, initial Codex-only provider and deferred transport. Current sensitive tools and outbound context require exact consent; no provider fallback, cloud deployment, microphone background capture, memory collection or public OS API was added. PowerShell retains current-user authority. Process output capture, native interruption, audit retention and later client authentication need continued attention (OPEN_ISSUES).

Event/task growth is bounded. CPU STT, rendering and native-tool latency remain unprofiled against approved budgets. Stop cancels queued work and pending approvals and requests child-process cancellation; it cannot undo completed actions or promise instant native-call interruption.

### Verification and remaining work

See TESTING_AND_ACCEPTANCE for commands, actual outputs, resolved development failures and exact limits. Observed environment: Windows 10 kernel 10.0.19045/Python 3.13.14. Existing features were checked through the original tests, additional mock regressions, real widget controls and WebView2 startup; audio/accounts/native app behavior and fresh installation are not certified.

Known gates: missing standalone visual references; no Inno Setup on this machine; no live provider/mail/audio acceptance; no approved performance budgets, VPS/SQL/vector/voice/signing/retention decisions. Phase 02 has not started. Recommended next task is owner review plus the remaining Phase 01 live/manual acceptance matrix; after acceptance, scope Phase 02 provider routing/memory against explicit provider and data-sharing choices.

### Migration and rollback

Run `python -m pip install -r requirements.txt`; existing `python clydex_widget.pyw` and `python clydex_voice_agent.pyw` launch paths remain. Optional `python -m pip install -e ".[dev]"` enables lint. Review source changes and commits locally on `v2`; no push is authorized. Save work and switch to `main` for the original release. Runtime data is outside source and is not deleted or downgraded. Legacy registry voice preferences are left untouched. No destructive data migration was performed.

Checkpoint status: engineering implementation delivered; owner acceptance and declared manual gates pending. Stop before Phase 02. Nothing pushed remotely.

## Owner follow-up — move V1 to `v1-old/`

- Preserved all 43 original tracked baseline files from e65fe46 under `v1-old/`, verified byte-for-byte against Git archive data. Added README_ARCHIVE.md explaining independent launch/testing and provenance. No runtime data, credentials or Git metadata copied.
- Moved active shared widget/theme/hologram implementations into `src/clydex/desktop/`; original root names are compatibility launchers/imports. V2 uses its own current UI and does not import anything from the V1 archive.
- Moved active PNG artwork into `assets/legacy/`, original voice tests into `tests/test_voice_routing.py`, and removed duplicate root PS1 files (active packaged copies and original archived copies remain). Updated PyInstaller resources and documented actual layout.
- Authorization is the owner's explicit V1 organization request; Phase 02 remains untouched and no remote push is authorized.
- Follow-up validation complete: active V2 **76 tests passed**, standalone V1 **4 passed**, both versions' safe UI smoke checks passed, lint/compilation passed and both updated V2 EXEs built successfully. Archive and artwork integrity verified; existing live integration/installer acceptance gaps remain unchanged.

## Owner correction — clear leftover files from the repository root

- Removed seven obsolete root Python facades. Active voice regressions now import the package directly. No active business behavior was rewritten.
- Moved .pyw launchers and .bat shortcuts into scripts/windows, .spec files into installer/pyinstaller, Inno Setup/notes into installer/windows, desktop requirements into deployment/windows and setup guidance into docs.
- Moved the unchanged current static UI into frontend/legacy. Updated resource paths, widget-to-agent launch path, tests, smoke utility, CI and installer paths. Original V1 remains independent and unchanged.
- Added a concise root README.md. Root now contains project metadata/instructions only. Generated build/cache/release remnants were preserved outside the checkout at `%LOCALAPPDATA%/CLYDEX/tmp/repository-cleanup-20261126-150704/`.
- ADR-017 records the explicit owner authorization to retire the old root paths. Source launch commands are now `python scripts/windows/clydex_widget.pyw` and `python scripts/windows/clydex_voice_agent.pyw`.
- The interrupted push did not create remote v2; these changes remain local pending the current organization work. Main is unchanged and no later development phase was started.
- Validation completed: exactly six root metadata/documentation files, 76 V2 tests and four independent V1 tests passed, safe UI smoke/lint/compilation/JS checks passed, and both executable builds succeeded with the relocated specs/resources. Original archive and product-document integrity checks passed.
