"""Typed fleet declaration and safe agent-facing access plans.

The registry owns declarations. It does not probe hosts and it never executes
the command it returns. A caller gets an argv vector, not a shell string, so a
host record cannot smuggle shell syntax into an agent's execution path.
"""

from __future__ import annotations

import os
import re
import tomllib
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from ipaddress import ip_address
from pathlib import Path
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    IPvAnyAddress,
    field_validator,
    model_validator,
)

REGISTRY_ENV = "DOTMAC_FLEET_REGISTRY"
SCHEMA = "dotmac.fleet.v1"
DEFAULT_MAX_AGE_DAYS = 45

_HOST_ID = re.compile(r"\A[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")
_SSH_ALIAS = re.compile(r"\A[a-z0-9](?:[a-z0-9.-]{0,61}[a-z0-9])?\Z")
_SSH_USER = re.compile(r"\A[a-z_][a-z0-9_-]{0,31}\Z")
_SECRET_SHAPES = (
    "-----begin openssh private key-----",
    "-----begin private key-----",
    "ghp_",
    "github_pat_",
)


class EvidenceClass(StrEnum):
    """The class of proof a fleet claim points at."""

    LIVE_OBSERVATION = "live_observation"
    PROVIDER_RECORD = "provider_record"
    REPOSITORY_BYTES = "repository_bytes"
    KNOWLEDGE_REFERENCE = "knowledge_reference"
    RELAYED_UNVERIFIED = "relayed_unverified"


class HostStatus(StrEnum):
    ACTIVE = "active"
    RESERVED = "reserved"
    DECOMMISSIONED = "decommissioned"


class FactStatus(StrEnum):
    CONFIRMED = "confirmed"
    CONFLICTED = "conflicted"
    UNVERIFIED = "unverified"


class AccessStatus(StrEnum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    UNAVAILABLE = "unavailable"


class AuthenticationMethod(StrEnum):
    """Password login is deliberately not a member."""

    SSH_PUBLIC_KEY = "ssh_public_key"
    SSH_CERTIFICATE = "ssh_certificate"
    OIDC = "oidc"
    CONSOLE_ONLY = "console_only"


class ApiAuthenticationMethod(StrEnum):
    PROXMOX_API_TOKEN = "proxmox_api_token"  # noqa: S105 -- contract vocabulary
    SSH_PVESH = "ssh_pvesh"


class FleetRefusalCode(StrEnum):
    HOST_NOT_FOUND = "FLEET_HOST_NOT_FOUND"
    HOST_CONFLICTED = "FLEET_HOST_CONFLICTED"
    HOST_UNVERIFIED = "FLEET_HOST_UNVERIFIED"
    HOST_INACTIVE = "FLEET_HOST_INACTIVE"
    ACCESS_UNVERIFIED = "FLEET_ACCESS_UNVERIFIED"
    ACCESS_UNAVAILABLE = "FLEET_ACCESS_UNAVAILABLE"
    RECORD_STALE = "FLEET_RECORD_STALE"
    PRODUCTION_CONFIRMATION_REQUIRED = "FLEET_PRODUCTION_CONFIRMATION_REQUIRED"


class FleetRefusal(ValueError):
    """A stable refusal that survives CLI and MCP wrappers."""

    def __init__(self, code: FleetRefusalCode, message: str) -> None:
        self.code = code
        super().__init__(message)

    def as_dict(self) -> dict[str, object]:
        return {"ok": False, "refusal": {"code": self.code.value, "message": str(self)}}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class EvidenceRef(StrictModel):
    evidence_class: EvidenceClass
    ref: Annotated[str, Field(min_length=1, max_length=500)]
    observed_at: datetime | None = None

    @field_validator("observed_at")
    @classmethod
    def observed_at_is_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("evidence observed_at must include a timezone")
        return value


class SshAccess(StrictModel):
    status: AccessStatus
    alias: str | None = None
    endpoint: str | None = None
    user: str | None = None
    port: Annotated[int, Field(ge=1, le=65535)] = 22
    proxy_jump: str | None = None
    authentication: AuthenticationMethod | None = None
    identity_ref: str | None = None
    recovery_secret_ref: str | None = None
    verified_at: datetime | None = None
    evidence: tuple[EvidenceRef, ...] = ()

    @field_validator("alias")
    @classmethod
    def alias_is_safe(cls, value: str | None) -> str | None:
        if value is not None and not _SSH_ALIAS.fullmatch(value):
            raise ValueError("SSH alias must be a plain DNS-like token")
        return value

    @field_validator("user")
    @classmethod
    def user_is_safe(cls, value: str | None) -> str | None:
        if value is not None and not _SSH_USER.fullmatch(value):
            raise ValueError("SSH user must be a plain account name")
        return value

    @field_validator("endpoint")
    @classmethod
    def endpoint_is_an_address_or_dns_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            ip_address(value)
        except ValueError:
            if not _SSH_ALIAS.fullmatch(value):
                raise ValueError(
                    "SSH endpoint must be an IP address or DNS name"
                ) from None
        return value

    @field_validator("proxy_jump")
    @classmethod
    def proxy_jump_is_alias(cls, value: str | None) -> str | None:
        if value is not None and not _SSH_ALIAS.fullmatch(value):
            raise ValueError("proxy_jump must name another SSH alias")
        return value

    @field_validator("identity_ref")
    @classmethod
    def identity_is_a_pointer(cls, value: str | None) -> str | None:
        if value is None:
            return None
        lowered = value.lower()
        if any(shape in lowered for shape in _SECRET_SHAPES) or "\n" in value:
            raise ValueError("identity_ref must be a pointer, never key material")
        if not value.startswith(("local-key:", "ssh-agent:", "bao://")):
            raise ValueError("identity_ref must use local-key:, ssh-agent:, or bao://")
        return value

    @field_validator("recovery_secret_ref")
    @classmethod
    def recovery_is_only_a_bao_pointer(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith("bao://"):
            raise ValueError("recovery_secret_ref must be an OpenBao pointer")
        return value

    @field_validator("verified_at")
    @classmethod
    def verified_at_is_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("access verified_at must include a timezone")
        return value

    @model_validator(mode="after")
    def verified_access_is_complete(self) -> SshAccess:
        if self.status is AccessStatus.VERIFIED:
            missing = [
                name
                for name, value in (
                    ("alias", self.alias),
                    ("user", self.user),
                    ("authentication", self.authentication),
                    ("identity_ref", self.identity_ref),
                    ("verified_at", self.verified_at),
                )
                if value is None
            ]
            if missing:
                raise ValueError(
                    "verified access is missing " + ", ".join(sorted(missing))
                )
            if self.authentication not in {
                AuthenticationMethod.SSH_PUBLIC_KEY,
                AuthenticationMethod.SSH_CERTIFICATE,
            }:
                raise ValueError("verified SSH access must use a key or certificate")
            if not self.evidence:
                raise ValueError("verified access needs evidence")
        return self


class ApiAccess(StrictModel):
    name: Annotated[str, Field(min_length=1, max_length=80)]
    status: AccessStatus
    endpoint: Annotated[str, Field(min_length=1, max_length=500)]
    authentication: ApiAuthenticationMethod
    credential_ref: str | None = None
    via_ssh_alias: str | None = None
    verified_at: datetime | None = None
    evidence: tuple[EvidenceRef, ...] = ()
    limitation: str | None = None

    @field_validator("credential_ref")
    @classmethod
    def credential_is_only_a_bao_pointer(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith("bao://"):
            raise ValueError("API credential_ref must be an OpenBao pointer")
        return value

    @field_validator("via_ssh_alias")
    @classmethod
    def via_ssh_is_alias(cls, value: str | None) -> str | None:
        if value is not None and not _SSH_ALIAS.fullmatch(value):
            raise ValueError("via_ssh_alias must name an SSH alias")
        return value

    @field_validator("verified_at")
    @classmethod
    def api_verified_at_is_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("API verified_at must include a timezone")
        return value

    @model_validator(mode="after")
    def verified_api_is_complete(self) -> ApiAccess:
        if self.status is AccessStatus.VERIFIED:
            if self.verified_at is None or not self.evidence:
                raise ValueError("verified API access needs time and evidence")
            if (
                self.authentication is ApiAuthenticationMethod.PROXMOX_API_TOKEN
                and self.credential_ref is None
            ):
                raise ValueError("verified token API access needs an OpenBao pointer")
            if (
                self.authentication is ApiAuthenticationMethod.SSH_PVESH
                and self.via_ssh_alias is None
            ):
                raise ValueError("verified pvesh API access needs an SSH alias")
        return self


class FleetHost(StrictModel):
    host_id: str
    provider_ref: Annotated[str, Field(min_length=1, max_length=200)]
    environment: Annotated[str, Field(min_length=1, max_length=60)]
    purpose: Annotated[str, Field(min_length=1, max_length=500)]
    owner_ref: Annotated[str, Field(min_length=1, max_length=200)]
    production: bool
    status: HostStatus
    fact_status: FactStatus
    public_addresses: tuple[IPvAnyAddress, ...] = ()
    private_addresses: tuple[IPvAnyAddress, ...] = ()
    dns_names: tuple[str, ...] = ()
    last_verified_at: datetime
    evidence: tuple[EvidenceRef, ...]
    access: SshAccess
    api_access: tuple[ApiAccess, ...] = ()

    @field_validator("host_id")
    @classmethod
    def host_id_is_stable(cls, value: str) -> str:
        if not _HOST_ID.fullmatch(value):
            raise ValueError("host_id must be lowercase kebab-case")
        return value

    @field_validator("dns_names")
    @classmethod
    def dns_names_are_plain(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        for value in values:
            if not _SSH_ALIAS.fullmatch(value):
                raise ValueError(f"invalid DNS name {value!r}")
        return values

    @field_validator("last_verified_at")
    @classmethod
    def last_verified_is_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("last_verified_at must include a timezone")
        return value

    @model_validator(mode="after")
    def active_host_has_an_address_and_evidence(self) -> FleetHost:
        if self.status is HostStatus.ACTIVE and not (
            self.public_addresses or self.private_addresses or self.dns_names
        ):
            raise ValueError("an active host needs at least one address or DNS name")
        if not self.evidence:
            raise ValueError("a host declaration needs evidence")
        return self


class FleetRegistry(StrictModel):
    schema_version: Literal["dotmac.fleet.v1"]
    max_age_days: Annotated[int, Field(ge=1, le=365)] = DEFAULT_MAX_AGE_DAYS
    hosts: tuple[FleetHost, ...]

    @model_validator(mode="after")
    def identities_are_unique(self) -> FleetRegistry:
        ids = [host.host_id for host in self.hosts]
        aliases = [host.access.alias for host in self.hosts if host.access.alias]
        public = [str(ip) for host in self.hosts for ip in host.public_addresses]
        for label, values in (
            ("host_id", ids),
            ("SSH alias", aliases),
            ("public IP", public),
        ):
            duplicates = sorted({value for value in values if values.count(value) > 1})
            if duplicates:
                raise ValueError(f"duplicate {label}: {', '.join(duplicates)}")
        return self

    def by_id(self, host_id: str) -> FleetHost:
        for host in self.hosts:
            if host.host_id == host_id:
                return host
        raise FleetRefusal(
            FleetRefusalCode.HOST_NOT_FOUND,
            f"no fleet host has id {host_id!r}",
        )


class AccessPlan(StrictModel):
    host_id: str
    production: bool
    alias: str
    user: str
    port: int
    authentication: AuthenticationMethod
    identity_ref: str
    recovery_secret_ref: str | None
    argv: tuple[str, ...]
    verified_at: datetime
    evidence_classes: tuple[EvidenceClass, ...]


def default_registry_path() -> Path:
    configured = os.getenv(REGISTRY_ENV)
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).with_name("data") / "fleet.toml"


def load_registry(path: Path | None = None) -> FleetRegistry:
    source = path or default_registry_path()
    with source.open("rb") as handle:
        document = tomllib.load(handle)
    return FleetRegistry.model_validate(document)


def _jsonable(model: BaseModel) -> dict[str, object]:
    value = model.model_dump(mode="json")
    assert isinstance(value, dict)
    return value


def decide_access_plan(
    registry: FleetRegistry,
    host_id: str,
    *,
    confirm_production_host: str | None = None,
    now: datetime | None = None,
) -> AccessPlan:
    """Own the access-plan decision independently of every transport adapter."""
    host = registry.by_id(host_id)
    moment = now or datetime.now(UTC)
    if moment.tzinfo is None:
        raise ValueError("now must include a timezone")
    if host.fact_status is FactStatus.CONFLICTED:
        raise FleetRefusal(
            FleetRefusalCode.HOST_CONFLICTED,
            f"{host_id} has conflicting fleet facts; resolve them before access",
        )
    if host.fact_status is FactStatus.UNVERIFIED:
        raise FleetRefusal(
            FleetRefusalCode.HOST_UNVERIFIED,
            f"{host_id} has not been verified by its fleet owner",
        )
    if host.status is not HostStatus.ACTIVE:
        raise FleetRefusal(
            FleetRefusalCode.HOST_INACTIVE,
            f"{host_id} is {host.status.value}, not active",
        )
    if moment - host.last_verified_at.astimezone(UTC) > timedelta(
        days=registry.max_age_days
    ):
        raise FleetRefusal(
            FleetRefusalCode.RECORD_STALE,
            f"{host_id} was last verified at {host.last_verified_at.isoformat()}",
        )
    access = host.access
    if access.status is AccessStatus.UNAVAILABLE:
        raise FleetRefusal(
            FleetRefusalCode.ACCESS_UNAVAILABLE,
            f"{host_id} has no agent SSH access path",
        )
    if access.status is not AccessStatus.VERIFIED:
        raise FleetRefusal(
            FleetRefusalCode.ACCESS_UNVERIFIED,
            f"{host_id} SSH access has not been verified",
        )
    assert access.verified_at is not None
    if moment - access.verified_at.astimezone(UTC) > timedelta(
        days=registry.max_age_days
    ):
        raise FleetRefusal(
            FleetRefusalCode.RECORD_STALE,
            f"{host_id} SSH access was last verified at "
            f"{access.verified_at.isoformat()}",
        )
    if host.production and confirm_production_host != host.host_id:
        raise FleetRefusal(
            FleetRefusalCode.PRODUCTION_CONFIRMATION_REQUIRED,
            "production access requires confirm_production_host to equal "
            f"{host.host_id!r}",
        )
    assert access.alias is not None
    assert access.user is not None
    assert access.authentication is not None
    assert access.identity_ref is not None
    return AccessPlan(
        host_id=host.host_id,
        production=host.production,
        alias=access.alias,
        user=access.user,
        port=access.port,
        authentication=access.authentication,
        identity_ref=access.identity_ref,
        recovery_secret_ref=access.recovery_secret_ref,
        argv=("ssh", access.alias),
        verified_at=access.verified_at,
        evidence_classes=tuple(
            sorted(
                {item.evidence_class for item in access.evidence},
                key=lambda item: item.value,
            )
        ),
    )


class FleetService:
    """Read-only application service used by the CLI and MCP adapters."""

    def __init__(self, registry: FleetRegistry) -> None:
        self.registry = registry

    def list_hosts(
        self,
        *,
        environment: str | None = None,
        production: bool | None = None,
        status: HostStatus | None = None,
    ) -> dict[str, object]:
        hosts = sorted(self.registry.hosts, key=lambda item: item.host_id)
        selected = [
            host
            for host in hosts
            if (environment is None or host.environment == environment)
            and (production is None or host.production is production)
            and (status is None or host.status is status)
        ]
        return {
            "ok": True,
            "schema_version": self.registry.schema_version,
            "count": len(selected),
            "hosts": [_jsonable(host) for host in selected],
        }

    def get_host(self, host_id: str) -> dict[str, object]:
        return {"ok": True, "host": _jsonable(self.registry.by_id(host_id))}

    def access_plan(
        self,
        host_id: str,
        *,
        confirm_production_host: str | None = None,
        now: datetime | None = None,
    ) -> AccessPlan:
        return decide_access_plan(
            self.registry,
            host_id,
            confirm_production_host=confirm_production_host,
            now=now,
        )

    def access_plan_payload(
        self,
        host_id: str,
        *,
        confirm_production_host: str | None = None,
        now: datetime | None = None,
    ) -> dict[str, object]:
        try:
            plan = self.access_plan(
                host_id,
                confirm_production_host=confirm_production_host,
                now=now,
            )
        except FleetRefusal as refusal:
            return refusal.as_dict()
        return {"ok": True, "plan": _jsonable(plan)}

    def render_ssh_config(self) -> str:
        """Render verified aliases only; never render a secret or key value."""
        blocks: list[str] = []
        for host in sorted(self.registry.hosts, key=lambda item: item.host_id):
            access = host.access
            if (
                host.status is not HostStatus.ACTIVE
                or host.fact_status is not FactStatus.CONFIRMED
                or access.status is not AccessStatus.VERIFIED
            ):
                continue
            assert access.alias is not None
            assert access.user is not None
            assert access.identity_ref is not None
            address = access.endpoint or (
                str(host.public_addresses[0])
                if host.public_addresses
                else (
                    host.dns_names[0]
                    if host.dns_names
                    else str(host.private_addresses[0])
                )
            )
            lines = [
                f"# fleet-host: {host.host_id}",
                f"# identity-ref: {access.identity_ref}",
                f"Host {access.alias}",
                f"  HostName {address}",
                f"  User {access.user}",
                f"  Port {access.port}",
                "  IdentitiesOnly yes",
            ]
            if access.proxy_jump:
                lines.append(f"  ProxyJump {access.proxy_jump}")
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks) + ("\n" if blocks else "")

    def health(self, *, now: datetime | None = None) -> dict[str, object]:
        moment = now or datetime.now(UTC)
        stale = sorted(
            host.host_id
            for host in self.registry.hosts
            if moment - host.last_verified_at.astimezone(UTC)
            > timedelta(days=self.registry.max_age_days)
        )
        conflicts = sorted(
            host.host_id
            for host in self.registry.hosts
            if host.fact_status is FactStatus.CONFLICTED
        )
        unverified_facts = sorted(
            host.host_id
            for host in self.registry.hosts
            if host.fact_status is FactStatus.UNVERIFIED
        )
        unverified_access = sorted(
            host.host_id
            for host in self.registry.hosts
            if host.status is HostStatus.ACTIVE
            and host.access.status is AccessStatus.UNVERIFIED
        )
        missing_recovery_pointers = sorted(
            host.host_id
            for host in self.registry.hosts
            if host.status is HostStatus.ACTIVE
            and host.access.recovery_secret_ref is None
        )
        unavailable_api_access = sorted(
            f"{host.host_id}/{api.name}"
            for host in self.registry.hosts
            for api in host.api_access
            if api.status is not AccessStatus.VERIFIED
        )
        return {
            "ok": True,
            "schema_version": self.registry.schema_version,
            "host_count": len(self.registry.hosts),
            "verified_access_count": sum(
                host.access.status is AccessStatus.VERIFIED
                for host in self.registry.hosts
            ),
            "stale_host_ids": stale,
            "conflicted_host_ids": conflicts,
            "unverified_fact_host_ids": unverified_facts,
            "unverified_access_host_ids": unverified_access,
            "missing_recovery_pointer_host_ids": missing_recovery_pointers,
            "unavailable_api_access_ids": unavailable_api_access,
            "ready": not stale
            and not conflicts
            and not unverified_facts
            and not unverified_access,
        }


__all__ = [
    "DEFAULT_MAX_AGE_DAYS",
    "REGISTRY_ENV",
    "SCHEMA",
    "AccessPlan",
    "AccessStatus",
    "ApiAccess",
    "ApiAuthenticationMethod",
    "AuthenticationMethod",
    "EvidenceClass",
    "EvidenceRef",
    "FactStatus",
    "FleetHost",
    "FleetRefusal",
    "FleetRefusalCode",
    "FleetRegistry",
    "FleetService",
    "HostStatus",
    "SshAccess",
    "decide_access_plan",
    "default_registry_path",
    "load_registry",
]
