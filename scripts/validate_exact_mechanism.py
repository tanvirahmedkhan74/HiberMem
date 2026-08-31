"""Recompute an exact-mechanism report without inference. No qualification capability."""

import argparse
from pathlib import Path

from hibermem.experiments.exact_mechanism import validate_mechanism_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--allow-mock", action="store_true")
    args = parser.parse_args()
    try:
        validate_mechanism_report(args.report, allow_mock=args.allow_mock)
    except Exception as error:
        print(f"Artifact validation: FAIL ({type(error).__name__}: {error})")
        return 2
    print("Artifact validation: PASS. Development diagnostics only; no qualification or test unlock.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
