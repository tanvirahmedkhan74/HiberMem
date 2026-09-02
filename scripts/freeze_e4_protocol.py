"""Freeze one readiness-passing E3c contract into a new E4 design config."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from hibermem.environments.controlled.contract import contract_prompt_hash
from hibermem.experiments.contract import validate_contract_report
from hibermem.experiments.prospective import validate_prospective_config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract-report", type=Path, required=True)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report_path = args.contract_report.resolve()
        report = validate_contract_report(report_path)
        if args.contract not in report["analysis"]["passing_contracts"]:
            raise ValueError("selected contract did not pass every frozen readiness check")
        config = json.loads(args.template.read_text(encoding="utf-8"))
        if config["output_contract"]["status"] != "requires_e3c_freeze":
            raise ValueError("template was already frozen or is not an E4 template")
        contract_generation = json.loads(
            (report_path.parent / "config.json").read_text(encoding="utf-8")
        )["generation"]
        config["output_contract"] = {
            "name": args.contract,
            "status": "frozen_development",
            "e3c_report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
            "prompt_sha256": contract_prompt_hash(args.contract),
        }
        # Preserve the generation budget under which readiness was measured.
        config["generation"] = contract_generation
        validate_prospective_config(config, real=True)
        output = args.output.resolve()
        if output.exists():
            raise FileExistsError("refusing to overwrite an E4 frozen config")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"Frozen development config: {output}")
        print("Review, commit, and push this exact config before real E4 inference.")
        print("This does not create a confirmation config or unlock a test.")
        return 0
    except Exception as error:
        print(f"E4 freeze stopped: {type(error).__name__}: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
