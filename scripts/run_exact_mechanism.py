"""Development-only exact games. Exit 0=completed diagnostics, 2=error; never qualification."""

import argparse
import json
from pathlib import Path

from hibermem.experiments.exact_mechanism import run_mechanism, symbolic_controls, validate_config

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/experiments/exact_mechanism_e1.json")
    parser.add_argument("--candidate", choices=("qwen", "phi", "mock"), default="qwen")
    parser.add_argument("--run-dir", type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--controls-only", action="store_true")
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        suite = validate_config(config)
        if args.dry_run or args.controls_only:
            print(json.dumps({"protocol": config["protocol"], "planned_conditions": suite.manifest()["planned_conditions"],
                              "variants": config["variants"], "model_loaded": False,
                              "controls": symbolic_controls(suite) if args.controls_only else None}, indent=2))
        else:
            if args.run_dir is None:
                raise ValueError("--run-dir is required for inference")
            report = run_mechanism(root=ROOT, config=config, candidate=args.candidate, run_dir=args.run_dir.resolve())
            print(f"Validated development report: {args.run_dir.resolve() / 'report.json'}")
            print(f"Complete: {report['planned_conditions']} conditions; engineering_only={report['engineering_only']}")
        print("No qualification decision. Confirmation and test remain locked.")
        return 0
    except Exception as error:
        print(f"Exact mechanism stopped: {type(error).__name__}: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
