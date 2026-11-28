# Phase 05 — Cloud Infrastructure and Knowledge Vault

Publication update: after the engineering handoff below, the owner explicitly requested a GitHub push. The completed checkpoint is authorized for commit/publication on `v2` only. The historical uncommitted/unpublished/no-push statements describe the original handoff; they do not restrict this subsequent publication. No deployment, main merge, tag, release, workflow recreation or Phase 06 work is authorized. Publication review additionally corrected duplicate generated SQL constraint names before any native migration/deployment. Canonical DDL, cloud tests/lint/compilation and package artifacts were reverified: 28 cloud tests passed and one native SQL test remains skipped. Desktop/frontend/native evidence and external acceptance gates are unchanged.

Date: 2026-11-28. Branch: `v2`, based on reviewed `f2b1a094252c7db76c73812ff451fdc27bcf9263`; Phase 04 checkpoint `d39e1d58ba1d5ed19e4b199ac354fb5db90408e8`. This is a **local engineering owner-review checkpoint**, not a deployment or production-acceptance claim. Changes remain uncommitted/unpublished. No push, merge, tag, release or automatic GitHub Actions workflow was created.

The owner explicitly approved SQL Server 2025/Ubuntu GA exact vectors and server-managed AES-256-GCM envelope encryption with separate keys and owner-held recovery exports. The VPS can decrypt for ingestion/search; this is **not E2EE**. Production edition/licensing, hosting, public exposure, model installation and private-data activation remain separate owner decisions.

## Admission and preservation

Read both official specifications, AGENTS, Phase 02–04 reports and development/architecture/provider/voice/UI documents. Inspected Core/queue/lifecycle, SQLite, coordinator/providers/outbound policy, conversations, memory, personality, desktop bridge/frontend and assets. Admission: **201 Python tests passed (17.533 s)**, **16 frontend tests passed (24.82 s)**, TypeScript/build passed (Vite 8.64 s). Reviewed Phase 04 native/packaging evidence and unresolved privacy/storage/lifecycle gates.

The initial working tree was clean on `v2`. Main, the independent archive, both official specifications and approved logo/avatar bytes are preserved. The existing workstation SQL service was not used or modified; no SQL image/license or production database was activated. Runtime/test/build data lives outside the repository. The owner-removed automatic build workflow remains absent; local scripts provide verification. Earlier acoustic, wake/model, language and production-rig acceptance is unchanged.

## Completed engineering tasks

| ID | Delivered implementation |
|---|---|
| P5-01 | Foundation audit/regression admission, official SQL/Linux/vector/license reconciliation and recorded owner baseline |
| P5-02 | Independent FastAPI distribution, 31 REST path contracts, authenticated OpenAPI, limits, safe errors/logging and owned lifecycle |
| P5-03 | SQL Server-only production adapter, 26-table versioned T-SQL, indexes/constraints, transactional operator migration/checksum/empty rollback and guarded native suite |
| P5-04 | Argon2id provisioning/login/recovery, short access/hashed rotating refresh/replay revocation and scoped pairing/device rotation/revocation |
| P5-05 | Owner-isolated encrypted UUID storage, quotas/checksums/idempotency, versions, authenticated downloads and retryable deletion |
| P5-06 | Bounded parser/process/job pipeline, literal UTF-8/SQL/code, PDF text, OOXML, saved HTML and notes; explicit image/audio processing limitations |
| P5-07 | Keyword ranking/citations, licensed installed-local-model adapter and gated native exact vector path; RAG through existing coordinator/outbound approvals |
| P5-08 | Disabled-by-default categories, DPAPI offline queue/inbox/cache, idempotency/conflicts/tombstones, account binding and atomic reviewed source imports |
| P5-09 | Functional React account/status, vault/search/cache, devices and synchronization screens through the same three-method HUD bridge |
| P5-10 | Private Linux/Docker/nginx/TLS templates, operator tooling, encrypted logical export and actual isolated synthetic restore |
| P5-11 | Expanded Python/cloud/frontend tests, actual loopback TLS, native Windows screenshots/modes/legacy checks and local package verification |
| P5-12 | Seven requested design/API/deployment/completion documents, diagrams, screenshots, tracking updates and declared acceptance gates |

These IDs mean engineering within the stated boundaries, not completion of the native/deployed/model acceptance items below.

## Backend, database and security

The separate `clydex-cloud` package shares headless contracts/parsers, never starts a desktop/AI/voice engine and exposes no Windows operating-control endpoint. The desktop reuses one Core/coordinator/supervised queue. Cloud is disabled and all sync categories are off by default. Invalid cloud configuration does not prevent local startup.

API ownership comes only from validated credentials, never caller-supplied owner fields. Accounts/devices/sessions are checked on every authenticated request. Refresh reuse revokes the session family; recovery rotates the one-use code and revokes sessions. Pending pairing requires independent account approval; device scopes cannot grant desktop control. The HUD never returns reusable tokens, stored API keys or arbitrary paths/routes/Python/shell dispatch. Passwords bind exact reviews by digest and are cleared from the form.

SQL Server major 17, verified ODBC 18 TLS, bounded pool/connect/query/lock waits, parameterized statements and SERIALIZABLE transactions are implemented. Canonical packaged migrations cover accounts, keys, devices, sessions/revocations, preferences, conversations/messages, memory revisions, collections/documents/versions/chunks/embeddings, synchronization/change tracking/tombstones, jobs, audit and backup metadata. Startup never migrates or provisions accounts. **Actual SQL Server DDL, locking/deadlock, exact-vector and native restore verification remain pending.** SQLite is injected only in explicit tests and is labeled simulation; it is not a substituted cloud primary.

Private profiles/content/chunks/vectors/sync payloads/files use owner/role-bound AES-GCM envelopes. Keys live separately from SQL/files; passwords and reusable refresh credentials are not stored plaintext. Blind HMAC term indexes leak within-owner equality/frequency, documented as a tradeoff. Logs contain request metadata, not filenames, queries, bodies, credentials or private text. Upload/header/JSON/rate/concurrency/index/job limits are enforced. Lock, privacy, Offline routing, disabled scopes, exact approval and cancellation remain authoritative. Completed remote effects cannot be undone by Stop.

## Documents, retrieval and citations

| Source | Checkpoint support |
|---|---|
| Text/Markdown/code/SQL/structured UTF-8 | Literal extraction/chunks; never executed |
| PDF | Text layer with page/chunk references; encrypted PDFs rejected, scanned PDFs need OCR |
| DOCX/XLSX/PPTX | Actual bounded OOXML text/cached values and paragraph/cell/slide locations; no macro/formula execution |
| Saved HTML and personal notes | Visible text/explicit note title; no live URL/resource fetch or scripts |
| Selected folders | Bounded explicit native snapshot, no watcher/unrestricted scanning |
| PNG/JPEG and PCM WAV | Encrypted storage/container metadata; `needs_ocr` / `needs_transcription`, no inference claim |
| Legacy Office, archives, other media, live web crawl | Unsupported; explicit trusted conversion or later approved implementation required |

`pypdf`, `defusedxml`, stdlib parsers and pinned OSS service dependencies are used; installed license metadata is recorded in the design documents. Microsoft SQL/ODBC production terms remain separate. Parsers run in an owned timeout/JSON-bound process; Linux resource limits are not an OS sandbox or an antivirus guarantee. Jobs cannot publish after cancellation/deletion/version changes. Default original-file quota is 100 MiB/account; reported bytes do not equal total SQL/VPS disk usage.

Keyword retrieval/citation source IDs, version/revision, filename, source location and actual excerpts are verified on synthetic fixtures. The final API has a typed citation response matching the frontend. Private RAG excerpts enter the existing coordinator, at most five/10,000 characters. Empty evidence skips inference. External-provider transfer needs the existing exact private-context review; offline questions force a local provider. Reference membership is validated; factual entailment and live AI quality are not claimed.

Semantic retrieval is implemented behind an explicitly licensed installed local model/digest/dimension gate and SQL Server GA `VECTOR_DISTANCE`. Vectors remain encrypted at rest; at most 1,000 candidates are scanned in bounded parameter batches. No preview vector index, separate vector database, remote embedding provider, model download or actual semantic inference was activated.

## Synchronization and offline behavior

Incremental owner/category changes use base versions, immutable operation UUID/digests, transaction rollback, duplicate acknowledgements and content-free tombstones. Local-only/unconfirmed memories, temporary/sensitive/tool history, raw assistant microphone audio, credentials and permissions/activation settings are excluded. Source consent/revision is checked again before transfer. Failures use bounded owner-reviewed retry/backoff; conflicts preserve local changes. Incoming pages and cursors stage atomically; source imports and mappings share one local SQLite transaction. Re-enabling categories replays from zero safely.

Confirmed memory/saved history imports require individual review and never replace the active conversation or a modified/local-only record. Harmless preferences can be retained; runtime voice activation remains under existing controls. Themes/device/workflow/knowledge metadata become encrypted replicas, with a separate existing-scope appearance review for themes. Workflow contracts are inert version 1 data, not an automation studio. There is no automatic background synchronization.

Only selected extracted excerpts enter the account-bound DPAPI cache, with expiration, encrypted-byte quota, local keyword search/removal and connected invalidation. Historical replay preserves a newer cache revision. A disconnected device cannot immediately receive deletion/revocation. DPAPI ciphertext never uploads or crosses devices as a decryption mechanism. See [synchronization design](SYNCHRONIZATION_DESIGN.md) for conflict, retention and recovery implications.

## Actual verification

| Check | Actual evidence and scope |
|---|---|
| Active Python regression suite | **222 passed in 32.462 s**; final log retained in local evidence summary |
| Cloud suite | **28 passed, 1 skipped** (29 discovered, 30.279 s); native SQL test explicitly skipped because no authorized disposable environment was supplied |
| Frontend | **22 passed (20.98 s)**, TypeScript compilation and production Vite build (3.27 s) passed; existing lazy Three chunk advisory remains |
| Lint/compilation | Python root/cloud lint and compilation passed; runtime dependency check passed |
| Archive | **4 passed** in a separate fresh Python process; tracked archive bytes unchanged |
| HTTP/TLS | Actual loopback Uvicorn/FastAPI and verified ephemeral test certificate with real desktop transport; synthetic SQL, no Internet endpoint |
| Native cloud HUD | Actual Windows WebView2, real bridge/Core/DPAPI/FastAPI routes with in-process SQL simulation: **14 exact reviews**, upload/processing, one verified citation, one cache item, responsive 760-width check and joined shutdown |
| Existing native HUD | Six modes, two detected monitor moves, shared timer, encrypted memory/UI refresh, review restoration, reduced/minimized suspension and WebGL fallback passed |
| Legacy/widget | Actual Tk/WebView2 smoke passed, with a recorded WebView2 Crashpad metrics temporary-folder cleanup warning; complete browser-temp cleanup is not claimed |
| Recovery | Actual AES-GCM/scrypt export/restore of synthetic rows/files into an empty isolated simulated SQL repository, checksum/content verification, wrong-passphrase/tamper/refusal tests and revoked restored sessions passed |
| Packaging | Clean PyInstaller build, exact embedded source/resource/frontend checks, local headless/cloud wheels and isolated frozen window startup/clean shutdown; final manifests linked below |
| Deployment templates | Actual `docker compose config --quiet` passed; image build, nginx/TLS runtime, Linux host and real SQL deployment were not run |

Final timings/build fingerprints are retained in [verification.json](evidence/phase05/verification.json), [native cloud results](evidence/phase05/native-results.json), [HUD regression results](evidence/phase05/hud-regression-results.json), [package results](evidence/phase05/package-results.json) and [frozen startup results](evidence/phase05/frozen-native-results.json). These separate synthetic, mocked, real local HTTP, native Windows, undeployed and unverified results.

Resolved Phase 05 validation findings include a missing HTTP runtime dependency, stale replay invalidating newer cache data, mismatched source/revision response fields, Windows legacy-code-page punctuation corruption and a cancellation error-path lint defect, and schema-level constraint-name collisions found during publication review. Dependencies/contracts/UTF-8 handling and final packages were corrected and reverified; tests were not weakened. Admission had no baseline failures.

## Screenshots and measurements

All screenshots are actual WebView2 client-area captures from an isolated **synthetic** profile, not production data or a browser-only mockup. Backend routes/parsers/encryption are real; the SQL repository and device are synthetic. Native file-picker gestures and physical lock were not interactively tested.

- [Cloud unconfigured](evidence/phase05/cloud-unconfigured-1360.png), [observed cloud status](evidence/phase05/cloud-observed-1360.png)
- [Knowledge Vault](evidence/phase05/knowledge-1360.png), [actual sources and offline cache](evidence/phase05/knowledge-sources-1360.png), [760-width view](evidence/phase05/knowledge-760.png)
- [Devices](evidence/phase05/devices-1360.png), [synchronization](evidence/phase05/synchronization-1360.png)

The native test records actual elapsed workflow time and Python working-set bytes in its JSON. That working set includes the test's in-process cloud simulation and excludes WebView subprocesses; it is not production cloud/app memory. The broader HUD regression observed actual frame counters, including zero updates while minimized/reduced-motion. Concurrent build/test load affects those samples. No steady-state FPS, app-specific CPU/GPU, production latency/capacity, embedding accuracy or acoustic measurement is invented.

Actual checkpoint samples: native workflow **19.104 s** including verification waits; Python working set **151,875,584 bytes**. The broader HUD run observed **27 render updates over its two-second sample**, and **zero over one second** while minimized/reduced-motion. These are observations from concurrent verification workloads, not a reference-hardware benchmark or service latency measurement.

## Changed files and delivery documents

The complete created/modified inventory is [CHANGED_FILES.txt](evidence/phase05/CHANGED_FILES.txt). Main groups are `cloud/`, `database/mssql/`, `deployment/{docker,linux,nginx}`, `src/clydex/{cloud,knowledge,synchronization}`, local schema 4, minimal existing coordinator/Core/repository/HUD/policy/transport extensions, four React features/tests, local verification/generation scripts and maintained management documents. Windows requirements/installer paths retain the existing client lifecycle; the server is not bundled into the Windows desktop. Generated builds/wheels/runtime data remain outside source.

New documents: [cloud architecture](CLOUD_ARCHITECTURE.md), [database design](DATABASE_DESIGN.md), [Knowledge Vault](KNOWLEDGE_VAULT.md), [deployment/recovery](CLOUD_DEPLOYMENT_GUIDE.md), [synchronization](SYNCHRONIZATION_DESIGN.md), [API reference](API_REFERENCE.md) and this report. Original product specifications are unchanged.

## Owner decisions, external gates and Phase 06 readiness

Before live activation, select/approve production SQL edition/license, supported Ubuntu build, VPS budget/size, private SQL/TLS/CA/proxy/firewall identities and endpoint. Supply a separately authorized disposable SQL Server environment for native migration/transaction/vector/recovery tests. Review operator key custody, recovery passphrase retention, live key-rotation procedure, backup retention/size limits and disaster recovery. The logical export caps at 256 MiB/100k rows per table; native SQL `.bak`/Linux restore and filesystem crash reconciliation are unverified.

Select/license/install a genuinely local embedding model and qualify its languages, retrieval quality, native SQL compatibility and resource use. Resolve OCR/audio/live-web/legacy-document needs explicitly; do not infer those capabilities from text generation. Complete real multi-device/offline/conflict/revocation stress, long-run security/performance/accessibility, native picker/physical-lock/mixed-DPI, fresh installer/signing and release acceptance. The Inno compiler is unavailable locally. Phase 03 acoustic/model/language/wake and Phase 04 approved matching rig/viseme/provenance gates remain open.

The engineering contracts provide a basis for owner-reviewed Phase 06 work. **Phase 06 has not started; production readiness remains conditional on the gates above. Stop at this Phase 05 owner-review checkpoint.**
