# Phase 05 API contract

The independently deployable FastAPI service uses `/v1`. Request models in `cloud/src/clydex_cloud/api/contracts.py` and route response contracts are authoritative; the local OpenAPI export is generated from the application, never hand-maintained as a competing interface. Public docs are disabled by default. No endpoint controls Windows, runs SQL supplied by clients, executes shell/code/macros, or invokes an AI orchestration engine.

## Contract inventory

| Resource | Operations and boundary |
|---|---|
| Health | `GET /healthz`, `GET /readyz`; generic alive/readiness codes, no secrets/account data. |
| Account | `POST /v1/auth/register` (closed by default, operator invitation), `/login`, `/refresh`, `/logout`, `/recover`; secure Argon2id password hashing, hashed opaque credentials, one-use refresh rotation/reuse revocation. |
| Devices | Owned `/v1/devices`, `/v1/devices/pairings`, pairing approval/claim, credential rotation and revocation. Account authorization and fixed scopes; pairing never grants desktop control. |
| Collections/documents | Owned collection CRUD; bounded raw-byte uploads with required idempotency key; versioned documents, authorized downloads, reprocessing and deletion. Files never use unauthenticated static URLs. |
| Processing | Owned `/v1/jobs`, bounded worker processing/status and stable errors. No text/body/filename in diagnostic logs. |
| Search | `POST /v1/knowledge/search`; explicit keyword or gated native exact-vector mode, bounded excerpts and stable source/document/version/location citations. No silent semantic fallback. |
| Sync | Per-category preferences, bounded versioned push and cursor-based change pull. Operation UUID/digest deduplication, optimistic version conflicts and tombstones. Workflows are inert versioned contracts only. |
| Usage/recovery | Owned document-byte quotas, operator-only encrypted backup/restore interfaces. Cloud keys are separately held; server-managed encryption is not E2EE. |

Bearer access tokens are short-lived opaque credentials; token/session/device/account validity and scopes are checked on every request. Refresh tokens are hashed and single-use, with family revocation on reuse. These are not OAuth interoperability claims. Unknown body fields/types are rejected; validation errors omit submitted values. Responses use stable status/error codes and random server request IDs, not caller-controlled log data.

Uploads have a 10 MiB maximum and non-upload JSON is separately bounded. The reverse proxy and API both enforce limits; no automatic proxy trust, CORS wildcard or public database port. Owner IDs always come from authentication, never a trusted request field. Missing/foreign object IDs use indistinguishable unavailable responses. Retry ambiguous mutations only with the identical operation/idempotency ID and bytes; changing a digest under the same ID conflicts.

The owner approved the SQL Server 2025/Ubuntu and AES-256-GCM engineering baseline on 2026-11-28. Production hosting, licenses and private-data transfer remain separate gates. The actual generated [OpenAPI contract](../cloud/openapi.json) is the complete field/response inventory. Regenerate with `scripts/export_cloud_openapi.py --output cloud/openapi.json` in the cloud environment; it starts no database or network service. When explicitly enabled, authenticated `/v1/openapi.json` exposes that same contract. No Swagger CDN is loaded.

## Requests and errors

`POST /v1/auth/login` accepts `login` and `password`; `POST /v1/auth/refresh` accepts `refresh_token`. Successful authentication returns opaque access/refresh tokens, `expires_in`, account/device ID and fixed scopes. Only trusted clients retain tokens; the desktop UI receives authenticated/account/expiry status, never those reusable credentials. `POST /v1/auth/logout?all_sessions=true` requires account scope; recovery rotates the one-time recovery code and revokes all sessions.

Pairing creates a pending one-use token, requires independent authenticated approval at `/v1/devices/pairings/{id}/approval`, then can be claimed through `/v1/devices/claims`. Account sessions manage devices; device sessions only receive chosen vault/sync scopes. `DELETE /v1/devices/{id}` revokes access; credential rotation revokes previous sessions. The HUD's rotation control discards new reusable credentials and requires re-pairing, rather than exposing them to the WebView.

Create a collection using `POST /v1/collections` with `title` and `description`. Original file upload is **raw `application/octet-stream`**, not multipart/base64:

```text
POST /v1/collections/{collection_uuid}/documents?name=synthetic.md
Authorization: Bearer <runtime access token>
Idempotency-Key: <new operation UUID>
Content-Type: application/octet-stream

Synthetic selected source bytes
```

New versions use `POST /v1/documents/{id}/versions` with name/collection/expected revision query parameters and an idempotency key. Downloads at `/content?version=N` require vault-read scope, use attachment/octet-stream and include a SHA-256 header. `/versions` lists bounded metadata; `/excerpts?offset=0&limit=20` returns current owned extracted passages and a truncation flag for explicit offline selection. Reprocessing returns 202 with job ID; GET jobs reports actual state/error. Delete collection/document uses exact `expected_revision`; nonempty collections cannot be removed as a shortcut. Notes accept explicit title/text/collection/operation UUID.

Keyword/semantic search body example (synthetic):

```json
{"query":"CYAN marker","mode":"keyword","limit":5}
```

An optional collection UUID narrows retrieval. Results include stable citation/document/version/revision/source location/excerpt fields and `insufficient_evidence`. An empty keyword result is explicit; unavailable semantic configuration returns a stable error. RAG is a desktop coordinator operation, not a duplicate cloud AI endpoint.

Sync policy requires seven explicit booleans. `/v1/sync/operations` accepts 1–20 validated operations, each with UUID, category, entity UUID, base version, deletion flag and bounded payload. `/v1/sync/changes?cursor=N&limit=M` returns owner-filtered changes, cursor and `has_more`. Operations are transactional; conflicts never partially apply the batch. Re-enable/replay rules are in [SYNCHRONIZATION_DESIGN](SYNCHRONIZATION_DESIGN.md).

Errors have the following shape; values are never echoed:

```json
{"error":{"code":"sync_conflict","current_version":2,"request_id":"server-generated-UUID"}}
```

429/503 may include bounded `retry_after` metadata and Retry-After header. Request IDs are generated server-side. Validation errors include only field locations/types. Stable codes distinguish unconfigured models, unavailable object/ownership, session expiry/replay, revision/idempotency conflicts, file limits and parser failures. Generic failures never include credentials, database URLs, SQL parameter contents or extracted text.

## Verification and compatibility

TestClient tests exercise actual routes against simulated SQL, including ownership, signatures, parsing, citations, deletion, quotas, errors and consent. A separate real loopback **verified TLS/HTTP** test exercises the desktop HTTP client against Uvicorn/FastAPI with an ephemeral trusted test certificate and synthetic SQL repository. This is not public certificate/VPS/native SQL acceptance. No Postman workspace, remote mock, collection or documentation was published.

The HUD still exposes only `hud_snapshot`, `hud_read`, `hud_command`. It adds the `cloud` read plus validated `cloud.configure`, `cloud.action` and native `knowledge.select` operations in the shared contract. The inner operation whitelist is in `cloud/workspace.py`; it accepts no arbitrary HTTP route, shell command, Python object, credential read or frontend file path. Local packaged frontend assets retain all Phase 04 identity and fallback behavior.
