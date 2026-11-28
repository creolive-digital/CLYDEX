# SQL Server deployment boundary

The canonical, version-controlled migration is packaged at
`cloud/src/clydex_cloud/repositories/migrations/001_core.sql`, with its reverse script beside it.
`scripts/generate_cloud_schema.py` regenerates those files from SQLAlchemy metadata. Review the diff;
the operator migrator validates its SHA-256 and uses one SERIALIZABLE transaction. Startup never creates tables.
This location avoids two divergent copies of the same DDL and keeps the cloud wheel independently deployable.

Use SQL Server 2025 (17.x), a supported Ubuntu deployment, a dedicated database and least-privilege API identity.
Install ODBC Driver 18 and a trusted server certificate; require `Encrypt=yes&TrustServerCertificate=no`.
Do not supply `sa` credentials to the API. Provisioning the database/login/grants is an owner-operated step.
Use a separate migration identity with DDL rights; runtime needs only SELECT/INSERT/UPDATE/DELETE on `clx_*` tables.
No seeds, default passwords, live connections, automatic edition selection or preview feature enablement are provided.

Review [database design](../../docs/DATABASE_DESIGN.md) and [deployment/recovery](../../docs/CLOUD_DEPLOYMENT_GUIDE.md)
before applying anything. Empty-schema rollback is explicit; populated rollback must use a validated recovery export.
