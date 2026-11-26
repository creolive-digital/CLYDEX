# Requirements traceability

Source: Blueprint v1.1 page references; master instructions; latest owner Phase 01 and mandatory structure instructions. Status vocabulary: Implemented / Partially implemented / Not implemented / Requires refactoring / Requires technical validation / Blocked or requires owner approval. Baseline states below; Phase 1 results are appended after verification.

| ID | Source / requirement | Baseline status and evidence | Phase / task |
|---|---|---|---|
| FND-01 | pp13,21 modular headless core, preserve entries | Requires refactoring: mixed VoiceEngine/Studio | 1/P1-01,06 |
| FND-02 | master: typed request/event/tool/provider | Not implemented | 1/P1-01 |
| FND-03 | master: configuration/secrets | Partially implemented: registry/env only | 1/P1-02,03 |
| FND-04 | pp15,18 logging/audit/errors | Not implemented | 1/P1-03,04 |
| FND-05 | pp10,13 queue/cancel/backpressure | Partially implemented: busy guard/browser worker | 1/P1-05 |
| FND-06 | p15 local SQLite schema/cache | Not implemented; no sensitive cache in Phase 1 | 1/P1-02 |
| FND-07 | owner: src layout/packaging/runtime paths | Not implemented | 1/P1-01,02,07 |
| SEC-01 | p16 granular permissions/exact one-use expiry | Partially implemented: boolean approvals | 1/P1-04,06 |
| SEC-02 | pp8,16 private context/cloud boundaries | Requires refactoring: prompt instructions only | 1/P1-04,06; 2 |
| SEC-03 | p16 emergency stop, mic/camera/privacy/revoke | Partially implemented: record stop/close only | 1/P1-05; 3,6,8 |
| SEC-04 | pp16,17 path/account/plugin/device scopes | Not implemented; no plugins/device service | 1 interfaces; 6,8 |
| BASE-01 | p4 clock/weather/timer/alarm/stopwatch | Implemented in widget; live acceptance pending | Preserve/P1-07 |
| BASE-02 | p4 Windows apps/browser/Outlook/drafts | Implemented in legacy tools; centralized scopes absent | Preserve/P1-06,07 |
| VO-01 | p7 five configurable activation modes | Partially implemented: manual only | 3 |
| VO-02 | p7 VAD/silence/confidence/stop | Partially implemented: 30 s limit, VAD/confidence | 1 cancel; 3 |
| VO-03 | p7 local TTS provider/SAPI fallback/cinematic male | Partially implemented: SAPI default voice | 3 technical validation |
| VO-04 | p7 genuine spectrum/timing/visemes | Partially implemented: real audio bands, no visemes | 3,4 |
| VO-05 | p7 English/Sinhala/Singlish/Tamil | Requires technical validation: STT auto/English, voice dependent | 3 |
| AI-01 | p8 seven providers/credentials/health/models | Partially implemented: Codex only | 1 abstraction; 2 full |
| AI-02 | p8 hybrid routing/budgets/profiles/status | Not implemented | 2 owner provider/cost choices |
| AI-03 | p8 streaming/cancel/timeout/retry/local commands | Partially implemented: CLI timeout/local parser | 1 adapter/cancel; 2 |
| MEM-01 | p8 automatic/explicit memory/provenance/control | Not implemented: bounded in-process history only | 2 |
| MEM-02 | p8 SQLite cache/category sync/no secrets | Not implemented | 1 safe DB; 2,5 |
| TOOL-01 | p9 all 13 categories | Partially implemented: apps, shell/files, browser/mail | 1 contracts/policy; 6 |
| TOOL-02 | p9 typed schema/risk/scope/timeout/result | Requires refactoring: model schema but no central execution | 1/P1-04,06 |
| AUTO-01 | p10 universal studio/routines/triggers/queue | Not implemented beyond sequential plans | 1 queue; 6 studio |
| FEED-01 | p10 feeds/notifications/DND/digest | Partially implemented: widget weather/alarms only | 4,6 |
| KB-01 | p11 supported sources/import | Not implemented | 5 |
| KB-02 | p11 checksums/provenance/parse caps/version | Not implemented | 5 |
| KB-03 | p11 versioned embeddings/native SQL vectors | Requires technical validation and owner platform decision | 5 |
| KB-04 | p11 scoped citations/fact vs inference | Not implemented | 5 |
| KB-05 | p11 encrypted vault/ACL/quota/deletion/backup | Not implemented | 5 |
| DEV-01 | p12 developer console/scoped diagnostics | Partially implemented: Codex/approved PowerShell only | 6 |
| MODE-01 | p12 modes/hybrid switch/no escalation | Not implemented | 2,4,6 |
| UI-01 | pp5–6 branding/typography/avatar/modes/HUD | Requires refactoring; assets missing; existing UI preserved | 4, OI-01 |
| CLOUD-01 | pp14–15 Ubuntu/MSSQL/files/account/sync | Blocked or requires owner approval: sizing/cost/licensing/auth | 5 |
| CLOUD-02 | p15 category sync excluding notifications | Not implemented | 5 |
| API-01 | p17 authenticated local/cloud versioned interfaces | Not implemented; same-process WebView API only | 1 internal contracts; later transport |
| PLUG-01 | p17 manager/SDK/manifest/isolation/integrations | Not implemented | 6 |
| DEVICES-01 | p17 secure pair/revoke/capabilities | Not implemented; physical work explicitly deferred | 8 |
| PERF-01 | p18 adaptive resources/benchmarks | Requires technical validation; continuous canvas loop | 1 queue; 3,4,7 |
| OFF-01 | p18 offline AI/STT/TTS/cache/local operation | Partially implemented: cached STT/SAPI/tools/widget | 2,3,5,6 |
| LIFE-01 | p18 setup/update/backup/recovery/sounds | Partially implemented: installer only | 4,7 |
| TEST-01 | p20 eleven test categories | Partially implemented: 4 unit cases only | 1/P1-07; each later phase |

## Confirmed decisions D01–D58 coverage

| Decisions | Baseline classification | Tracking |
|---|---|---|
| D01,D03,D13–D20,D44–D49 | Partially implemented / Requires refactoring; approved identity not production assets | UI-01, FEED-01, LIFE-01; Phase 4 |
| D02,D07–D09 | Partially implemented / Not implemented | AI-01–03, MEM-01–02; Phase 2 |
| D04,D05,D06,D38,D50–D52 | Partially implemented / Requires technical validation; name open | VO-01–05, OI-09; Phases 2–3 |
| D10–D12 | Partially implemented | SEC-01–04, TOOL-01–02; Phases 1,6 |
| D21–D24,D26–D30 | Not implemented except shell/weather/mail subset | AUTO-01, FEED-01, DEV-01, MODE-01, PLUG-01, KB-01; Phases 4–6 |
| D25,D33–D35,D43,D53–D55 | Not implemented / Requires technical validation / Blocked or requires owner approval | CLOUD-01–02, FND-06, KB-03; Phases 1,5 |
| D31,D32 | Requires refactoring | FND-01,07, UI-01; Phases 1,4 |
| D36,D37 | Partially implemented / Requires technical validation | OFF-01, PERF-01 |
| D39–D41 | Partially implemented | LIFE-01; Phase 7 |
| D42 | Not implemented | DEVICES-01; Phase 8 |
| D56 | Partially implemented | TEST-01 |
| D57,D58 | Implemented as development process: v2/foundation first | P0/P1 management; no claim of product completion |

## Phase 01 implementation checkpoint

| ID / task | Result / implementation status | Acceptance evidence / limits |
|---|---|---|
| FND-01,07 / P1-01,06 | Implemented for foundation: src package, headless CoreApplication, UI bridge adapter, compatible root imports/entries | Application/regression tests, wheel isolated import, real Tk/WebView2 smoke; residual legacy orchestration intentionally retained. |
| FND-02 / P1-01 | Implemented: immutable context/action/provider contracts, typed events/tool inputs/result types | Canonical snapshot/digest, schema rejection, injected/unexpected args tests; general plugin JSON Schema not claimed. |
| FND-03,06 / P1-02,03 | Implemented foundation: config/templates/runtime layout, SQLite migration and preferences, Credential Manager | Validation/reopen/concurrency/rollback/newer-schema tests; native synthetic credential round-trip. No memory/history/vault persistence. |
| FND-04 / P1-03 | Implemented: safe failure categories, allowlisted rotating diagnostics and audit metadata | Secret/exception-text exclusion and allowlist tests; retention policy remains open. |
| FND-05 / P1-05 | Implemented foundation: bounded serial queue/events, runtime owner lock, stop/cancel/time budgets | Queue/concurrency/process-cancel/close tests; native noncooperative work limits OI-14. |
| SEC-01 / P1-04,06 | Implemented for current tool pathways | Deny/replay/payload/identity/expiry/racing-consume/close/disabled-scope tests; OS sandbox not claimed. |
| SEC-02 / P1-04,06 | Implemented Phase 1 cloud/privacy guard and separate private-context transfer review; overall Partially implemented | Private history/web/mail transfer tests. Per-memory/document classifications are Phase 2/5. |
| SEC-03 / P1-05 | Partially implemented overall: Stop task and approval revocation delivered | Active/pending cancel and real Stop-control smoke; camera/device/plugin controls belong to later phases. |
| AI-01,03 / P1-06 | Partially implemented overall: real Codex adapter behind provider protocol, local response validation/cancel | Provider stdin/flags/schema/temp cleanup/timeouts tested with mocks; no new provider/routing/streaming/health UI. |
| BASE-01,02 / P1-07 | Existing capabilities preserved via incremental adapters; live acceptance Partially implemented | Widget real control smoke, routing, windows, browser/tab, inbox/draft and PowerShell mocks. Live accounts/devices unverified. |
| TEST-01 / P1-07 | Partially implemented product-wide; foundation automated scope complete | 75 passing tests, lint, source syntax, JS syntax, real Tk/WebView2/credential smoke, both EXE builds and wheel resources/import. Manual release/hardware gates remain open. |

All other product requirements retain their earlier classification and delivery phase. No Phase 02–08 feature is presented as implemented. Owner review and outstanding live acceptance gates remain required before advancing.

Owner-requested organization follow-up: original V1 now resides in `v1-old/`; FND-01/07 entry-point compatibility is retained through root launchers and the active desktop package. Original voice regression cases moved to `tests/test_voice_routing.py`; the archive retains its independent original tests. See ADR-016 and PROJECT_STRUCTURE.md.
