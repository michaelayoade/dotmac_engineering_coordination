# Agent setup

The MCP server is local and STDIO-only in this slice. It opens no listening
socket and needs no token. It reads the packaged fleet registry once at startup
and exposes read-only tools.

## Codex

Current Codex supports local STDIO servers through `codex mcp add` or an
`[mcp_servers.<name>]` table. Install this repository into an environment
outside the governed source tree, then register that executable:

```console
codex mcp add dotmacFleet -- /absolute/path/to/venvs/dotmac-engineering-coordination/bin/dotmac-coordination-mcp
codex mcp list
```

Equivalent configuration:

```toml
[mcp_servers.dotmacFleet]
command = "/absolute/path/to/venvs/dotmac-engineering-coordination/bin/dotmac-coordination-mcp"
cwd = "/absolute/path/to/dotmac_engineering_coordination"
required = true
enabled = true
enabled_tools = [
  "fleet_list",
  "fleet_get",
  "fleet_access_plan",
  "fleet_registry_health",
  "fleet_render_ssh_config",
  "fleet_inspect",
  "fleet_api_access",
  "fleet_topology",
]
default_tools_approval_mode = "auto"
startup_timeout_sec = 20
tool_timeout_sec = 30
```

Codex reads MCP configuration from `~/.codex/config.toml` or a trusted
project's `.codex/config.toml`. Start a fresh local session after changing the
configuration, then inspect `/mcp` or run `codex mcp list`. Configuration does
not inject tools into a session that is already running.

Official reference:
<https://learn.chatgpt.com/docs/extend/mcp?surface=cli>

## Generated SSH config

Include the reviewed fragment from the local machine's SSH configuration:

```sshconfig
Include /absolute/path/to/dotmac_engineering_coordination/generated/ssh_config
```

The fragment contains only hostnames, account names, ports and identity
pointers. It does not contain a private key or secret. An identity pointer is a
declaration; each machine still needs the corresponding local key material
through its approved bootstrap.

`seabone` and `proxmox` are included. The latter uses `ProxyJump seabone` and
the separately declared local key pointer. For read-only Proxmox inventory,
use the verified SSH-backed API path (`ssh proxmox pvesh ...`) or inspect the
verified HTTPS coordinate and OpenBao pointer through
`fleet_api_access("proxmox")`. The HTTPS identity is non-root and limited to
`PVEAuditor`; its value is not exposed by this MCP.

Do not copy the fragment into another repository. Regenerate it from the typed
registry and review the byte diff:

```console
dotmac-coordination render-ssh
```

## Production rule

An MCP tool call for a production access plan must include the exact id twice:

```json
{
  "host_id": "erp",
  "confirm_production_host": "erp"
}
```

That returns `argv: ["ssh", "erp"]`; it still does not execute the command.
The agent's existing rule remains in force: Michael must name the production
target before any SSH tool is called.
