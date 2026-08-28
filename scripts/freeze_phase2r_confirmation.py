"""Freeze a fresh-bank Phase 2 confirmation config from a qualified screen."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = ROOT / "configs" / "experiments" / "phase2_local_4050.json"
DEFAULT_OUTPUT = ROOT / "configs" / "experiments" / "phase2r_kaggle_confirmation.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze_config(
    *, screen_report_path: Path, base_config_path: Path, output_path: Path
) -> dict[str, object]:
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite frozen config: {output_path}")
    screen = json.loads(screen_report_path.read_text(encoding="utf-8"))
    selected = screen.get("selected_candidate")
    if not isinstance(selected, dict):
        raise RuntimeError("the Phase 2-R screen did not select a qualified candidate")
    backend = selected.get("backend")
    if not isinstance(backend, dict) or backend.get("type") != "hf_local":
        raise RuntimeError("the selected screen candidate is not a pinned HF backend")
    revision = str(backend.get("model_revision", ""))
    if len(revision) != 40 or any(character not in "0123456789abcdef" for character in revision):
        raise RuntimeError("the selected model revision must be a 40-character commit hash")

    config = json.loads(base_config_path.read_text(encoding="utf-8"))
    config.update(
        {
            "profile": "phase2r-kaggle-confirmation-fresh-banks-v1",
            "scientific_gate_eligible": True,
            "require_clean_git": True,
            "seed": 314159,
            "bank_start": 200,
            "backend": backend,
            "development_screen_report_sha256": _sha256(screen_report_path),
            "development_selection": {
                "model_label": selected.get("model_label"),
                "selection_rule": selected.get("selection_rule"),
            },
        }
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return config


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
