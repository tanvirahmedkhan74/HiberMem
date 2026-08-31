"""E0: read-only validated v2 four-corner reanalysis; preserve original artifacts."""

import argparse
import json
from pathlib import Path

from hibermem.evaluation.artifacts import validate_report
from hibermem.evaluation.mechanism import local_v2_contrasts


def analyze(report_path):
    validate_report(report_path)
    result = local_v2_contrasts(json.loads((report_path.parent / "evaluations.json").read_text()))
    result["source_report"] = str(report_path.resolve())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(analyze(args.report), indent=2))
    except Exception as error:
        print(f"Reanalysis failed: {type(error).__name__}: {error}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
