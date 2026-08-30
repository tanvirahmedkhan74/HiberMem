"""Record stage-aware launcher status; setup/test errors are never model results."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path


def classify_exit(stage: str, raw_exit: int, validated: bool) -> dict:
    completed = stage == "complete" and validated and raw_exit in (0, 1)
    return {
        "stage": stage,
        "raw_exit_code": raw_exit,
        "exit_code": raw_exit if completed else 2,
        "outcome": ("development_qualified" if raw_exit == 0 else "development_negative")
                   if completed else "infrastructure_error",
        "screen_result_validated": completed,
        "scientific_gate_eligible": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--raw-exit", type=int, required=True)
    parser.add_argument("--validated", type=int, choices=(0, 1), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    result = classify_exit(args.stage, args.raw_exit, bool(args.validated))
    result.update({"candidate": args.candidate, "git_commit": args.commit,
                   "recorded_at_utc": datetime.now(timezone.utc).isoformat()})
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except OSError as error:
        print(f"Could not persist launcher diagnostics: {error}")
        return 2
    print(f"Launcher outcome: {result['outcome']} (stage={args.stage}, "
          f"raw_exit={args.raw_exit}, exit={result['exit_code']})")
    if result["outcome"] == "infrastructure_error":
        print("No validated model result from this launch; preserve the diagnostic artifact.")
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
