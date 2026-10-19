#!/usr/bin/env python3
"""Smoke Supported/Experimental specs against the pinned SimulationCraft binary."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIMC = ROOT / "engine/simc/bin/simc"
CATALOG = ROOT / "packages/game-data/catalog/12.1.5/catalog.json"
PRESETS = ROOT / "packages/game-data/presets/12.1.5"


def main() -> int:
    if not SIMC.is_file():
        print("Missing simc binary. Run ./engine/simc/build.sh", file=sys.stderr)
        return 2

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    failures: list[str] = []
    for wow_class in catalog["classes"]:
        for spec in wow_class["specs"]:
            support = spec.get("readiness") or spec["simulationSupport"]
            if support == "unsupported" or not spec.get("canAccurate", support != "unsupported"):
                continue
            profile = spec.get("presetProfile")
            if not profile:
                failures.append(f"{spec['name']}: missing preset")
                continue
            path = PRESETS / profile
            if not path.is_file():
                failures.append(f"{spec['name']}: preset file missing ({profile})")
                continue
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "report.json"
                text = path.read_text(encoding="utf-8")
                # Mirror composer fallback for known broken hashes
                if support in {"partial", "implemented"} and "talents=" in text:
                    lines = [ln for ln in text.splitlines() if not ln.startswith("talents=")]
                    hero = spec.get("defaultHeroTalent")
                    if hero:
                        lines.append(f"hero_talents={hero}")
                    text = "\n".join(lines) + "\n"
                profile_path = Path(tmp) / "profile.simc"
                profile_path.write_text(text, encoding="utf-8")
                proc = subprocess.run(
                    [
                        str(SIMC),
                        str(profile_path),
                        "iterations=5",
                        "max_time=60",
                        "threads=1",
                        f"json2={out}",
                        "output=/dev/null",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )
                ok = out.is_file()
                mean = 0.0
                if ok:
                    report = json.loads(out.read_text(encoding="utf-8"))
                    mean = report["sim"]["players"][0]["collected_data"]["dps"]["mean"]
                    ok = mean > 0
                status = "OK" if ok else "FAIL"
                print(f"[{status}] {wow_class['name']} {spec['name']} ({support}) dps={mean:.1f}")
                if not ok:
                    failures.append(f"{spec['name']}: sim failed ({proc.stderr[-200:]})")
    if failures:
        print("\nFailures:", file=sys.stderr)
        for f in failures:
            print(f" - {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
