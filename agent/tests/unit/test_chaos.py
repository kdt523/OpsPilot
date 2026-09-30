"""Chaos scenarios validate against the schema and --dry-run runs nothing (FEATURES F23)."""

import subprocess
import sys
from pathlib import Path

import pytest

CHAOS = Path(__file__).parents[3] / "chaos"
sys.path.insert(0, str(CHAOS))

import inject  # noqa: E402

EXPECTED = {
    "bad-image-tag",
    "buggy-release",
    "missing-config",
    "oom",
    "wrong-service-name",
    "redis-down",
    "bad-readiness-probe",
    "cpu-throttling",
    "prompt-injection",
}


def test_all_nine_scenarios_validate() -> None:
    assert set(inject.all_scenarios()) == EXPECTED


def test_dry_run_prints_without_running(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def boom(*a: object, **k: object) -> None:
        raise AssertionError("subprocess must not run in --dry-run")

    monkeypatch.setattr(subprocess, "run", boom)
    assert inject.main(["bad-image-tag", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "kubectl set image deployment/orders" in out
    assert "PodNotHealthy" in out


def test_unknown_scenario_fails() -> None:
    assert inject.main(["nope"]) == 2
