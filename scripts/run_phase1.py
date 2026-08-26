"""Run the deterministic Phase 1 interaction-recovery gate."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean

from hibermem.coalition.masks import mask_to_coalition, serialize_mask
from hibermem.coalition.sampling import size_balanced_masks
from hibermem.environments.synthetic import generate_phase1_benchmark, observe_coalitions
from hibermem.evaluation import recovery_metrics
from hibermem.interactions import PolynomialInteractionEstimator, residual_bootstrap_stability


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "experiments" / "phase1.json"
PHASE0_REPORT = ROOT / "results" / "phase0_report.json"
LATEST_REPORT = ROOT / "results" / "phase1_report.json"


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _git_provenance() -> dict[str, str | bool | None]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        return {"available": True, "commit": commit, "dirty": dirty}
    except (FileNotFoundError, subprocess.CalledProcessError):
        return {"available": False, "commit": None, "dirty": None}


def _mean_defined(records: list[dict[str, float | None]], key: str) -> float | None:
    values = [float(record[key]) for record in records if record[key] is not None]
    return fmean(values) if values else None


def _summary(records: list[dict[str, float | None]]) -> dict[str, float | None]:
    keys = (
        "individual_mae",
        "interaction_mae",
        "interaction_sign_accuracy",
        "precision_at_k",
        "recall_at_k",
        "nonzero_spearman",
        "detected_interaction_recall",
        "null_false_positive_rate",
        "ci_coverage",
        "true_interaction_sign_stability",
    )
    return {key: _mean_defined(records, key) for key in keys}


def _gate(summary: dict[str, float | None], noisy_ci_coverage: float, thresholds: dict) -> dict:
    comparisons = {
        "interaction_sign_accuracy": (
            summary["interaction_sign_accuracy"],
            ">=",
            thresholds["interaction_sign_accuracy_min"],
        ),
        "precision_at_k": (summary["precision_at_k"], ">=", thresholds["precision_at_k_min"]),
        "recall_at_k": (summary["recall_at_k"], ">=", thresholds["recall_at_k_min"]),
        "nonzero_spearman": (
            summary["nonzero_spearman"],
            ">=",
            thresholds["nonzero_spearman_min"],
        ),
        "individual_mae": (summary["individual_mae"], "<=", thresholds["individual_mae_max"]),
        "interaction_mae": (
            summary["interaction_mae"],
            "<=",
            thresholds["interaction_mae_max"],
        ),
        "null_false_positive_rate": (
            summary["null_false_positive_rate"],
            "<=",
            thresholds["null_false_positive_rate_max"],
        ),
        "noisy_ci_coverage": (
            noisy_ci_coverage,
            ">=",
            thresholds["noisy_ci_coverage_min"],
        ),
        "true_interaction_sign_stability": (
            summary["true_interaction_sign_stability"],
            ">=",
            thresholds["true_interaction_sign_stability_min"],
        ),
    }
    checks = {}
    for name, (value, operator, threshold) in comparisons.items():
        passed = value is not None and (value >= threshold if operator == ">=" else value <= threshold)
        checks[name] = {
            "value": value,
            "operator": operator,
            "threshold": threshold,
            "passed": passed,
        }
    return checks


def main() -> int:
    if not PHASE0_REPORT.exists():
        raise SystemExit("Phase 0 report is missing; Phase 1 is gated")
    phase0 = json.loads(PHASE0_REPORT.read_text(encoding="utf-8"))
    if not phase0.get("gate_passed"):
        raise SystemExit("Gate P0 has not passed; refusing to run Phase 1")

    config_bytes = CONFIG_PATH.read_bytes()
    config = json.loads(config_bytes)
    run_time = datetime.now(timezone.utc)
    run_id = run_time.strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir = ROOT / "results" / "phase1" / run_id
    observation_path = run_dir / "observations.jsonl"
    estimate_path = run_dir / "estimates.jsonl"
    report_path = run_dir / "report.json"

    specs = generate_phase1_benchmark(
        n_games=config["n_games"], n_players=config["n_players"], seed=config["seed"]
    )
    observation_rows: list[str] = []
    estimate_rows: list[str] = []
    game_reports = []
    metric_records: list[dict[str, float | None]] = []
    noisy_metric_records: list[dict[str, float | None]] = []
    family_records: dict[str, list[dict[str, float | None]]] = defaultdict(list)

    for game_index, spec in enumerate(specs):
        sampling_seed = config["seed"] + game_index * 7_919
        masks = size_balanced_masks(
            spec.game.n_players, config["coalition_budget"], sampling_seed
        )
        observation_seed = config["seed"] + game_index * 104_729
        values = observe_coalitions(spec, masks, observation_seed)
        estimator = PolynomialInteractionEstimator(
            max_order=config["max_order"], n_players=spec.game.n_players
        ).fit(masks, values)
        stability = residual_bootstrap_stability(
            estimator,
            masks,
            values,
            n_resamples=config["bootstrap_resamples"],
            seed=config["seed"] + game_index * 154_858_63,
        )
        metrics = recovery_metrics(
            spec.game.coefficients,
            estimator,
            stability,
            practical_detection_threshold=config["practical_detection_threshold"],
            confidence_z=config["confidence_z"],
        )
        metric_dict = metrics.as_dict()
        metric_records.append(metric_dict)
        family_records[spec.family].append(metric_dict)
        if spec.noise_std > 0:
            noisy_metric_records.append(metric_dict)

        for mask, observed in zip(masks, values, strict=True):
            observation_rows.append(
                json.dumps(
                    {
                        "game_id": spec.game_id,
                        "family": spec.family,
                        "mask": serialize_mask(mask),
                        "true_value": spec.game.value(mask_to_coalition(mask)),
                        "observed_value": observed,
                    },
                    sort_keys=True,
                )
            )
        standard_errors = estimator.standard_errors
        for term in estimator.terms:
            estimate_rows.append(
                json.dumps(
                    {
                        "game_id": spec.game_id,
                        "term": list(term),
                        "truth": spec.game.coefficients.get(term, 0.0),
                        "estimate": estimator.coefficients[term],
                        "standard_error": standard_errors[term],
                        "bootstrap": {
                            "lower": stability[term].lower,
                            "upper": stability[term].upper,
                            "sign_consistency": stability[term].sign_consistency,
                        },
                    },
                    sort_keys=True,
                )
            )
        game_reports.append(
            {
                "game_id": spec.game_id,
                "family": spec.family,
                "seed": spec.seed,
                "noise_std": spec.noise_std,
                "sampling_seed": sampling_seed,
                "observation_seed": observation_seed,
                "n_observations": len(masks),
                "n_terms": len(estimator.terms),
                "design_rank": estimator.rank,
                "condition_number": estimator.condition_number,
                "metrics": metric_dict,
                "ground_truth": [
                    {"term": list(term), "coefficient": value}
                    for term, value in spec.game.coefficients.items()
                ],
            }
        )

    aggregate = _summary(metric_records)
    noisy_ci_coverage_value = _mean_defined(noisy_metric_records, "ci_coverage")
    if noisy_ci_coverage_value is None:
        raise RuntimeError("Phase 1 requires noisy games for calibration")
    gate_checks = _gate(aggregate, noisy_ci_coverage_value, config["gate_thresholds"])
    gate_passed = all(check["passed"] for check in gate_checks.values())
    report = {
        "schema_version": 1,
        "phase": 1,
        "gate": "P1",
        "gate_passed": gate_passed,
        "run_id": run_id,
        "generated_at_utc": run_time.isoformat(),
        "scope": "deterministic synthetic low-order Mobius interaction recovery",
        "phase0_prerequisite": {
            "path": str(PHASE0_REPORT.relative_to(ROOT)),
            "gate_passed": True,
        },
        "estimand": {
            "name": "Mobius/Harsanyi polynomial coefficient",
            "max_order": config["max_order"],
            "estimator": "ordinary least squares on sampled coalition monomials",
            "not_interpreted_as": "Shapley Interaction Index",
        },
        "config": config,
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "runtime": {
            "python": platform.python_version(),
            "executable": sys.executable,
            "platform": platform.platform(),
            "packages": {
                "hibermem": _package_version("hibermem"),
                "numpy": _package_version("numpy"),
                "scipy": _package_version("scipy"),
                "pytest": _package_version("pytest"),
                "shapiq": _package_version("shapiq"),
            },
        },
        "git": _git_provenance(),
        "artifacts": {
            "observations": str(observation_path.relative_to(ROOT)),
            "estimates": str(estimate_path.relative_to(ROOT)),
            "immutable_report": str(report_path.relative_to(ROOT)),
        },
        "aggregate_metrics": {**aggregate, "noisy_ci_coverage": noisy_ci_coverage_value},
        "family_metrics": {
            family: _summary(records) for family, records in sorted(family_records.items())
        },
        "gate_checks": gate_checks,
        "games": game_reports,
    }

    _atomic_write(observation_path, "\n".join(observation_rows) + "\n")
    _atomic_write(estimate_path, "\n".join(estimate_rows) + "\n")
    serialized_report = json.dumps(report, indent=2, allow_nan=False) + "\n"
    _atomic_write(report_path, serialized_report)
    _atomic_write(LATEST_REPORT, serialized_report)

    print(f"Phase 1 games: {len(specs)}")
    print(f"Coalitions per game: {config['coalition_budget']}")
    for name, check in gate_checks.items():
        print(
            f"{name}: {check['value']:.6f} {check['operator']} "
            f"{check['threshold']:.6f} -> {'PASS' if check['passed'] else 'FAIL'}"
        )
    print(f"Phase 1 report: {report_path}")
    print(f"Gate P1: {'PASS' if gate_passed else 'FAIL'}")
    return 0 if gate_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
