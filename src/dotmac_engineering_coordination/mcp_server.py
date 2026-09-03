"""Read-only MCP adapter over the fleet registry.

Tool functions close over one immutable registry loaded at server creation. A
reload therefore has an explicit lifecycle: restart the service with reviewed
bytes. No tool mutates the registry, executes SSH, or dereferences OpenBao.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastmcp import FastMCP

from dotmac_engineering_coordination.registry import (
    FleetRefusal,
    FleetService,
    HostStatus,
    load_registry,
)
from dotmac_engineering_coordination.topology import (
    default_provider_snapshot_path,
    default_workload_snapshot_path,
    inspect_topology_host,
    load_provider_snapshot,
    load_workload_snapshot,
    render_markdown_census,
    render_mermaid_topology,
    topology_drift,
    topology_payload,
)

_READ_ONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}


def create_server(
    registry_path: Path | None = None,
    provider_snapshot_path: Path | None = None,
    workload_snapshot_path: Path | None = None,
) -> FastMCP:
    """Build the real server and wire every tool to one service instance."""
    service = FleetService(load_registry(registry_path))
    provider = load_provider_snapshot(
        provider_snapshot_path or default_provider_snapshot_path()
    )
    workloads = load_workload_snapshot(
        workload_snapshot_path or default_workload_snapshot_path()
    )
    server = FastMCP(
        name="Dotmac Engineering Coordination",
        instructions=(
            "Use fleet tools to discover hosts and request a safe access plan. "
            "No tool executes a connection or returns a secret value. A production "
            "plan requires the exact host id in confirm_production_host."
        ),
    )

    @server.tool(annotations=_READ_ONLY)
    def fleet_list(
        environment: str | None = None,
        production: bool | None = None,
        status: Literal["active", "reserved", "decommissioned"] | None = None,
    ) -> dict[str, object]:
        """List fleet hosts with evidence-classed, non-secret access metadata."""
        return service.list_hosts(
            environment=environment,
            production=production,
            status=HostStatus(status) if status is not None else None,
        )

    @server.tool(annotations=_READ_ONLY)
    def fleet_get(host_id: str) -> dict[str, object]:
        """Get one host by stable id; return a stable refusal when it is unknown."""
        try:
            return service.get_host(host_id)
        except FleetRefusal as refusal:
            return refusal.as_dict()

    @server.tool(annotations=_READ_ONLY)
    def fleet_access_plan(
        host_id: str,
        confirm_production_host: str | None = None,
    ) -> dict[str, object]:
        """Return a safe SSH argv plan; never execute it or retrieve a secret."""
        return service.access_plan_payload(
            host_id,
            confirm_production_host=confirm_production_host,
        )

    @server.tool(annotations=_READ_ONLY)
    def fleet_registry_health() -> dict[str, object]:
        """Report freshness, conflicts, and access-coverage debt by host id."""
        declaration_health = service.health()
        drift = topology_drift(service.registry, provider, workloads)
        drift_payload = drift.model_dump(mode="json")
        topology_ready = not any(drift_payload.values())
        declaration_ready = declaration_health["ready"] is True
        return {
            **declaration_health,
            "declaration_ready": declaration_ready,
            "topology_ready": topology_ready,
            "ready": declaration_ready and topology_ready,
            "topology_drift": drift_payload,
        }

    @server.tool(annotations=_READ_ONLY)
    def fleet_render_ssh_config() -> dict[str, object]:
        """Render deterministic SSH config for confirmed, verified active hosts."""
        return {"ok": True, "ssh_config": service.render_ssh_config()}

    @server.tool(annotations=_READ_ONLY)
    def fleet_inspect(host_id: str) -> dict[str, object]:
        """Join one declaration with its provider and live workload observations."""
        try:
            return inspect_topology_host(
                service.registry,
                provider,
                workloads,
                host_id,
            )
        except FleetRefusal as refusal:
            return refusal.as_dict()

    @server.tool(annotations=_READ_ONLY)
    def fleet_api_access(host_id: str) -> dict[str, object]:
        """Return declared API coordinates, status, and secret pointers only."""
        try:
            host = service.registry.by_id(host_id)
        except FleetRefusal as refusal:
            return refusal.as_dict()
        return {
            "ok": True,
            "host_id": host.host_id,
            "api_access": [item.model_dump(mode="json") for item in host.api_access],
        }

    @server.tool(annotations=_READ_ONLY)
    def fleet_topology(
        format: Literal["json", "mermaid", "markdown"] = "json",
    ) -> dict[str, object]:
        """Return the current evidence-classed fleet and container topology."""
        if format == "mermaid":
            return {
                "ok": True,
                "schema_version": "dotmac.fleet-topology.v1",
                "mermaid": render_mermaid_topology(
                    service.registry,
                    provider,
                    workloads,
                ),
            }
        if format == "markdown":
            return {
                "ok": True,
                "schema_version": "dotmac.fleet-topology.v1",
                "markdown": render_markdown_census(
                    service.registry,
                    provider,
                    workloads,
                ),
            }
        return topology_payload(service.registry, provider, workloads)

    return server


# The deployed entry point. Tests call this exact object through FastMCP's
# in-memory transport, so deleting create_server's wiring makes the suite red.
mcp = create_server()


def run() -> None:
    """Run the coordination MCP over stdio for local agent clients."""
    mcp.run(transport="stdio")


if __name__ == "__main__":  # pragma: no cover - exercised by the console script
    run()


__all__ = ["create_server", "mcp", "run"]
