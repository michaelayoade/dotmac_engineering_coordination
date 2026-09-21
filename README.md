# dotmac_engineering_coordination

The control-plane owner for short-lived engineering coordination and safe,
agent-facing infrastructure discovery. This repository is public by explicit
policy: its reviewed addresses, topology, SSH account names/routes, provider
resource identifiers, and secret pointers are non-secret operational metadata.
Every tracked byte must be safe for Internet publication; secret values remain
forbidden.

This first slice owns one declared artifact: the fleet registry. It gives an
agent a stable answer to “which servers exist, what are they for, and how may I
address them?” without ever returning a password, private key, bearer token, or
retrieved OpenBao value.

## Ownership boundary

- **This repository:** reviewed host identity, purpose, environment, addresses,
  safe SSH metadata, evidence class, freshness, and agent discovery tools.
- **Deployment Control:** desired deployment state, approvals, rollouts and
  deployment acknowledgements. A host id may be referenced there; this service
  does not decide a rollout.
- **OpenBao:** secret values. This registry may contain only a `bao://` pointer.
- **Knowledge:** durable lessons and a pointer to this owner, never a copied
  fleet table.
- **Live observers/providers:** observations. They do not silently rewrite the
  reviewed declaration.

## Commands

```console
dotmac-coordination check
dotmac-coordination list
dotmac-coordination get observe
dotmac-coordination access-plan observe
dotmac-coordination access-plan sub-prod --confirm-production-host sub-prod
dotmac-coordination render-ssh
dotmac-coordination topology --provider src/dotmac_engineering_coordination/data/provider_snapshot.json --workloads src/dotmac_engineering_coordination/data/workload_snapshot.json --format mermaid
dotmac-coordination-mcp
```

`access-plan` only prints an argument vector. It never runs SSH. Production
requires the caller to repeat the exact host id. Stale, conflicted, inactive or
access-unverified records refuse with a stable code.

Host recovery is a separate typed plan, not an optional password field on SSH.
Supported methods include provider, hypervisor and physical consoles, SSH
keys/certificates, and an OpenBao-held credential. A plan becomes `verified`
only with an owner decision, runbook, and dated live rehearsal evidence bound
to the exact host and recovery method. Its reference uses
`live:recovery-rehearsal:<host_id>:<method>[:<safe-token>]`; it cannot carry
free-form or secret material. Existing
OpenBao pointers remain `declared` until that proof exists; missing and
unverified plans keep declaration health red rather than manufacturing
coverage. Verified rehearsals also become unready when their timestamps are in
the future or older than the registry's configured maximum age.

The non-disruptive rehearsal procedures live under `docs/recovery/`. They
separate proving console reachability from any restart, rescue boot, password
reset or other production mutation.

`generated/ssh_config` is the reviewed renderer output. CI byte-compares it
with the typed registry; consumers include that fragment from their own SSH
configuration rather than maintaining another host map.

The registry defaults to the packaged `data/fleet.toml`. Set
`DOTMAC_FLEET_REGISTRY` to an explicit non-secret file path to use another
reviewed registry.

## MCP tools

- `fleet_list`
- `fleet_get`
- `fleet_access_plan`
- `fleet_registry_health`
- `fleet_render_ssh_config`
- `fleet_inspect`
- `fleet_api_access`
- `fleet_topology`

All are annotated read-only and closed-world. The server has no tool that
connects to a host or dereferences a secret pointer.

The fleet joins three explicit evidence classes: 28 reviewed declarations in
`fleet.toml`, a safe-field 20-instance Contabo provider snapshot, and a
read-only guest/container snapshot covering those VPS hosts, Seabone, the
single-node Proxmox cluster, and all 20 QEMU guests. Five guests with verified
SSH routes are also first-class declarations; the other 15 remain observed
guests until their coordinates and access are proven.
`generated/fleet_topology.mmd` is rendered from those inputs, and
`generated/fleet_census.md` is the corresponding review table, including safe
SSH/OpenBao/API pointers; neither is maintained as a second fleet map.

The Proxmox host exposes two verified read paths: `ssh proxmox pvesh` and the
HTTPS API. The latter uses the dedicated non-root
`fleet-inventory@pve!agent-fleet-readonly` token, with `PVEAuditor` applied
to both the user and privilege-separated token. Its value exists only in
OpenBao at `bao://secret/dotmac/proxmox/fleet-inventory#api_token`; the
registry and MCP expose that pointer, never the value. Cutover evidence
includes a 20-guest inventory read and an HTTP 403 for a planted same-value
user update.

See [`docs/AGENT_SETUP.md`](docs/AGENT_SETUP.md) for Codex registration and the
generated SSH-config include. The repository does not modify an agent's global
configuration automatically.

## Validation

```console
python -m pytest
ruff check .
mypy src
dotmac-coordination check
```
