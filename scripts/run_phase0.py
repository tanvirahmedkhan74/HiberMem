"""Run the Phase 0 mathematical gate and persist an auditable report."""

from __future__ import annotations

import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "results" / "phase0_report.json"
TESTS = [
    "tests/test_masks.py",
    "tests/test_mobius.py",
    "tests/test_interaction_sign.py",
    "tests/test_estimators.py",
    "tests/test_shapiq_reference.py",
]


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _git_provenance() -> dict[str, str | bool | None]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        return {"available": True, "commit": commit, "dirty": dirty}
    except (FileNotFoundError, subprocess.CalledProcessError):
        return {"available": False, "commit": None, "dirty": None}


def main() -> int:
    command = [sys.executable, "-m", "pytest", "-q", *TESTS]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    reference_available = _package_version("shapiq") is not None
    gate_passed = completed.returncode == 0 and reference_available
    report = {
        "schema_version": 1,
        "phase": 0,
        "gate": "P0",
        "gate_passed": gate_passed,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "mathematical correctness; no LLM inference",
        "conventions": {
            "mask_bit_order": "player i is bit i",
            "polynomial_decomposition": "Mobius/Harsanyi",
            "shapley_family_reference": "Grabisch-Roubens SII",
            "local_interaction": "reported separately from SII and Mobius",
        },
        "reference_agreement": {
            "library": "shapiq",
            "available": reference_available,
            "version": _package_version("shapiq"),
            "required_for_gate": True,
        },
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "pytest": _package_version("pytest"),
            "command": command,
        },
        "git": _git_provenance(),
        "tests": {
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "files": TESTS,
        },
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="")
    print(f"Phase 0 report: {REPORT_PATH}")
    print(f"Gate P0: {'PASS' if gate_passed else 'FAIL'}")
    return 0 if gate_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
