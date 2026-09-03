"""Create a verification config only from a passing real E3d development artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from hibermem.experiments.grounding import build_verification_config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        output = args.output.resolve()
        if output.exists():
            raise FileExistsError("refusing to overwrite an E3d verification config")
        config = build_verification_config(args.development_report.resolve())
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"Frozen E3d verification config: {output}")
        print("Review and commit this exact file before the one permitted verification run.")
        print("This does not unlock E4, E5, confirmation, or historical test data.")
        return 0
    except Exception as error:
        print(f"E3d verification freeze stopped: {type(error).__name__}: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
