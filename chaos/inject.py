"""Chaos injector: apply a scenario's kubectl commands (FEATURES F23).

Usage: python chaos/inject.py <scenario-id> [--dry-run] | --list
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import validate

ROOT = Path(__file__).parent
SCENARIOS = ROOT / "scenarios"
SCHEMA = ROOT / "scenario.schema.json"


def load_scenario(path: Path) -> dict[str, Any]:
    """Load a scenario YAML and validate it against the JSON schema."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    validate(data, json.loads(SCHEMA.read_text(encoding="utf-8")))
    return dict(data)


def all_scenarios() -> dict[str, dict[str, Any]]:
    """Every scenario keyed by id."""
    return {s["id"]: s for s in (load_scenario(p) for p in sorted(SCENARIOS.glob("*.yaml")))}


def run(scenario: dict[str, Any], dry_run: bool = False) -> None:
    """Print and execute each inject command (kubectl), then say which alert to watch."""
    print(f"Scenario: {scenario['id']} - {scenario['title']}")
    for args in scenario["inject"]:
        cmd = ["kubectl", *args]
        print("$ " + " ".join(shlex.quote(a) for a in cmd))
        if not dry_run:
            subprocess.run(cmd, check=True)
    wait = scenario["wait_for_alert"]
    print(f"Watch for alert {wait['alertname']} (up to {wait.get('timeout_s', 300)}s).")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", nargs="?")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args(argv)

    scenarios = all_scenarios()
    if args.list:
        for sid, s in scenarios.items():
            print(f"{sid:22} {s['title']}")
        return 0
    if not args.scenario or args.scenario not in scenarios:
        print(f"unknown scenario {args.scenario!r}; use --list", file=sys.stderr)
        return 2
    run(scenarios[args.scenario], dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
