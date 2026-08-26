"""Qualify the configured local model on discovery-only Phase 2 prompts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean

from hibermem.environments.controlled import QuerySplit, build_messages, generate_phase2_dataset
from hibermem.evaluation import parse_action
from hibermem.experiments.phase2 import make_backend, runtime_provenance


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "experiments" / "phase2_local_4050.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else ROOT / args.config
    config = json.loads(config_path.read_text(encoding="utf-8"))
    backend = make_backend(config["backend"])
    dataset = generate_phase2_dataset(1)
    bank = dataset.banks[0]
    view = dataset.view(QuerySplit.DISCOVERY)
    queries = view.for_bank(bank.bank_id)
    rows = []

    for chain in range(4):
        direct = queries[chain * 5]
        final = queries[chain * 5 + 1]
        conditions = (
            ("direct", direct, (bank.memories[chain * 2],)),
            ("complete_pair", final, bank.memories[chain * 2 : chain * 2 + 2]),
            ("missing_link", final, (bank.memories[chain * 2],)),
        )
        for condition, query, memories in conditions:
            result = backend.generate(build_messages(tuple(memories), query), **config["generation"])
            parsed = parse_action(result.text, query.options)
            rows.append(
                {
                    "chain": chain,
                    "condition": condition,
                    "query_id": query.query_id,
                    "raw_output": result.text,
                    "parsed_action": parsed,
                    "reward": view.score(query, parsed),
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                }
            )

    parse_rate = sum(row["parsed_action"] is not None for row in rows) / len(rows)
    supported_rows = [row for row in rows if row["condition"] != "missing_link"]
    missing_rows = [row for row in rows if row["condition"] == "missing_link"]
    supported_accuracy = fmean(row["reward"] for row in supported_rows)
    supported_parse_rate = fmean(
        row["parsed_action"] is not None for row in supported_rows
    )
    missing_false_positive_rate = fmean(row["reward"] for row in missing_rows)
    thresholds = config["backend_qualification"]
    checks = {
        "supported_parse_rate": {
            "value": supported_parse_rate,
            "operator": ">=",
            "threshold": float(thresholds["supported_parse_rate_min"]),
            "passed": supported_parse_rate
            >= float(thresholds["supported_parse_rate_min"]),
        },
        "overall_parse_rate": {
            "value": parse_rate,
            "operator": ">=",
            "threshold": float(thresholds["overall_parse_rate_min"]),
            "passed": parse_rate >= float(thresholds["overall_parse_rate_min"]),
        },
        "supported_accuracy": {
            "value": supported_accuracy,
            "operator": ">=",
            "threshold": float(thresholds["supported_accuracy_min"]),
            "passed": supported_accuracy >= float(thresholds["supported_accuracy_min"]),
        },
        "missing_link_false_positive_rate": {
            "value": missing_false_positive_rate,
            "operator": "<=",
            "threshold": float(thresholds["missing_link_false_positive_rate_max"]),
            "passed": missing_false_positive_rate
            <= float(thresholds["missing_link_false_positive_rate_max"]),
        },
    }
    report = {
        "schema_version": 1,
        "phase": 2,
        "scope": "discovery-only backend qualification; not P2 evidence",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": str(config_path.relative_to(ROOT)),
        "provenance": runtime_provenance(ROOT, backend),
        "metrics": {
            "parse_rate": parse_rate,
            "supported_parse_rate": supported_parse_rate,
            "supported_accuracy": supported_accuracy,
            "missing_link_false_positive_rate": missing_false_positive_rate,
        },
        "checks": checks,
        "checks_passed": all(check["passed"] for check in checks.values()),
        "evaluations": rows,
    }
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    output = ROOT / "results" / "phase2_backend_check" / run_id / "report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Backend qualification report: {output}")
    print("Backend qualification: " + ("PASS" if report["checks_passed"] else "FAIL"))
    return 0 if report["checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
