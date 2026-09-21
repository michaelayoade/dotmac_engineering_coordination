from __future__ import annotations

import json
from pathlib import Path

from dotmac_engineering_coordination.cli import main

DATA_DIR = Path(__file__).parents[1] / "src/dotmac_engineering_coordination/data"
DATA = DATA_DIR / "fleet.toml"
WORKLOAD_BASELINE = DATA_DIR / "workload_snapshot.json"


def test_cli_check_is_a_positive_control(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(("--registry", str(DATA), "check")) == 0
    assert json.loads(capsys.readouterr().out)["host_count"] == 28


def test_cli_refusal_keeps_its_code(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(("--registry", str(DATA), "access-plan", "erp")) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["refusal"]["code"] == "FLEET_PRODUCTION_CONFIRMATION_REQUIRED"


def test_cli_workload_merge_records_a_declared_hosts_first_observation(
    tmp_path: Path, capsys  # type: ignore[no-untyped-def]
) -> None:
    """Uses its own baseline fixture -- a copy of the real checked-in
    workload_snapshot.json with the dotmac-labs entry stripped back out --
    rather than asserting against the live file directly. The real file may
    already have dotmac-labs merged into it (that is precisely what this
    repo's own data is meant to end up recording); pointing this test at it
    directly would silently stop exercising the first-observation/growth
    branch of upsert_workload_observation the moment that merge landed, and
    instead exercise only the replace branch -- exactly the class of bug
    this whole feature was built to fix. Keeping a "never-yet-observed"
    baseline here is what actually proves the growth path."""
    real_baseline = json.loads(WORKLOAD_BASELINE.read_text())
    real_baseline["hosts"] = [
        host for host in real_baseline["hosts"] if host["host_id"] != "dotmac-labs"
    ]
    baseline_without_dotmac_labs = tmp_path / "baseline-without-dotmac-labs.json"
    baseline_without_dotmac_labs.write_text(json.dumps(real_baseline))

    probe_input = tmp_path / "dotmac-labs-probe.txt"
    probe_input.write_text(
        "BEGIN|dotmac-labs|10.120.120.42\n"
        "HOSTNAME|dotmac-labs\n"
        "DOCKER|true\n"
        "CONTAINER|clab-academy-r1|ghcr.io/example/routeros:1|running|Up 3 hours\n"
        "END|dotmac-labs|0\n"
    )
    exit_code = main(
        (
            "--registry",
            str(DATA),
            "workload-merge",
            "--baseline",
            str(baseline_without_dotmac_labs),
            "--input",
            str(probe_input),
            "--observed-at",
            "2026-09-21T18:00:00+00:00",
        )
    )
    assert exit_code == 0
    merged = json.loads(capsys.readouterr().out)
    by_host = {host["host_id"]: host for host in merged["hosts"]}
    assert by_host["dotmac-labs"]["observed_at"] == "2026-09-21T18:00:00Z"
    assert by_host["dotmac-labs"]["containers"][0]["name"] == "clab-academy-r1"
    # Every previously observed host survives untouched, and the document's
    # own last-full-sweep observed_at does not advance.
    assert merged["observed_at"] == real_baseline["observed_at"]
    assert len(merged["hosts"]) == len(real_baseline["hosts"]) + 1


def test_cli_workload_merge_refuses_multi_host_input(
    tmp_path: Path, capsys  # type: ignore[no-untyped-def]
) -> None:
    probe_input = tmp_path / "two-hosts-probe.txt"
    probe_input.write_text(
        "BEGIN|dotmac-labs|10.120.120.42\n"
        "HOSTNAME|dotmac-labs\n"
        "DOCKER|true\n"
        "END|dotmac-labs|0\n"
        "BEGIN|garki-core|160.119.127.252\n"
        "HOSTNAME|garki-core\n"
        "DOCKER|false\n"
        "END|garki-core|0\n"
    )
    exit_code = main(
        (
            "--registry",
            str(DATA),
            "workload-merge",
            "--baseline",
            str(WORKLOAD_BASELINE),
            "--input",
            str(probe_input),
            "--observed-at",
            "2026-09-21T18:00:00+00:00",
        )
    )
    assert exit_code == 2
    assert "exactly one host" in capsys.readouterr().err


def test_cli_workload_merge_refuses_an_undeclared_host(
    tmp_path: Path, capsys  # type: ignore[no-untyped-def]
) -> None:
    probe_input = tmp_path / "ghost-probe.txt"
    probe_input.write_text(
        "BEGIN|never-registered-anywhere|0.0.0.0\n"
        "HOSTNAME|ghost\n"
        "DOCKER|false\n"
        "END|never-registered-anywhere|0\n"
    )
    exit_code = main(
        (
            "--registry",
            str(DATA),
            "workload-merge",
            "--baseline",
            str(WORKLOAD_BASELINE),
            "--input",
            str(probe_input),
            "--observed-at",
            "2026-09-21T18:00:00+00:00",
        )
    )
    assert exit_code == 2
    assert "not a declared fleet host" in capsys.readouterr().err
