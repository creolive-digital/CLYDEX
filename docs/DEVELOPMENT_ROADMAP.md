# Development roadmap

## Current Phase 05 disposition (2026-11-28)

P5-01–12 engineering is delivered for owner review with explicitly gated SQL/model/Linux/production acceptance. The owner approved the SQL Server 2025 and server-managed AES-GCM baseline; no hosting, paid activation or private transfer follows from that approval. See PHASE_05_COMPLETION_REPORT for implemented versus simulated/native/unverified results, remaining decisions and actual evidence.

Phase 06 remains unimplemented and requires a new owner instruction. Workflow synchronization contains inert versioned contracts only. Mobile, robot, marketplace and full automation execution are not activated. Stop at Phase 05. The removed GitHub Actions workflow stays removed; local scripts provide checks. No push/merge/tag/release.

## Current Phase 04 disposition (2026-11-27)

The explicit Phase 04 owner instruction supersedes historical checkpoint stops below. P4-01 audit/admission, P4-02 frontend/bridge, P4-03 functional screens, P4-04 reference renderer, P4-05 display modes, P4-06 startup/sounds, P4-07 shared widget/notifications, P4-08 declared verification and P4-09 documentation are implemented for local review. The authorized fallback is a labeled owner reference with an extensible renderer; facial/full-body rigging, blinking and precise lip sync remain asset-dependent, not completed features. Live voice/provider acceptance is unchanged. See PHASE_04_COMPLETION_REPORT. Stop at Phase 04; Phase 05–08 remain unimplemented/unapproved.

## Current Phase 03 disposition (2026-11-27)

Latest owner instruction supersedes historical Phase 02 stops. P3-01 admission, P3-02 audio/STT/VAD, P3-03 local TTS, P3-04 lifecycle/privacy/cancel, P3-05 activation adapters, P3-06 personality/languages, P3-07 Core/UI integration, P3-08 declared verification and P3-09 documentation are delivered in the engineering scope. Activation/voice assets and live language/acoustic/performance acceptance remain external gates, not completed models or certification. See PHASE_03_COMPLETION_REPORT for evidence and conditional capabilities. Stop at Phase 03; all Phase 04–08 rows remain future work. Historical rows below describe their original checkpoint dates.

Source: Blueprint pp19–21 and master instructions. No dates, budgets or later-phase approvals inferred.

| Phase | Tasks / deliverable | Dependencies | Acceptance / status |
|---|---|---|---|
| 0 Baseline | P0-01 read specs; P0-02 inventory/threat model; P0-03 baseline tests/branch; P0-04 Windows/hardware benchmark | Supplied docs/repo | Static audit and 4 baseline tests complete; manual/reference hardware gate open OI-12. |
| 1 Foundation | P1-01 package/contracts; P1-02 config/SQLite; P1-03 safe logs/errors/secrets; P1-04 permissions; P1-05 bounded execution/cancel; P1-06 legacy/provider/UI adapters; P1-07 regression/security/packaging; P1-08 documentation | Baseline, incremental migration | Delivered and hardened for Phase 02 admission. Exact approvals and source launcher behavior preserved; external acceptance gates declared. |
| 2 Intelligence | P2-01–09: seven provider adapters, constrained routing, owned histories/memory and functional controls | H1-01–03 hardening admission; provider data/cost choices before activation | Engineering implemented; deterministic/native acceptance and packaging recorded below. Owner/live acceptance pending. Stop at Phase 02 checkpoint. |
| 3 Voice | Activation modes, cinematic local TTS, language/voice contract | Phase 2; licensed voice, reference hardware | Mic privacy, stop, latency and language matrix. NOT STARTED. |
| 4 HUD | React/TS, approved humanoid/logo, modes, themes, accessible notifications | Assets OI-01; core/voice contracts | Usability, reduced motion, resource/DPI checks. NOT STARTED. |
| 5 Cloud | Ubuntu VPS/MSSQL/vector validation, auth, vault, sync | Owner infrastructure/budget/retention decisions | Auth/isolation/citations/restore/conflict tests. NOT STARTED. |
| 6 Tools | Studio, integrations, developer tools, plugins/MCP | Central permissions and scoped profiles | Per-tool consent, sandbox/isolation and integration evidence. NOT STARTED. |
| 7 Release | Setup wizard, signing, approved update, backup/recovery | Full regression and owner release governance | Fresh install/uninstall, signed package and recovery acceptance. NOT STARTED. |
| 8 Devices | Pair/revoke, client SDK; robot/mobile separately scoped | Authenticated gateways and separate hardware approval | Simulated device contracts; no physical robot now. NOT STARTED. |

P1 dependencies: 01 → 02/03 → 04 → 05/06 → 07 → 08. Each change retains legacy behavior behind adapters. Implementation status and evidence: DEVELOPMENT_PROGRESS and TESTING_AND_ACCEPTANCE. Phase 02 requires owner review of the Phase 01 checkpoint.

Checkpoint: P1-01–06 implemented and verified in the automated scope. P1-07 automated tests/builds/safe native UI and credential checks complete; live audio/account/installer/hardware acceptance remains open. P1-08 management documentation updated. Stop here for owner review; Phase 02 has not started.

## Owner-authorized Phase 02 continuation (2026-11-26)

The latest owner instruction supersedes the historical Phase 01 stop above. The actual clean `v2` baseline was reviewed commit `0c0213d5a7637ecb944eddde9a4d049f9f91e1f7`. H1-01–03 engineering admission resolved shutdown ownership and process-bound concerns before new features. External manual gates are recorded separately; no account/hardware acceptance was inferred.

| Task | Dependencies | Acceptance / result |
|---|---|---|
| H1-01 | Baseline 76 tests | Queue/native cleanup retains instance lock until actual termination; regression test passes. |
| H1-02 | H1-01 | Job-owned subprocesses, bounded combined output/generated files, timeout/cancel; safe native tests pass. |
| H1-03 | H1-01,02 | 80 tests, migration rollback, native UI smoke and reviewed baseline CI success; engineering admission granted, external gates open. |
| P2-01 | H1-03 | Validated provider registry, immutable configurations, Credential Manager and explicit model/capability/health settings. |
| P2-02 | P2-01 | Six HTTP adapters plus existing Codex; structured validation, streaming on HTTP, safe normalized errors/limits and synthetic adapter tests. |
| P2-03 | P2-01,02 | Manual and Fast/Balanced/Advanced/Offline priorities, capabilities/context/cost/health checks; explicit fallbacks only. |
| P2-04 | P2-03 | Shared outbound policy, compartment minimization, exact snapshots/reviews, local-only memory/history isolation. |
| P2-05 | H1-03 | SQLite 1→3 migration; encrypted owned sessions, temporary defaults, search/resume/export/retention/archive/delete. |
| P2-06 | P2-04,05 | Six memory categories, provenance/revisions, explicit consent and opt-in reviewed suggestions, bounded local retrieval. |
| P2-07 | P2-01–06 | Existing WebView controls for providers/routing/privacy/history/memory; central queue and approvals retained. |
| P2-08 | P2-01–07 | Unit/security/regression, actual synthetic loopback HTTP, safe native UI/DPAPI/credential checks, compilation/lint and packaging evidence. |
| P2-09 | P2-08 | Update all management documents, configuration guide, decisions and checkpoint report. |

Next phase remains Phase 03 voice, subject to owner review of this checkpoint and explicit voice/licensing/hardware decisions. No Phase 03 code, service activation, deployment or remote publication is included.
