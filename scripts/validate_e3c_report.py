"""Independently validate a complete E3c artifact without model loading."""

from __future__ import annotations

import argparse
from pathlib import Path

from hibermem.experiments.contract import validate_contract_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--allow-mock", action="store_true")
    args = parser.parse_args()
    try:
        validate_contract_report(args.report.resolve(), allow_mock=args.allow_mock)
        print("Artifact validation: PASS. Development-only; no qualification or test unlock.")
        return 0
    except Exception as error:
        print(f"Artifact validation: FAIL: {type(error).__name__}: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
