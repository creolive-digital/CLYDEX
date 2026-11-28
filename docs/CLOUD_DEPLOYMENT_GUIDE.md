# Private Linux deployment and recovery

## Phase 06 boundary (2026-11-28)

Phase 06 adds local operating services and backward-compatible workflow data contracts only. It does not deploy the VPS, run production SQL migrations or expose a public Windows/workflow-control endpoint. Existing hosting/license/key-custody/TLS and live acceptance approvals remain required.

These are prepared engineering configurations, **not a deployed service**. No VPS, DNS, public ports, paid service, production database, SQL container image, license or large model was activated. The automatic GitHub Actions workflow remains removed. Use local verification scripts. Before deployment, the owner must approve hosting costs, production SQL edition/terms, ODBC terms, image digests, certificates, retention/recovery ownership and private-data activation.

## Selected topology and prerequisites

Use a supported Ubuntu host for SQL Server 2025, private SQL connectivity and a separate non-root FastAPI/worker Docker Compose deployment behind nginx TLS. This implements the approved VPS filesystem architecture without changing databases or introducing a vector service. SQL may run as the supported Ubuntu system service; Compose deliberately does not provision SQL or choose its edition. Keep SQL off public interfaces/firewalls. The Windows client never connects directly to SQL.

Install ODBC Driver 18 with its terms explicitly accepted, a trusted SQL server certificate and the matching CA in the API image. SQL connections require verified TLS; never fix certificate errors by setting `TrustServerCertificate=yes`. `deployment/linux/mssql.conf.example` supplies force-encryption/TLS paths. Bind/firewall SQL to the API's private network only and restrict administration to the owner's management channel. Certificate CN/SAN must match the DSN hostname. [Microsoft encrypted Linux connections](https://learn.microsoft.com/en-us/sql/linux/security/encrypted-connections?view=sql-server-ver17).

Production edition/licensing remains unresolved. Developer is not a production entitlement; the [edition and vector gates](DATABASE_DESIGN.md) must pass on the actual chosen build. Budget RAM/disk for SQL, API, bounded parser children, originals, indexes and backup duplication. No measured production sizing is supplied. A local embedding service is optional and off; no model is installed, pulled or licensed by these templates.

## Private paths and identities

Recommended operator-created paths, all outside source and web roots:

| Path | Purpose and ownership |
|---|---|
| `/srv/clydex/data` | Private persistent vault, UID/GID 10001, directory mode 0700 |
| `/srv/clydex/keys` | Independent `master.key`, `auth.key` files, 32 bytes each, mode 0600, API-readable and mounted read-only |
| `/srv/clydex/operator/database-url` | Protected DSN file, mode 0600, separate from keys/data; use a dedicated least-privilege identity |
| `/srv/clydex/tls` | nginx certificates/private key, appropriate restricted ownership, never committed |
| `/srv/clydex/backups` | Encrypted owner recovery exports, mode 0700, not a web/static mount |

Separate system identities/grants are required for SQL migrations versus runtime. Runtime needs SELECT/INSERT/UPDATE/DELETE on `clx_*` tables and no `sa`, server-admin, arbitrary OS or schema modification rights. Migration credentials are an explicit operator resource, not the API DSN. Set POSIX ownership on host-mounted files; Docker file-secret permission hints alone may not change host permissions. Windows development permission tests do not establish Linux ACL correctness.

The protected URL file follows this **placeholder-only** form:

```text
mssql+pyodbc://CLX_RUNTIME_USER:URL_ENCODED_OWNER_SUPPLIED_VALUE@PRIVATE_SQL_HOST/CLYDEX?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no
```

Do not put real credentials in an env file, command argument, history, repository or logs. URL-encode actual credentials with an operator-owned secret tool. No default password/admin account is supplied.

## Build and initialize after approval

1. Run `scripts/verify_phase05.ps1` locally using the isolated cloud Python interpreter. Review the generated OpenAPI and migration diff. Select reviewed immutable Python 3.13/Debian 12 and nginx image digests; Linux image builds and dependency compatibility still need verification. `cloud/requirements-runtime.lock` pins the captured runtime dependency resolution; review/rebuild it deliberately when upgrading.
2. Build from repository root with `deployment/docker/Dockerfile`. Supply `PYTHON_IMAGE=<reviewed digest>`, `ACCEPT_ODBC_EULA=YES` only after accepting the terms, and BuildKit secret `sql_ca=<path to public SQL CA PEM>`. Only the public CA is baked into the image; SQL/private/TLS keys are not. The Docker context allowlist excludes the archive, user data, credentials, tests and frontend artifacts. The root headless package and cloud package install together; do not resolve an unrelated `clydex` package from a public registry.
3. Provision the approved **empty dedicated database** and migration identity through the owner's SQL administration process. With protected migration DSN mounted, run `python -m clydex_cloud.cli migrate`. Startup never applies DDL. Switch the runtime to its restricted identity afterward. Validate native migrations/constraints/rollback/vectors using the separately guarded disposable test suite before putting user content in SQL.
4. Initialize separate key files using the interactive operator environment: `python -m clydex_cloud.cli keys`. It refuses replacement. Back up recovery ownership immediately; do not generate new keys against existing encrypted data. Provision the personal account with `python -m clydex_cloud.cli provision`; password input is hidden and the one-time recovery code is intentionally shown once to the operator for offline storage. Do not run this in a logged unattended pipeline. Registration remains disabled.
5. Copy `deployment/linux/cloud.env.example` to a private operator location, set the approved host and absolute protected paths, and configure the required Compose substitutions. Match nginx `server_name` to `CLYDEX_PUBLIC_HOST`. Start one API process and one owned worker. API inline workers stay at zero when the separate worker runs. The Compose API is not host-published; its reverse proxy defaults to **loopback port 8443**. Public port/DNS changes require separate owner approval.
6. Verify valid TLS chains/hostname, `healthz`, `readyz`, login/rotation/revocation, quotas, parser limits, encrypted files, audit/log privacy, backups/restore and shutdown on that exact Linux/SQL build. Set the desktop's HTTPS origin, review enabling it and sign in. Category sync stays off until explicitly reviewed.

The private Compose network is `172.31.55.0/28`; Uvicorn trusts forwarding only there, and nginx replaces Host/X-Forwarded-Proto/X-Forwarded-For. Review conflicts before changing subnets and update both sides together. Do not expose port 8000 directly: otherwise a caller could forge proxy metadata. This is one process with per-process rate limits, not a horizontally scaled cluster. `docker compose config` is a local structural check, not deployment/TLS acceptance.

## Retention and secrets

Original documents/versions remain until explicit owner deletion. Files are removed through retryable garbage records; quota is released only after physical cleanup. Sync tombstones/idempotency metadata are retained to prevent stale resurrection/replay. Deleted cloud entity histories are scrubbed of private payloads, but previously exported backups remain separate copies. Set `CLYDEX_AUDIT_RETENTION_DAYS` (0 = retain, 1–3650 = worker cleanup); request logs contain metadata only and Compose rotates them. Cache retention is selected per document on each device.

Do not rotate master/auth files by replacing bytes: owner-key wrappers and login/credential HMACs depend on them. A reviewed master-key rewrap/auth-key migration is required for a live rotation; no automatic key-rotation claim is made. Compromise response includes revoking sessions/devices, isolating the service and reviewing data/key exposure. Loss of keys and recovery passphrases can permanently lose the vault. Host/disk/TDE encryption and external penetration testing remain deployment decisions.

## Encrypted backup and tested logical recovery

Stop API/worker for an operator maintenance snapshot. Run `deployment/linux/backup.sh /private/backups/new-export.clxrec` in the protected operator environment. It prompts for a 16–1024-character recovery passphrase; use a strong independently held passphrase. The bounded `CLXREC1` format uses fixed scrypt parameters (N=32768, r=8, p=1), random salt/nonce and AES-GCM over the manifest, SQL rows, encrypted file objects and recovery key material. Connection strings and operator passwords are not included. This is a **full-service** recovery export, not a per-account public download. It caps at 256 MiB and 100,000 rows/table; larger deployments need a reviewed streaming/native backup strategy rather than silent truncation.

Copy encrypted exports to owner-controlled protected backup storage and retain the passphrase separately. Set a deliberate number/age/retention schedule; none is silently activated. Keep metadata/checksums and deletion records outside older exports as appropriate. Backup metadata is recorded only after the export is written. Test copies and recovery passphrase regularly; merely creating a file is not proof of restore.

For restore, keep clients disconnected. Create a separate empty migrated database, empty vault and empty independent key directory; mount the operator DSN outside that key directory. Run `deployment/linux/restore.sh <export>`. It authenticates the envelope, validates tables/columns/file identities/checksums and original content, restores inside a transaction, cleans only newly created files on failure, and revokes every recovered session/device/pairing. Login credentials remain the recovered password hashes; reauthorize devices separately. Never point this command at a populated production target.

An actual isolated synthetic logical export/restore test has passed, including original content/checksum, wrong-passphrase/tamper rejection, refusal to overwrite, login recovery and old-session revocation. It used simulated SQL storage. **Native SQL Server `.bak` backup/restore, live SQL logical restore/identity handling, Linux filesystem recovery and disaster recovery timing are unverified.** Do not describe those as passed. SQL native backup/TDE/backup encryption requires the chosen edition, separate key handling and an actual isolated restore before production acceptance.

## Local verification commands

```powershell
python -m venv "$env:LOCALAPPDATA/CLYDEX/tmp/cloud-dev"
# Explicit development installation; no models, providers or infrastructure activated:
& "$env:LOCALAPPDATA/CLYDEX/tmp/cloud-dev/Scripts/python.exe" -m pip install -e . -e './cloud[test]'
./scripts/verify_phase05.ps1 -CloudPython "$env:LOCALAPPDATA/CLYDEX/tmp/cloud-dev/Scripts/python.exe"
```

The optional native SQL suite stays skipped unless the owner sets `CLYDEX_ALLOW_ISOLATED_SQL_TESTS=true` and supplies `CLYDEX_TEST_SQL_URL_FILE` for an empty disposable `clx_phase05_*` database. Never reuse the workstation's existing SQL service merely because it is installed. Native Windows screenshots test desktop rendering/bridge/DPAPI; they do not establish Linux, real SQL, Internet TLS, production security or audio/model acceptance.
