"""Fail closed on retired v1 or v2 capability-only confirmation requests.

The audit retired the v1 freeze route. A v2 screen is not interaction feasibility
evidence and is deliberately not compatible with the legacy Phase 2 generator.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = ROOT / "configs" / "experiments" / "phase2_local_4050.json"
DEFAULT_OUTPUT = ROOT / "configs" / "experiments" / "phase2r_kaggle_confirmation.json"


def freeze_config(
    *, screen_report_path: Path, base_config_path: Path, output_path: Path
) -> dict[str, object]:
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite frozen config: {output_path}")
    screen = json.loads(screen_report_path.read_text(encoding="utf-8"))
    if screen.get("schema_version") == 2:
        from hibermem.evaluation.artifacts import validate_report

        evidence = validate_report(screen_report_path)
        if not evidence["qualified"]:
            raise RuntimeError("v2 development qualification failed")
        raise RuntimeError(
            "v2 capability screening is not interaction-feasibility evidence; "
            "freeze remains disabled until a reviewed compatible confirmation protocol exists"
        )
    selected = screen.get("selected_candidate")
    if not isinstance(selected, dict):
        raise RuntimeError("the Phase 2-R screen did not select a qualified candidate")
    raise RuntimeError(
        "legacy v1 confirmation freezing is retired after the validity audit; "
        "a selected_candidate field alone is not qualification evidence"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screen-report", type=Path, required=True)
    parser.add_argument("--base-config", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    screen = args.screen_report if args.screen_report.is_absolute() else ROOT / args.screen_report
    base = args.base_config if args.base_config.is_absolute() else ROOT / args.base_config
    output = args.output if args.output.is_absolute() else ROOT / args.output
    config = freeze_config(
        screen_report_path=screen,
        base_config_path=base,
        output_path=output,
    )
    print(f"Frozen confirmation config: {output}")
    print(f"Selected model: {config['backend']['model_id']}")
    print("Review, commit, and push this config before running Kaggle confirmation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
