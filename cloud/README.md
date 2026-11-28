# CLYDEX independent cloud service

Install the repository's headless `clydex` package and this package together in a separate Python 3.11+ environment. The desktop does not require the cloud server dependencies. Start only after protected operator configuration is supplied:

```text
python -m uvicorn clydex_cloud.api.app:create_app --factory --host 127.0.0.1 --no-access-log
python -m clydex_cloud.cli worker
```

Normal production traffic requires verified HTTPS at the private proxy and verified SQL TLS. The example command is a private backend listener, not a public deployment. Startup never creates databases, accounts, keys, models or desktop engines. Use `python -m clydex_cloud.cli` for explicit operator migration/provisioning/backup/recovery actions.

See [deployment](../docs/CLOUD_DEPLOYMENT_GUIDE.md), [architecture](../docs/CLOUD_ARCHITECTURE.md), [API contract](../docs/API_REFERENCE.md), [database](../docs/DATABASE_DESIGN.md), [vault](../docs/KNOWLEDGE_VAULT.md) and [sync](../docs/SYNCHRONIZATION_DESIGN.md). `openapi.json` is generated locally from the real routes; no external Swagger assets are required. Tests use synthetic data and simulated SQL by default; native SQL is a separately guarded acceptance test.
