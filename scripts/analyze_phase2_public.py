"""Analyze existing discovery/validation artifacts only; never read or unlock test."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import fmean

from hibermem.coalition import deserialize_mask
from hibermem.coalition.masks import mask_to_coalition, mask_to_index
from hibermem.coalition.sampling import size_balanced_masks
from hibermem.evaluation.predictive import paired_bank_interval, prediction_metrics
from hibermem.interactions import PolynomialInteractionEstimator
from hibermem.interactions.mobius import mobius_transform
from hibermem.retention import item_value_mask, mobius_to_shapley_items
from hibermem.experiments.phase2 import _atomic_json


def analyze(run_dir: Path) -> dict:
    discovery = json.loads((run_dir / "discovery.json").read_text())
    validation = json.loads((run_dir / "validation.json").read_text())
    if discovery.get("stage") != "discovery" or validation.get("stage") != "validation":
        raise ValueError("only discovery and validation artifacts are accepted")
    banks = []
    for row in discovery["bank_results"]:
        masks = [deserialize_mask(value) for value in row["coalition_masks"]]
        values = row["coalition_values"]
        n = len(masks[0])
        models = {order: PolynomialInteractionEstimator(max_order=order, n_players=n).fit(masks, values)
                  for order in (1, 2)}
        result = {"bank_id": row["bank_id"], "in_sample_only": True,
                  "predictive_metrics": {str(order): prediction_metrics(values, fit.predict(masks))
                                         for order, fit in models.items()}}
        if len(masks) == 2 ** n:
            table = [0.0] * (2 ** n)
            for mask, value in zip(masks, values):
                table[mask_to_index(mask)] = value
            exact_coefficients = {tuple(i for i in range(n) if mask & (1 << i)): value
                                  for mask, value in enumerate(mobius_transform(table))}
            exact_items = mobius_to_shapley_items(exact_coefficients, n)
            surrogate_items = mobius_to_shapley_items(models[2].coefficients, n)
            result["exact_shapley_items"] = exact_items
            result["surrogate_shapley_items"] = surrogate_items
            result["severe_budget_selections"] = {
                str(keep): {"exact": mask_to_coalition(item_value_mask(exact_items, n, keep)),
                            "surrogate": mask_to_coalition(item_value_mask(surrogate_items, n, keep))}
                for keep in (2, 3)
            }
            full_top = set(sorted(models[2].interactions(2), key=lambda t: (-abs(models[2].coefficients[t]), t))[:4])
            sensitivity = []
            for seed in range(5):
                sampled = size_balanced_masks(n, 128, seed)
                fitted = PolynomialInteractionEstimator(max_order=2, n_players=n).fit(
                    sampled, [table[mask_to_index(mask)] for mask in sampled])
                top = set(sorted(fitted.interactions(2), key=lambda t: (-abs(fitted.coefficients[t]), t))[:4])
                sensitivity.append({"seed": seed, "top4_overlap_with_full_OLS": len(top & full_top) / 4})
            result["coalition_sampling_sensitivity"] = sensitivity
        banks.append(result)
    curves, severe = defaultdict(list), defaultdict(lambda: defaultdict(list))
    for record in validation["retention_records"]:
        if record["split"] != "validation":
            raise ValueError("non-validation row in public analysis")
        curves[(record["actual_deletion_ratio"], record["policy"])].append(record["accuracy"])
        if record["actual_deletion_ratio"] > .5 and record["policy"] in ("interaction", "item"):
            severe[record["bank_id"]][record["policy"]].append(record["accuracy"])
    differences = [fmean(v["interaction"]) - fmean(v["item"]) for _, v in sorted(severe.items())]
    return {"scope": "exploratory public-split diagnostics; not a gate or cross-query R2",
            "bank_fits": banks,
            "validation_curves": [{"actual_deletion_ratio": ratio, "policy": policy, "accuracy": fmean(values)}
                                  for (ratio, policy), values in sorted(curves.items())],
            "severe_validation_bank_effects": dict(zip(sorted(severe), differences)),
            "severe_validation_interval": paired_bank_interval(differences)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.run_dir.resolve()):
        raise SystemExit("write diagnostics outside the original run to preserve it")
    if args.output.exists():
        raise SystemExit("output already exists; choose a new diagnostic artifact")
    _atomic_json(args.output, analyze(args.run_dir))
    print(f"Exploratory public-split diagnostics: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
