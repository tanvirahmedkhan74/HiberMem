"""Screen pinned Kaggle model candidates on fresh Phase 2-R calibration banks.

This is development-only model/task qualification. It never obtains a test
evaluation view and cannot decide Gate P2.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import re
import traceback
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
from typing import Mapping, Sequence

from hibermem.coalition import serialize_mask
from hibermem.coalition.cache import EvaluationCache
from hibermem.environments.controlled import QuerySplit, generate_phase2_dataset
from hibermem.experiments.phase2 import (
    CoalitionEvaluator,
    git_provenance,
    make_backend,
    runtime_provenance,
)
from hibermem.environments.controlled.prompts import prompt_template_hash


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "experiments" / "phase2r_kaggle_screen.json"


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _json_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _slug(model_id: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", model_id.lower()).strip("-")


def _mask(width: int, *positions: int) -> tuple[bool, ...]:
    selected = set(positions)
    return tuple(index in selected for index in range(width))


def _mean(rows: Sequence[Mapping[str, object]], field: str = "reward") -> float:
    if not rows:
        raise ValueError("cannot summarize an empty calibration condition")
    return fmean(float(row[field]) for row in rows)


def _summarize_bank(
    bank_id: str,
    rows: Sequence[Mapping[str, object]],
    thresholds: Mapping[str, object],
) -> dict[str, object]:
    bank_rows = [row for row in rows if row["bank_id"] == bank_id]
    full = [row for row in bank_rows if row["condition"] == "full"]
    empty = [row for row in bank_rows if row["condition"] == "empty"]
    full_direct = [row for row in full if row["query_kind"] == "direct"]
    full_two_hop = [row for row in full if row["query_kind"] == "two_hop"]
    direct_minimal = [
        row for row in bank_rows if row["condition"] == "direct_minimal"
    ]
    pair_only = [row for row in bank_rows if row["condition"] == "pair_only"]
    missing = [
        row
        for row in bank_rows
        if row["condition"] in {"missing_first", "missing_second"}
    ]
    metrics = {
        "direct_minimal_accuracy": _mean(direct_minimal),
        "pair_only_two_hop_accuracy": _mean(pair_only),
        "full_direct_accuracy": _mean(full_direct),
        "full_two_hop_accuracy": _mean(full_two_hop),
        "full_accuracy": _mean(full),
        "empty_accuracy": _mean(empty),
        "memory_gap": _mean(full) - _mean(empty),
        "missing_link_false_positive_rate": _mean(missing),
        "full_parse_rate": fmean(not bool(row["parse_null"]) for row in full),
    }
    checks = {
        "full_direct_accuracy": metrics["full_direct_accuracy"]
        >= float(thresholds["full_direct_accuracy_min"]),
        "full_two_hop_accuracy": metrics["full_two_hop_accuracy"]
        >= float(thresholds["full_two_hop_accuracy_min"]),
        "memory_gap": metrics["memory_gap"]
        >= float(thresholds["memory_gap_min"]),
        "full_parse_rate": metrics["full_parse_rate"]
        >= float(thresholds["full_parse_rate_min"]),
    }
    return {
        "bank_id": bank_id,
        "metrics": metrics,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _screen_candidate(
    *,
    root: Path,
    candidate: Mapping[str, object],
    config: Mapping[str, object],
    dataset,
    run_dir: Path,
    code_identity: str,
) -> dict[str, object]:
    backend_config = candidate["backend"]
    model_id = str(backend_config["model_id"])
    candidate_dir = run_dir / _slug(model_id)
    candidate_dir.mkdir(parents=True, exist_ok=True)
    backend = make_backend(backend_config)
    provenance = runtime_provenance(root, backend)
    rows: list[dict[str, object]] = []
    views = (
        dataset.view(QuerySplit.DISCOVERY),
        dataset.view(QuerySplit.VALIDATION),
    )

    with EvaluationCache(candidate_dir / "evaluations.sqlite3") as cache:
        evaluator = CoalitionEvaluator(
            backend=backend,
            cache=cache,
            generation_config=config["generation"],
            seed=int(config["seed"]),
            code_commit=code_identity,
        )
        for bank in dataset.banks:
            width = len(bank.memories)
            full_mask = _mask(width, *range(width))
            empty_mask = _mask(width)
            for view in views:
                for query in view.for_bank(bank.bank_id):
                    chain = int(query.dependency_group.rsplit("-", 1)[1])
                    first = chain * 2
                    second = first + 1
                    query_kind = (
                        "direct" if "direct" in query.template_family else "two_hop"
                    )
                    conditions = [("full", full_mask), ("empty", empty_mask)]
                    if query_kind == "direct":
                        conditions.append(("direct_minimal", _mask(width, first)))
                    else:
                        conditions.extend(
                            (
                                ("pair_only", _mask(width, first, second)),
                                ("missing_first", _mask(width, second)),
                                ("missing_second", _mask(width, first)),
                            )
                        )
                    for condition, coalition_mask in conditions:
                        result = evaluator.evaluate(bank, query, view, coalition_mask)
                        rows.append(
                            {
                                "bank_id": bank.bank_id,
                                "query_id": query.query_id,
                                "split": query.split.value,
                                "template_family": query.template_family,
                                "query_kind": query_kind,
                                "condition": condition,
                                "mask": serialize_mask(coalition_mask),
                                "reward": result.reward,
                                "parse_null": result.parsed_action is None,
                            }
                        )
            print(f"{model_id}: {bank.bank_id} calibration complete", flush=True)

        cache_summary = {
            "rows": cache.count(),
            "hits": evaluator.cache_hits,
            "misses": evaluator.cache_misses,
        }

    thresholds = config["qualification_thresholds"]
    bank_results = [
        _summarize_bank(bank.bank_id, rows, thresholds) for bank in dataset.banks
    ]
    passing_fraction = fmean(bool(bank["passed"]) for bank in bank_results)
    missing_rate = fmean(
        float(bank["metrics"]["missing_link_false_positive_rate"])
        for bank in bank_results
    )
    checks = {
        "passing_bank_fraction": {
            "value": passing_fraction,
            "operator": ">=",
            "threshold": float(thresholds["passing_bank_fraction_min"]),
            "passed": passing_fraction
            >= float(thresholds["passing_bank_fraction_min"]),
        },
        "mean_missing_link_false_positive_rate": {
            "value": missing_rate,
            "operator": "<=",
            "threshold": float(thresholds["missing_link_false_positive_rate_max"]),
            "passed": missing_rate
            <= float(thresholds["missing_link_false_positive_rate_max"]),
        },
    }
    summary = {
        "mean_direct_minimal_accuracy": fmean(
            float(bank["metrics"]["direct_minimal_accuracy"])
            for bank in bank_results
        ),
        "mean_pair_only_two_hop_accuracy": fmean(
            float(bank["metrics"]["pair_only_two_hop_accuracy"])
            for bank in bank_results
        ),
        "mean_full_direct_accuracy": fmean(
            float(bank["metrics"]["full_direct_accuracy"])
            for bank in bank_results
        ),
        "mean_full_two_hop_accuracy": fmean(
            float(bank["metrics"]["full_two_hop_accuracy"])
            for bank in bank_results
        ),
        "mean_full_accuracy": fmean(
            float(bank["metrics"]["full_accuracy"]) for bank in bank_results
        ),
        "mean_empty_accuracy": fmean(
            float(bank["metrics"]["empty_accuracy"]) for bank in bank_results
        ),
        "mean_memory_gap": fmean(
            float(bank["metrics"]["memory_gap"]) for bank in bank_results
        ),
        "mean_missing_link_false_positive_rate": missing_rate,
        "passing_bank_fraction": passing_fraction,
    }
    result = {
        "model_label": str(candidate["label"]),
        "backend": dict(backend_config),
        "provenance": provenance,
        "cache": cache_summary,
        "summary": summary,
        "checks": checks,
        "qualified": all(check["passed"] for check in checks.values()),
        "bank_results": bank_results,
        "evaluation_artifact": str(
            (candidate_dir / "evaluations.json").relative_to(root)
        ),
    }
    _atomic_json(candidate_dir / "evaluations.json", rows)
    _atomic_json(candidate_dir / "report.json", result)

    del evaluator
    del backend
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass
    return result


def run_screen(
    *, root: Path, config: Mapping[str, object], run_dir: Path
) -> dict[str, object]:
    if str(config.get("phase")) != "2-R":
        raise ValueError("the Kaggle screening config must declare phase '2-R'")
    if bool(config.get("scientific_gate_eligible", True)):
        raise ValueError("Phase 2-R model screening must not be scientific-gate eligible")
    bank_start = int(config["calibration"]["bank_start"])
    n_banks = int(config["calibration"]["n_banks"])
    if n_banks < 1 or bank_start < 100 or bank_start + n_banks > 200:
        raise ValueError("legacy calibration must stay inside banks [100, 200); confirmation is reserved")
    dataset = generate_phase2_dataset(n_banks, bank_start=bank_start)
    git = git_provenance(root)
    source_tree = hashlib.sha256(
        json.dumps(git, sort_keys=True, default=str).encode()
    ).hexdigest()
    commit = git["commit"]
    code_identity = commit if isinstance(commit, str) else f"screen-tree:{source_tree}"
    report: dict[str, object] = {
        "schema_version": 1,
        "phase": "2-R",
        "scope": "development-only public-split model/task calibration; not P2 evidence",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config_sha256": _json_hash(config),
        "dataset_sha256": dataset.sha256(),
        "prompt_template_sha256": prompt_template_hash(),
        "git": git,
        "calibration": dict(config["calibration"]),
        "qualification_thresholds": dict(config["qualification_thresholds"]),
        "candidates": [],
        "selected_candidate": None,
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    _atomic_json(run_dir / "config.json", config)
    _atomic_json(run_dir / "dataset_manifest.json", dataset.public_manifest())
    _atomic_json(run_dir / "report.json", report)

    for candidate in config["candidates"]:
        try:
            candidate_result = _screen_candidate(
                root=root,
                candidate=candidate,
                config=config,
                dataset=dataset,
                run_dir=run_dir,
                code_identity=code_identity,
            )
        except Exception as error:  # Preserve other candidate results on model failure.
            candidate_result = {
                "model_label": str(candidate.get("label", "unknown")),
                "backend": dict(candidate.get("backend", {})),
                "qualified": False,
                "load_or_runtime_error": f"{type(error).__name__}: {error}",
                "traceback": traceback.format_exc(),
            }
        report["candidates"].append(candidate_result)
        _atomic_json(run_dir / "report.json", report)

    qualified = [item for item in report["candidates"] if item.get("qualified")]
    if qualified:
        selected = max(
            qualified,
            key=lambda item: (
                float(item["summary"]["mean_full_two_hop_accuracy"]),
                float(item["summary"]["mean_memory_gap"]),
                float(item["summary"]["mean_full_direct_accuracy"]),
            ),
        )
        report["selected_candidate"] = {
            "model_label": selected["model_label"],
            "backend": selected["backend"],
            "selection_rule": (
                "qualified candidates ordered by full two-hop accuracy, then memory "
                "gap, then full direct accuracy"
            ),
        }
    report["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    _atomic_json(run_dir / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-dir", type=Path)
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else ROOT / args.config
    config = json.loads(config_path.read_text(encoding="utf-8"))
    run_dir = args.run_dir
    if run_dir is None:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        run_dir = ROOT / "results" / "phase2r_kaggle_screen" / run_id
    elif not run_dir.is_absolute():
        run_dir = ROOT / run_dir
    report = run_screen(root=ROOT, config=config, run_dir=run_dir)
    print(f"Phase 2-R screening report: {run_dir / 'report.json'}")
    selected = report["selected_candidate"]
    if selected is None:
        print("Phase 2-R screening: NO MODEL QUALIFIED")
        return 1
    print(f"Phase 2-R selected development candidate: {selected['model_label']}")
    print("This is development selection only; freeze and commit before confirmation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
