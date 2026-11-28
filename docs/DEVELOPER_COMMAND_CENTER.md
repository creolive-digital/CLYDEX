# Developer Command Center

The React Developer Center combines native selections, reviewed profiles, the installed tool console and selected-content analysis through the existing IntelligenceCoordinator. Defaults are read-only/disabled. Local selections expire after 30 minutes and are cleared on lock. Re-select paths after restarting; handles are intentionally not portable credentials.

| Area | Delivered behavior | Qualification |
|---|---|---|
| Codex / documentation / logs / error analysis / code review / ticket assistance | Explicit selected UTF-8 content, normal read approval, then existing provider/outbound policy and structured answer | No new AI engine, automatic file upload, ticket-system mutation or live inference claim |
| Git | Status, 20-entry history, bounded actual diff, branches, clean-workspace branch create/switch | Argument vectors; hooks/fsmonitor/external diff/textconv disabled, configured filters refused for switching. Push/reset/merge/release are not exposed by this adapter |
| GitHub | Selected repository metadata, issues and individually reviewed issue creation | Official REST codec; credentials/scopes/accounts and live acceptance pending |
| SQL Server | Explicit read/write/schema profiles, Credential Manager password, ODBC 18 with verified TLS, transaction and bounded child timeout/results | Native SQL remains unverified. Read classifier is conservative and is not SQL authorization; least-privilege server credentials are mandatory |
| REST / Azure | Selected HTTPS endpoint GET/reviewed POST; Reader resource-group inventory | No arbitrary credential header/route dispatch or TLS bypass; OAuth issuance/live service acceptance pending |
| Windows / IIS | Fixed services, adapter status, own-process counters and IIS website diagnostics | IIS module/service availability unverified; no elevated shell |
| PowerShell / Python | Owner-selected `.ps1` / `.py`, checksum and exact source review; owned process, output/time/memory bounds | Executes trusted code with this OS user's authority. No sandbox claim; PowerShell policy is not bypassed |
| Docker | Explicit context inventory/client version; reviewed exact-container start/stop/restart | No `exec`, arbitrary `run`, mount, image pull, delete or implicit daemon selection |
| SSH | Explicit host/user/native-selected known-hosts/key; fixed uptime/disk/memory; reviewed literal service restart | Strict host-key checks, batch mode, no forwarding or automatic trust/elevation; live hosts unverified |

Example disabled SQL profile (non-secret):

```json
{"name":"Selected read-only SQL","kind":"sql","enabled":false,"server":"tcp:sql.example,1433","database":"SelectedDatabase","user":"least_privilege_reader","mode":"read","least_privilege_attested":true}
```

Use SQL Server's supported server syntax, for example `tcp:sql.example,1433`, when configuring a real approved profile. The example is illustrative, not a deployed connection. Store its password using **Owner-provisioned credential**, not JSON. Separate `write` and `schema` identities/scopes are required. Read mode permits a single conservative SELECT; ambiguous statements, literals/comments, dynamic/external data sources and SELECT INTO are refused. Write/schema actions are owner-reviewed SQL, not an SQL sandbox. Server-side permissions must remain least privilege. No real database was contacted for acceptance.

Windows profile: `{"name":"Local diagnostics","kind":"windows","enabled":false}`. Docker adds `"context":"explicit-context"`. SSH requires `host`, `user`, `known_hosts` and `key`; the last two are current native file-selection UUIDs. Review/save disabled, reload the record, then explicitly enable through another configuration review. Profiles and local selections do not synchronize. Credentials never appear in SQL child arguments or logs.

The private frozen helper mode dispatches only fixed SQL/capture/plugin/Python-script operations. It restores inherited pipes in the windowed executable and starts no Core/voice/queue. Parent-owned Windows jobs bound descendants, time, output and aggregate committed memory for executable code. This is resource ownership, not protection from hostile code running as the same user. Optional ODBC/OpenCV libraries and real external service qualification remain separate.
