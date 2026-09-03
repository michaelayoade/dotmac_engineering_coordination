# ADR 0001: Fleet registry is declared and agent-readable

- Status: Accepted
- Date: 2026-09-03
- Owner: dotmac_engineering_coordination
- Repository visibility: private

## Context

Fleet facts were spread across Knowledge entries and individual SSH configs.
The inspected inventory named twenty Contabo VPS instances plus Seabone and a
single-node Proxmox cluster, while one agent's SSH config covered eight
addresses and only six friendly aliases. Records also
disagreed about the observability canary and the former CRM/SON ERP host.

Knowledge is recall-oriented and SSH config is machine-local. Neither is an
enforced owner for operational discovery.

## Decision

This repository owns one typed, reviewed fleet registry. The MCP server reads
that declaration and exposes only read tools. It never connects to a host,
retrieves a secret, or decides a deployment.

Access metadata is safe metadata: alias, endpoint, username, port, proxy jump,
authentication method, local identity reference, optional OpenBao pointer and
typed API coordinates/status.
Secret values are structurally absent. Password authentication is not in the
vocabulary.

Production access requires an exact host-id confirmation. Records that are
stale, conflicted, inactive or not access-verified cannot produce an access
plan. Each refusal has a stable code.

Provider and workload facts are separate, dated observations. The Contabo
projection selects only instance identity, provider hostname/label, product,
region, lifecycle and IP configuration; raw account responses remain outside
Git. The workload projection selects guest hostname, interface addresses,
container name/image/state and hypervisor guest identity/status/capacity only.
Neither projection can write declared purpose, ownership, lifecycle or access
policy. A hypervisor guest address is reported only when a live guest agent
provided it; absence remains explicit.

The repository is private because resolved fleet addresses and topology are
operational material. Knowledge indexes the owning revision and reusable
lessons; public repositories may carry only logical identifiers.

## Evidence classes

Every claim names its class. `live_observation` outranks a
`knowledge_reference`; `relayed_unverified` never becomes a live observation by
being copied here. Evidence is descriptive and never an authorization input.

## Consequences

The fleet is searchable through a stable MCP vocabulary. A deterministic SSH
fragment can be byte-compared in CI. Knowledge keeps a pointer to this
repository rather than a second inventory.

Michael accepted the ownership and initial migration mapping on 2026-09-03.
Acceptance authorizes publication and installation of this read-only discovery
surface. It does not authorize a production connection or mutation: those
still require the exact target and the applicable deployment/access control.
