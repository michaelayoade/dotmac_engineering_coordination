from __future__ import annotations

import json
from pathlib import Path

from dotmac_engineering_coordination.cli import main

DATA = Path(__file__).parents[1] / "src/dotmac_engineering_coordination/data/fleet.toml"


def test_cli_check_is_a_positive_control(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(("--registry", str(DATA), "check")) == 0
    assert json.loads(capsys.readouterr().out)["host_count"] == 27


def test_cli_refusal_keeps_its_code(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(("--registry", str(DATA), "access-plan", "erp")) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["refusal"]["code"] == "FLEET_PRODUCTION_CONFIRMATION_REQUIRED"
