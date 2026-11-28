# Controlled MCP client

Phase 06 implements explicitly configured **2026-07-28 Streamable HTTP**. Official documentation now specifies stateless per-request metadata rather than the legacy initialize/session handshake. There is no silent fallback, version downgrade or retry of a potentially modifying call. Legacy 2025-11-25 and stdio transports are unsupported at this checkpoint, and no configuration can launch an arbitrary server command. [Official versioning](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning).

Disabled profile example:

```json
{"name":"Selected MCP service","endpoint":"https://mcp.example/endpoint","enabled":false,"protocol_version":"2026-07-28"}
```

Save, review enablement, optionally provision a correctly audience-scoped bearer token into Credential Manager, and review discovery. Client requests include protocol/client identity/capabilities in `params._meta`, matching protocol/method/name headers, and Accept JSON plus SSE. Each request uses the shared cancellation-aware bounded HTTP transport. TLS verification is never disabled; literal loopback HTTP is allowed for explicit local test services. There is no OAuth browser flow or token refresh impersonation in this initial adapter.

`server/discover` reports identity/capabilities, followed by at most four bounded tools/list pages and 64 supported tools. Descriptions, annotations, icons and outputs are untrusted. Unsupported/complex schemas are excluded; duplicate identities fail. No icon, resource URL, remote code or schema reference is fetched. Inventories are persisted encrypted with canonical schema/name/description fingerprints. Discovery clears previous tool reviews and grants no authority.

The owner reviews each selected discovered fingerprint. Changing server configuration clears inventory/reviews. Tool calls require enabled server + reviewed exact fingerprint, locally validated arguments, HIGH host risk, existing outbound policy and a separate exact-action approval displaying destination/configuration and data. Server risk hints cannot reduce host risk or grant a scope.

The client supports required JSON and request-scoped SSE results, bounded progress/messages, response identity validation, closing the response on completion/cancellation, output schema validation where supported, primitive `x-mcp-header` paths and prescribed header encoding. It sends no roots, sampling, subscriptions, reusable approvals or host credentials as capabilities. Input-required/MRTR or unsolicited server requests stop with an explicit unsupported error; no elicitation response is automatically authorized. Header/version/protocol errors are surfaced without automatic replay. [HTTP binding](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http), [tool contracts](https://modelcontextprotocol.io/specification/2026-07-28/server/tools).

Only bounded text content is presented from tool results. Images, embedded resources and remote URLs are not automatically interpreted. A returned instruction is data and cannot become an installed CLYDEX tool. Actual JSON/SSE loopback fixtures verify wire behavior, schema/header validation, review gating and refusal of additional-input authority. They do not establish interoperability with a live external MCP account/server, full JSON Schema 2020-12 conformance, OAuth authorization-server support or production cancellation quality.
