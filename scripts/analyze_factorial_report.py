"""Validate and audit E3 artifacts without inference or rewriting source reports."""

import argparse
import json
from pathlib import Path

from hibermem.evaluation.factorial_audit import compare_bundles, read_validated_bundle, summarize_bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--compare", type=Path, help="Otherwise-identical report with a larger decoding cap")
    parser.add_argument("--allow-mock", action="store_true")
    parser.add_argument("--output", type=Path, help="Create a new audit JSON; never overwrite an existing file")
    args = parser.parse_args()
    try:
        bundle = read_validated_bundle(args.report, allow_mock=args.allow_mock)
        result = summarize_bundle(*bundle[:3])
        if args.compare:
            result["decoding_comparison"] = compare_bundles(
                bundle, read_validated_bundle(args.compare, allow_mock=args.allow_mock))
        encoded = json.dumps(result, indent=2, allow_nan=False)
        if args.output:
            # Exclusive creation preserves previous audits and original evidence.
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(encoded + "\n")
            print(f"Validated read-only audit: {args.output.resolve()}")
        else:
            print(encoded)
        print("No qualification decision. Source artifacts unchanged.")
        return 0
    except Exception as error:
        print(f"Factorial audit stopped: {type(error).__name__}: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
