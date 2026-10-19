from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


class SimulationCraftError(Exception):
    def __init__(self, message: str, *, exit_code: int | None = None, stderr: str = "") -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.stderr = stderr


@dataclass
class SimcRunResult:
    report_path: Path
    stdout: str
    stderr: str
    exit_code: int
    work_dir: Path


def run_simc(
    *,
    simc_path: str,
    profile_text: str,
    extra_args: list[str],
    timeout_seconds: int,
) -> SimcRunResult:
    binary = Path(simc_path)
    if not binary.is_file():
        raise SimulationCraftError(
            f"SimulationCraft binary not found at {simc_path}. Run engine/simc/build.sh first."
        )

    work_dir = Path(tempfile.mkdtemp(prefix="wowdpslab-simc-"))
    profile_path = work_dir / "profile.simc"
    report_path = work_dir / "report.json"
    profile_path.write_text(profile_text, encoding="utf-8")

    argv = [
        str(binary),
        str(profile_path),
        f"json2={report_path}",
        "output=/dev/null",
        *extra_args,
    ]

    try:
        completed = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=str(work_dir),
            env={**os.environ, "LANG": "C.UTF-8"},
        )
    except subprocess.TimeoutExpired as exc:
        raise SimulationCraftError(
            f"SimulationCraft timed out after {timeout_seconds}s",
            exit_code=None,
            stderr=str(exc),
        ) from exc

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    combined = f"{stdout}\n{stderr}"

    if "Initialization error" in combined and not report_path.exists():
        raise SimulationCraftError(
            "SimulationCraft initialization failed",
            exit_code=completed.returncode,
            stderr=combined,
        )

    if completed.returncode not in (0,) or not report_path.exists():
        raise SimulationCraftError(
            f"SimulationCraft failed with exit code {completed.returncode}",
            exit_code=completed.returncode,
            stderr=combined[-4000:],
        )

    return SimcRunResult(
        report_path=report_path,
        stdout=stdout,
        stderr=stderr,
        exit_code=completed.returncode,
        work_dir=work_dir,
    )
