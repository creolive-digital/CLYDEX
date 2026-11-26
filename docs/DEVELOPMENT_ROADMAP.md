# Development roadmap

Source: Blueprint pp19–21 and master instructions. No dates, budgets or later-phase approvals inferred.

| Phase | Tasks / deliverable | Dependencies | Acceptance / status |
|---|---|---|---|
| 0 Baseline | P0-01 read specs; P0-02 inventory/threat model; P0-03 baseline tests/branch; P0-04 Windows/hardware benchmark | Supplied docs/repo | Static audit and 4 baseline tests complete; manual/reference hardware gate open OI-12. |
| 1 Foundation | P1-01 package/contracts; P1-02 config/SQLite; P1-03 safe logs/errors/secrets; P1-04 permissions; P1-05 bounded execution/cancel; P1-06 legacy/provider/UI adapters; P1-07 regression/security/packaging; P1-08 documentation | Baseline, incremental migration | Current authorized scope. Old entry points usable; exact approvals enforced, tests pass, gaps declared. |
| 2 Intelligence | Seven provider adapters, configured routing, histories/memory provenance and consent | Phase 1 review; provider data/cost choices | Error/cancel/local-only tests; no unapproved provider or memory activation. NOT STARTED. |
| 3 Voice | Activation modes, cinematic local TTS, language/voice contract | Phase 2; licensed voice, reference hardware | Mic privacy, stop, latency and language matrix. NOT STARTED. |
| 4 HUD | React/TS, approved humanoid/logo, modes, themes, accessible notifications | Assets OI-01; core/voice contracts | Usability, reduced motion, resource/DPI checks. NOT STARTED. |
| 5 Cloud | Ubuntu VPS/MSSQL/vector validation, auth, vault, sync | Owner infrastructure/budget/retention decisions | Auth/isolation/citations/restore/conflict tests. NOT STARTED. |
| 6 Tools | Studio, integrations, developer tools, plugins/MCP | Central permissions and scoped profiles | Per-tool consent, sandbox/isolation and integration evidence. NOT STARTED. |
| 7 Release | Setup wizard, signing, approved update, backup/recovery | Full regression and owner release governance | Fresh install/uninstall, signed package and recovery acceptance. NOT STARTED. |
| 8 Devices | Pair/revoke, client SDK; robot/mobile separately scoped | Authenticated gateways and separate hardware approval | Simulated device contracts; no physical robot now. NOT STARTED. |

P1 dependencies: 01 → 02/03 → 04 → 05/06 → 07 → 08. Each change retains legacy behavior behind adapters. Implementation status and evidence: DEVELOPMENT_PROGRESS and TESTING_AND_ACCEPTANCE. Phase 02 requires owner review of the Phase 01 checkpoint.

Checkpoint: P1-01–06 implemented and verified in the automated scope. P1-07 automated tests/builds/safe native UI and credential checks complete; live audio/account/installer/hardware acceptance remains open. P1-08 management documentation updated. Stop here for owner review; Phase 02 has not started.
