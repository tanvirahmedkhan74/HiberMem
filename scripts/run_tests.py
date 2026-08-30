"""Run pytest with this interpreter and a fresh, workspace-owned temp directory.

Use .conda/python.exe to select the project environment explicitly on Windows.
Never point pytest --basetemp at an existing user directory: pytest clears it.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def test_command(root: Path, arguments: list[str]) -> list[str]:
    if any(arg == "--basetemp" or arg.startswith("--basetemp=") for arg in arguments):
        raise ValueError("run_tests owns a fresh basetemp; do not supply --basetemp")
    parent = (root / "results" / "pytest-runs").resolve()
    if not parent.is_relative_to(root.resolve()):
        raise ValueError("pytest scratch directory must remain inside the workspace")
    parent.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.mkdtemp(prefix="run-", dir=parent)
    return [sys.executable, "-m", "pytest", "--basetemp", temporary, *(arguments or ["-q"])]


def main(arguments: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if arguments is None else arguments)
    if "--help" in arguments or "-h" in arguments:
        print("Usage: python scripts/run_tests.py [pytest arguments]\n"
              "Uses the invoking Python and a unique results/pytest-runs directory.")
        return 0
    command = test_command(ROOT, arguments)
    print(f"Test interpreter: {sys.executable}", flush=True)
    print(f"Test scratch directory: {command[4]}", flush=True)
    return subprocess.run(command, cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
