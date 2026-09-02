"""E4 prospective development pipeline; real runs require explicit past/freeze/future stages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from hibermem.environments.controlled.prospective import symbolic_prospective_controls
from hibermem.experiments.prospective import (
    freeze_prospective_policies,
    run_prospective_all_mock,
    run_prospective_future,
    run_prospective_past,
    validate_prospective_config,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs/experiments/e4_engineering_mock.json",
    )
    parser.add_argument("--candidate", choices=("qwen", "mock"), default="qwen")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument(
        "--stage",
        choices=("past", "freeze", "future", "all-mock"),
        default="past",
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--controls-only", action="store_true")
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        real = args.candidate != "mock"
        suite, probe = validate_prospective_config(config, real=real)
        if args.dry_run or args.controls_only:
            public = suite.public_manifest()
            # Future content is not printed by either mode.
            print(
                json.dumps(
                    {
                        "protocol": config["protocol"],
                        "cohort": config["cohort"]["name"],
                        "independent_base_banks": public["n_banks"],
                        "past_conditions": public["past_planned_conditions"],
                        "prediction_probe_masks": len(probe),
                        "future_content_exposed": False,
                        "model_loaded": False,
                        "controls": (
                            symbolic_prospective_controls(suite)
                            if args.controls_only
                            else None
                        ),
                    },
                    indent=2,
                )
            )
        else:
            if args.run_dir is None:
                raise ValueError("--run-dir is required")
            run_dir = args.run_dir.resolve()
            if args.stage == "all-mock":
                if args.candidate != "mock":
                    raise ValueError("real E4 must use separate past/freeze/future commands")
                report = run_prospective_all_mock(
                    root=ROOT, config=config, run_dir=run_dir
                )
                print(f"Validated E4 engineering report: {run_dir / 'report.json'}")
            elif args.stage == "past":
                report = run_prospective_past(
                    root=ROOT,
                    config=config,
                    candidate=args.candidate,
                    run_dir=run_dir,
                )
                print(f"Validated past stage: {run_dir / 'past_report.json'}")
                print("Next explicit stage: freeze")
            elif args.stage == "freeze":
                frozen = freeze_prospective_policies(
                    root=ROOT,
                    config=config,
                    candidate=args.candidate,
                    run_dir=run_dir,
                )
                print(f"Frozen selections: {run_dir / 'frozen_selections.json'}")
                print(f"Banks frozen: {len(frozen['bank_results'])}; future_data_used=false")
            else:
                report = run_prospective_future(
                    root=ROOT,
                    config=config,
                    candidate=args.candidate,
                    run_dir=run_dir,
                )
                print(f"Validated E4 development report: {run_dir / 'report.json'}")
                print(json.dumps(report["analysis"]["primary_interval"], indent=2))
        print("No P2/P3 decision. Historical confirmation and test remain locked.")
        return 0
    except Exception as error:
        print(f"E4 stopped: {type(error).__name__}: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
