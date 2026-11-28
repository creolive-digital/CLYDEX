# Workflow schema v2

The executable local schema is a deliberately constrained data contract. `automation/workflows/schema.py` is authoritative; the cloud reuses validation without importing or constructing a desktop engine. See [local_health.json](../examples/workflows/local_health.json) for a complete original synthetic example.

Required root fields: `contract_version` (integer 2), canonical UUID `id`, `name`, explicit object JSON Schema `inputs`, `nodes`, `edges`, and integer `timeout` 1–300. No extra root/node/config/edge fields are permitted. Enablement, credential references, permission grants and approvals are not part of the portable workflow contract.

Every node has `id`, `kind`, `config`, numeric bounded `x`,`y`. IDs use ASCII letters/digits/underscore/hyphen and must be unique; `inputs` and `iteration` are reserved. Coordinates affect presentation only. Edges have `from`, `to`, `port`; ports are `true`/`false` after conditions and `next` otherwise. Cycles and duplicate edges are rejected. Use an explicit bounded loop node for repetition.

| Kind | Exact config |
|---|---|
| input | `{}`; returns validated inputs |
| note | `{"text":"Literal note"}` |
| tool | `{"tool":"installed.id","arguments":{}}` |
| condition | `{"left":1,"operator":"eq","right":1}` |
| delay | `{"seconds":1}` |
| approval | `{"message":"Review this checkpoint"}` |
| loop | `{"count":2,"tool":"installed.id","arguments":{}}` |
| output | `{"value":{"$ref":"upstream.field"}}` |

References are exact single-property objects, never interpolated strings or code. They select object fields from `inputs`, a transitive predecessor, or loop-only `iteration.index`. Tool arguments resolve, then undergo the installed tool's validation before every invocation. Loop results are bounded arrays; no implicit recursive loops or arbitrary expression evaluation exists.

Condition operators: `eq`, `ne` (type-sensitive), numeric `gt`,`gte`,`lt`,`lte`, `contains`, `exists`. `exists` tests whether the resolved value is non-null; unresolved references still fail. Boolean values are not numbers. Inputs and tool/plugin/MCP schemas use the documented bounded JSON Schema subset: types, explicit properties/required/additionalProperties, array items, enums and numeric/length/count bounds. References/composition/regex and external schema resolution are unsupported and fail closed.

`workflow.preview` validates and returns an effect inventory/time bound with `effects_executed:0`; it never contacts a provider, service or plugin. Invalid previews return fixed validator explanations. `workflow.save` reviews and CAS-saves disabled; `workflow.enable` reviews the exact local definition. `workflow.run` executes only the saved enabled version with separately validated inputs. Save while editing does not execute. `workflow.restore` reviews a retained revision and creates a new disabled version.

V1 workflow replicas contain only input/note/output text. Explicit migration converts these to inert notes with a new local identity; cyclic/invalid contracts require correction. V2 synchronization excludes secret-like/authority fields and recognized credential patterns; this conservative filter cannot recognize every secret embedded in arbitrary literal text. Do not place credentials in workflow constants. Use reviewed profiles and Credential Manager. Local selections are device/session-bound and must be re-bound after import; cloud arrival never authorizes execution.
