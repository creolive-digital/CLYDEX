# Phase 02 engineering checkpoint

Date: 2026-11-26. Branch: `v2`. Reviewed baseline: `0c0213d5a7637ecb944eddde9a4d049f9f91e1f7`. Objective: harden the foundation, then deliver extensible multi-provider intelligence, owned conversation persistence and consented personal memory through the existing Core and desktop bridge.

Engineering scope is implemented and verified as described below. Owner/live acceptance is pending. No push, merge, release, new paid provider activation, real API credential use, private email testing or production resource testing occurred. Stop here before Phase 03.

## Completed tasks and architecture

| Tasks | Delivered / verified |
|---|---|
| H1-01–03 | Baseline 76 tests/CI reviewed; shutdown ownership waits for actual queue/browser/model work; bounded process I/O/files, deadline/cancel, job descendants and failed assignment cleanup. Foundations admitted before Phase 02. |
| P2-01 | Seven-provider registry, immutable configuration/capabilities, explicit models, atomic non-secret settings and existing Credential Manager. |
| P2-02 | Codex retained; six working HTTP request/response/stream codecs with auth/schema validation, normalized errors, caps, cancellation and usage when supplied. |
| P2-03 | Manual and automatic Fast/Balanced/Advanced/Offline priorities; capability/model/context/health/network observations, preference and budget restrictions. |
| P2-04 | Common outbound policy, six context compartments, minimization, local-only derived history, trusted specs/exact approvals, explicit same-policy fallbacks retaining original request ceiling. No model retry replays tools. |
| P2-05 | Owned encrypted sessions/messages, temporary default, title/times/provider metadata, resume/search/rename/archive/delete/export/retention; schema 1→3 preserves settings/audit and rolls back on failure. |
| P2-06 | Six memory categories, explicit commands/UI, provenance/ownership/timestamps/status/confirmation, revisions/correction/forget/disable, lexical retrieval and opt-in reviewed literal suggestions. |
| P2-07 | Functional settings/model/routing/status/privacy/offline/history/memory controls in existing frontend/legacy and Studio, through same queue/approval system. |
| P2-08 | 132 deterministic/regression/security/native tests; real synthetic loopback HTTP; lint/syntax/native UI/encryption/credential checks; wheel and both EXE builds. |
| P2-09 | All eight management documents, AGENTS, README, actual/target structure, provider guide and this checkpoint/file manifest maintained. |

ADRs 018–028 record the decisions and rationale. No second tool orchestrator was created. Provider adapters depend on shared contracts/transport, not UI or permission grants. Local data repositories depend on LocalStore and production Windows DPAPI; SQLite technology is unchanged. CoreApplication owns services; Studio exposes functional controls through the same serial queue. No public OS endpoint or expanded Windows/shell/mail privilege was added.

Local review commits: `3d38311`, `023fb4d`, `fe6f969`, `e0eb512`, followed by checkpoint documentation. Main remains `e65fe46e19e554066a43926f4a0e5335843096c8`. All 43 original V1 files match the reviewed intake byte-for-byte; older original-Git byte identity claims had preexisting CRLF-only differences in 31 text files, now documented as OI-24 without changing the archive. Official product document SHA256 values and active artwork remain unchanged.

## Provider capabilities and live gates

| Provider | Implemented and verified | Actual live acceptance |
|---|---|---|
| Codex CLI | Existing tool-disabled/ephemeral CLI default, model override, bounded owned process/files, cancellation/timeout and local schema validation; mocked CLI contract plus actual process primitives | Login, selected/default model and actual inference unverified. CLI streaming/usage unavailable, reported as such. |
| OpenAI API | Responses JSON schema/store false, bearer auth, SSE terminal/usage handling | Disabled, no key/model; needs owner account/model/budget/data approval and real validation. |
| Claude | Messages output_config, bearer/current version/workspace header, SSE and usage | Disabled; same owner gate, including workspace scoping. |
| Gemini | GenerateContent/streamGenerateContent, API-key header, responseJsonSchema, SSE/usage | Disabled; model/schema compatibility and account gate. |
| Ollama | Loopback chat/schema/NDJSON/usage; actual wire format against synthetic HTTP server | Disabled; no model/server contacted. Owner must configure OLLAMA_NO_CLOUD=1, a local model and confirm locality. |
| OpenRouter | Chat schema/SSE/usage, one pinned upstream, server fallback disabled/data controls | Disabled; model/upstream/key/price/data terms require acceptance. |
| Custom compatible | HTTPS Chat Completions schema/SSE/usage and configurable token parameter | Disabled; endpoint/schema/model/auth compatibility must be validated for the actual service. |

All six HTTP adapters were tested with deterministic fixtures. Only the synthetic local server was contacted for HTTP execution tests. No model ID, successful connection, inference quality or billing guarantee was invented. [PROVIDER_CONFIGURATION.md](PROVIDER_CONFIGURATION.md) records current official references and exact setup/security requirements.

Routing is deterministic and explainable: first eligible configured provider under the chosen profile, with capability/limits/cached-health/price/privacy filtering. No implicit cloud/paid fallback; each explicit fallback is rechecked and reviewed. Offline/privacy block cloud including Codex. At most one configured retry follows a rate-limit rejection and receives fresh approval. Network/timeout failures are not retried on the same service. Original configured per-request estimated cost ceiling cannot be weakened by remote fallback; this is not an aggregate conversation billing cap.

## Conversation, memory and migration acceptance

Conversations start temporary in RAM. Explicit saved-session consent permits encrypted local user/assistant persistence. Sensitive tool/mail turns and known credential patterns are omitted. Sessions support multiple titles, UTC timestamps, provider/model metadata, resume, search, rename, archive/unarchive, deletion, JSON export and configurable retention. SQLite queries are parameterized and owner-scoped; title/text encryption has no plaintext fallback. Archived sessions cannot receive a new request until unarchived.

Schema-1 synthetic fixtures containing settings/audit upgrade to 3 without losing records. Failed migration 003 rolls migration 002 back in the same transaction. Reopen is idempotent; newer schema refuses downgrade. No real owner profile was opened for migration testing. Recovery instructions require a separate protected backup/profile; no destructive downgrade is performed. Native DPAPI ciphertext and wrong-owner rejection were tested.

Memory commands and UI support remember/review/update/forget across preferences/profile/projects/routines/work/facts. Records retain explicit/inferred origin separately from user confirmation, owner, source kind/opaque ID, created/modified times, local-only flag and revision/status. Retrieval uses up to five relevant confirmed local records. Cloud-eligible records require outbound consent; local-only records and history derived from them cannot leave through a later cloud request.

Automatic suggestions remain off. Opt-in requires chosen categories; initial extraction recognizes literal current-user statements and saves no proposal until reviewed. Mail/tool/external content is not an automatic source. Disable prevents retrieval/new memory and clears proposals while retaining existing records for owner review/deletion. Local repository/provenance/tombstone boundaries allow a future sync adapter; no synchronization infrastructure, embedding service or cloud database was implemented.

Bounds: UI lists 500 recent sessions and searches 10,000 recent messages; resume loads 100; model history retains the existing six-message window. Temporary sessions keep 100 safe messages. Full saved-session JSON export has an 8 MiB content-plus-metadata allowance and fails explicitly above it. Maximum 1,000 active memories and five retrieval hits. Secret filtering is conservative, not universal; do not store secrets. Delete/retention cannot revoke independent exports/backups or provider-held copies.

## Verification and known limits

| Check | Result |
|---|---|
| `python -m unittest discover -q` | **132 passed**, no failures/errors/skips; final recorded run 8.023 s on Windows/Python 3.13.14. |
| Ruff / compileall / JS syntax | Passed; inherited legacy engine style exclusion preserved, syntax and regressions included. |
| Real synthetic HTTP | Serialization/status/redirect/response limits/stream/deadline/cancellation passed, including HTTP/1.0 stalled responses. |
| Safe Tk/WebView2 | Clock/timer/alarm/stopwatch and real bridge/provider controls/approval/encrypted session defaults passed. No microphone/weather/private services contacted. |
| Native DPAPI/Credential Manager | Synthetic encrypted data and credential write/read/delete passed; no real key inspected/used. |
| Wheel / isolated import | Passed, including new data/provider/UI modules and migrations. |
| PyInstaller / frozen resource checks | Both EXEs built; coordinator/adapters/data/DPAPI extension/migrations/frontend included. Artifacts outside source under `%LOCALAPPDATA%/CLYDEX/tmp/phase02-verification/`. |
| GitHub Actions | Reviewed baseline run 45795129836 succeeded on Python 3.11 through Inno/artifact upload. Current checks updated locally; no new CI run without authorized push. |

Existing Windows/voice/browser/mail behavior has regression/mock coverage and safe widget/UI smoke. Actual microphone/SAPI/Whisper quality, Codex/account services, local Ollama inference, real window/browser/Outlook effects, human accessibility/DPI, clean installation/uninstallation and frozen interactive behavior remain unverified. Local Inno compiler is absent. Reference CPU/RAM/latency budgets and long-duration performance are unapproved.

Established sockets honor cancel/deadline; OS DNS/connect can still delay completion beyond the configured timeout. Core retains queue and instance ownership until it finishes. Native COM/STT cannot necessarily stop immediately or undo completed effects. Trusted Python approvals do not sandbox malicious same-user code. These are explicit OI-07/12/14/18 acceptance limits, not successful live validation claims.

## Owner decisions and Phase 03 readiness

Owner review is required before continuing phases. Remaining decisions: real accounts/models/keys, paid/private live-test authorization, actual provider prices/spending/data-retention terms, local Ollama deployment, optional automatic memory/category activation, conversation/audit retention and backup/recovery expectations, human Windows/hardware/installer acceptance and missing approved standalone branding assets. No owner response was assumed during implementation.

The architecture is ready to support the next planned voice phase, subject to this checkpoint review and explicit licensed local voice, language quality, reference hardware and latency/activation/privacy decisions. Phase 03, full cinematic HUD/avatar, cloud deployment, plugin marketplace and physical devices were not started.

## Changed-file manifest

Paths below are relative to reviewed `0c0213d`; original owner specifications and the archive are not changed.

Created (37):

```text
docs/PHASE_02_COMPLETION_REPORT.md
docs/PROVIDER_CONFIGURATION.md
frontend/legacy/intelligence.js
src/clydex/conversations/__init__.py
src/clydex/conversations/models.py
src/clydex/conversations/repository.py
src/clydex/conversations/service.py
src/clydex/core/context.py
src/clydex/core/data_actions.py
src/clydex/core/orchestrator.py
src/clydex/database/migrations/002_conversations.sql
src/clydex/database/migrations/003_memory.sql
src/clydex/desktop/intelligence.py
src/clydex/memory/__init__.py
src/clydex/memory/models.py
src/clydex/memory/repository.py
src/clydex/memory/retrieval.py
src/clydex/memory/service.py
src/clydex/providers/anthropic_provider.py
src/clydex/providers/base.py
src/clydex/providers/custom_provider.py
src/clydex/providers/gemini_provider.py
src/clydex/providers/http_provider.py
src/clydex/providers/ollama_provider.py
src/clydex/providers/openai_provider.py
src/clydex/providers/openrouter_provider.py
src/clydex/providers/registry.py
src/clydex/providers/router.py
src/clydex/providers/transport.py
src/clydex/security/content.py
src/clydex/security/encryption.py
src/clydex/security/outbound.py
tests/test_hardening.py
tests/test_intelligence.py
tests/test_intelligence_controls.py
tests/test_personal_data.py
tests/test_provider_transport.py
```

Modified (32):

```text
.env.example
.github/workflows/build.yml
AGENTS.md
README.md
docs/ARCHITECTURE_DECISIONS.md
docs/CHANGELOG.md
docs/CURRENT_STATE_ANALYSIS.md
docs/DEVELOPMENT_PROGRESS.md
docs/DEVELOPMENT_ROADMAP.md
docs/OPEN_ISSUES.md
docs/REQUIREMENTS_TRACEABILITY.md
docs/TESTING_AND_ACCEPTANCE.md
docs/architecture/PROJECT_STRUCTURE.md
frontend/legacy/desktop.css
frontend/legacy/index.html
frontend/legacy/studio.js
scripts/verify_windows_smoke.py
src/clydex/automation/tasks.py
src/clydex/core/application.py
src/clydex/core/errors.py
src/clydex/core/events.py
src/clydex/core/legacy_engine.py
src/clydex/core/processes.py
src/clydex/database/store.py
src/clydex/desktop/studio.py
src/clydex/providers/__init__.py
src/clydex/providers/codex.py
src/clydex/security/permissions.py
src/clydex/tools/desktop.py
src/clydex/tools/windows_apps.py
tests/test_foundation.py
tests/test_regression.py
```
