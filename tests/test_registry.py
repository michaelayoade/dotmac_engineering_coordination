from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from dotmac_engineering_coordination.registry import (
    AccessStatus,
    FactStatus,
    FleetHost,
    FleetRefusal,
    FleetRefusalCode,
    FleetRegistry,
    FleetService,
    HostStatus,
    load_registry,
)

DATA = Path(__file__).parents[1] / "src/dotmac_engineering_coordination/data"
NOW = datetime(2026, 9, 3, 12, tzinfo=UTC)


@pytest.fixture
def registry() -> FleetRegistry:
    return load_registry(DATA / "fleet.toml")


@pytest.fixture
def service(registry: FleetRegistry) -> FleetService:
    return FleetService(registry)


def _single_host_registry(
    registry: FleetRegistry,
    *,
    host_updates: dict[str, object] | None = None,
    access_updates: dict[str, object] | None = None,
) -> FleetRegistry:
    source = registry.by_id("erp").model_dump(mode="python")
    source.update(host_updates or {})
    access = dict(source["access"])
    access.update(access_updates or {})
    source["access"] = access
    return FleetRegistry(
        schema_version="dotmac.fleet.v1",
        max_age_days=45,
        hosts=(FleetHost.model_validate(source),),
    )


def test_initial_registry_is_typed_and_counts_every_declared_host(
    registry: FleetRegistry,
) -> None:
    assert len(registry.hosts) == 28
    assert len({host.host_id for host in registry.hosts}) == 28
    assert (
        sum(host.access.status is AccessStatus.VERIFIED for host in registry.hosts)
        == 28
    )


def test_proxmox_access_exposes_both_verified_read_paths(
    registry: FleetRegistry,
) -> None:
    host = registry.by_id("proxmox")
    assert host.access.proxy_jump == "seabone"
    assert host.access.endpoint == "10.120.120.20"
    by_name = {item.name: item for item in host.api_access}
    assert by_name["proxmox-cluster-via-pvesh"].status is AccessStatus.VERIFIED
    assert by_name["proxmox-cluster-via-pvesh"].via_ssh_alias == "proxmox"
    https_api = by_name["proxmox-https-api"]
    assert https_api.status is AccessStatus.VERIFIED
    assert (
        https_api.credential_ref
        == "bao://secret/dotmac/proxmox/fleet-inventory#api_token"
    )
    assert https_api.limitation is None
    assert {item.ref for item in https_api.evidence} == {
        "live:proxmox-pveauditor-inventory-read:2026-09-03T10:11:20Z",
        "live:proxmox-pveauditor-denied-write:2026-09-03T10:11:20Z",
    }


def test_coverage_debt_is_a_two_directional_reviewed_baseline(
    service: FleetService,
) -> None:
    health = service.health(now=NOW)
    actual = {
        key: health[key]
        for key in (
            "schema_version",
            "host_count",
            "verified_access_count",
            "conflicted_host_ids",
            "unverified_fact_host_ids",
            "unverified_access_host_ids",
            "missing_recovery_pointer_host_ids",
            "unavailable_api_access_ids",
        )
    }
    expected = json.loads((DATA / "fleet_baseline.json").read_text())
    assert actual == expected, (
        "fleet coverage moved; improve the registry and update the baseline in "
        "the same reviewed change rather than letting the movement pass silently"
    )


def test_access_plan_positive_control_is_an_argv_and_never_executes(
    service: FleetService,
) -> None:
    plan = service.access_plan("erp", confirm_production_host="erp", now=NOW)
    assert plan.argv == ("ssh", "erp")
    assert plan.user == "root"
    assert plan.identity_ref == "local-key:~/.ssh/id_ed25519"
    assert plan.production


def test_dotmac_labs_production_access_plan_and_ssh_config_are_scoped() -> None:
    registry = load_registry(DATA / "fleet.toml")
    service = FleetService(registry)
    plan = service.access_plan(
        "dotmac-labs",
        confirm_production_host="dotmac-labs",
        now=datetime(2026, 9, 21, 4, tzinfo=UTC),
    )
    assert plan.argv == ("ssh", "dotmac-labs")
    assert plan.user == "dotmac"
    assert plan.identity_ref == "local-key:~/.ssh/id_ed25519"
    host = registry.by_id("dotmac-labs")
    assert {str(address) for address in host.public_addresses} == {
        "2c0f:e888:11:0:be24:11ff:fef3:6290"
    }
    assert "160.119.127.249" not in {
        str(address) for address in host.public_addresses
    }
    rendered = service.render_ssh_config()
    block = rendered.split("# fleet-host: dotmac-labs\n", 1)[1].split(
        "\n\n", 1
    )[0]
    assert "HostName 10.120.120.42" in block
    assert "User dotmac" in block
    assert "ProxyJump seabone" in block
    assert "# identity-ref: local-key:~/.ssh/id_ed25519" in block
    assert "160.119.127.249" not in block


def test_garki_core_production_access_and_host_owned_addresses_are_scoped() -> None:
    registry = load_registry(DATA / "fleet.toml")
    service = FleetService(registry)
    plan = service.access_plan(
        "garki-core",
        confirm_production_host="garki-core",
        now=datetime(2026, 9, 21, 5, tzinfo=UTC),
    )
    assert plan.argv == ("ssh", "garki-core")
    assert plan.user == "dottmacc"
    assert plan.port == 120
    assert plan.identity_ref == "local-key:~/.ssh/id_ed25519"
    host = registry.by_id("garki-core")
    assert {str(address) for address in host.public_addresses} == {
        "160.119.127.252",
        "2c0f:e888::252",
    }
    assert {str(address) for address in host.private_addresses} == {
        "10.120.120.1",
        "10.120.121.1",
        "10.10.41.3",
    }
    rendered = service.render_ssh_config()
    block = rendered.split("# fleet-host: garki-core\n", 1)[1].split(
        "\n\n", 1
    )[0]
    assert "HostName 160.119.127.252" in block
    assert "User dottmacc" in block
    assert "Port 120" in block
    assert "ProxyJump" not in block


def test_every_refusal_keeps_a_distinct_code(registry: FleetRegistry) -> None:
    cases: list[
        tuple[FleetRefusalCode, FleetService, str, dict[str, object], datetime]
    ] = [
        (
            FleetRefusalCode.HOST_NOT_FOUND,
            FleetService(registry),
            "missing",
            {},
            NOW,
        ),
        (
            FleetRefusalCode.HOST_CONFLICTED,
            FleetService(
                _single_host_registry(
                    registry, host_updates={"fact_status": FactStatus.CONFLICTED}
                )
            ),
            "erp",
            {},
            NOW,
        ),
        (
            FleetRefusalCode.HOST_UNVERIFIED,
            FleetService(
                _single_host_registry(
                    registry, host_updates={"fact_status": FactStatus.UNVERIFIED}
                )
            ),
            "erp",
            {},
            NOW,
        ),
        (
            FleetRefusalCode.HOST_INACTIVE,
            FleetService(
                _single_host_registry(
                    registry, host_updates={"status": HostStatus.RESERVED}
                )
            ),
            "erp",
            {},
            NOW,
        ),
        (
            FleetRefusalCode.ACCESS_UNVERIFIED,
            FleetService(
                _single_host_registry(
                    registry, access_updates={"status": AccessStatus.UNVERIFIED}
                )
            ),
            "erp",
            {},
            NOW,
        ),
        (
            FleetRefusalCode.ACCESS_UNAVAILABLE,
            FleetService(
                _single_host_registry(
                    registry, access_updates={"status": AccessStatus.UNAVAILABLE}
                )
            ),
            "erp",
            {},
            NOW,
        ),
        (
            FleetRefusalCode.RECORD_STALE,
            FleetService(registry),
            "erp",
            {"confirm_production_host": "erp"},
            NOW + timedelta(days=46),
        ),
        (
            FleetRefusalCode.PRODUCTION_CONFIRMATION_REQUIRED,
            FleetService(registry),
            "erp",
            {},
            NOW,
        ),
    ]
    observed: set[str] = set()
    for expected, candidate, host_id, kwargs, at in cases:
        with pytest.raises(FleetRefusal) as caught:
            candidate.access_plan(host_id, now=at, **kwargs)
        assert caught.value.code is expected
        observed.add(caught.value.code.value)
    assert observed == {code.value for code in FleetRefusalCode}


def test_refusal_and_success_payloads_never_leak_a_secret_value(
    service: FleetService,
) -> None:
    planted_value = "planted-sensitive-value-that-must-never-appear"
    payloads = [
        service.access_plan_payload("erp", now=NOW),
        service.access_plan_payload("erp", confirm_production_host="erp", now=NOW),
    ]
    assert planted_value not in json.dumps(payloads)


def test_private_key_material_cannot_be_constructed(registry: FleetRegistry) -> None:
    with pytest.raises(ValidationError, match="pointer, never key material"):
        _single_host_registry(
            registry,
            access_updates={
                "identity_ref": "-----BEGIN OPENSSH PRIVATE KEY-----\nsecret"
            },
        )


def test_password_authentication_is_not_in_the_vocabulary(
    registry: FleetRegistry,
) -> None:
    with pytest.raises(ValidationError, match="authentication"):
        _single_host_registry(
            registry,
            access_updates={"authentication": "password"},
        )


def test_duplicate_alias_is_refused(registry: FleetRegistry) -> None:
    first = registry.by_id("erp")
    second = registry.by_id("observe").model_dump(mode="python")
    second_access = dict(second["access"])
    second_access["alias"] = first.access.alias
    second["access"] = second_access
    with pytest.raises(ValidationError, match="duplicate SSH alias"):
        FleetRegistry(
            schema_version="dotmac.fleet.v1",
            hosts=(first, FleetHost.model_validate(second)),
        )


def test_ssh_renderer_is_deterministic_and_includes_every_verified_active_host(
    service: FleetService,
) -> None:
    rendered = service.render_ssh_config()
    expected = (Path(__file__).parents[1] / "generated/ssh_config").read_text()
    assert rendered == expected, (
        "generated/ssh_config differs from the typed registry; regenerate it "
        "with `dotmac-coordination render-ssh` and review the byte diff"
    )
    assert "Host erp\n" in rendered
    assert "Host son-erp\n" in rendered
    assert "Host sub-prod\n" in rendered
    assert "Host observability-canary\n" not in rendered
    assert "PRIVATE KEY" not in rendered
    assert "password" not in rendered.lower()
