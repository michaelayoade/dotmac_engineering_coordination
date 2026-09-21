from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from dotmac_engineering_coordination.registry import EvidenceClass, load_registry
from dotmac_engineering_coordination.topology import (
    ContainerObservation,
    HostWorkloadObservation,
    WorkloadSnapshot,
    canonical_snapshot_json,
    load_provider_snapshot,
    load_workload_snapshot,
    provider_snapshot_from_contabo,
    render_markdown_census,
    render_mermaid_topology,
    topology_drift,
    workload_snapshot_from_probe,
)

DATA = Path(__file__).parents[1] / "src/dotmac_engineering_coordination/data"
OBSERVED_AT = datetime(2026, 9, 3, 9, 15, tzinfo=UTC)


def _provider_payload(*, ipv4: str = "149.102.158.167") -> str:
    return json.dumps(
        {
            "data": [
                {
                    "customerId": "discarded-customer-field",
                    "instanceId": 202400001,
                    "name": "vmi2988431",
                    "displayName": "erp dotmac",
                    "productId": "V95",
                    "productName": "Cloud VPS",
                    "dataCenter": "European Union 1",
                    "region": "EU",
                    "status": "running",
                    "ipConfig": {
                        "v4": {"ip": ipv4, "netmaskCidr": 21, "gateway": "x"},
                        "v6": {
                            "ip": "2a02:c207:3001:1::1",
                            "netmaskCidr": 64,
                            "gateway": "x",
                        },
                    },
                    "createdDate": "2025-01-02T03:04:05Z",
                    "cancelDate": None,
                    "sshKeys": [12345],
                    "macAddress": "discarded",
                }
            ]
        }
    )


def _private_network_payload() -> str:
    return json.dumps(
        {
            "data": [
                {
                    "privateNetworkId": 61441,
                    "name": "idp",
                    "cidr": "10.0.0.0/22",
                    "region": "UK",
                    "dataCenter": "United Kingdom",
                    "instances": [],
                    "customerId": "discarded-customer-field",
                }
            ]
        }
    )


def _workloads() -> WorkloadSnapshot:
    return WorkloadSnapshot(
        schema_version="dotmac.workload-snapshot.v1",
        observed_at=OBSERVED_AT,
        evidence_class=EvidenceClass.LIVE_OBSERVATION,
        hosts=(
            HostWorkloadObservation(
                host_id="erp",
                guest_hostname="vmi2988431",
                docker_available=True,
                containers=(
                    ContainerObservation(
                        name="dotmac_erp_app",
                        image="registry.dotmac.io/dotmac/erp@sha256:abc",
                        state="running",
                        runtime_status="Up 2 hours (healthy)",
                        health="healthy",
                    ),
                ),
            ),
        ),
    )


def test_contabo_response_is_reduced_to_safe_typed_provider_fields() -> None:
    registry = load_registry(DATA / "fleet.toml")
    snapshot = provider_snapshot_from_contabo(
        registry,
        _provider_payload(),
        observed_at=OBSERVED_AT,
        private_network_payload=_private_network_payload(),
    )
    assert snapshot.instances[0].host_id == "erp"
    assert str(snapshot.instances[0].ipv6) == "2a02:c207:3001:1::1"
    rendered = canonical_snapshot_json(snapshot)
    assert "discarded-customer-field" not in rendered
    assert "sshKeys" not in rendered
    assert "macAddress" not in rendered
    assert snapshot.private_networks[0].instance_ids == ()
    assert "discarded-customer-field" not in rendered


def test_unknown_provider_instance_is_visible_drift_not_silently_dropped() -> None:
    registry = load_registry(DATA / "fleet.toml")
    snapshot = provider_snapshot_from_contabo(
        registry,
        _provider_payload(ipv4="203.0.113.10"),
        observed_at=OBSERVED_AT,
        private_network_payload=_private_network_payload(),
    )
    drift = topology_drift(registry, snapshot, _workloads())
    assert drift.unknown_provider_host_ids == ("unmapped-instance-202400001",)
    assert "erp" in drift.missing_provider_host_ids


def test_mermaid_topology_has_a_positive_host_container_edge() -> None:
    registry = load_registry(DATA / "fleet.toml")
    provider = provider_snapshot_from_contabo(
        registry,
        _provider_payload(),
        observed_at=OBSERVED_AT,
        private_network_payload=_private_network_payload(),
    )
    rendered = render_mermaid_topology(registry, provider, _workloads())
    assert 'erp["erp<br/>vmi2988431<br/>production' in rendered
    assert "IPv4 149.102.158.167" in rendered
    assert "IPv6 2a02:c207:3001:1::1" in rendered
    assert 'erp_c0(["dotmac_erp_app<br/>' in rendered
    assert "erp --> erp_c0" in rendered
    assert "observe -.-> observe_workloads_missing" in rendered


def test_mermaid_topology_wires_proxmox_to_real_virtual_guests() -> None:
    registry = load_registry(DATA / "fleet.toml")
    provider = load_provider_snapshot(DATA / "provider_snapshot.json")
    workloads = load_workload_snapshot(DATA / "workload_snapshot.json")
    rendered = render_mermaid_topology(registry, provider, workloads)
    assert "provider_onprem_proxmox --> proxmox" in rendered
    assert 'proxmox_vm124(["qemu 124: dotmac-control-runner' in rendered
    assert "proxmox --> proxmox_vm124" in rendered
    planted = workloads.model_copy(
        update={
            "hosts": tuple(
                host.model_copy(update={"virtual_guests": ()})
                if host.host_id == "proxmox"
                else host
                for host in workloads.hosts
            )
        }
    )
    assert "proxmox --> proxmox_vm124" not in render_mermaid_topology(
        registry, provider, planted
    )


def test_topology_detector_bites_when_live_workload_wiring_is_deleted() -> None:
    registry = load_registry(DATA / "fleet.toml")
    provider = provider_snapshot_from_contabo(
        registry,
        _provider_payload(),
        observed_at=OBSERVED_AT,
        private_network_payload=_private_network_payload(),
    )
    positive = render_mermaid_topology(registry, provider, _workloads())
    planted_missing = render_mermaid_topology(
        registry,
        provider,
        WorkloadSnapshot(
            schema_version="dotmac.workload-snapshot.v1",
            observed_at=OBSERVED_AT,
            evidence_class=EvidenceClass.LIVE_OBSERVATION,
            hosts=(),
        ),
    )
    assert "erp --> erp_c0" in positive
    assert "erp --> erp_c0" not in planted_missing
    assert "erp -.-> erp_workloads_missing" in planted_missing


def test_workload_probe_parser_keeps_only_narrow_runtime_facts() -> None:
    payload = """BEGIN|erp|149.102.158.167
HOSTNAME|vmi2988431.contaboserver.net
DOCKER|true
CONTAINER|dotmac_erp_app|ghcr.io/example/erp:1|running|Up 2 hours (healthy)
ADDRESS4|eth0 UP 149.102.158.167/21
ADDRESS6|eth0 UP 2a02:c204:2298:8431::1/64
END|erp|0
"""
    snapshot = workload_snapshot_from_probe(payload, observed_at=OBSERVED_AT)
    assert snapshot.hosts[0].containers[0].health == "healthy"
    assert str(snapshot.hosts[0].addresses[1].address) == ("2a02:c204:2298:8431::1/64")


def test_workload_probe_parser_refuses_a_failed_ssh_result() -> None:
    payload = """BEGIN|erp|149.102.158.167
END|erp|255
"""
    try:
        workload_snapshot_from_probe(payload, observed_at=OBSERVED_AT)
    except ValueError as error:
        assert "exit 255" in str(error)
    else:
        raise AssertionError("failed SSH result was accepted")


def test_reviewed_snapshots_and_topology_are_exact_renderer_bytes() -> None:
    registry = load_registry(DATA / "fleet.toml")
    provider_path = DATA / "provider_snapshot.json"
    workload_path = DATA / "workload_snapshot.json"
    provider = load_provider_snapshot(provider_path)
    workloads = load_workload_snapshot(workload_path)
    assert provider_path.read_text() == canonical_snapshot_json(provider)
    assert workload_path.read_text() == canonical_snapshot_json(workloads)
    expected = (Path(__file__).parents[1] / "generated/fleet_topology.mmd").read_text()
    assert expected == render_mermaid_topology(registry, provider, workloads)
    expected_census = (
        Path(__file__).parents[1] / "generated/fleet_census.md"
    ).read_text()
    assert expected_census == render_markdown_census(registry, provider, workloads)


def test_live_snapshot_covers_all_hosts_and_exposes_ipv6_gap() -> None:
    registry = load_registry(DATA / "fleet.toml")
    provider = load_provider_snapshot(DATA / "provider_snapshot.json")
    workloads = load_workload_snapshot(DATA / "workload_snapshot.json")
    drift = topology_drift(registry, provider, workloads)
    assert len(provider.instances) == 20
    assert len(registry.hosts) == 27
    assert len(workloads.hosts) == 26
    assert sum(len(host.containers) for host in workloads.hosts) == 193
    assert sum(len(host.virtual_guests) for host in workloads.hosts) == 20
    proxmox = next(host for host in workloads.hosts if host.host_id == "proxmox")
    assert {guest.kind for guest in proxmox.virtual_guests} == {"qemu"}
    assert sum(guest.state == "running" for guest in proxmox.virtual_guests) == 19
    assert next(
        guest for guest in proxmox.virtual_guests if guest.vm_id == 124
    ).addresses
    assert drift.missing_guest_ipv4_host_ids == ()
    assert drift.missing_guest_ipv6_host_ids == ("nhia-moh-cloud",)
    assert drift.missing_provider_host_ids == ()
    assert drift.missing_workload_host_ids == ("dotmac-labs",)


def test_missing_declared_workload_renders_without_inventing_addresses() -> None:
    registry = load_registry(DATA / "fleet.toml")
    provider = load_provider_snapshot(DATA / "provider_snapshot.json")
    workloads = load_workload_snapshot(DATA / "workload_snapshot.json")
    rendered = render_markdown_census(registry, provider, workloads)
    assert (
        "| `dotmac-labs` | `not-applicable` | on-prem | "
        "`workload observation missing` |" in rendered
    )
    assert "160.119.127.249" not in rendered


def test_reviewed_snapshots_exclude_raw_provider_and_secret_fields() -> None:
    rendered = (DATA / "provider_snapshot.json").read_text() + (
        DATA / "workload_snapshot.json"
    ).read_text()
    for forbidden in (
        "customerId",
        "tenantId",
        "sshKeys",
        "macAddress",
        "client_secret",
        "api_password",
        "root_password",
    ):
        assert forbidden not in rendered
