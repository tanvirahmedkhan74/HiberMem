"""Run E3d grounding qualification. Exit 0=validated artifact, 2=stopped/error."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from hibermem.environments.controlled.grounding import symbolic_grounding_controls
from hibermem.experiments.grounding import (
    run_grounding,
    validate_grounding_config,
    validate_verification_source,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs/experiments/e3d_grounding_development.json",
    )
    parser.add_argument("--candidate", choices=("qwen", "mock"), default="qwen")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument(
        "--development-report",
        type=Path,
        help="required source artifact when the config stage is verification",
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--controls-only", action="store_true")
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        suite = validate_grounding_config(config)
        development_report = (
            args.development_report.resolve()
            if args.development_report is not None
            else None
        )
        validate_verification_source(config, development_report)
        if args.dry_run or args.controls_only:
            print(
                json.dumps(
                    {
                        "protocol": config["protocol"],
                        "stage": config["stage"],
                        "planned_conditions": suite.manifest()["planned_conditions"],
                        "conditions_per_base_bank_per_arm": 288,
                        "arms": config["arms"],
                        "base_bank_seeds": config["cohort"]["base_bank_seeds"],
                        "model_loaded": False,
                        "controls": (
                            symbolic_grounding_controls(suite)
                            if args.controls_only
                            else None
                        ),
                    },
                    indent=2,
                )
            )
        else:
            if args.run_dir is None:
                raise ValueError("--run-dir is required for E3d inference")
            report = run_grounding(
                root=ROOT,
                config=config,
                candidate=args.candidate,
                run_dir=args.run_dir.resolve(),
                development_report_path=development_report,
            )
            readiness = report["analysis"]["readiness"]["query_anchored_v1"]
            print(f"Validated E3d report: {args.run_dir.resolve() / 'report.json'}")
            print(
                json.dumps(
                    {
                        "stage": report["stage"],
                        "query_anchored_passed": readiness["passed"],
                        "failed_checks": readiness["failed_checks"],
                        "automatic_selection": None,
                    },
                    indent=2,
                )
            )
        print("No retention result, confirmation capability, or historical-test access.")
        return 0
    except Exception as error:
        print(f"E3d stopped: {type(error).__name__}: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
