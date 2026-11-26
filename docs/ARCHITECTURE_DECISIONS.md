# Architecture decisions

Status: historical Phase 01 decisions followed by owner-authorized Phase 02 decisions below; approved product identity and database technology remain unchanged.

## Phase 02 decisions (2026-11-26)

| ADR | Decision | Rationale / consequence |
|---|---|---|
| 018 | Latest owner authorizes Phase 01 engineering admission then Phase 02; retain actual reviewed V2 baseline and immutable main/V1/specifications. | Supersedes earlier Phase 01 stop/metadata-only scope for authorized conversations/memory. No authority to activate paid services, use real keys/private data or publish. |
| 019 | Retain instance ownership until actual queue/browser/model completion. Own suspended child processes before resuming and join bounded I/O cleanup. | Prevent native operation overlap across instances. Failed job assignment kills the still-suspended process; job descendants terminate before return. Cleanup failure retains ownership. Native calls still have interruption/rollback limits. |
| 020 | Immutable seven-provider registry and shared stdlib HTTPS codecs/transport; no additional provider SDKs or model defaults. | Existing dependencies suffice; deterministic wire contracts tested. New adapters disabled, explicit models/keys, no startup network. Official API/schema/version/authentication references in PROVIDER_CONFIGURATION. |
| 021 | Deterministic capability/cost/context/observed-health routing with owner-defined profile priorities and explicit fallbacks. | Avoid opaque paid/cloud choices. Offline/privacy policy is always checked, including retries/fallback. Cached failures represent observed availability, not a predictive network guarantee. |
| 022 | Single IntelligenceCoordinator supplies the existing agent; fixed trusted ToolSpecs remain authorization authority. Separate context compartments and exact immutable configuration snapshots. | No second orchestration system or model-generated permission scope. Every new provider request, fallback and rate-limit retry gets review. Provider-native tools are not exposed. |
| 023 | Schema 1→3 additive SQLite migrations and DPAPI payload encryption, scoped repositories, temporary default, explicit persistence consent. | Keep approved database technology/settings/audit. No raw audio, keys or sensitive tool/mail turns in conversation records. Downgrade refused; restore old-profile backup separately. No cross-account DPAPI portability promised. |
| 024 | Manual memory plus opt-in literal-current-user suggestions with per-record review. Preserve inferred origin and explicit confirmation separately. | Conservative first collector avoids silent model/mailbox inference. Category permissions, provenance, revisions, disabling and local lexical retrieval implemented. No cloud synchronization/vector service. |
| 025 | Local-only memory taints derived chat context; omit derived turns from persistent history and block later cloud transfer until context reset. | Filtering memory records alone would leak their content through subsequent assistant history. Regression tests cover this boundary. Relevant cloud-eligible memories still require exact outbound review. |
| 026 | Extend existing Studio/WebView frontend with functional provider/routing/history/memory controls and same queue/approval dialog. | No branding/React/avatar rewrite. Keys entered locally never returned; review binds only key digest plus non-secret settings. Render external/private text as text nodes. |
| 027 | Bound HTTP bodies/streams, child output and export/search/retrieval; coalesce provider telemetry. No automatic retry after network/timeout. | Avoid unbounded buffering and duplicate bills/side effects. Socket cancellation tested against real synthetic HTTP/1.0. OS DNS/connect cancellation and reference-hardware performance remain declared technical gates; instance ownership remains held. |
| 028 | Adopt current Claude Messages version/authentication and optional workspace header while leaving models blank. | Official 2026-11-26 references document version 2026-10-21 and workspace selection. Tests validate headers/shape only; no account or successful inference invented. |

Low-risk decisions implement the explicitly approved phase. Added scopes cover provider configuration/health and local history/memory management; existing Windows/shell/mail scope and risk policies are unchanged. If private-context transfer is declined after an already completed tool action, the existing receipt fallback can report local results without transmitting them. No tool is replayed.

| ADR | Decision | Rationale / consequence |
|---|---|---|
| 001 | Parallel branch `v2` at e65fe46; no push. Preserve original docs and root entry points. | Isolated, reversible migration; main unchanged. |
| 002 | `src/clydex/` package via pyproject; implement only core/providers/security/database/automation/desktop now. | Owner target layout; no empty future-feature stubs. Root wrappers preserve existing import/launch use. |
| 003 | Extract existing orchestrator behind adapter and retain Windows tool modules; move Studio bridge into desktop package. | Headless business services independent of WebView. Avoid changing stable widget/audio/tool logic unnecessarily. |
| 004 | Frozen typed request/event/provider/tool contracts; strict JSON canonicalization and local validation. | Model output is untrusted; risk/scope fixed by trusted adapters, never selected by model payload. |
| 005 | Process-local authorization authority; random one-use approval IDs bound to digest, identity, target and expiry; fail closed. | UI approves an exact pending operation, never a global privileged mode. Approval tokens are not remote credentials. |
| 006 | Bounded serial task queue and event buffers, explicit cancellation and safe error mapping. | Existing single-turn behavior preserved; no unlimited worker growth. Native operations remain cooperatively cancellable. |
| 007 | `%LOCALAPPDATA%/CLYDEX/` runtime folders; validated central non-secret settings and SQLite schema-versioned settings/audit metadata. | No runtime data in checkout. No conversations/raw audio/vault content or credentials in SQLite in Phase 1. SQLite is not encrypted; only safe metadata stored. |
| 008 | Windows Credential Manager for durable secrets; environment lookup for deployment secrets; no plaintext fallback. | Approved platform storage with lazy Windows imports; no provider keys sent to WebView. |
| 009 | JSON logs use allowlisted metadata, safe error codes and rotation. | Never log prompt/tool text, command output, titles, email or arbitrary exception text; redaction of unknown data is fail-closed. |
| 010 | Existing Codex-only provider adapter; no silent cloud fallback and no new network services. | Seven-provider routing is Phase 2. Enforce privacy/cloud disabled checks before any Codex call; explicit approval for private context transmission. |
| 011 | Retain HKCU speech-mode preference as legacy import fallback; central settings takes precedence. | Preserve existing user choice without destructive migration. New settings outside repository. |
| 012 | Internal authenticated transport not exposed during Phase 1. | No need for HTTP/IPC listener while same-process bridge is retained. FastAPI/versioned endpoint rollout needs authentication and process isolation acceptance later. |
| 013 | Per-runtime OS file lock, released on crash/close. | Enforce one local Core queue per user; widget remains independent. No stale PID-file deletion. |
| 014 | Keep original supplied document bytes under Git attributes. | No line-ending normalization of owner specifications; verify SHA256 before handoff. |
| 015 | Registry read fallback, SQLite preference writes, immutable startup policy and optional disabled capability scopes. | Preserve voice choice while enabling least privilege without a new provider/permission escalation UI. Restart required to apply policy edits. |
| 016 | Preserve standalone V1 from exact baseline under owner-requested `v1-old/`; move active shared Tk implementation into desktop package and retain root launchers. | Keep V1 independently runnable while V2 avoids archive imports and remains modular. Current V2 static UI stays active; legacy PNGs move to assets/legacy. No Phase 02 work or branding changes. |
| 017 | Retire root import facades and relocate launchers/build/setup/UI files into their required folders, following the owner's explicit correction. | Supersedes the root-file compatibility portion of ADR-003/016. Preserve V2 behavior and installed EXE names; source launchers retain filenames under scripts/windows. Root holds metadata and README only. Original V1 files remain frozen in v1-old. |

Implementation clarification: ToolSpec declares typed input fields, result types, scope, risk and time budget. Existing Codex responses also receive local validation of the schema subset actually used. This does not claim a general-purpose JSON Schema validator or plugin SDK. The legacy WebView may use its existing loopback asset server; no new core control endpoint was introduced.

## Planned touched files and migration sequence (before implementation)

1. Documentation and AGENTS; `.gitignore`, `.env.example`, `pyproject.toml`.
2. New package contracts/config/errors/events; SQLite migration/repository; credential and authorization modules; serial execution service and tests.
3. Extract Codex subprocess adapter, command parser and VoiceEngine into package behind root shim; integrate exact authorization around legacy Windows effects; add portable regression tests.
4. Extract Studio bridge into package; integrate configuration, errors, queue, stop action; keep .pyw launcher and static UI. Update PyInstaller source paths and Windows CI test/lint gate.
5. Run tests, syntax/lint, packaging/import checks and safe Windows UI smoke tests; update all acceptance/status documents, report remaining manual gaps. Stop at Phase 01 checkpoint.

Risks: packaging imports, caller compatibility, COM thread affinity, approval UI waiting/deadlock, native cancellation limits. Mitigation: mocked tests, explicit deadlines, one queue, lazy platform imports, unchanged root widget and reversible wrappers. Rollback: switch to main after saving V2 work; runtime data is independent and never deleted by rollback. No automated DB downgrades.
