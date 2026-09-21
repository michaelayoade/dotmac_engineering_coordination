"""Evidence-classed provider/workload observations and fleet topology rendering.

The declared fleet and live observations stay different types and different
files. Provider or runtime observations can expose drift; they cannot silently
rewrite a host's declared owner, purpose, lifecycle, or access policy.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from ipaddress import ip_address, ip_interface, ip_network
from pathlib import Path
from typing import Annotated, Literal, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    IPvAnyAddress,
    IPvAnyInterface,
    IPvAnyNetwork,
    field_validator,
    model_validator,
)

from dotmac_engineering_coordination.registry import (
    EvidenceClass,
    FleetRegistry,
    StrictModel,
)

_SAFE_NAME = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9_.:/@+-]{0,254}\Z")


class ExternalModel(BaseModel):
    """Provider input accepts new fields but never lets them leak into output."""

    model_config = ConfigDict(extra="ignore", frozen=True, populate_by_name=True)


class ContaboAddress(ExternalModel):
    ip: IPvAnyAddress
    netmask_cidr: int = Field(alias="netmaskCidr")


class ContaboIpConfig(ExternalModel):
    v4: ContaboAddress
    v6: ContaboAddress


class ContaboInstance(ExternalModel):
    instance_id: int = Field(alias="instanceId")
    name: str
    display_name: str = Field(alias="displayName")
    product_id: str = Field(alias="productId")
    product_name: str | None = Field(default=None, alias="productName")
    data_center: str | None = Field(default=None, alias="dataCenter")
    region: str | None = None
    status: str
    ip_config: ContaboIpConfig = Field(alias="ipConfig")
    created_at: datetime = Field(alias="createdDate")
    cancellation_date: str | None = Field(default=None, alias="cancelDate")


class ContaboInstancesResponse(ExternalModel):
    data: tuple[ContaboInstance, ...]


class ContaboPrivateNetwork(ExternalModel):
    private_network_id: int = Field(alias="privateNetworkId")
    name: str
    cidr: IPvAnyNetwork
    region: str | None = None
    data_center: str | None = Field(default=None, alias="dataCenter")
    instances: tuple[int, ...] = ()


class ContaboPrivateNetworksResponse(ExternalModel):
    data: tuple[ContaboPrivateNetwork, ...]


class ProviderInstanceObservation(StrictModel):
    host_id: str
    instance_id: Annotated[int, Field(gt=0)]
    provider_hostname: Annotated[str, Field(min_length=1, max_length=255)]
    display_name: Annotated[str, Field(min_length=1, max_length=255)]
    product_id: Annotated[str, Field(min_length=1, max_length=80)]
    product_name: str | None = None
    data_center: str | None = None
    region: str | None = None
    status: Annotated[str, Field(min_length=1, max_length=80)]
    ipv4: IPvAnyAddress
    ipv4_prefix: Annotated[int, Field(ge=0, le=32)]
    ipv6: IPvAnyAddress
    ipv6_prefix: Annotated[int, Field(ge=0, le=128)]
    created_at: datetime
    cancellation_date: str | None = None

    @field_validator("created_at")
    @classmethod
    def created_at_is_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("provider created_at must include a timezone")
        return value

    @model_validator(mode="after")
    def address_families_are_correct(self) -> ProviderInstanceObservation:
        if self.ipv4.version != 4:
            raise ValueError("ipv4 must be an IPv4 address")
        if self.ipv6.version != 6:
            raise ValueError("ipv6 must be an IPv6 address")
        return self


class ProviderSnapshot(StrictModel):
    schema_version: Literal["dotmac.provider-snapshot.v1"]
    provider: Literal["contabo"]
    observed_at: datetime
    evidence_class: Literal[EvidenceClass.PROVIDER_RECORD]
    instances: tuple[ProviderInstanceObservation, ...]
    private_networks: tuple[ProviderPrivateNetworkObservation, ...]

    @field_validator("observed_at")
    @classmethod
    def observed_at_is_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("provider observed_at must include a timezone")
        return value

    @model_validator(mode="after")
    def provider_identities_are_unique(self) -> ProviderSnapshot:
        for label, values in (
            ("host id", [item.host_id for item in self.instances]),
            ("instance id", [str(item.instance_id) for item in self.instances]),
            ("IPv4", [str(item.ipv4) for item in self.instances]),
            ("IPv6", [str(item.ipv6) for item in self.instances]),
        ):
            duplicates = sorted({value for value in values if values.count(value) > 1})
            if duplicates:
                raise ValueError(f"duplicate provider {label}: {', '.join(duplicates)}")
        return self


class ProviderPrivateNetworkObservation(StrictModel):
    network_id: Annotated[int, Field(gt=0)]
    name: Annotated[str, Field(min_length=1, max_length=255)]
    cidr: IPvAnyNetwork
    region: str | None = None
    data_center: str | None = None
    instance_ids: tuple[int, ...]


class ContainerObservation(StrictModel):
    name: Annotated[str, Field(min_length=1, max_length=255)]
    image: Annotated[str, Field(min_length=1, max_length=500)]
    state: Annotated[str, Field(min_length=1, max_length=80)]
    runtime_status: Annotated[str, Field(min_length=1, max_length=255)]
    health: str | None = None

    @field_validator("name")
    @classmethod
    def name_is_safe(cls, value: str) -> str:
        if not _SAFE_NAME.fullmatch(value):
            raise ValueError("container name contains an unsafe character")
        return value


class VirtualGuestObservation(StrictModel):
    """A QEMU or LXC guest reported by its owning hypervisor."""

    kind: Literal["qemu", "lxc"]
    vm_id: Annotated[int, Field(gt=0)]
    name: Annotated[str, Field(min_length=1, max_length=255)]
    state: Annotated[str, Field(min_length=1, max_length=80)]
    node: Annotated[str, Field(min_length=1, max_length=255)]
    vcpus: Annotated[int, Field(ge=0)]
    max_memory_bytes: Annotated[int, Field(ge=0)]
    max_disk_bytes: Annotated[int, Field(ge=0)]
    addresses: tuple[IPvAnyAddress, ...] = ()
    address_evidence: Literal["guest_agent", "unavailable"] = "unavailable"

    @field_validator("name", "node")
    @classmethod
    def names_are_safe(cls, value: str) -> str:
        if not _SAFE_NAME.fullmatch(value):
            raise ValueError("virtual guest name contains an unsafe character")
        return value


class GuestAddressObservation(StrictModel):
    interface: Annotated[str, Field(min_length=1, max_length=80)]
    state: Annotated[str, Field(min_length=1, max_length=40)]
    family: Literal[4, 6]
    address: IPvAnyInterface

    @model_validator(mode="after")
    def family_matches_address(self) -> GuestAddressObservation:
        if self.address.version != self.family:
            raise ValueError("guest address family does not match address")
        return self


class HostWorkloadObservation(StrictModel):
    host_id: str
    guest_hostname: Annotated[str, Field(min_length=1, max_length=255)]
    docker_available: bool
    containers: tuple[ContainerObservation, ...]
    addresses: tuple[GuestAddressObservation, ...] = ()
    virtual_guests: tuple[VirtualGuestObservation, ...] = ()

    @model_validator(mode="after")
    def runtime_shape_is_consistent(self) -> HostWorkloadObservation:
        if not self.docker_available and self.containers:
            raise ValueError("a host without Docker cannot report containers")
        names = [item.name for item in self.containers]
        duplicates = sorted({value for value in names if names.count(value) > 1})
        if duplicates:
            raise ValueError("duplicate container name: " + ", ".join(duplicates))
        guest_ids = [item.vm_id for item in self.virtual_guests]
        duplicate_guest_ids = sorted(
            {value for value in guest_ids if guest_ids.count(value) > 1}
        )
        if duplicate_guest_ids:
            raise ValueError(
                "duplicate virtual guest id: "
                + ", ".join(str(value) for value in duplicate_guest_ids)
            )
        return self


class WorkloadSnapshot(StrictModel):
    schema_version: Literal["dotmac.workload-snapshot.v1"]
    observed_at: datetime
    evidence_class: Literal[EvidenceClass.LIVE_OBSERVATION]
    hosts: tuple[HostWorkloadObservation, ...]

    @field_validator("observed_at")
    @classmethod
    def observed_at_is_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("workload observed_at must include a timezone")
        return value

    @model_validator(mode="after")
    def host_ids_are_unique(self) -> WorkloadSnapshot:
        values = [item.host_id for item in self.hosts]
        duplicates = sorted({value for value in values if values.count(value) > 1})
        if duplicates:
            raise ValueError("duplicate workload host id: " + ", ".join(duplicates))
        return self


class _WorkloadBuilder:
    """Ephemeral parser accumulator; never crosses a contract boundary."""

    host_id: str
    guest_hostname: str | None
    docker_available: bool | None
    containers: list[ContainerObservation]
    addresses: list[GuestAddressObservation]
    virtual_guests: list[VirtualGuestObservation]

    def __init__(self, host_id: str) -> None:
        self.host_id = host_id
        self.guest_hostname = None
        self.docker_available = None
        self.containers = []
        self.addresses = []
        self.virtual_guests = []


class TopologyDrift(StrictModel):
    provider_non_running_host_ids: tuple[str, ...]
    missing_provider_host_ids: tuple[str, ...]
    unknown_provider_host_ids: tuple[str, ...]
    provider_address_mismatch_host_ids: tuple[str, ...]
    missing_guest_ipv4_host_ids: tuple[str, ...]
    missing_guest_ipv6_host_ids: tuple[str, ...]
    missing_workload_host_ids: tuple[str, ...]
    unknown_workload_host_ids: tuple[str, ...]


def load_provider_snapshot(path: Path) -> ProviderSnapshot:
    return ProviderSnapshot.model_validate_json(path.read_bytes())


def load_workload_snapshot(path: Path) -> WorkloadSnapshot:
    return WorkloadSnapshot.model_validate_json(path.read_bytes())


def default_provider_snapshot_path() -> Path:
    return Path(__file__).with_name("data") / "provider_snapshot.json"


def default_workload_snapshot_path() -> Path:
    return Path(__file__).with_name("data") / "workload_snapshot.json"


def provider_snapshot_from_contabo(
    registry: FleetRegistry,
    payload: bytes | str,
    *,
    observed_at: datetime,
    private_network_payload: bytes | str,
) -> ProviderSnapshot:
    """Select the safe provider fields and bind rows to declarations by IPv4."""
    if observed_at.tzinfo is None:
        raise ValueError("provider observed_at must include a timezone")
    response = ContaboInstancesResponse.model_validate_json(payload)
    private_network_response = ContaboPrivateNetworksResponse.model_validate_json(
        private_network_payload
    )
    declared_by_ipv4 = {
        str(address): host.host_id
        for host in registry.hosts
        for address in host.public_addresses
        if address.version == 4
    }
    instances = []
    for item in response.data:
        if item.ip_config.v4.ip.version != 4 or item.ip_config.v6.ip.version != 6:
            raise ValueError(f"instance {item.instance_id} has wrong address families")
        ipv4 = str(item.ip_config.v4.ip)
        host_id = declared_by_ipv4.get(ipv4, f"unmapped-instance-{item.instance_id}")
        instances.append(
            ProviderInstanceObservation(
                host_id=host_id,
                instance_id=item.instance_id,
                provider_hostname=item.name,
                display_name=item.display_name,
                product_id=item.product_id,
                product_name=item.product_name,
                data_center=item.data_center,
                region=item.region,
                status=item.status,
                ipv4=item.ip_config.v4.ip,
                ipv4_prefix=item.ip_config.v4.netmask_cidr,
                ipv6=item.ip_config.v6.ip,
                ipv6_prefix=item.ip_config.v6.netmask_cidr,
                created_at=item.created_at,
                cancellation_date=item.cancellation_date,
            )
        )
    return ProviderSnapshot(
        schema_version="dotmac.provider-snapshot.v1",
        provider="contabo",
        observed_at=observed_at,
        evidence_class=EvidenceClass.PROVIDER_RECORD,
        instances=tuple(sorted(instances, key=lambda value: value.host_id)),
        private_networks=tuple(
            ProviderPrivateNetworkObservation(
                network_id=item.private_network_id,
                name=item.name,
                cidr=item.cidr,
                region=item.region,
                data_center=item.data_center,
                instance_ids=item.instances,
            )
            for item in sorted(
                private_network_response.data,
                key=lambda value: value.private_network_id,
            )
        ),
    )


def workload_snapshot_from_probe(
    payload: str,
    *,
    observed_at: datetime,
) -> WorkloadSnapshot:
    """Parse the deliberately narrow, non-secret fleet probe output."""
    if observed_at.tzinfo is None:
        raise ValueError("workload observed_at must include a timezone")
    current: _WorkloadBuilder | None = None
    hosts: list[HostWorkloadObservation] = []
    for line_number, line in enumerate(payload.splitlines(), start=1):
        if not line:
            continue
        kind, separator, remainder = line.partition("|")
        if kind == "BEGIN":
            if current is not None:
                raise ValueError(f"nested BEGIN at line {line_number}")
            host_id, host_separator, _access_address = remainder.partition("|")
            if not host_separator:
                raise ValueError(f"malformed BEGIN at line {line_number}")
            current = _WorkloadBuilder(host_id=host_id)
            continue
        if current is None:
            raise ValueError(f"{kind} outside a host block at line {line_number}")
        if kind == "HOSTNAME":
            current.guest_hostname = remainder
        elif kind == "DOCKER":
            if remainder not in {"true", "false"}:
                raise ValueError(f"invalid Docker flag at line {line_number}")
            current.docker_available = remainder == "true"
        elif kind == "CONTAINER":
            values = remainder.split("|", 3)
            if len(values) != 4:
                raise ValueError(f"malformed container at line {line_number}")
            name, image, state, runtime_status = values
            health = None
            if "(healthy)" in runtime_status:
                health = "healthy"
            elif "(unhealthy)" in runtime_status:
                health = "unhealthy"
            current.containers.append(
                ContainerObservation(
                    name=name,
                    image=image,
                    state=state,
                    runtime_status=runtime_status,
                    health=health,
                )
            )
        elif kind == "VIRTUAL_GUEST":
            values = remainder.split("|", 9)
            if len(values) != 10:
                raise ValueError(f"malformed virtual guest at line {line_number}")
            (
                guest_kind,
                vm_id,
                name,
                state,
                node,
                vcpus,
                max_memory_bytes,
                max_disk_bytes,
                address_evidence,
                addresses_text,
            ) = values
            if guest_kind not in {"qemu", "lxc"}:
                raise ValueError(f"invalid virtual guest kind at line {line_number}")
            if address_evidence not in {"guest_agent", "unavailable"}:
                raise ValueError(
                    f"invalid virtual guest address evidence at line {line_number}"
                )
            addresses = tuple(
                ip_address(address) for address in addresses_text.split(",") if address
            )
            current.virtual_guests.append(
                VirtualGuestObservation(
                    kind=cast(Literal["qemu", "lxc"], guest_kind),
                    vm_id=int(vm_id),
                    name=name,
                    state=state,
                    node=node,
                    vcpus=int(vcpus),
                    max_memory_bytes=int(max_memory_bytes),
                    max_disk_bytes=int(max_disk_bytes),
                    addresses=addresses,
                    address_evidence=cast(
                        Literal["guest_agent", "unavailable"], address_evidence
                    ),
                )
            )
        elif kind in {"ADDRESS4", "ADDRESS6"}:
            values = remainder.split()
            if len(values) < 3:
                raise ValueError(f"malformed address at line {line_number}")
            interface, state, *address_tokens = values
            family = 4 if kind == "ADDRESS4" else 6
            for token in address_tokens:
                try:
                    parsed = ip_interface(token)
                except ValueError:
                    continue
                if parsed.version != family:
                    continue
                current.addresses.append(
                    GuestAddressObservation(
                        interface=interface,
                        state=state,
                        family=family,
                        address=parsed,
                    )
                )
        elif kind == "END":
            host_id, host_separator, return_code = remainder.partition("|")
            if not host_separator or host_id != current.host_id:
                raise ValueError(f"malformed END at line {line_number}")
            if return_code != "0":
                raise ValueError(
                    f"probe for {current.host_id} refused with exit {return_code}"
                )
            if current.guest_hostname is None or current.docker_available is None:
                raise ValueError(f"incomplete probe for {current.host_id}")
            hosts.append(
                HostWorkloadObservation(
                    host_id=current.host_id,
                    guest_hostname=current.guest_hostname,
                    docker_available=current.docker_available,
                    containers=tuple(current.containers),
                    addresses=tuple(current.addresses),
                    virtual_guests=tuple(current.virtual_guests),
                )
            )
            current = None
        elif separator:
            raise ValueError(f"unknown probe record {kind!r} at line {line_number}")
        else:
            raise ValueError(f"malformed probe line {line_number}")
    if current is not None:
        raise ValueError(f"unterminated probe for {current.host_id}")
    return WorkloadSnapshot(
        schema_version="dotmac.workload-snapshot.v1",
        observed_at=observed_at,
        evidence_class=EvidenceClass.LIVE_OBSERVATION,
        hosts=tuple(sorted(hosts, key=lambda item: item.host_id)),
    )


def topology_drift(
    registry: FleetRegistry,
    provider: ProviderSnapshot,
    workloads: WorkloadSnapshot,
) -> TopologyDrift:
    declared = {host.host_id: host for host in registry.hosts}
    provider_declared = {
        host.host_id: host for host in registry.hosts if host.provider_ref == "contabo"
    }
    observed_provider = {item.host_id: item for item in provider.instances}
    observed_workloads = {item.host_id: item for item in workloads.hosts}
    active_ids = {
        host.host_id for host in registry.hosts if host.status.value == "active"
    }
    mismatched = []
    missing_guest_ipv4 = []
    missing_guest_ipv6 = []
    for host_id in provider_declared.keys() & observed_provider.keys():
        declared_addresses = {
            str(value) for value in declared[host_id].public_addresses
        }
        observed_addresses = {
            str(observed_provider[host_id].ipv4),
            str(observed_provider[host_id].ipv6),
        }
        if not declared_addresses.issubset(observed_addresses):
            mismatched.append(host_id)
        workload = observed_workloads.get(host_id)
        if workload is not None:
            guest_addresses = {str(item.address.ip) for item in workload.addresses}
            if str(observed_provider[host_id].ipv4) not in guest_addresses:
                missing_guest_ipv4.append(host_id)
            if str(observed_provider[host_id].ipv6) not in guest_addresses:
                missing_guest_ipv6.append(host_id)
    return TopologyDrift(
        provider_non_running_host_ids=tuple(
            sorted(
                item.host_id for item in provider.instances if item.status != "running"
            )
        ),
        missing_provider_host_ids=tuple(
            sorted(set(provider_declared) - set(observed_provider))
        ),
        unknown_provider_host_ids=tuple(sorted(set(observed_provider) - set(declared))),
        provider_address_mismatch_host_ids=tuple(sorted(mismatched)),
        missing_guest_ipv4_host_ids=tuple(sorted(missing_guest_ipv4)),
        missing_guest_ipv6_host_ids=tuple(sorted(missing_guest_ipv6)),
        missing_workload_host_ids=tuple(sorted(active_ids - set(observed_workloads))),
        unknown_workload_host_ids=tuple(
            sorted(set(observed_workloads) - set(declared))
        ),
    )


def inspect_topology_host(
    registry: FleetRegistry,
    provider: ProviderSnapshot,
    workloads: WorkloadSnapshot,
    host_id: str,
) -> dict[str, object]:
    declaration = registry.by_id(host_id)
    provider_item = next(
        (item for item in provider.instances if item.host_id == host_id), None
    )
    workload_item = next(
        (item for item in workloads.hosts if item.host_id == host_id), None
    )
    return {
        "ok": True,
        "schema_version": "dotmac.fleet-topology.v1",
        "declaration": declaration.model_dump(mode="json"),
        "provider_observation": (
            provider_item.model_dump(mode="json") if provider_item else None
        ),
        "workload_observation": (
            workload_item.model_dump(mode="json") if workload_item else None
        ),
    }


def topology_payload(
    registry: FleetRegistry,
    provider: ProviderSnapshot,
    workloads: WorkloadSnapshot,
) -> dict[str, object]:
    provider_by_host = {item.host_id: item for item in provider.instances}
    workloads_by_host = {item.host_id: item for item in workloads.hosts}
    hosts: list[dict[str, object]] = []
    for host in sorted(registry.hosts, key=lambda item: item.host_id):
        provider_item = provider_by_host.get(host.host_id)
        workload_item = workloads_by_host.get(host.host_id)
        hosts.append(
            {
                "declaration": host.model_dump(mode="json"),
                "provider_observation": (
                    provider_item.model_dump(mode="json") if provider_item else None
                ),
                "workload_observation": (
                    workload_item.model_dump(mode="json") if workload_item else None
                ),
            }
        )
    return {
        "ok": True,
        "schema_version": "dotmac.fleet-topology.v1",
        "provider_observed_at": provider.observed_at.isoformat(),
        "workloads_observed_at": workloads.observed_at.isoformat(),
        "drift": topology_drift(registry, provider, workloads).model_dump(mode="json"),
        "hosts": hosts,
    }


def _mermaid_text(value: str) -> str:
    return value.replace('"', "'").replace("\n", " ")


def render_mermaid_topology(
    registry: FleetRegistry,
    provider: ProviderSnapshot,
    workloads: WorkloadSnapshot,
) -> str:
    """Render stable Mermaid bytes from all three evidence classes."""
    provider_by_host = {item.host_id: item for item in provider.instances}
    workloads_by_host = {item.host_id: item for item in workloads.hosts}
    lines = ["flowchart LR", '  provider_contabo["Contabo provider record"]']
    source_nodes: dict[str, str] = {"contabo": "provider_contabo"}
    for source in sorted(
        {
            host.provider_ref
            for host in registry.hosts
            if not host.provider_ref.startswith("proxmox:vm/")
        }
    ):
        if source == "contabo":
            continue
        source_node = "provider_" + re.sub(r"[^a-z0-9_]", "_", source.lower())
        source_nodes[source] = source_node
        lines.append(f'  {source_node}["{_mermaid_text(source)} declaration"]')
    instance_host_ids = {item.instance_id: item.host_id for item in provider.instances}
    for provider_network in provider.private_networks:
        network_node = f"provider_network_{provider_network.network_id}"
        network_label = _mermaid_text(
            f"provider network: {provider_network.name}<br/>"
            f"{provider_network.cidr}<br/>"
            f"{len(provider_network.instance_ids)} members"
        )
        lines.append(f'  {network_node}{{"{network_label}"}}')
        lines.append(f"  provider_contabo --> {network_node}")
        for instance_id in sorted(provider_network.instance_ids):
            host_id = instance_host_ids.get(instance_id)
            if host_id is not None:
                lines.append(f"  {network_node} --> {host_id.replace('-', '_')}")

    overlay_members: dict[str, list[str]] = {}
    overlay_labels: dict[str, str] = {}
    for workload_host in workloads.hosts:
        for address in workload_host.addresses:
            if address.interface == "eth0" or address.interface == "docker0":
                continue
            if address.interface.startswith("br-") or address.family != 4:
                continue
            observed_network = ip_network(str(address.address), strict=False)
            key = str(observed_network)
            overlay_members.setdefault(key, []).append(workload_host.host_id)
            overlay_labels[key] = (
                f"observed {address.interface} range: {observed_network}"
                "<br/>connectivity not asserted"
            )
    for index, network_key in enumerate(sorted(overlay_members)):
        network_node = f"guest_network_{index}"
        lines.append(
            f'  {network_node}{{"{_mermaid_text(overlay_labels[network_key])}"}}'
        )
        for host_id in sorted(overlay_members[network_key]):
            lines.append(f"  {host_id.replace('-', '_')} -.-> {network_node}")

    for host in sorted(registry.hosts, key=lambda item: item.host_id):
        node = host.host_id.replace("-", "_")
        observed = provider_by_host.get(host.host_id)
        declared_ipv4 = next(
            (str(address) for address in host.public_addresses if address.version == 4),
            next(
                (
                    str(address)
                    for address in host.private_addresses
                    if address.version == 4
                ),
                "not declared",
            ),
        )
        declared_ipv6 = next(
            (str(address) for address in host.public_addresses if address.version == 6),
            next(
                (
                    str(address)
                    for address in host.private_addresses
                    if address.version == 6
                ),
                "not declared",
            ),
        )
        ipv4 = str(observed.ipv4) if observed else declared_ipv4
        ipv6 = str(observed.ipv6) if observed else declared_ipv6
        workload_observation = workloads_by_host.get(host.host_id)
        guest_hostname = (
            workload_observation.guest_hostname
            if workload_observation
            else "workload observation missing"
        )
        label = _mermaid_text(
            f"{host.host_id}<br/>{guest_hostname}<br/>{host.environment}<br/>"
            f"IPv4 {ipv4}<br/>IPv6 {ipv6}<br/>{host.purpose}"
        )
        lines.append(f'  {node}["{label}"]')
        if host.provider_ref.startswith("proxmox:vm/"):
            lines.append(f"  proxmox --> {node}")
        else:
            lines.append(f"  {source_nodes[host.provider_ref]} --> {node}")
        if workload_observation is None:
            missing = f"{node}_workloads_missing"
            lines.append(f'  {missing}["workload observation missing"]')
            lines.append(f"  {node} -.-> {missing}")
            continue
        if not workload_observation.docker_available:
            host_only = f"{node}_host_only"
            lines.append(f'  {host_only}["host-only / no Docker"]')
            lines.append(f"  {node} --> {host_only}")
        else:
            for index, container in enumerate(
                sorted(workload_observation.containers, key=lambda item: item.name)
            ):
                container_node = f"{node}_c{index}"
                container_label = _mermaid_text(
                    f"{container.name}<br/>{container.image}<br/>{container.state}"
                )
                lines.append(f'  {container_node}(["{container_label}"])')
                lines.append(f"  {node} --> {container_node}")
        for guest in sorted(
            workload_observation.virtual_guests, key=lambda item: item.vm_id
        ):
            guest_node = f"{node}_vm{guest.vm_id}"
            addresses = ", ".join(str(value) for value in guest.addresses)
            address_line = addresses or "address unavailable"
            guest_label = _mermaid_text(
                f"{guest.kind} {guest.vm_id}: {guest.name}<br/>{guest.state}<br/>"
                f"{address_line}"
            )
            lines.append(f'  {guest_node}(["{guest_label}"])')
            lines.append(f"  {node} --> {guest_node}")
    return "\n".join(lines).rstrip() + "\n"


def render_markdown_census(
    registry: FleetRegistry,
    provider: ProviderSnapshot,
    workloads: WorkloadSnapshot,
) -> str:
    """Render the review surface for addresses, hostnames, and containers."""
    provider_by_host = {item.host_id: item for item in provider.instances}
    workloads_by_host = {item.host_id: item for item in workloads.hosts}
    drift = topology_drift(registry, provider, workloads)
    lines = [
        "# Fleet census",
        "",
        f"- Provider observation: `{provider.observed_at.isoformat()}`",
        f"- Workload observation: `{workloads.observed_at.isoformat()}`",
        f"- Declared hosts: `{len(registry.hosts)}`",
        f"- Running Docker containers: `"
        f"{sum(len(item.containers) for item in workloads.hosts)}`",
        f"- Declared virtual guests: `"
        f"{sum(len(item.virtual_guests) for item in workloads.hosts)}`",
        "- Evidence: `provider_record` plus `live_observation`",
        "",
        "Provider state does not decide declared purpose or lifecycle. Guest "
        "addresses report configured interfaces, not external reachability.",
        "",
        "| Host | Provider hostname | Provider label | Guest hostname | IPv4 | "
        "IPv6 | Containers | Purpose |",
        "|---|---|---|---|---|---|---:|---|",
    ]
    for declared_host in sorted(registry.hosts, key=lambda item: item.host_id):
        provider_item = provider_by_host.get(declared_host.host_id)
        workload_item = workloads_by_host.get(declared_host.host_id)
        provider_hostname = (
            provider_item.provider_hostname if provider_item else "not-applicable"
        )
        provider_label = provider_item.display_name if provider_item else "on-prem"
        ipv4 = (
            str(provider_item.ipv4)
            if provider_item
            else next(
                (
                    str(address)
                    for address in (
                        *declared_host.public_addresses,
                        *declared_host.private_addresses,
                    )
                    if address.version == 4
                ),
                "not-declared",
            )
        )
        ipv6 = (
            f"{provider_item.ipv6}/{provider_item.ipv6_prefix}"
            if provider_item
            else next(
                (
                    str(address)
                    for address in (
                        *declared_host.public_addresses,
                        *declared_host.private_addresses,
                    )
                    if address.version == 6
                ),
                "not-declared",
            )
        )
        guest_hostname = (
            workload_item.guest_hostname
            if workload_item
            else "workload observation missing"
        )
        container_count = len(workload_item.containers) if workload_item else 0
        lines.append(
            f"| `{declared_host.host_id}` | `{provider_hostname}` | "
            f"{provider_label} | `{guest_hostname}` | "
            f"`{ipv4}` | `{ipv6}` | "
            f"{container_count} | "
            f"{declared_host.purpose} |"
        )
    lines.extend(["", "## Provider private networks", ""])
    for network in provider.private_networks:
        lines.append(
            f"- `{network.name}` (`{network.cidr}`, id `{network.network_id}`): "
            f"{len(network.instance_ids)} attached instances."
        )
    lines.extend(["", "## Drift", ""])
    drift_payload = drift.model_dump(mode="json")
    for key, values in drift_payload.items():
        rendered_values = ", ".join(f"`{value}`" for value in values) or "none"
        lines.append(f"- `{key}`: {rendered_values}")
    lines.extend(
        [
            "",
            "## Agent access",
            "",
            "Pointers identify where credentials are held; this report never "
            "dereferences them.",
            "",
            "| Host | SSH alias | User | Route | Identity pointer | Recovery "
            "pointer | API access |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for declared_host in sorted(registry.hosts, key=lambda item: item.host_id):
        access = declared_host.access
        route = (
            f"via {access.proxy_jump} to {access.endpoint or access.alias}"
            if access.proxy_jump
            else str(access.endpoint or access.alias or "unavailable")
        )
        api_summary = (
            "; ".join(
                f"{item.name}: {item.status.value} ({item.endpoint})"
                + (f" [{item.credential_ref}]" if item.credential_ref else "")
                for item in declared_host.api_access
            )
            or "none declared"
        )
        lines.append(
            f"| `{declared_host.host_id}` | `{access.alias or 'unavailable'}` | "
            f"`{access.user or 'unavailable'}` | `{route}` | "
            f"`{access.identity_ref or 'none'}` | "
            f"`{access.recovery_secret_ref or 'not verified'}` | "
            f"{api_summary} |"
        )
    lines.extend(["", "## Containers by host", ""])
    for workload_host in sorted(workloads.hosts, key=lambda item: item.host_id):
        lines.extend([f"### {workload_host.host_id}", ""])
        if not workload_host.docker_available:
            lines.extend(["Host-only; Docker is not installed.", ""])
            continue
        if not workload_host.containers:
            lines.extend(["Docker is installed; no running containers observed.", ""])
        else:
            lines.extend(
                [
                    "| Container | Image | State | Health |",
                    "|---|---|---|---|",
                ]
            )
            for container in sorted(
                workload_host.containers, key=lambda item: item.name
            ):
                lines.append(
                    f"| `{container.name}` | `{container.image}` | "
                    f"`{container.state}` | `{container.health or 'not-reported'}` |"
                )
            lines.append("")
        if workload_host.virtual_guests:
            lines.extend(
                [
                    "| Guest | Type | State | vCPU | Memory bytes | Disk bytes "
                    "| Addresses |",
                    "|---|---|---|---:|---:|---:|---|",
                ]
            )
            for guest in sorted(
                workload_host.virtual_guests, key=lambda item: item.vm_id
            ):
                addresses = ", ".join(str(value) for value in guest.addresses)
                lines.append(
                    f"| `{guest.vm_id}: {guest.name}` | `{guest.kind}` | "
                    f"`{guest.state}` | {guest.vcpus} | {guest.max_memory_bytes} | "
                    f"{guest.max_disk_bytes} | `{addresses or 'unavailable'}` |"
                )
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def canonical_snapshot_json(model: BaseModel) -> str:
    """Return stable reviewed bytes; callers decide whether and where to write."""
    return (
        json.dumps(
            model.model_dump(mode="json"),
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
        )
        + "\n"
    )


__all__ = [
    "ContainerObservation",
    "ContaboInstancesResponse",
    "GuestAddressObservation",
    "HostWorkloadObservation",
    "ProviderInstanceObservation",
    "ProviderSnapshot",
    "TopologyDrift",
    "VirtualGuestObservation",
    "WorkloadSnapshot",
    "canonical_snapshot_json",
    "default_provider_snapshot_path",
    "default_workload_snapshot_path",
    "inspect_topology_host",
    "load_provider_snapshot",
    "load_workload_snapshot",
    "provider_snapshot_from_contabo",
    "render_mermaid_topology",
    "render_markdown_census",
    "topology_drift",
    "topology_payload",
    "workload_snapshot_from_probe",
]
