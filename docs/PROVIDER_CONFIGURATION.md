# Phase 02 configuration and privacy

## Phase 06 boundary (2026-11-28)

Phase 06 routes selected-content developer analysis and voice/text workflow drafting through the existing IntelligenceCoordinator and outbound policy. Installed tool schemas are public planner instructions; private selections/tool content are not silently injected. Existing providers stay disabled/unconfigured as before, and private result transfer still requires exact review. No new provider or paid activation follows the operating UI.

## Phase 05 Knowledge Vault boundary (2026-11-28)

Personal cloud storage is a separate reviewed service, not an eighth AI provider. The seven-provider registry and Fast/Balanced/Advanced/Offline routing remain unchanged. Cloud storage is disabled by default and obeys the existing startup allow-cloud, privacy/personality and Offline ceilings. It does not make paid inference requests. Every selected transfer is exactly reviewed; login/category selection does not activate background sync.

Knowledge-assisted answers reuse IntelligenceCoordinator and classify retrieved excerpts as private context. External AI transfer requires the existing provider-specific exact review; excerpts cannot grant permissions. Insufficient evidence avoids a model call; offline cached questions require a configured local provider. The optional cloud-side local embedding adapter is explicitly licensed/digest-pinned, off by default and never downloads a model. Native vector/inference quality and all live provider acceptance remain pending.

Phase 03 continuation: voice transcripts use the same IntelligenceCoordinator, outbound compartments, configured providers, cost ceilings and exact-action reviews described here. Personality privacy mode adds a cloud restriction; it cannot enable a provider or relax core/routing privacy. Optional encrypted addressing is private context and requires transfer review. No new AI provider or cloud speech service was activated. See [voice configuration](VOICE_CONFIGURATION.md) and [Phase 03 evidence](PHASE_03_COMPLETION_REPORT.md). Historical Phase 02 protocol/configuration guidance below remains applicable.

Validated against official documentation on 2026-11-26. These are implementation contracts and synthetic test results, not live connectivity or model-availability claims. No SDK dependency or invented default model was added. The existing logged-in Codex CLI remains the only enabled default provider. Six HTTP providers start disabled without models or credentials.

## Desktop setup

Open **AI & Memory**. Select a provider, enter an actual account-available structured-output model, configure limits, and explicitly enable it. Remote/custom adapters also require **Permit billed requests**. Save uses the existing exact-action review. Keys are passed to the local Python bridge and stored in Windows Credential Manager (`CLYDEX/provider.<id>`), never returned to the frontend or written to JSON/SQLite/logs. ASCII token limit: 1,280 characters, consistent with the existing native credential store. Blank key leaves the existing key unchanged; removal is explicit. No connectivity check occurs on startup or save.

Use **Review connection check** only when ready to contact the endpoint. It checks the selected model's metadata/listing with no prompt/history/memory. A reachable model listing does not prove inference or schema support. Codex status reports executable presence with login explicitly unverified. Configure a provider again or explicitly recheck after a cached network/auth/model failure.

| Provider ID | Implemented API and authentication | Owner configuration / live gate |
|---|---|---|
| `codex` | Existing `codex exec`, ephemeral tool-disabled read-only session; optional explicit model | Existing CLI login; CLI default model preserved when blank. No streaming/usage feed claimed. |
| `openai` | HTTPS `/v1/responses`, bearer token, `text.format` JSON schema, `store:false`, SSE | Account-available structured-output model, key, request limits and budget. |
| `anthropic` | HTTPS `/v1/messages`, bearer token, `anthropic-version`, `output_config.format`, SSE | Structured-output model/key; default API version `2026-10-21`. Add workspace ID for a key not scoped to one workspace. |
| `gemini` | HTTPS `v1beta/models/...:generateContent` / `:streamGenerateContent?alt=sse`, `x-goog-api-key`, `responseJsonSchema` | Model supporting the schema feature and account access; no model automatically chosen. |
| `ollama` | Literal loopback `/api/chat`, schema `format`, NDJSON, no key | Install/select an available local model. Start the server with `OLLAMA_NO_CLOUD=1` and confirm local-only deployment. Cloud-suffixed models rejected. |
| `openrouter` | HTTPS `/api/v1/chat/completions`, bearer, JSON schema/SSE | Explicit model and one approved upstream; server fallback disabled, supported parameters required, data collection denied. Server/account policy acceptance still needed. |
| `custom` | Owner-specified HTTPS endpoint, `/chat/completions`, bearer, JSON schema/SSE | Compatible API/schema model/key; optional `max_completion_tokens` parameter. Adapter compatibility is not assumed for every vendor. |

Built-in remote endpoints are fixed. Alternate services use `custom`. URLs cannot contain credentials, query strings or fragments. No insecure remote HTTP, redirects, environment proxy auto-discovery, arbitrary auth headers, automatic model downloads, OAuth flow or provider-native tools are enabled.

## Routing and outbound context

Manual routing uses the selected provider. Automatic routing considers task capability (conversation/planning/summary), explicit configured model, current context size, priority/user profile, cached availability/health, credential presence, privacy/offline policy and configured cost restrictions. Fast/Balanced/Advanced are configurable priority lists, not claims about a model's speed or quality. Offline always restricts selection to local Ollama, even if a cloud provider is put in its priority list. Privacy blocks cloud providers including Codex. Startup environment/config privacy/no-cloud restrictions remain an upper bound on UI choices. There is no background network probe; cached failures represent observed network/model availability, not a network guarantee.

Only explicitly configured fallback providers can be considered after a request failure. Each fallback rechecks all policies and gets fresh approval. The original provider’s configured per-request estimated cost ceiling also applies to remote fallbacks, including rejection of unknown prices. This is not a cumulative conversation budget or a guarantee of actual provider charges. Timeouts/network failures are never retried on the same provider because billing might already have occurred. One explicitly configured retry is possible only after a rate-limit rejection, with fresh approval. No tool plan or side effect is replayed. Authentication, invalid request and invalid structured response failures do not trigger fallback. The existing first-turn direct Codex prompt consent is preserved; private history/context always requires separate review. Every new HTTP provider request receives review.

Prompt, history, personal memory, knowledge, sensitive tool results and external documents have separate data compartments. Only relevant confirmed memories are retrieved (lexical matching, maximum five). Local-only memories are removed before cloud requests. History derived from local-only memory is marked local-only too, and is omitted from durable history. Clear context or start/resume another conversation before changing such a session to a cloud provider. External text/model output cannot add trusted tools, scopes or approvals. Streaming progress never executes partial/unvalidated plans.

Cost fields are owner-supplied in a consistent provider currency. A configured request ceiling requires both token prices; unknown pricing fails closed. Estimates conservatively use the configured maximum input byte limit plus output token allowance. They are not billing guarantees, especially for provider-specific reasoning/caching charges; configure provider account spending limits too. No automatic prices or model catalog is fetched.

HTTP response bytes and requests are bounded, streaming has a terminal-event/schema gate, TLS validates server certificates, and established sockets are interrupted on deadline/cancel, including HTTP/1.0 responses. OS DNS/connect behavior can delay completion beyond the requested timeout; the Core retains queue/instance ownership until it actually returns. This is a remaining native timeout validation limitation, not a claim of hard real-time cancellation. An owner-confirmed local Ollama deployment is trusted: loopback alone cannot prove the server does not proxy requests. No cloud sync is implemented.

## Conversations and memory

Sessions start temporary and RAM-only (last 100 safe messages). Explicitly create a saved conversation to consent to encrypted local persistence. The service stores only reviewed-session user/assistant text; sensitive tool/mail turns, known credential patterns and financial credential-like text are omitted. Provider/model/times and opaque IDs are metadata. Secrets filtering is conservative, not a universal detector; do not dictate/store secrets. Resume loads the last 100 messages; the model receives at most the existing six-message context window. Search scans up to 10,000 recent messages and lists up to 500 recent sessions. Export includes the complete selected saved conversation up to an 8 MiB content-plus-metadata allowance; larger exports fail explicitly with no partial result. Temporary export contains only its bounded RAM window. Export text is local and copied by the owner; no file is silently created or uploaded.

Rename/archive/unarchive/delete and retention policy changes use exact reviews. Retention defaults off; choosing 1–3,650 days reviews and immediately purges expired owned sessions, then applies again at startup and on policy changes. Delete clears message/title payloads and retains a content-free tombstone. Archived sessions are read-only until unarchived. Retention/forget does not erase independent backups/exports or data already sent to a provider.

Memory is separate from chat history. Manual commands: `Remember this: preferences: ...`, `What do you remember about me?`, `Update this memory <ID>: ...`, `Forget this information <ID>`. UI supports the same review/correction/deletion and disabling. Six approved categories: preferences, profile, projects, routines, work, facts. Records carry owner, origin, source kind/opaque ID, created/updated timestamps, confirmed status, local-only choice and optimistic revision. Manual UI and current-user commands have distinct provenance; outside/tool/mail text is not an automatic memory source.

Automatic suggestions default off. Opt in explicitly and choose categories. This initial conservative collector recognizes literal statements (`I prefer ...`, `My name is ...`, `I am working on ...`, `I usually ...`, `At work, ...`, `A fact about me is ...`). It does not silently infer facts from mailbox/tool/model content. Suggestions are unconfirmed RAM-only proposals; saving each needs review. Once accepted they retain inferred origin plus user-confirmed status. Disabling clears proposals and prevents retrieval/new memories, while existing records remain available for review/delete. Maximum 1,000 active memories; no embeddings, cloud account or synchronization worker is introduced.

## Schema upgrade and recovery

`data/core.sqlite3` upgrades transactionally from schema 1 to 3: 002 adds owned conversations/messages/retention, 003 adds owned memories/policies. Settings and audit records are preserved. A failed migration rolls back the whole pending batch; reopening is idempotent; a newer schema is refused. Titles/text/memories use Windows current-user DPAPI with owner entropy and no plaintext fallback. This does not protect against malicious code running as the same Windows account; protect that account and backups. Timestamps/provider metadata are not encrypted. Cross-device/account DPAPI recovery needs a separately approved design in the synchronization phase.

Before upgrading a real profile, close CLYDEX and back up the database and settings outside source using the owner's chosen protected location. Verification here used isolated synthetic profiles only. Do not downgrade a schema-3 file in place. To roll back, preserve it and its settings, use the prior V2 commit with a separately restored schema-1 backup/profile; or run the independent V1 archive. Credentials remain in Credential Manager; no downgrade exports them. No automated destructive downgrade or backup infrastructure is implemented.

## Official protocol references

- OpenAI [Responses create](https://developers.openai.com/api/reference/resources/responses/methods/create) and [streaming](https://developers.openai.com/api/docs/guides/streaming-responses).
- Claude [Messages](https://platform.claude.com/docs/en/api/messages/create), [structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs), [authentication/workspace selection](https://platform.claude.com/docs/en/manage-claude/authentication) and [API versions](https://platform.claude.com/docs/en/api/versioning).
- Google [GenerateContent API](https://aistudio.google.com/api-reference/generate-content) and [official generation configuration types](https://googleapis.github.io/js-genai/release_docs/interfaces/types.GenerateContentConfig.html).
- Ollama [chat](https://docs.ollama.com/api/chat), [model tags](https://docs.ollama.com/api/tags) and [cloud-disable configuration](https://github.com/ollama/ollama/blob/main/envconfig/config.go).
- OpenRouter [API overview](https://openrouter.ai/docs/api_reference/overview) and [provider routing controls](https://openrouter.ai/docs/guides/routing/provider-selection).
- Custom compatible [Chat Completions contract](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create).

No successful live connection, real key validity, chosen model availability, paid service activation or provider data-retention agreement is asserted by these references.
# Phase 04 navigation note

The current HUD exposes provider configuration and routing in **Intelligence**, history in **Conversation** or Intelligence's history tab, and consented records in **Memory**. Exact reviews, stored-key protections, startup privacy ceilings and the seven adapters below are unchanged. The legacy **AI & Memory** interface remains available with `--legacy`. No new provider is activated or remotely verified by the UI migration.
