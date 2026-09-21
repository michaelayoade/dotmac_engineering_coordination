from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from dotmac_engineering_coordination.registry import (
    AccessStatus,
    EvidenceClass,
    EvidenceRef,
    FactStatus,
    FleetHost,
    FleetRefusal,
    FleetRefusalCode,
    FleetRegistry,
    FleetService,
    HostStatus,
    RecoveryMethod,
    RecoveryPlan,
    RecoveryRehearsalEvidence,
    RecoveryStatus,
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
        schema_version="dotmac.fleet.v2",
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
            "invalid_recovery_time_host_ids",
            "missing_recovery_plan_host_ids",
            "stale_recovery_plan_host_ids",
            "unverified_recovery_plan_host_ids",
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


def test_academy_web_dns_identity_is_declared(registry: FleetRegistry) -> None:
    host = registry.by_id("academy")
    assert host.dns_names == ("academy.dotmac.io",)
    assert {str(address) for address in host.public_addresses} == {
        "149.102.135.97",
        "2a02:c204:2249:731::1",
    }


def test_access_plan_includes_separate_recovery_payload(
    service: FleetService,
) -> None:
    plan = service.access_plan("erp", confirm_production_host="erp", now=NOW)
    assert plan.recovery is not None
    assert plan.recovery.status is RecoveryStatus.DECLARED
    assert plan.recovery.credential_ref == (
        "bao://secret/dotmac/hosts/erp#root_password"
    )
    payload = service.access_plan_payload(
        "erp", confirm_production_host="erp", now=NOW
    )
    assert payload["schema_version"] == "dotmac.access-plan.v2"
    refusal = service.access_plan_payload("erp", now=NOW)
    assert refusal["schema_version"] == "dotmac.access-plan.v2"


def test_v1_registry_is_explicitly_rejected(registry: FleetRegistry) -> None:
    source = registry.model_dump(mode="python")
    source["schema_version"] = "dotmac.fleet.v1"
    with pytest.raises(ValidationError):
        FleetRegistry.model_validate(source)


def test_verified_recovery_requires_dated_live_rehearsal_evidence() -> None:
    with pytest.raises(
        ValidationError, match="dated live-observation rehearsal evidence"
    ):
        RecoveryPlan(
            status=RecoveryStatus.VERIFIED,
            method=RecoveryMethod.PROVIDER_CONSOLE,
            owner_ref="engineering",
            runbook_ref="repo://docs/recovery/contabo-console.md",
            decided_at=NOW,
            last_rehearsed_at=NOW,
        )
    plan = RecoveryPlan(
        status=RecoveryStatus.VERIFIED,
        method=RecoveryMethod.PROVIDER_CONSOLE,
        owner_ref="engineering",
        runbook_ref="repo://docs/recovery/contabo-console.md",
        decided_at=NOW,
        last_rehearsed_at=NOW,
        evidence=(
            RecoveryRehearsalEvidence(
                evidence_class=EvidenceClass.LIVE_OBSERVATION,
                host_id="test-server",
                method=RecoveryMethod.PROVIDER_CONSOLE,
                ref="live:recovery-rehearsal:test-server:provider_console",
                observed_at=NOW,
            ),
        ),
    )
    assert plan.status is RecoveryStatus.VERIFIED


def test_verified_recovery_rejects_stale_rehearsal_evidence() -> None:
    evidence = RecoveryRehearsalEvidence(
        evidence_class=EvidenceClass.LIVE_OBSERVATION,
        host_id="erp",
        method=RecoveryMethod.PROVIDER_CONSOLE,
        ref="live:recovery-rehearsal:erp:provider_console",
        observed_at=NOW - timedelta(days=1),
    )
    with pytest.raises(
        ValidationError, match="dated live-observation rehearsal evidence"
    ):
        RecoveryPlan(
            status=RecoveryStatus.VERIFIED,
            method=RecoveryMethod.PROVIDER_CONSOLE,
            owner_ref="engineering",
            runbook_ref="repo://docs/recovery/contabo-console.md",
            decided_at=NOW,
            last_rehearsed_at=NOW,
            evidence=(evidence,),
        )


def test_generic_ssh_observation_cannot_certify_recovery() -> None:
    with pytest.raises(ValidationError):
        RecoveryPlan(
            status=RecoveryStatus.VERIFIED,
            method=RecoveryMethod.PROVIDER_CONSOLE,
            owner_ref="dotmac_erp",
            runbook_ref="repo://docs/recovery/contabo-console.md",
            decided_at=NOW,
            last_rehearsed_at=NOW,
            evidence=(
                {
                    "evidence_class": "live_observation",
                    "ref": "live:ssh-census:erp",
                    "observed_at": NOW,
                },
            ),
        )


def test_generic_live_observation_remains_valid_for_ssh_access() -> None:
    evidence = EvidenceRef(
        evidence_class=EvidenceClass.LIVE_OBSERVATION,
        ref="live:ssh-census:erp",
        observed_at=NOW,
    )
    assert evidence.ref == "live:ssh-census:erp"


def test_recovery_evidence_is_bound_to_plan_method_and_fleet_host(
    registry: FleetRegistry,
) -> None:
    wrong_method = RecoveryRehearsalEvidence(
        evidence_class=EvidenceClass.LIVE_OBSERVATION,
        host_id="erp",
        method=RecoveryMethod.PHYSICAL_CONSOLE,
        ref="live:recovery-rehearsal:erp:physical_console",
        observed_at=NOW,
    )
    with pytest.raises(ValidationError, match="method must match"):
        RecoveryPlan(
            status=RecoveryStatus.VERIFIED,
            method=RecoveryMethod.PROVIDER_CONSOLE,
            owner_ref="dotmac_erp",
            runbook_ref="repo://docs/recovery/contabo-console.md",
            decided_at=NOW,
            last_rehearsed_at=NOW,
            evidence=(wrong_method,),
        )

    wrong_host = _verified_recovery(NOW, host_id="other-host")
    source = registry.by_id("erp").model_dump(mode="python")
    source["recovery"] = wrong_host.model_dump(mode="python")
    with pytest.raises(ValidationError, match="host_id must match"):
        FleetHost.model_validate(source)


@pytest.mark.parametrize(
    "ref",
    [
        "live:recovery-rehearsal:other-host:provider_console",
        "live:recovery-rehearsal:erp:physical_console",
        "live:recovery-rehearsal:erp:provider_console:\nplanted-secret",
        "live:recovery-rehearsal:erp:provider_console:?planted-secret",
    ],
)
def test_recovery_evidence_ref_is_bound_and_control_safe(ref: str) -> None:
    with pytest.raises(ValidationError, match="bind the host and method"):
        RecoveryRehearsalEvidence(
            evidence_class=EvidenceClass.LIVE_OBSERVATION,
            host_id="erp",
            method=RecoveryMethod.PROVIDER_CONSOLE,
            ref=ref,
            observed_at=NOW,
        )


@pytest.mark.parametrize(
    "credential_ref",
    [
        "bao://",
        "bao://secret/path",
        "bao://secret/../path#field",
        "bao://secret/path#field\nplanted-secret",
        "bao://secret/path#field?planted-secret",
    ],
)
def test_recovery_credentials_require_exact_openbao_pointers(
    credential_ref: str,
) -> None:
    with pytest.raises(ValidationError, match="exact OpenBao pointer"):
        RecoveryPlan(
            status=RecoveryStatus.DECLARED,
            method=RecoveryMethod.OPENBAO_CREDENTIAL,
            owner_ref="engineering",
            credential_ref=credential_ref,
        )


@pytest.mark.parametrize(
    "runbook_ref",
    [
        "repo://",
        "repo:///absolute.md",
        "repo://docs/../secret.md",
        "repo://docs\\x.md",
        "repo://docs/runbook.md?x",
        "repo://docs/runbook.md#x",
    ],
)
def test_repo_runbook_refs_reject_non_normalized_paths(runbook_ref: str) -> None:
    with pytest.raises(ValidationError, match="normalized relative path"):
        RecoveryPlan(
            status=RecoveryStatus.DECLARED,
            method=RecoveryMethod.PROVIDER_CONSOLE,
            owner_ref="engineering",
            runbook_ref=runbook_ref,
        )


@pytest.mark.parametrize(
    "method",
    [
        RecoveryMethod.OPENBAO_CREDENTIAL,
        RecoveryMethod.SSH_PUBLIC_KEY,
        RecoveryMethod.SSH_CERTIFICATE,
    ],
)
def test_credential_backed_recovery_requires_openbao_pointer(
    method: RecoveryMethod,
) -> None:
    with pytest.raises(ValidationError, match="credential_ref"):
        RecoveryPlan(status=RecoveryStatus.DECLARED, method=method, owner_ref="team")
    with pytest.raises(ValidationError, match="OpenBao pointer"):
        RecoveryPlan(
            status=RecoveryStatus.DECLARED,
            method=method,
            owner_ref="team",
            credential_ref="password-value",
        )


def test_checked_in_repo_runbooks_resolve_inside_repository(
    registry: FleetRegistry,
) -> None:
    root = DATA.parents[2]
    for host in registry.hosts:
        plan = host.recovery
        if plan is None or plan.runbook_ref is None:
            continue
        if not plan.runbook_ref.startswith("repo://"):
            continue
        relative = plan.runbook_ref.removeprefix("repo://")
        resolved = (root / relative).resolve()
        assert resolved.is_relative_to(root)
        assert resolved.is_file(), plan.runbook_ref


def test_unavailable_recovery_requires_limitation_and_stays_red(
    registry: FleetRegistry,
) -> None:
    with pytest.raises(ValidationError, match="needs a limitation"):
        RecoveryPlan(
            status=RecoveryStatus.UNAVAILABLE,
            method=RecoveryMethod.PROVIDER_CONSOLE,
            owner_ref="dotmac_erp",
        )
    host = registry.by_id("erp")
    unavailable = RecoveryPlan(
        status=RecoveryStatus.UNAVAILABLE,
        method=RecoveryMethod.PROVIDER_CONSOLE,
        owner_ref="dotmac_erp",
        limitation="Provider console authority is not currently assigned.",
    )
    changed = host.model_copy(update={"recovery": unavailable})
    updated = registry.model_copy(update={"hosts": (changed,)})
    health = FleetService(updated).health(now=NOW)
    assert health["ready"] is False
    assert "erp" in health["unverified_recovery_plan_host_ids"]


def _verified_recovery(
    at: datetime, *, host_id: str = "erp"
) -> RecoveryPlan:
    return RecoveryPlan(
        status=RecoveryStatus.VERIFIED,
        method=RecoveryMethod.PROVIDER_CONSOLE,
        owner_ref="dotmac_erp",
        runbook_ref="repo://docs/recovery/contabo-console.md",
        decided_at=at,
        last_rehearsed_at=at,
        evidence=(
            RecoveryRehearsalEvidence(
                evidence_class=EvidenceClass.LIVE_OBSERVATION,
                host_id=host_id,
                method=RecoveryMethod.PROVIDER_CONSOLE,
                ref=(
                    f"live:recovery-rehearsal:{host_id}:provider_console"
                ),
                observed_at=at,
            ),
        ),
    )


def test_recovery_readiness_rejects_future_and_stale_rehearsals(
    registry: FleetRegistry,
) -> None:
    host = registry.by_id("erp")
    future = host.model_copy(
        update={"recovery": _verified_recovery(NOW + timedelta(seconds=1))}
    )
    future_health = FleetService(
        registry.model_copy(update={"hosts": (future,)})
    ).health(now=NOW)
    assert future_health["invalid_recovery_time_host_ids"] == ["erp"]
    assert future_health["ready"] is False

    stale = host.model_copy(
        update={
            "recovery": _verified_recovery(
                NOW - timedelta(days=registry.max_age_days, seconds=1)
            )
        }
    )
    stale_health = FleetService(
        registry.model_copy(update={"hosts": (stale,)})
    ).health(now=NOW)
    assert stale_health["stale_recovery_plan_host_ids"] == ["erp"]
    assert stale_health["ready"] is False

    boundary = host.model_copy(
        update={
            "recovery": _verified_recovery(
                NOW - timedelta(days=registry.max_age_days)
            )
        }
    )
    boundary_health = FleetService(
        registry.model_copy(update={"hosts": (boundary,)})
    ).health(now=NOW)
    assert boundary_health["invalid_recovery_time_host_ids"] == []
    assert boundary_health["stale_recovery_plan_host_ids"] == []
    assert boundary_health["ready"] is True


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
            schema_version="dotmac.fleet.v2",
            hosts=(first, FleetHost.model_validate(second)),
        )


def test_duplicate_dns_name_is_refused(registry: FleetRegistry) -> None:
    academy = registry.by_id("academy")
    other = registry.by_id("erp").model_copy(
        update={"dns_names": academy.dns_names}
    )
    with pytest.raises(ValidationError, match="duplicate DNS name"):
        FleetRegistry(
            schema_version="dotmac.fleet.v2",
            hosts=(academy, other),
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
