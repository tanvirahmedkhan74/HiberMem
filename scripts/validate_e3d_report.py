"""Independently reconstruct and validate a complete E3d artifact."""

from __future__ import annotations

import argparse
from pathlib import Path

from hibermem.experiments.grounding import validate_grounding_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--allow-mock", action="store_true")
    parser.add_argument(
        "--development-report",
        type=Path,
        help="required bound source artifact for a verification report",
    )
    args = parser.parse_args()
    try:
        report = validate_grounding_report(
            args.report.resolve(),
            allow_mock=args.allow_mock,
            development_report_path=(
                args.development_report.resolve()
                if args.development_report is not None
                else None
            ),
        )
        print(
            "Artifact validation: PASS. "
            f"E3d {report['stage']} measurement-only evidence."
        )
        print("No retention result, confirmation capability, or historical-test access.")
        return 0
    except Exception as error:
        print(f"Artifact validation: FAIL: {type(error).__name__}: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
