# Open issues and requirement conflicts

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
