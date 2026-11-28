# Open issues and requirement conflicts

## Phase 06 checkpoint issues (2026-11-28)

| ID | Engineering disposition | External / remaining acceptance |
|---|---|---|
| OI-51 | Selected trusted adapters, fixed schemas and process/socket ownership implemented | Same-user filesystem races, OS DNS/native interruption and completed-effect limits remain; no OS sandbox claim |
| OI-52 | Workflow engine/editor, disabled versions/session arming, bounded scheduling/receipts | Real voice/model drafting, DST/long-idle/user accessibility and sustained event stress remain qualification |
| OI-53 | Local plugin manifest/install/trust/hash/owned runtime implemented | Hostile third-party code must not be enabled; lower-privilege containment and richer dynamic SDK extensions remain future reviewed work |
| OI-54 | Official modern MCP HTTP and service codecs tested on fixtures/loopback | Legacy MCP/stdio, OAuth onboarding, external accounts/subscriptions and live sends/control remain unavailable/unverified |
| OI-55 | Native SQL/camera/MQTT adapters optional, explicit, disabled/gated | Owner-selected dependencies/profiles/devices, actual SQL TLS/least privilege and hardware qualification pending; no real SQL/device used |
| OI-56 | Webhook verification/source event contracts and feed-derived events implemented | No public/local HTTP ingress listener or automatic native/email subscription delivered; provider signature mapping/approved ingress remains partial |
| OI-57 | Scope recheck and ordinary-chat catalog compartment regression corrected | Final regression evidence in Phase 06 report; baseline admission was green |
| OI-58 | V2 workflow sync/import and connected deletion disabling implemented | Multi-device live/offline qualification; a disconnected client cannot immediately learn revocation |

All Phase 03 acoustic/wake/language, Phase 04 matching rig and Phase 05 SQL/embedding/VPS/production gates remain open. Automatic GitHub Actions remains removed. No deployment/publication is implied.

## Phase 05 checkpoint disposition (2026-11-28)

| ID | Engineering disposition | Remaining owner / external acceptance |
|---|---|---|
| OI-41 | SQL Server 2025-only TLS adapter, generated 26-table migration/checksum/empty rollback, test-only simulated repository and guarded native suite. | Production edition/license, Ubuntu build/CA/hardware, actual native migrations/locking/vector/restore. Existing workstation SQL untouched; no SQL image/EULA accepted. |
| OI-42 | Blind keyword retrieval works on synthetic fixtures; optional exact local model digest and encrypted native vector scan are implemented. | Owner selects/licenses/installs a model, validates languages/quality and SQL native distance/performance. Fixed loopback model service needs a reviewed container networking arrangement before activation. |
| OI-43 | Approved server-managed AES-GCM and independent recovery exports; no E2EE/DPAPI cross-device claim. | Operator key custody, live master/auth rotation procedure, retention, disk/TDE policy, passphrase recovery and compromise response. Losing keys/exports can lose content. |
| OI-44 | Private non-root Compose/nginx/TLS/SQL templates and bounded metadata logging/limits. | No Linux image/service deployed; actual TLS/proxy trust, firewall, least privilege, penetration testing and capacity acceptance remain open. Per-process limiter assumes one API process. |
| OI-45 | UTF-8, PDF text layer, OOXML, saved HTML and notes extracted; images/WAV stored with explicit status. | No OCR, audio inference, live URL crawl, legacy Office conversion or exhaustive hostile parser certification. JPEG checks are container signatures, not a decoder guarantee. |
| OI-46 | Actual encrypted logical export/restore on synthetic isolated SQL simulation, tamper rejection and revoked restored sessions. | Native SQL `.bak` and logical restore/identity handling, Linux filesystem/crash recovery and large-scale streaming exports. Logical format caps at 256 MiB/100k rows per table; reconcile any crash-orphan encrypted files during operator maintenance. |
| OI-47 | Actual source WebView2 screens, preserved legacy widget/UI and clean frozen startup/resources verified. | Native picker gestures, physical lock/mixed-DPI/accessibility, Inno/fresh install/signing and long-run acceptance. Legacy smoke emitted a WebView2 Crashpad metrics temporary-directory cleanup warning; checks/shutdown passed, but complete browser-temp cleanup is not claimed. |
| OI-48 | Manual opt-in categories, immutable idempotent operations, conflicts/tombstones, DPAPI queue/cache and reviewed atomic imports. | Real multi-device/offline stress and owner conflict/retention policy. Preferences/metadata replicas do not imply automatic runtime capture changes; workflows remain inert Phase 06 contracts. Offline revocation is observed only on reconnection. |
| OI-49 | Final review corrected missing cloud HTTP runtime dependency, stale-replay cache invalidation and duplicate generated SQL constraint names; tests/packaging/local scripts cover these. | Linux wheel/image resolution and native SQL performance remain unverified; no claim of production readiness follows from local passing tests. |

Previous OI-25–29/32 and OI-34–40 acceptance qualifications remain applicable. Phase 05 supersedes historical scope stops, without claiming acoustic/model/rig/production acceptance. No automatic CI, remote push or public deployment.

## Phase 04 checkpoint disposition (2026-11-27)

| IDs | Engineering disposition | Owner / external acceptance |
|---|---|---|
| OI-01,34 | Both exact approved reference PNGs now supplied/preserved. React presents the exact face with a labeled reference fallback and licensed local fonts/icons. Renderer never substitutes a generic face. | Original production artwork/redistribution provenance and matching optimized rig/bones/morphs/animations still needed. Blink, facial/head articulation, emotion and full body remain incomplete. |
| OI-35 | Six native modes share one Core/window/tool state; tray is reviewed, pending review restores a full window; geometry supports logical negative monitor coordinates. | Mixed-DPI/multiple-monitor hardware matrix, screen reader, taskbar/work-area behavior, long-idle and physical Windows lock/disconnect acceptance. Floating mode is framed/on-top, not transparent compositor integration. |
| OI-36 | Frame-rate/particle/detail controls, idle/focus/gaming reduction, minimized/reduced-motion suspension and actual WebGL context-loss fallback verified. | Reference-hardware long-run CPU/GPU/RAM/thermal/latency and live audio synchronization benchmarks. Python working set excludes WebView subprocesses; global CPU is not app CPU. Lazy Three chunk exceeds Vite's advisory 500 kB warning threshold. |
| OI-37 | Procedural original cue categories and generic native tray balloons implemented; sound muted by default, DND/lock/background protected. | Audible volume/quality and assistive notification acceptance; browser autoplay requires gesture and shutdown cue is best effort. No OS notification history content is persisted. |
| OI-38 | Local React/TS tests/build and PyInstaller integration updated; legacy fallback retained. Windows MIME registry `text/plain` defect and startup timer-reset defect fixed and covered. | No Phase 04 remote CI because no push authorized. Inno compiler absent locally; fresh install/uninstall and signed release remain external. Supplied reference rights require owner confirmation before redistribution. |
| OI-39 | One full verification run under concurrent workloads hit Windows temporary-directory sharing failure after the existing descendant-process assertions; isolated six hardening tests and subsequent complete suite passed. | Cause not established as a live descendant regression; retain evidence and monitor recurrence. No test was weakened or arbitrary cleanup sleep added. |
| OI-40 | Native active-timer mode test exposed an intermittent hang in PyWebView's worker-thread TopMost setter. UI-thread dispatch added, covered by an affinity regression test and actual native mode repetition. | Continue native long-run mode/driver stress acceptance; synthetic tests alone cannot qualify Windows message-loop behavior. |

Phase 03 acoustic/model/language/wake/provider gates OI-25–29,32 remain open. Stop at Phase 04 review. No paid activation, private transmission, large asset download, push/merge/tag/release or later phase is authorized by this implementation. Older phase-stop/asset-missing statements below are historical.

## Phase 03 checkpoint disposition (2026-11-27)

| IDs | Engineering disposition | External owner/technical acceptance |
|---|---|---|
| OI-25 | Implicit model downloads removed; complete local cache required; exact reviewed anonymous preparation with model/directory/storage/network disclosure. | Owner approves actual selected model preparation; no model downloaded or real inference tested here. Native download cancellation can wait for library cleanup. |
| OI-26,09 | Local custom-wake/Piper interfaces, licensed artifact manifests/fingerprints, SAPI fallback and no invented name/voice. | No validated Hey CLYDEX model, original cinematic voice or redistribution package supplied. Owner selects/licenses/auditions assets and measures false activations. Wake is gated, not claimed working acoustically. |
| OI-27 | Independent recognition/response/synthesis languages, actual SAPI metadata and visible text-only/English-notice fallback. | Only English SAPI voices installed; Sinhala/Tamil/Singlish recognition/pronunciation and all actual neural capabilities unverified. |
| OI-28,14 | Separate finish vs cancel, async SAPI purge, owned PCM playback/process/model cleanup and foreground token cancellation. Repeated reviews recover after Stop/sleep/error. | Live driver/COM/STT cancellation remains cooperative; completed effects are not undone. No spoken full-duplex barge-in/AEC. |
| OI-29 | Opt-in/muted defaults, bounded transient buffers, half duplex, Core-owned lock/session watcher, action-time guards and hidden-background tray/indicator checks. | Human lock/disconnect/hidden/long-idle UX, acoustic feedback and physical access/spoof testing remain open. No real ambient recording or speaker test performed. |
| OI-31 | Intake synthetic ownership test failed intermittently because injected adapters still imported heavy Whisper dependencies before a two-second wait; failure cleanup was also incomplete. Both corrected and covered. | This was an intake working-tree verification defect, separate from the passing isolated 135-test committed foundation. |
| OI-32 | Native hotkey/tray lifecycle and real legacy voice controls verified in safe scope; optional wake code collected only when installed for the build. | Standard frozen build has no optional wake runtime/models. Native activation by a real key/menu, optional frozen runtime, Inno/fresh install and acoustic use remain acceptance gates. |
| OI-33 | Incremental PyInstaller rebuild reused stale PYZ code despite reanalysis; embedded bytecode inspection detected it. Fresh clean build passed and final embedded rejection branch verified. | Continue using clean builds/fresh work directories and embedded-code checks. Existing CI/build commands already use `--clean`; this is a resolved local packaging finding, not successful frozen interaction evidence. |

OI-01/07/10/12/17–24 remain applicable as qualified below. Phase 03 authorization supersedes the historical Phase 02 stop; stop now at the Phase 03 engineering checkpoint. No provider/private/paid activation, push, merge or release is authorized.

## Phase 03 intake

- Latest owner authorizes voice/personality implementation after engineering admission. Phase 02 CI 45807025777 succeeded; historical no-current-CI statements below are superseded for that reviewed commit. New Phase 03 code is not authorized for push/merge/release.
- OI-25: existing model loader silently downloads a missing Whisper model. Remove implicit download; add explicit reviewed model preparation with storage/network disclosure. Cached loading must remain local, including tokenizer/config closure.
- OI-26: no owner-approved validated Hey CLYDEX wake model or cinematic neural voice is supplied. Evaluate current official local engines and implement real gated adapters; keep activation disabled and SAPI working. Do not relabel a generic detector or voice as approved/validated.
- OI-27: installed SAPI voices and local neural models may not support Sinhala/Tamil/Singlish. Separate recognition/text-response/synthesis preferences; query actual installed metadata and provide visible text-only/explicit fallback. Native pronunciation/false-activation/quality/performance tests remain owner/hardware gates.
- OI-28: baseline recording stops into transcription and synchronous SAPI lacks cooperative synthesis interruption. Separate finish-recording from cancel/mute, retain ownership of native work, and prevent playback or uncertain/ambient audio from authorizing subsequent effects.
- OI-29: always-listening creates a new microphone privacy surface. Require opt-in, visible state, mute/Stop, lock/hidden-window policy and bounded transient buffers; no ambient persistence or cloud wake processing. Initial conversation is half duplex, not AEC/full duplex.
- OI-30: expanded stress exposed a preexisting intermittent Windows HTTP close/read cancellation race. Resolved with owner-thread nonblocking connect/TLS/send/read polling, standard HTTP framing and new deterministic HTTP/1.0/chunked/verified local TLS tests. 30/30 focused cancellation repeats pass. Native DNS remains OI-18; no external provider/private content used.

## Current Phase 02 disposition (supersedes historical rows where stated)

| ID | Current issue / resolution | Owner or technical gate |
|---|---|---|
| OI-02,04 | Latest owner explicitly authorizes Phase 01 hardening then Phase 02. Foundations passed engineering admission. | Resolved for this scope; stop before Phase 03. No push authorized. |
| OI-08,15 | Reviewed baseline CI 45795129836 passed Python 3.11, both EXEs and Inno compilation. Current work is local, so no new CI result exists. | Local compiler still absent; current installer compilation, clean install/uninstall and frozen live flows remain unverified. Default `py` remains broken; use `python`. |
| OI-13 | Child I/O and answer-file bounds, deadline/cancel and owned descendant cleanup implemented and tested; native shutdown now retains the instance lock. | Broad dependency pinning/signing/updater and account scope review remain later release work. |
| OI-11,17 | Provider configuration/budget and conversation retention controls implemented; automatic memory off, temporary default, no real keys or live inference used. | Owner selects actual models/accounts/prices/retention, permits live tests/private transfer and elects automatic suggestions. Audit retention still unresolved. |
| OI-18 | Established HTTP sockets honor deadline/cancel; OS DNS/connect may delay completion beyond configured timeout. | Native DNS interruption is not certified. Queue/instance remains owned until completion, preventing overlap. Test on target networks before live acceptance. |
| OI-19 | Local Ollama can itself proxy cloud models. Literal loopback and cloud-name rejection alone cannot prove locality. | Owner runs server with OLLAMA_NO_CLOUD=1 and confirms local model/deployment; no endpoint contacted during development. |
| OI-20 | Account/model/schema compatibility and provider-side retention, billing, OpenRouter upstream policies not live-verified. | All new adapters disabled; real credentials, paid calls and private context require explicit owner authorization. Listed model does not prove successful inference. |
| OI-21 | Secret-pattern filtering cannot identify every possible private/financial/mail value. | Temporary default, explicit saving, DPAPI, sensitive-turn exclusion and review reduce exposure; owner must avoid storing secrets. Deletion does not revoke exports/backups/provider-held data. |
| OI-22 | Bounded history/retrieval and local DPAPI encryption are deliberate first local implementation. No vector search/sync/cross-device DPAPI recovery. | UI lists 500 recent sessions/searches 10,000 recent messages; resume 100; model window six; export full session up to 8 MiB allowance; 1,000 active memories. Later expansion needs profiling/design. |
| OI-23 | New functional settings/history/memory controls passed safe native startup/bridge checks. | Human DPI/keyboard/screen-reader usability, large approval payloads and frozen executable interactions remain owner acceptance. |
| OI-24 | Historical archive notes claim raw byte identity with e65fe46. Current verification finds 31 preexisting CRLF-only text differences from those original blobs. All 43 original archived files are byte-identical to reviewed 0c0213d. | Record provenance clarification; protected archive remains untouched. No substantive V1 content difference detected after newline normalization. |

OI-01 approved standalone reference assets remain missing; branding/artwork unchanged. OI-07 trusted-adapter/OS sandbox boundary, OI-09 voice selection, OI-10 hosting/SQL decisions, OI-12 hardware performance and OI-14 native rollback limits remain open. No blocker is hidden as successful live verification.

| ID | Issue / conflict | Disposition / dependency |
|---|---|---|
| OI-01 | Both specified standalone approved visual reference PNGs are missing. Blueprint embeds screenshots, not production assets. Existing UI differs from approved final branding. | Record; preserve current artwork. Owner supplies references and licensed production assets before Phase 4. No invented replacement. |
| OI-02 | Blueprint p21 requests owner review of plan before broad implementation; latest owner explicitly authorizes independent Phase 01. | Resolved: execute bounded foundation only, stop before Phase 02; no remote push. |
| OI-03 | Old AGENTS describes flat layout/no tests/no Git; actual baseline has Git, unittest, packaging and expanded tools. | Update instructions to actual state and approved incremental src layout. |
| OI-04 | Master instructions put provider interfaces/SQLite in Phase 1; roadmap p19 lists full routing/memory in Phase 2. | Implement interfaces + existing Codex adapter + SQLite settings/audit foundation only. No new providers, memory capture or sync. |
| OI-05 | Separate background service/authenticated FastAPI/React target versus safe incremental existing WebView bridge. | In-process headless application service now; no HTTP listener. Transport/process split and React deferred; document contracts. |
| OI-06 | Current low-friction sensitive reads/drafts conflict with granular authorization requirement. | Centralize one-time scope review, including sensitive context leaving PC. Preserve capability with extra explicit approval. No silent widening of permissions. |
| OI-07 | PowerShell has full current-user authority; approvals cannot constrain arbitrary scripts or prevent malicious native code running as the user. | Display exact script, bind consent, no elevation; document trusted adapter boundary. OS-level sandbox/scoped tool replacement needs separately reviewed design. |
| OI-08 | Default `py` points at missing 3.14; working Python is 3.13.14. | Record environment failure; use `python`. Do not modify user's Python installation. CI 3.11 verification pending. |
| OI-09 | Preferred name unspecified; selected cinematic male local voice and Sinhala/Tamil quality unvalidated. | Neutral greeting; Phase 3 owner/technical validation. |
| OI-10 | VPS host/region/budget/backup target; SQL Server version/edition/Linux/licensing/native vectors unresolved. | Phase 5 gate; no alternate database/vector service, deployment or spend. |
| OI-11 | Provider accounts/models/budgets/data rules, retention/auth/recovery and signing decisions open. | Owner choices before corresponding feature activation. No keys collected now. |
| OI-12 | Reference hardware, numeric performance targets and live Windows smoke tests incomplete. | Measure local foundation tests separately; do not claim hardware acceptance or production readiness. |
| OI-13 | Broad dependency ranges, no signed installer/updater, Graph scopes broad, child-process output not bounded while capturing. | Track security/release hardening; no dependency churn or account-scope changes in foundation. |
| OI-14 | Cooperative cancellation cannot roll back completed effects or instantly interrupt COM, native driver calls or STT inference. | Prevent subsequent actions; cancel approval waits/queued work/provider process where feasible. Surface limits and manual checks. |
| OI-15 | Inno Setup is not installed on the verification workstation. | Both PyInstaller EXEs built; full installer compilation, fresh install/uninstall and frozen-app live flows remain release/manual gates. CI configuration updated but not remotely run. |
| OI-16 | Core currently runs in-process with the existing desktop bridge, guarded by a per-user runtime lock. No versioned FastAPI/IPC server is running. | Deliberate incremental boundary, not a replacement technology. Authenticated transport/process separation remains to be delivered before additional clients. A second agent instance is refused; focus-existing-instance UX is future lifecycle polish. |
| OI-17 | Audit metadata retention is not yet owner-selected. | Diagnostic logs rotate (1 MiB × 4); audit metadata is not silently purged. Set retention/backup requirements before long-term data/history rollout. |

## Phase 01 resolutions

- OI-03 resolved: AGENTS updated for actual Git/tests/packaging and approved src architecture.
- OI-06 resolved for existing assistant pathways: central exact-action authorization, sensitive reads/drafts/context transfers, replay/expiry/revocation checks and optional disabled scopes. New tool categories remain subject to their own later-phase tests.
- Credential integration defect discovered during implementation: native pywin32 CredWrite expects Unicode text rather than bytes on this workstation. Corrected; real synthetic write/read/delete smoke passed and mock contract now checks text. This was a new development issue, not a baseline failure.
- Missing build backend in the initial `--no-build-isolation` attempt was an environment/tooling gap. Standard editable install succeeded; setuptools/wheel/lint/PyInstaller installed for verification. No existing runtime dependency versions were deliberately changed.
