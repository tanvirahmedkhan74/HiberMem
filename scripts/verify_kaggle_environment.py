"""Fail-fast validation for a Kaggle HiberMem GPU checkout."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import os
import shutil
import subprocess
import tomllib
from datetime import datetime, timezone
from pathlib import Path

from packaging.version import Version


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MIN_FREE_STORAGE_GIB = 30.0


def configured_min_free_storage_gib() -> float:
    """Read an explicit, validated Kaggle storage floor from the environment."""
    raw_value = os.environ.get("HIBERMEM_MIN_FREE_STORAGE_GIB")
    if raw_value is None:
        return DEFAULT_MIN_FREE_STORAGE_GIB
    try:
        value = float(raw_value)
    except ValueError as error:
        raise RuntimeError(
            "HIBERMEM_MIN_FREE_STORAGE_GIB must be a positive number of GiB"
        ) from error
    if not math.isfinite(value) or value <= 0:
        raise RuntimeError(
            "HIBERMEM_MIN_FREE_STORAGE_GIB must be a positive number of GiB"
        )
    return value


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def verify(
    root: Path, *, min_free_storage_gib: float | None = None
) -> dict[str, object]:
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    project_name = str(project["project"]["name"])
    if project_name != "hibermem":
        raise RuntimeError(
            f"wrong GitHub repository: expected project 'hibermem', found {project_name!r}"
        )
    try:
        import torch
    except ImportError as error:
        raise RuntimeError("Kaggle's CUDA-enabled PyTorch is missing") from error
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable; enable a GPU accelerator in Kaggle")
    if Version(torch.__version__.split("+")[0]) < Version("2.5"):
        raise RuntimeError(f"PyTorch >= 2.5 is required; found {torch.__version__}")
    transformers_version = importlib.metadata.version("transformers")
    if transformers_version != "5.16.1":
        raise RuntimeError(
            "unexpected Transformers version; install configs/requirements/"
            f"kaggle-phase2r.txt (found {transformers_version})"
        )
    required_free_storage_gib = (
        configured_min_free_storage_gib()
        if min_free_storage_gib is None
        else min_free_storage_gib
    )
    if not math.isfinite(required_free_storage_gib) or required_free_storage_gib <= 0:
        raise ValueError("min_free_storage_gib must be positive")
    free_bytes = shutil.disk_usage(root).free
    if free_bytes < required_free_storage_gib * 1024**3:
        raise RuntimeError(
            "at least "
            f"{required_free_storage_gib:g} GiB of free working storage is required"
        )
    return {
        "schema_version": 1,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": project_name,
        "root": str(root),
        "git_commit": _git(root, "rev-parse", "HEAD"),
        "git_remote": _git(root, "remote", "get-url", "origin"),
        "python_packages": {
            name: importlib.metadata.version(name)
            for name in ("hibermem", "numpy", "scipy", "torch", "transformers")
        },
        "cuda": {
            "available": True,
            "runtime": torch.version.cuda,
            "device_count": torch.cuda.device_count(),
            "devices": [
                torch.cuda.get_device_name(index)
                for index in range(torch.cuda.device_count())
            ],
        },
        "free_storage_gib": free_bytes / 1024**3,
        "required_free_storage_gib": required_free_storage_gib,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "phase2r_kaggle_environment.json",
    )
    args = parser.parse_args()
    report = verify(args.root.resolve())
    output = args.output if args.output.is_absolute() else args.root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Kaggle environment report: {output}")
    print(f"GPU: {', '.join(report['cuda']['devices'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
