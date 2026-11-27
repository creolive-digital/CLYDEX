# Development progress

## Owner-authorized checkpoint publication (2026-11-27)

After the Phase 03 engineering handoff, the owner explicitly requested a GitHub push. Publish the existing provider-cancellation hardening and reviewed Phase 03 implementation/documentation on `v2` only; no main merge, tag or release. Pre-publication review found 67 changed/new paths relative to the reviewed Phase 02 checkpoint, no generated/runtime artifacts and no high-signal credential patterns. Local source verification remains 185 passing V2 tests plus four separate archive tests; current remote CI is not yet claimed.

## Phase 03 continuation audit and checkpoint (2026-11-27)

This continuation found `v2` at `aa084d453e41152c6c007a90a1b05c892fd72cf4` with substantial uncommitted Phase 03 implementation already present. Changes were backed up outside source and preserved. Both specifications and all management documents were reread. Main, archive and official document hashes remain protected. The earlier clean-6b8 intake below is historical evidence from the previous implementation work, not the state encountered by this continuation.

Admission repeated: isolated HEAD **135 passed** (9.805 s). GitHub API confirms Phase 02 run 45807025777 at exactly `6b8c452` succeeded through Python 3.11 checks, both EXEs, Inno compilation and artifact upload; release skipped. Current working-tree baseline: **178 tests**, one ownership-test timing failure plus consequent open-log cleanup error. The injected model/cache adapters now avoid unnecessary heavyweight imports and the test always releases/joins cleanup. No product, hardware or provider acceptance was inferred.

P3-02–07 extraction/integration was audited and completed with headless lock monitoring, action-time/privacy approval checks, canceled foreground tokens, native minimize/restore privacy, rejected muted activation, settings recovery after Stop/sleep/error and standby completion. Hidden background capture requires trusted native indicator/Stop availability; tray metadata updates independently of frontend polling. Unsupported speech warnings remain visible outside settings. Personality, memory, provider policies, trusted tool scopes and text chat remain integrated through the original Core architecture.

P3-08 safe Windows checks passed: legacy Tk/WebView2 controls, actual isolated/hidden .pyw launcher, reviewed voice settings and simulated lock shield; native English SAPI-to-RAM synthesis and joined temporary hotkey/tray registrations. Screenshot captured/reviewed with isolated Edge and network blocked. No microphone/speaker, real model inference, wake model, private content or provider account was exercised. P3-09 current setup/licensing/language/decisions/structure and completion report document the result and external gates. Full final counts/build evidence are in PHASE_03_COMPLETION_REPORT and TESTING_AND_ACCEPTANCE. No Phase 04 work, push, merge or release.

Final source run: **185 tests passed** (16.088 s), lint/syntax/UI checks passed. Speech rejection also treats high no-speech probability and missing automatic-language confidence as uncertain regardless of apparent text likelihood. Initial EXE builds passed, but checking an incremental rebuild's embedded code exposed stale PYZ caching. A fresh clean build and embedded-code check are used for final packaging evidence; existing CI/build commands already request clean builds. Final wheel contains the updated rejection code and imports in isolation.

Final clean agent build passed and its embedded confidence branch was verified directly. Both EXEs, final wheel and isolated imports passed; hashes/resource checks are recorded in the completion report and local packaging-final.json. Local Inno compiler is absent, and frozen interactive/clean-install acceptance remains open. All eight management documents, configuration/setup/structure records and the 29-created/38-modified manifest (relative to reviewed 6b8c452, including preserved changes) are complete. Phase 03 engineering checkpoint reached; no Phase 04 activation or remote publication.

## Phase 03 admission and implementation plan (2026-11-26)

Latest owner explicitly authorizes Phase 03 after admission and supersedes the historical Phase 02 stop below. Actual intake: clean `v2` at reviewed `6b8c4524353c3b7f613c068c5757dfe693b494f4`. All official specifications and management documents reread; original files/archive/main protected. PDF extraction initially hit Windows console encoding on a decorative glyph; UTF-8 extraction then completed all 26 pages. No product content was guessed or changed.

Admission P3-01: **132 tests passed** (8.196 s), lint passed. Reviewed CI [45807025777](https://github.com/creolive-digital/CLYDEX/actions/runs/45807025777) at the exact reviewed SHA: Python 3.11 tests/lint/compilation, both EXEs, Inno compilation and artifact upload passed; no release. Existing ownership/cancel/provider privacy regressions pass. Real provider/audio/voice quality/hardware/installer acceptance remains external.

Audit findings before source edits: capture/STT/SAPI/playback are still mixed into VoiceEngine; missing Whisper models may download without approval; synchronous SAPI cannot promptly cancel synthesis; no mute/lock/background gate, continuous state machine, wake/hotkey/tray activation or personality service. Preserve the existing decode confidence/routing regression contracts while extracting services.

| Task | Dependencies | Implementation / acceptance plan |
|---|---|---|
| P3-01 | Reviewed Phase 02 | Read/audit/admission complete; newly discovered blockers addressed before dependent features. |
| P3-02 | P3-01 | Typed audio/STT/VAD/device/event interfaces, bounded transient capture, silence/noise/confidence checks, local-only model loading and explicit model-download review. |
| P3-03 | P3-02 | Local TTS interface, cancellable SAPI compatibility, actual PCM playback/spectrum, optional separately installed/licensed neural voice adapter. No cloud TTS. |
| P3-04 | P3-02,03 | Conversation lifecycle, half duplex, follow-ups/inactivity, mute/Stop/lock/background privacy and owned shutdown. |
| P3-05 | P3-04 | Manual/continuous/hotkey/tray activation; real local custom wake adapter gated on supplied licensed/validated Hey CLYDEX model. No generic wake model renamed as CLYDEX. |
| P3-06 | P3-01 | Independent personality profiles/response policy, encrypted optional addressing, independent recognition/response/synthesis languages; no permission escalation. |
| P3-07 | P3-02–06 | Reuse Core queue/coordinator/memory/executor and existing frontend/legacy controls; preserve text and entry points. |
| P3-08 | P3-07 | Deterministic audio/state/security/regression tests, safe native synthesis/metadata/UI where available, compilation/lint/packaging. No ambient capture or speaker playback without authorization. |
| P3-09 | P3-08 | Update all management/architecture/setup records and PHASE_03_COMPLETION_REPORT with exact capabilities, licensing, limits and owner gates. Stop before Phase 04; no remote publication authorized. |

Planned touched paths: functional `voice/` services and `personality/`; existing core application/legacy adapter/coordinator/event/spec boundaries; desktop voice settings/hotkey/tray adapters; current static frontend; tests, optional dependency/build metadata and docs. No root business logic, archive changes, brand replacement, public endpoint, cloud/robot/full HUD work. SQLite technology/schema remain unchanged unless a proven need is recorded.

Engineering defaults: microphone disabled/muted, background/wake/continuous/hotkey/tray activation off; no raw audio files or ambient retention; half duplex; no automatic model downloads. Keep SAPI installed-voice fallback, without claiming cinematic quality or Sinhala/Tamil pronunciation. Optional custom wake and neural artifacts require explicit owner selection/licensing/validation; implemented adapters will not be reported as live-validated models. Voice commands never approve sensitive actions.

P3-01 follow-up blocker found by expanded cancellation tests: Phase 02's cross-thread HTTP socket shutdown could intermittently leave a Windows response read blocked (4 failures in a 30-run focused reproduction, despite initial 132-test admission passing). Replaced that mechanism with cancel/deadline-polled nonblocking socket I/O on the owning thread, retaining stdlib HTTP framing and certificate-validated TLS. Focused stress is now 30/30 passing; deterministic post-HTTP/1.0-facade release, chunked framing and locally verified TLS cancellation tests pass. No real provider contacted. OS DNS delay remains explicitly unverified/owned. This is a newly discovered preexisting foundation defect, not successful live provider evidence.

## Phase 02 engineering completion checkpoint (2026-11-26)

Objective: extend the single existing Core with multi-model intelligence, persistent owned conversations and consented personal memory after resolving Phase 01 engineering blockers. H1-01–03 and P2-01–09 are complete in the declared automated/native scope. **132 tests pass**, lint/compilation/JS checks pass, native Tk/WebView2/DPAPI/synthetic credential checks pass, wheel/isolated imports and both EXE builds pass. Details and the complete changed-file manifest are in PHASE_02_COMPLETION_REPORT.md and TESTING_AND_ACCEPTANCE.md.

Local commits: `3d38311` shutdown/process hardening; `023fb4d` failed job-assignment/descendant verification; `fe6f969` provider/data/UI implementation; `e0eb512` original cost-ceiling protection across fallback. Documentation/checkpoint changes follow these locally. No push, merge or release; main, the independent archive, approved art and supplied specification bytes remain unchanged from intake. OI-24 qualifies older archive provenance claims: 31 text files already differed from original V1 Git blobs only in CRLF endings.

- P2-01/02: Codex default preserved; six opt-in HTTP adapters, immutable registry/configuration, explicit model/capability/health, safe auth/limits/schema validation/streaming. Current official protocol references and provider dependencies are recorded; no new SDK dependency or selected model invented.
- P2-03/04: manual/four-profile routing, observed health and capability/context/budget filters; shared outbound compartments, local-only memory and derived-history isolation, same-policy explicit fallbacks, original per-request ceiling and fresh exact review; no side-effect replay.
- P2-05: transactional SQLite 1→3 with settings/audit preserved and failed-batch rollback; DPAPI session payloads, temporary default, resume/search/title/archive/delete/export/retention controls. Only synthetic profiles used for migration tests.
- P2-06: six memory categories, provenance/ownership/status/timestamps, revisions, review/correction/forget/disable, local retrieval and opt-in literal suggestions with per-item review. Automatic suggestions remain off in defaults and no owner profile was enabled.
- P2-07: functional legacy UI controls use the existing queue/approval dialog. No full HUD, avatar replacement, voice redesign, cloud service, plugins or devices.
- P2-08/09: full regressions, actual synthetic loopback HTTP, native safety checks, packaging, CI check updates and all eight management documents/AGENTS/actual-target structure maintained. No new remote CI run is claimed.

ADRs 018–028 record scope, ownership, codecs, routing, outbound policy, encrypted local data, conservative memory collection, derived-context privacy, functional UI and bounded native behavior. P2-08 evidence distinguishes simulation from real native integration. Existing voice/tool paths are regression-tested; actual audio/accounts/browser/mail/hardware usability remain unverified. Socket cancellation is verified; OS DNS/connect may still delay timeout completion while Core ownership remains held.

Remaining owner gates: review this checkpoint, choose actual models/accounts/prices/retention and provider data policies, authorize live credentials/paid/private tests and optional automatic suggestions, validate local-only Ollama, accept live Windows/audio/UI/hardware behavior and current installer/frozen flows. Missing reference assets, audit retention, signing/recovery and reference budgets remain open. Phase 03 readiness is architectural only; await owner review plus local voice/licensing/language/hardware decisions. **Stop at this Phase 02 checkpoint.**

## Phase 02 intake and Phase 01 hardening (2026-11-26)

Owner authorizes Phase 02 only after foundation blockers are resolved. Baseline is clean `v2` at `0c0213d5a7637ecb944eddde9a4d049f9f91e1f7`; main and v1-old are protected. All required product/management documents were reread. No remote push/merge/release is authorized for this phase.

- H-01: fix shutdown ordering so the per-user lock stays held until queue/native browser/model workers finish; test noncooperative work and replacement-instance rejection.
- H-02: bound child stdin/stdout/stderr and generated answer files, enforce timeouts/cancellation and terminate owned child processes; test output flooding, timeout and cancellation with harmless local processes.
- H-03: verify existing transactional migrations, all 76 regressions and safe Tk/WebView2 smoke. Initial results: 76 passed (2.572 s), lint passed, UI smoke passed.
- CI evidence: [run 45795129836](https://github.com/creolive-digital/CLYDEX/actions/runs/45795129836), reviewed baseline SHA, successful Python 3.11 tests/lint, both EXE builds, Inno Setup compilation and installer artifact upload. Clean installation, actual audio/accounts and reference hardware budgets remain external acceptance gates.

Current task IDs are consolidated in DEVELOPMENT_ROADMAP: P2-01 registry/configuration; P2-02 adapters; P2-03 routing; P2-04 outbound security; P2-05 conversations/migrations; P2-06 personal memory; P2-07 desktop controls; P2-08 verification; P2-09 documentation. H-01–03 and H1-01–03 refer to the same admission gates. Dependencies follow this order; no duplicate tool orchestrator.

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
