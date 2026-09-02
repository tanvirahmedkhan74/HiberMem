"""E3c development diagnostic. Exit 0=validated completion, 2=error; never qualification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from hibermem.environments.controlled.contract import symbolic_contract_controls
from hibermem.experiments.contract import (
    run_contract,
    validate_contract_config,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs/experiments/e3c_output_contract.json",
    )
    parser.add_argument("--candidate", choices=("qwen", "mock"), default="qwen")
    parser.add_argument("--run-dir", type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--controls-only", action="store_true")
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        suite = validate_contract_config(config)
        if args.dry_run or args.controls_only:
            print(
                json.dumps(
                    {
                        "protocol": config["protocol"],
                        "planned_conditions": suite.manifest()["planned_conditions"],
                        "contracts": config["contracts"],
                        "independent_base_banks": suite.manifest()[
                            "independent_base_banks"
                        ],
                        "model_loaded": False,
                        "controls": (
                            symbolic_contract_controls(suite)
                            if args.controls_only
                            else None
                        ),
                    },
                    indent=2,
                )
            )
        else:
            if args.run_dir is None:
                raise ValueError("--run-dir is required for E3c inference")
            report = run_contract(
                root=ROOT,
                config=config,
                candidate=args.candidate,
                run_dir=args.run_dir.resolve(),
            )
            print(f"Validated E3c report: {args.run_dir.resolve() / 'report.json'}")
            print(
                json.dumps(
                    {
                        "passing_contracts": report["analysis"]["passing_contracts"],
                        "automatic_selection": None,
                    },
                    indent=2,
                )
            )
        print("Development only. No qualification, confirmation, or test access.")
        return 0
    except Exception as error:
        print(f"E3c stopped: {type(error).__name__}: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
