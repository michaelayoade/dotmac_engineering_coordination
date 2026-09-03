from __future__ import annotations

from pathlib import Path

import pytest
from fastmcp import Client, FastMCP

from dotmac_engineering_coordination.mcp_server import create_server, mcp

DATA = Path(__file__).parents[1] / "src/dotmac_engineering_coordination/data/fleet.toml"
REQUIRED_TOOLS = {
    "fleet_list",
    "fleet_get",
    "fleet_access_plan",
    "fleet_registry_health",
    "fleet_render_ssh_config",
    "fleet_inspect",
    "fleet_api_access",
    "fleet_topology",
}


def _assert_required_tools(names: set[str]) -> None:
    assert (
        REQUIRED_TOOLS <= names
    ), f"fleet MCP wiring missing: {sorted(REQUIRED_TOOLS - names)}"


async def _tool_names(server: FastMCP) -> set[str]:
    async with Client(server) as client:
        return {tool.name for tool in await client.list_tools()}


@pytest.mark.asyncio
async def test_real_mcp_entrypoint_wires_every_fleet_tool() -> None:
    _assert_required_tools(await _tool_names(mcp))


@pytest.mark.asyncio
async def test_wiring_detector_fails_when_the_tools_are_deleted() -> None:
    planted = FastMCP("planted-missing-wiring")
    with pytest.raises(AssertionError, match="fleet MCP wiring missing"):
        _assert_required_tools(await _tool_names(planted))


@pytest.mark.asyncio
async def test_real_protocol_call_returns_the_registry_positive_control() -> None:
    server = create_server(DATA)
    async with Client(server) as client:
        result = await client.call_tool("fleet_list", {"environment": "production"})
    assert result.data["ok"] is True
    assert result.data["count"] > 0
    assert any(host["host_id"] == "erp" for host in result.data["hosts"])


@pytest.mark.asyncio
async def test_fastmcp_advertises_every_required_parameter_it_validates() -> None:
    server = create_server(DATA)
    async with Client(server) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
    for name in (
        "fleet_get",
        "fleet_access_plan",
        "fleet_inspect",
        "fleet_api_access",
    ):
        schema = tools[name].inputSchema
        assert "host_id" in schema["properties"]
        assert "host_id" in schema["required"]


@pytest.mark.asyncio
async def test_mcp_preserves_the_production_refusal_code_end_to_end() -> None:
    server = create_server(DATA)
    async with Client(server) as client:
        result = await client.call_tool("fleet_access_plan", {"host_id": "erp"})
    assert result.data == {
        "ok": False,
        "refusal": {
            "code": "FLEET_PRODUCTION_CONFIRMATION_REQUIRED",
            "message": (
                "production access requires confirm_production_host to equal 'erp'"
            ),
        },
    }


@pytest.mark.asyncio
async def test_real_protocol_call_reaches_live_workload_observation() -> None:
    server = create_server(DATA)
    async with Client(server) as client:
        result = await client.call_tool("fleet_inspect", {"host_id": "son-erp"})
    assert result.data["ok"] is True
    assert result.data["provider_observation"]["status"] == "running"
    names = {item["name"] for item in result.data["workload_observation"]["containers"]}
    assert "son_erp_app" in names


@pytest.mark.asyncio
async def test_real_protocol_exposes_proxmox_api_truth_without_a_secret() -> None:
    server = create_server(DATA)
    async with Client(server) as client:
        result = await client.call_tool("fleet_api_access", {"host_id": "proxmox"})
    by_name = {item["name"]: item for item in result.data["api_access"]}
    assert by_name["proxmox-cluster-via-pvesh"]["status"] == "verified"
    assert by_name["proxmox-https-api"]["status"] == "unavailable"
    assert by_name["proxmox-https-api"]["credential_ref"] is None


@pytest.mark.asyncio
async def test_fleet_health_stays_red_for_missing_guest_ipv6() -> None:
    server = create_server(DATA)
    async with Client(server) as client:
        result = await client.call_tool("fleet_registry_health", {})
    assert result.data["declaration_ready"] is True
    assert result.data["topology_ready"] is False
    assert result.data["ready"] is False
    assert result.data["topology_drift"]["missing_guest_ipv6_host_ids"] == [
        "nhia-moh-cloud"
    ]
