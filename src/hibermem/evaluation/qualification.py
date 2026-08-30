"""Pure, auditable qualification rules for development screen v2."""

from __future__ import annotations

from collections import defaultdict
from statistics import fmean


def summarize_v2(rows: list[dict], thresholds: dict) -> dict:
    if not rows:
        raise ValueError("qualification requires a complete nonempty evaluation table")

    def mean(selected: list[dict], field: str = "reward") -> float:
        if not selected:
            raise ValueError("required calibration condition is missing")
        return fmean(float(row[field]) for row in selected)

    bank_results = []
    for bank_id in sorted({row["base_bank_id"] for row in rows}):
        bank = [row for row in rows if row["base_bank_id"] == bank_id]
        full = [r for r in bank if r["condition"] == "full"]
        metrics = {
            "full_direct_accuracy": mean([r for r in full if r["kind"] == "direct"]),
            "full_two_hop_accuracy": mean([r for r in full if r["kind"] == "two_hop"]),
            "full_accuracy": mean(full),
            "empty_accuracy": mean([r for r in bank if r["condition"] == "empty"]),
            "direct_minimal_accuracy": mean([r for r in bank if r["condition"] == "direct_minimal"]),
            "pair_only_accuracy": mean([r for r in bank if r["condition"] == "pair_only"]),
            "full_strict_format_rate": mean(full, "strict_format"),
        }
        metrics["memory_gap"] = metrics["full_accuracy"] - metrics["empty_accuracy"]
        checks = {metric: metrics[metric] >= float(thresholds[metric + "_min"])
                  for metric in ("full_direct_accuracy", "full_two_hop_accuracy", "memory_gap",
                                 "direct_minimal_accuracy", "pair_only_accuracy", "full_strict_format_rate")}
        bank_results.append({"base_bank_id": bank_id, "metrics": metrics,
                             "checks": checks, "passed": all(checks.values())})

    directional = {}
    for direction in ("first", "second"):
        for context in ("minimal", "context"):
            condition = f"missing_{direction}_{context}"
            selected = [r for r in rows if r["condition"] == condition]
            directional[condition] = {
                "accidental_correct_rate": mean(selected),
                "abstention_rate": mean(selected, "abstained"),
                "unsupported_assertion_rate": mean(selected, "unsupported_assertion"),
                "parse_null_rate": mean(selected, "parse_null"),
                "n_conditions": len(selected),
            }

    pairs: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row["counterfactual_id"] is not None:
            pairs[row["counterfactual_id"]][row["condition"]].append(row)
    full_pair_success, missing_pair_abstention, identical_outputs = [], [], []
    for pair in pairs.values():
        supported, missing = pair["cf_full"], pair["cf_missing"]
        if len(supported) != 2 or len(missing) != 2:
            raise ValueError("incomplete counterfactual pair")
        full_pair_success.append(all(r["reward"] == 1 for r in supported))
        missing_pair_abstention.append(all(r["abstained"] for r in missing))
        identical_outputs.append(missing[0]["raw_output_sha256"] == missing[1]["raw_output_sha256"])
    if not pairs:
        raise ValueError("counterfactual evidence is required")
    summary = {
        "passing_bank_fraction": fmean(b["passed"] for b in bank_results),
        "counterfactual_full_pair_accuracy": fmean(full_pair_success),
        "counterfactual_missing_pair_abstention": fmean(missing_pair_abstention),
        "counterfactual_identical_output_rate": fmean(identical_outputs),
        **{"mean_" + metric: fmean(b["metrics"][metric] for b in bank_results)
           for metric in bank_results[0]["metrics"]},
    }
    checks = {
        key: summary[key] >= float(thresholds[key + "_min"])
        for key in ("passing_bank_fraction", "counterfactual_full_pair_accuracy",
                    "counterfactual_missing_pair_abstention", "counterfactual_identical_output_rate")
    }
    for condition, metrics in directional.items():
        checks[condition + "_accidental_correct"] = (
            metrics["accidental_correct_rate"] <= float(thresholds["accidental_correct_rate_max"]))
        checks[condition + "_abstention"] = metrics["abstention_rate"] >= float(thresholds["abstention_rate_min"])
    return {"qualified": all(checks.values()), "checks": checks, "summary": summary,
            "bank_results": bank_results, "missing_link_conditions": directional}
