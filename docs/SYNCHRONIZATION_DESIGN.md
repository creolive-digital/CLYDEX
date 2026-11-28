# Opt-in synchronization

## Policy and contract

Every category starts disabled on the desktop and server: Knowledge Vault metadata, confirmed non-local personal memory, explicitly saved safe conversation history, whitelisted preferences, inert workflow contracts, registered-device metadata and themes. This matches product decision D35; notification history is not a synchronization category. File upload is a separate explicit operation. No account login, category toggle, startup, timer or reconnect silently initiates transfer.

Shared `clydex.synchronization.contracts` rejects unknown fields. It excludes local-only/unconfirmed/external-source memories, temporary/sensitive/private-derived history, tool/system messages, credentials, microphone recordings and permissions/activation settings. Secret-pattern screening is conservative and is not a guarantee to detect every secret. Persistent history already excludes sensitive turns under the existing conversation rules; only existing saved source IDs can be exported from the HUD.

Automation contracts are version 1 inert graphs with input/note/output nodes and validated IDs/edges. They cannot execute scripts/actions and do not represent a Phase 06 workflow engine. Device metadata cannot grant scopes or revoke a device. Themes contain appearance/resource settings only. Every configuration/action still uses the installed trusted executor.

## Transfer state

```mermaid
sequenceDiagram
    participant Owner
    participant Desktop
    participant Outbox
    participant Cloud
    Owner->>Desktop: Review category consent and selected source
    Desktop->>Outbox: DPAPI envelope with immutable operation UUID and source revision
    Owner->>Desktop: Review exact queued transfer and destination
    Desktop->>Desktop: Recheck privacy, cancellation and source consent/revision
    Desktop->>Cloud: Operation UUID, base version, validated clear payload over TLS
    Cloud->>Cloud: Owner filter, digest deduplication and transaction
    Cloud-->>Desktop: Version acknowledgement or conflict
    Desktop->>Outbox: Record account-bound mapping and remove acknowledged operation
    Owner->>Desktop: Review incremental change fetch
    Cloud-->>Desktop: Owner-filtered changes and cursor
    Desktop->>Desktop: Stage encrypted changes and cursor atomically
    Owner->>Desktop: Review each incoming change
    Desktop->>Desktop: Check local revision; import and mapping in one transaction
```

Operation IDs are UUIDs; the server stores a canonical digest and encrypted result. Identical replay returns the prior result; a changed request under the same ID conflicts. Updates require an exact base version, including deletes. A stale offline update cannot silently resurrect a tombstoned entity. Acknowledgements must match entity and next version. Ambiguous mutation failures are never automatically retried; an owner can review the same idempotent operation again after bounded exponential backoff (five attempts, up to 300 seconds). Conflicts remain visible and are resolved by discarding/reviewing a new operation, never overwriting by wall-clock timestamp.

The local queue is limited to 500 operations. Before upload, the selected memory/history source is reloaded and compared to the reviewed payload/revision. Changes to local-only status, contents or deletion stop transmission. Incoming pages are bounded to 20 entities per desktop request, 64 KiB/entity; the encrypted inbox is capped at 500 entries. Cursor and staged payloads commit together, so interruption cannot skip an unstaged record. Re-enabling a category resets the global cursor to zero for replay because disabled categories may have been skipped. Device delivery cursors are server metadata, not proof the device applied a change.

## Local apply and conflicts

SQLite schema 4 uses one transaction for the existing memory/conversation repositories and sync mappings. Remote IDs map to locally generated IDs per origin/account, preventing cross-account collisions. Local revision changes, queued local writes, local-only memories, disabled memory policy and the active conversation block remote replacement/deletion. Duplicates are idempotent. Incoming source material never becomes an automatic memory suggestion; each import is separately reviewed.

Selected harmless voice preferences can be persisted; the existing local voice controls remain the authority for runtime speech configuration. Theme/device/workflow/knowledge metadata is retained as encrypted replicas. Incoming themes offer a separate review through the existing desktop preference service and capability scope; no imported theme can change permissions or startup capture. Workflow replicas do not execute. This deliberately avoids background application of privacy/security-affecting settings.

Deletion retains content-free tombstones/cursors. Cloud historical entity payloads and memory revision content are scrubbed on deletion. A later deletion also removes older pending local inbox payloads. Local conflicts are shown rather than destructively resolved without owner review. Encrypted-file garbage collection is retryable and owner-scoped. Tombstones and idempotency metadata are not compacted automatically: retention/compaction requires reviewed multi-device acknowledgement/recovery policy.

## Key ownership and offline limitations

Windows DPAPI ciphertext never leaves its owner-bound local database. Approved transfers decrypt validated selected text locally, send it over reviewed TLS and re-encrypt it under the server's account key. Other devices use their own local encryption boundary. Server-managed encryption and full-service recovery exports are documented in [CLOUD_ARCHITECTURE](CLOUD_ARCHITECTURE.md); no cross-device DPAPI decryption or E2EE claim is made.

Cloud failure does not prevent local startup. Queue/cache data survives a desktop restart under DPAPI, while reusable cloud session credentials remain RAM-only. Offline deletion/revocation cannot reach a disconnected device immediately. Cached excerpts expire locally and are invalidated when a connected change/revocation is observed. Recovery of an old server export can reintroduce old data; keep clients disconnected during restore, reconcile tombstones against retained deletion records and re-authorize devices before resuming sync. Native SQL/production multi-device stress and real network fault/restore acceptance remain external gates.
