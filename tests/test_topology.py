from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from dotmac_engineering_coordination.registry import EvidenceClass, load_registry
from dotmac_engineering_coordination.topology import (
    ContainerObservation,
    HostWorkloadObservation,
    WorkloadSnapshot,
    canonical_snapshot_json,
    host_workload_observed_at,
    load_provider_snapshot,
    load_workload_snapshot,
    provider_snapshot_from_contabo,
    refresh_workload_observation,
    render_markdown_census,
    render_mermaid_topology,
    topology_drift,
    upsert_workload_observation,
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
        schema_version="dotmac.workload-snapshot.v2",
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
            schema_version="dotmac.workload-snapshot.v2",
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
    assert len(registry.hosts) == 28
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
    assert drift.missing_workload_host_ids == ("dotmac-labs", "garki-core")


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


def test_host_workload_observed_at_rejects_a_naive_timestamp() -> None:
    with pytest.raises(ValidationError, match="must include a timezone"):
        HostWorkloadObservation(
            host_id="erp",
            guest_hostname="vmi2988431",
            docker_available=True,
            containers=(),
            observed_at=datetime(2026, 9, 21, 12, 0),  # naive datetime
        )


def test_host_workload_observed_at_falls_back_to_the_document_sweep_time() -> None:
    """A host that has never been individually refreshed since the last full
    sweep must report that sweep's own time, not None and not "now"."""
    snapshot = _workloads()
    never_individually_refreshed = snapshot.hosts[0]
    assert never_individually_refreshed.observed_at is None
    effective = host_workload_observed_at(snapshot, never_individually_refreshed)
    assert effective == OBSERVED_AT


def test_host_workload_observed_at_prefers_the_hosts_own_later_timestamp() -> None:
    snapshot = _workloads()
    refreshed_later = datetime(2026, 9, 21, 15, 0, tzinfo=UTC)
    individually_refreshed = snapshot.hosts[0].model_copy(
        update={"observed_at": refreshed_later}
    )
    effective = host_workload_observed_at(snapshot, individually_refreshed)
    assert effective == refreshed_later


def test_refresh_workload_observation_replaces_only_the_named_host() -> None:
    """The whole point of this function: refreshing one host's workload data
    must never touch any other host's observation, and must never advance
    the document's own last-full-sweep observed_at -- that field staying
    still is how a caller tells "still just the last sweep" apart from "this
    host was independently refreshed since"."""
    baseline = WorkloadSnapshot(
        schema_version="dotmac.workload-snapshot.v2",
        observed_at=OBSERVED_AT,
        evidence_class=EvidenceClass.LIVE_OBSERVATION,
        hosts=(
            HostWorkloadObservation(
                host_id="erp",
                guest_hostname="vmi2988431",
                docker_available=True,
                containers=(),
            ),
            HostWorkloadObservation(
                host_id="dotmac-labs",
                guest_hostname="stale-hostname",
                docker_available=False,
                containers=(),
            ),
        ),
    )
    refreshed_at = datetime(2026, 9, 21, 15, 30, tzinfo=UTC)
    refreshed_labs = HostWorkloadObservation(
        host_id="dotmac-labs",
        guest_hostname="dotmac-labs",
        docker_available=True,
        containers=(
            ContainerObservation(
                name="academy-lab-worker",
                image="n/a",
                state="running",
                runtime_status="Up 1 hour",
                health=None,
            ),
        ),
        observed_at=refreshed_at,
    )

    updated = refresh_workload_observation(baseline, refreshed_labs)

    assert updated.observed_at == OBSERVED_AT  # last full sweep time: untouched
    by_host = {item.host_id: item for item in updated.hosts}
    assert by_host["erp"] == baseline.hosts[0]  # byte-identical, not just equal-ish
    assert by_host["dotmac-labs"].guest_hostname == "dotmac-labs"
    assert by_host["dotmac-labs"].docker_available is True
    assert host_workload_observed_at(updated, by_host["dotmac-labs"]) == refreshed_at
    # erp's own effective timestamp still falls back to the untouched sweep time.
    assert host_workload_observed_at(updated, by_host["erp"]) == OBSERVED_AT


def test_refresh_workload_observation_refuses_without_its_own_timestamp() -> None:
    baseline = _workloads()
    no_timestamp = HostWorkloadObservation(
        host_id="erp",
        guest_hostname="vmi2988431",
        docker_available=True,
        containers=(),
    )
    with pytest.raises(ValueError, match="must set its own observed_at"):
        refresh_workload_observation(baseline, no_timestamp)


def test_refresh_workload_observation_refuses_a_host_never_before_observed() -> None:
    """Adding a brand-new host's first-ever observation is a full probe's
    job; a targeted refresh may only narrow an existing gap."""
    baseline = _workloads()
    brand_new_host = HostWorkloadObservation(
        host_id="never-seen-before",
        guest_hostname="ghost",
        docker_available=False,
        containers=(),
        observed_at=datetime(2026, 9, 21, 15, 30, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="not present in the baseline"):
        refresh_workload_observation(baseline, brand_new_host)


def test_upsert_workload_observation_records_a_declared_hosts_first_observation() -> (
    None
):
    """The real Dotmac Labs gap this function exists to close: the fleet
    registry already declares "dotmac-labs", but no fleet-wide probe has
    ever observed it, so it is simply absent from the workload baseline --
    not present with stale data. A registry-aware upsert must admit exactly
    this case without touching any other host or the document sweep time."""
    registry = load_registry(DATA / "fleet.toml")
    assert any(host.host_id == "dotmac-labs" for host in registry.hosts)
    baseline = _workloads()
    assert not any(host.host_id == "dotmac-labs" for host in baseline.hosts)
    first_observed_at = datetime(2026, 9, 21, 18, 0, tzinfo=UTC)
    first_observation = HostWorkloadObservation(
        host_id="dotmac-labs",
        guest_hostname="dotmac-labs",
        docker_available=True,
        containers=(
            ContainerObservation(
                name="clab-academy-r1",
                image="ghcr.io/example/routeros:1",
                state="running",
                runtime_status="Up 3 hours",
                health=None,
            ),
        ),
        observed_at=first_observed_at,
    )
    merged = upsert_workload_observation(registry, baseline, first_observation)
    assert merged.observed_at == baseline.observed_at
    by_host = {host.host_id: host for host in merged.hosts}
    assert len(merged.hosts) == len(baseline.hosts) + 1
    assert by_host["dotmac-labs"] == first_observation
    for original in baseline.hosts:
        assert by_host[original.host_id] == original


def test_upsert_workload_observation_still_replaces_an_already_observed_host() -> None:
    registry = load_registry(DATA / "fleet.toml")
    baseline = _workloads()
    already_observed = baseline.hosts[0]
    refreshed_at = datetime(2026, 9, 21, 18, 0, tzinfo=UTC)
    refreshed = already_observed.model_copy(update={"observed_at": refreshed_at})
    merged = upsert_workload_observation(registry, baseline, refreshed)
    assert len(merged.hosts) == len(baseline.hosts)
    by_host = {host.host_id: host for host in merged.hosts}
    assert by_host[already_observed.host_id] == refreshed


def test_upsert_workload_observation_refuses_without_its_own_timestamp() -> None:
    registry = load_registry(DATA / "fleet.toml")
    baseline = _workloads()
    no_timestamp = HostWorkloadObservation(
        host_id="dotmac-labs",
        guest_hostname="dotmac-labs",
        docker_available=True,
        containers=(),
    )
    with pytest.raises(ValueError, match="must set its own observed_at"):
        upsert_workload_observation(registry, baseline, no_timestamp)


def test_upsert_workload_observation_refuses_a_host_the_registry_never_declared() -> (
    None
):
    """Unlike ``refresh_workload_observation``'s baseline-only check, this
    still must never let a probe silently mint a fleet host that was never
    registered at all -- growing the host set is only ever safe when the
    registry itself is the one vouching for the host_id."""
    registry = load_registry(DATA / "fleet.toml")
    baseline = _workloads()
    never_registered = HostWorkloadObservation(
        host_id="never-registered-anywhere",
        guest_hostname="ghost",
        docker_available=False,
        containers=(),
        observed_at=datetime(2026, 9, 21, 18, 0, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="not a declared fleet host"):
        upsert_workload_observation(registry, baseline, never_registered)
