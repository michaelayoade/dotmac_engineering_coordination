"""Operator CLI for validating and inspecting the fleet registry."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from dotmac_engineering_coordination.registry import (
    FleetRefusal,
    FleetService,
    load_registry,
)
from dotmac_engineering_coordination.topology import (
    canonical_snapshot_json,
    load_provider_snapshot,
    load_workload_snapshot,
    provider_snapshot_from_contabo,
    render_markdown_census,
    render_mermaid_topology,
    topology_payload,
    workload_snapshot_from_probe,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dotmac-coordination")
    parser.add_argument("--registry", type=Path, help="reviewed fleet TOML path")
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("check", help="validate schema and report debt")
    check.add_argument("--require-ready", action="store_true")

    commands.add_parser("list", help="list all fleet hosts")

    get = commands.add_parser("get", help="get one fleet host")
    get.add_argument("host_id")

    plan = commands.add_parser("access-plan", help="return, but never run, SSH argv")
    plan.add_argument("host_id")
    plan.add_argument("--confirm-production-host")

    commands.add_parser("render-ssh", help="render verified SSH aliases")

    provider = commands.add_parser(
        "provider-snapshot", help="normalize a Contabo API response from a file"
    )
    provider.add_argument("--input", type=Path, required=True)
    provider.add_argument("--private-networks", type=Path, required=True)
    provider.add_argument("--observed-at", type=datetime.fromisoformat, required=True)

    workload = commands.add_parser(
        "workload-snapshot", help="normalize the narrow read-only fleet probe"
    )
    workload.add_argument("--input", type=Path, required=True)
    workload.add_argument("--observed-at", type=datetime.fromisoformat, required=True)

    topology = commands.add_parser(
        "topology", help="join declarations and dated observations"
    )
    topology.add_argument("--provider", type=Path, required=True)
    topology.add_argument("--workloads", type=Path, required=True)
    topology.add_argument(
        "--format", choices=("json", "mermaid", "markdown"), default="json"
    )
    return parser


def _print(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    service = FleetService(load_registry(args.registry))

    if args.command == "check":
        health = service.health()
        _print(health)
        return 2 if args.require_ready and not health["ready"] else 0
    if args.command == "list":
        _print(service.list_hosts())
        return 0
    if args.command == "get":
        try:
            payload = service.get_host(args.host_id)
        except FleetRefusal as refusal:
            payload = refusal.as_dict()
        _print(payload)
        return 0 if payload["ok"] else 2
    if args.command == "access-plan":
        payload = service.access_plan_payload(
            args.host_id,
            confirm_production_host=args.confirm_production_host,
        )
        _print(payload)
        return 0 if payload["ok"] else 2
    if args.command == "render-ssh":
        sys.stdout.write(service.render_ssh_config())
        return 0
    if args.command == "provider-snapshot":
        provider_snapshot = provider_snapshot_from_contabo(
            service.registry,
            args.input.read_bytes(),
            observed_at=args.observed_at,
            private_network_payload=args.private_networks.read_bytes(),
        )
        sys.stdout.write(canonical_snapshot_json(provider_snapshot))
        return 0
    if args.command == "workload-snapshot":
        workload_snapshot = workload_snapshot_from_probe(
            args.input.read_text(),
            observed_at=args.observed_at,
        )
        sys.stdout.write(canonical_snapshot_json(workload_snapshot))
        return 0
    if args.command == "topology":
        provider = load_provider_snapshot(args.provider)
        workloads = load_workload_snapshot(args.workloads)
        if args.format == "mermaid":
            sys.stdout.write(
                render_mermaid_topology(service.registry, provider, workloads)
            )
        elif args.format == "markdown":
            sys.stdout.write(
                render_markdown_census(service.registry, provider, workloads)
            )
        else:
            _print(topology_payload(service.registry, provider, workloads))
        return 0
    raise AssertionError(f"unhandled command {args.command!r}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


__all__ = ["main"]
