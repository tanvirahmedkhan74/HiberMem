"""Independently validate E4 past or complete artifacts without model loading."""

from __future__ import annotations

import argparse
from pathlib import Path

from hibermem.experiments.prospective import (
    validate_prospective_past,
    validate_prospective_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--stage", choices=("past", "complete"), default="complete")
    parser.add_argument("--allow-mock", action="store_true")
    args = parser.parse_args()
    try:
        run_dir = args.run_dir.resolve()
        if args.stage == "past":
            validate_prospective_past(run_dir, allow_mock=args.allow_mock)
        else:
            validate_prospective_report(
                run_dir / "report.json", allow_mock=args.allow_mock
            )
        print("Artifact validation: PASS. No qualification or historical test access.")
        return 0
    except Exception as error:
        print(f"Artifact validation: FAIL: {type(error).__name__}: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
