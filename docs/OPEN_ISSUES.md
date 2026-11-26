# Open issues and requirement conflicts

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
