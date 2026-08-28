"""Leakage-resistant Phase 2 LLM coalition experiment."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import platform
import subprocess
import sys
import time
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from statistics import fmean, median

import numpy as np

from hibermem.backends import HFLocalBackend, LLMBackend, MockBackend
from hibermem.coalition.cache import CacheKey, CachedEvaluation, EvaluationCache
from hibermem.coalition.masks import Mask, mask_to_coalition, serialize_mask
from hibermem.coalition.sampling import size_balanced_masks
from hibermem.environments.controlled import (
    ControlledDataset,
    EvaluationView,
    MemoryBank,
    Query,
    QuerySplit,
    build_messages,
    generate_phase2_dataset,
    prompt_template_hash,
)
from hibermem.evaluation import normalized_memory_retention, parse_action
from hibermem.interactions import PolynomialInteractionEstimator
from hibermem.retention import (
    interaction_aware_mask,
    item_value_mask,
    mobius_to_shapley_items,
    random_mask,
)


class SplitLeakageError(PermissionError):
    """Raised when non-discovery data reaches an estimation path."""


def require_discovery_view(view: EvaluationView) -> None:
    if view.split is not QuerySplit.DISCOVERY:
        raise SplitLeakageError("interaction fitting accepts discovery capability only")


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _json_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def git_provenance(root: Path) -> dict[str, object]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status_lines = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        changed_paths = [line[3:].replace("\\", "/") for line in status_lines if line]
        source_changes = [path for path in changed_paths if not path.startswith("results/")]
        return {
            "available": True,
            "commit": commit,
            "dirty": bool(changed_paths),
            "source_dirty": bool(source_changes),
            "changed_path_count": len(changed_paths),
            "source_changed_paths": source_changes,
        }
    except (FileNotFoundError, subprocess.CalledProcessError):
        return {
            "available": False,
            "commit": None,
            "dirty": None,
            "source_dirty": None,
            "changed_path_count": None,
            "source_changed_paths": [],
        }


def _gpu_provenance() -> dict[str, str | None]:
    cuda_runtime = None
    cudnn_version = None
    try:
        import torch

        cuda_runtime = torch.version.cuda
        cudnn = torch.backends.cudnn.version()
        cudnn_version = str(cudnn) if cudnn is not None else None
    except ImportError:
        pass
    try:
        output = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return {
            "nvidia_smi": output or None,
            "torch_cuda_runtime": cuda_runtime,
            "cudnn_version": cudnn_version,
        }
    except (FileNotFoundError, subprocess.CalledProcessError):
        return {
            "nvidia_smi": None,
            "torch_cuda_runtime": cuda_runtime,
            "cudnn_version": cudnn_version,
        }


def _source_tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    paths = [
        path
        for base in (root / "src", root / "scripts")
        for path in base.rglob("*.py")
    ]
    paths.extend(
        path
        for path in (root / "pyproject.toml", root / "environment.yml")
        if path.exists()
    )
    for path in sorted(paths):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def runtime_provenance(root: Path, backend: LLMBackend) -> dict[str, object]:
    return {
        "python": platform.python_version(),
        "executable": sys.executable,
        "platform": platform.platform(),
        "packages": {
            name: _package_version(name)
            for name in ("hibermem", "numpy", "scipy", "torch", "transformers")
        },
        "git": git_provenance(root),
        "source_tree_sha256": _source_tree_sha256(root),
        "gpu": _gpu_provenance(),
        "backend": backend.provenance(),
    }


def make_backend(config: Mapping[str, object]) -> LLMBackend:
    backend_type = str(config["type"])
    if backend_type == "mock":
        return MockBackend()
    if backend_type == "hf_local":
        return HFLocalBackend(
            model_id=str(config["model_id"]),
            model_revision=str(config["model_revision"]),
            device=str(config.get("device", "cuda")),
            dtype=str(config.get("dtype", "float16")),
            quantization=str(config.get("quantization", "none")),
            local_files_only=bool(config.get("local_files_only", False)),
            trust_remote_code=bool(config.get("trust_remote_code", False)),
        )
    raise ValueError(f"unsupported Phase 2 backend type: {backend_type}")


class CoalitionEvaluator:
    def __init__(
        self,
        *,
        backend: LLMBackend,
        cache: EvaluationCache,
        generation_config: Mapping[str, object],
        seed: int,
        code_commit: str | None,
        progress: bool = False,
    ) -> None:
        if bool(generation_config.get("do_sample", False)):
            raise ValueError("Phase 2 requires do_sample=false")
        self.backend = backend
        self.cache = cache
        self.generation_config = dict(generation_config)
        self.seed = seed
        self.code_commit = code_commit
        self.progress = progress
        self.cache_hits = 0
        self.cache_misses = 0

    def evaluate(
        self,
        bank: MemoryBank,
        query: Query,
        view: EvaluationView,
        mask: Mask,
    ) -> CachedEvaluation:
        if len(mask) != len(bank.memories):
            raise ValueError("coalition mask width does not match the memory bank")
        if query.bank_id != bank.bank_id:
            raise ValueError("query and memory bank do not match")
        key = CacheKey(
            model_id=self.backend.model_id,
            model_revision=self.backend.model_revision,
            prompt_template_hash=prompt_template_hash(),
            memory_bank_id=bank.bank_id,
            query_id=query.query_id,
            coalition_mask=serialize_mask(mask),
            generation_config=self.generation_config,
            seed=self.seed,
            code_commit=self.code_commit,
        )
        cached = self.cache.get(key)
        if cached is not None:
            self.cache_hits += 1
            return cached

        memories = tuple(
            memory for memory, present in zip(bank.memories, mask, strict=True) if present
        )
        messages = build_messages(memories, query)
        start = time.perf_counter()
        generated = self.backend.generate(
            messages,
            **self.generation_config,
            seed=self.seed,
        )
        latency = time.perf_counter() - start
        parsed = parse_action(generated.text, query.options)
        reward = view.score(query, parsed)
        stored = self.cache.put(
            key,
            raw_output=generated.text,
            parsed_action=parsed,
            reward=reward,
            latency_seconds=latency,
            input_tokens=generated.input_tokens,
            output_tokens=generated.output_tokens,
        )
        self.cache_misses += 1
        return stored

    def reward_matrix(
        self,
        bank: MemoryBank,
        queries: Sequence[Query],
        view: EvaluationView,
        masks: Sequence[Mask],
    ) -> np.ndarray:
        rows = []
        for index, mask in enumerate(masks):
            rows.append([self.evaluate(bank, query, view, mask).reward for query in queries])
            if self.progress and ((index + 1) % 16 == 0 or index + 1 == len(masks)):
                print(
                    f"{view.split.value} {bank.bank_id}: {index + 1}/{len(masks)} coalitions",
                    flush=True,
                )
        return np.asarray(rows, dtype=float)


def _coefficient_rows(
    estimator: PolynomialInteractionEstimator,
    bootstrap: Mapping[tuple[int, ...], Mapping[str, float]],
) -> list[dict[str, object]]:
    return [
        {
            "term": list(term),
            "estimate": coefficient,
            "standard_error": estimator.standard_errors[term],
            "bootstrap": dict(bootstrap[term]),
        }
        for term, coefficient in estimator.coefficients.items()
    ]


def _query_bootstrap(
    masks: Sequence[Mask],
    rewards: np.ndarray,
    estimator: PolynomialInteractionEstimator,
    *,
    n_resamples: int,
    seed: int,
) -> dict[tuple[int, ...], dict[str, float]]:
    if n_resamples < 2:
        raise ValueError("query bootstrap requires at least two resamples")
    rng = np.random.default_rng(seed)
    terms = estimator.terms
    samples = np.empty((n_resamples, len(terms)), dtype=float)
    for replicate in range(n_resamples):
        indices = rng.integers(0, rewards.shape[1], size=rewards.shape[1])
        values = np.mean(rewards[:, indices], axis=1)
        fitted = PolynomialInteractionEstimator(max_order=2, n_players=len(masks[0])).fit(
            masks, values
        )
        samples[replicate] = [fitted.coefficients[term] for term in terms]

    summaries: dict[tuple[int, ...], dict[str, float]] = {}
    base = estimator.coefficients
    for column, term in enumerate(terms):
        term_samples = samples[:, column]
        reference_sign = np.sign(base[term])
        summaries[term] = {
            "lower": float(np.quantile(term_samples, 0.025)),
            "upper": float(np.quantile(term_samples, 0.975)),
            "sign_consistency": float(np.mean(np.sign(term_samples) == reference_sign)),
        }
    return summaries


def _ranked_pairs(estimator: PolynomialInteractionEstimator) -> list[tuple[int, int]]:
    return [
        tuple(term)  # type: ignore[arg-type]
        for term, _ in sorted(
            estimator.interactions(2).items(), key=lambda item: (-abs(item[1]), item[0])
        )
    ]


def fit_discovery_bank(
    *,
    bank: MemoryBank,
    view: EvaluationView,
    masks: Sequence[Mask],
    evaluator: CoalitionEvaluator,
    bootstrap_resamples: int,
    bootstrap_seed: int,
    top_k: int,
) -> dict[str, object]:
    require_discovery_view(view)
    queries = view.for_bank(bank.bank_id)
    rewards = evaluator.reward_matrix(bank, queries, view, masks)
    values = np.mean(rewards, axis=1)
    estimator = PolynomialInteractionEstimator(max_order=2, n_players=len(bank.memories)).fit(
        masks, values
    )
    bootstrap = _query_bootstrap(
        masks,
        rewards,
        estimator,
        n_resamples=bootstrap_resamples,
        seed=bootstrap_seed,
    )

    first_half = np.arange(rewards.shape[1]) % 2 == 0
    second_half = ~first_half
    halves = []
    for selected in (first_half, second_half):
        half_estimator = PolynomialInteractionEstimator(
            max_order=2, n_players=len(bank.memories)
        ).fit(masks, np.mean(rewards[:, selected], axis=1))
        halves.append(set(_ranked_pairs(half_estimator)[:top_k]))
    overlap = len(halves[0] & halves[1]) / top_k
    ranked = _ranked_pairs(estimator)
    top_terms = ranked[:top_k]
    top_sign_consistency = fmean(bootstrap[term]["sign_consistency"] for term in top_terms)
    n_pairs = math.comb(len(bank.memories), 2)

    return {
        "bank_id": bank.bank_id,
        "n_coalitions": len(masks),
        "n_discovery_queries": len(queries),
        "coalition_masks": [serialize_mask(mask) for mask in masks],
        "coalition_values": [float(value) for value in values],
        "design_rank": estimator.rank,
        "condition_number": estimator.condition_number,
        "coefficients": _coefficient_rows(estimator, bootstrap),
        "top_pairs": [list(term) for term in top_terms],
        "stability": {
            "split_half_top_k_overlap": overlap,
            "random_ranking_expected_overlap": top_k / n_pairs,
            "top_pair_mean_sign_consistency": top_sign_consistency,
        },
    }


def _coefficients_from_result(result: Mapping[str, object]) -> dict[tuple[int, ...], float]:
    rows = result["coefficients"]
    if not isinstance(rows, list):
        raise ValueError("malformed discovery coefficients")
    return {
        tuple(int(player) for player in row["term"]): float(row["estimate"])
        for row in rows
    }


def _retained_count(n_memories: int, deletion_ratio: float) -> int:
    return max(0, min(n_memories, math.ceil((1.0 - deletion_ratio) * n_memories)))


def _accuracy_for_mask(
    evaluator: CoalitionEvaluator,
    bank: MemoryBank,
    view: EvaluationView,
    mask: Mask,
) -> float:
    queries = view.for_bank(bank.bank_id)
    rewards = [evaluator.evaluate(bank, query, view, mask).reward for query in queries]
    return fmean(rewards)


def _retention_records(
    *,
    bank: MemoryBank,
    view: EvaluationView,
    evaluator: CoalitionEvaluator,
    coefficients: Mapping[tuple[int, ...], float],
    deletion_ratios: Sequence[float],
    random_replicates: int,
    random_seed: int,
) -> list[dict[str, object]]:
    n_players = len(bank.memories)
    full_mask = tuple(True for _ in range(n_players))
    empty_mask = tuple(False for _ in range(n_players))
    full_accuracy = _accuracy_for_mask(evaluator, bank, view, full_mask)
    empty_accuracy = _accuracy_for_mask(evaluator, bank, view, empty_mask)
    item_values = mobius_to_shapley_items(coefficients, n_players)
    records: list[dict[str, object]] = []

    for ratio_index, ratio in enumerate(deletion_ratios):
        keep_count = _retained_count(n_players, ratio)
        policy_masks: dict[str, list[Mask]] = {
            "item": [item_value_mask(item_values, n_players, keep_count)],
            "interaction": [interaction_aware_mask(coefficients, n_players, keep_count)],
            "random": [
                random_mask(
                    n_players,
                    keep_count,
                    random_seed + ratio_index * 10_007 + replicate * 1_009,
                )
                for replicate in range(random_replicates)
            ],
        }
        for policy, masks in policy_masks.items():
            for replicate, mask in enumerate(masks):
                accuracy = _accuracy_for_mask(evaluator, bank, view, mask)
                retained = [
                    memory
                    for memory, present in zip(bank.memories, mask, strict=True)
                    if present
                ]
                records.append(
                    {
                        "bank_id": bank.bank_id,
                        "split": view.split.value,
                        "policy": policy,
                        "replicate": replicate,
                        "nominal_deletion_ratio": ratio,
                        "actual_deletion_ratio": 1.0 - keep_count / n_players,
                        "keep_count": keep_count,
                        "mask": serialize_mask(mask),
                        "payload_storage_tokens": sum(
                            memory.storage_tokens for memory in retained
                        ),
                        "payload_storage_bytes": sum(memory.storage_bytes for memory in retained),
                        "accuracy": accuracy,
                        "empty_accuracy": empty_accuracy,
                        "full_accuracy": full_accuracy,
                        "normalized_retention": normalized_memory_retention(
                            accuracy, empty_accuracy, full_accuracy
                        ),
                    }
                )
        ratio_records = [
            record
            for record in records
            if float(record["nominal_deletion_ratio"]) == ratio
        ]
        token_costs = {int(record["payload_storage_tokens"]) for record in ratio_records}
        byte_costs = {int(record["payload_storage_bytes"]) for record in ratio_records}
        if len(token_costs) != 1 or len(byte_costs) != 1:
            raise RuntimeError("retention policies violated the locked payload budget")
    return records


def _validate_config(
    config: Mapping[str, object], root: Path, backend: LLMBackend | None = None
) -> None:
    if int(config["phase"]) != 2:
        raise ValueError("Phase 2 runner requires a Phase 2 config")
    if int(config["n_memories_per_bank"]) != 8:
        raise ValueError("the locked controlled dataset has eight memories per bank")
    if int(config["max_order"]) != 2:
        raise ValueError("the initial Phase 2 experiment is pairwise")
    configured_backend = str(config["backend"]["type"])
    if bool(config["scientific_gate_eligible"]) and (
        configured_backend == "mock" or isinstance(backend, MockBackend)
    ):
        raise ValueError("MockBackend can never be scientific-gate eligible")
    if bool(config["require_clean_git"]):
        git = git_provenance(root)
        if not git["available"] or git["source_dirty"]:
            raise RuntimeError(
                "scientific Phase 2 requires a committed revision with no source/config changes"
            )


def _p2a_gate(bank_results: Sequence[Mapping[str, object]], config: Mapping[str, object]) -> dict:
    stability = [result["stability"] for result in bank_results]
    overlaps = [float(item["split_half_top_k_overlap"]) for item in stability]
    random_expected = [float(item["random_ranking_expected_overlap"]) for item in stability]
    sign_consistency = [float(item["top_pair_mean_sign_consistency"]) for item in stability]
    mean_overlap = fmean(overlaps)
    mean_margin = fmean(
        overlap - expected for overlap, expected in zip(overlaps, random_expected, strict=True)
    )
    mean_sign = fmean(sign_consistency)
    checks = {
        "mean_split_half_top_k_overlap": {
            "value": mean_overlap,
            "operator": ">=",
            "threshold": float(config["mean_top_k_overlap_min"]),
            "passed": mean_overlap >= float(config["mean_top_k_overlap_min"]),
        },
        "mean_margin_over_random_ranking": {
            "value": mean_margin,
            "operator": ">=",
            "threshold": float(config["mean_overlap_margin_min"]),
            "passed": mean_margin >= float(config["mean_overlap_margin_min"]),
        },
        "mean_top_pair_sign_consistency": {
            "value": mean_sign,
            "operator": ">=",
            "threshold": float(config["mean_sign_consistency_min"]),
            "passed": mean_sign >= float(config["mean_sign_consistency_min"]),
        },
    }
    return {"passed": all(check["passed"] for check in checks.values()), "checks": checks}


def _validation_summary(records: Sequence[Mapping[str, object]], config: Mapping[str, object]) -> dict:
    full_by_bank: dict[str, float] = {}
    empty_by_bank: dict[str, float] = {}
    for record in records:
        bank_id = str(record["bank_id"])
        full_by_bank[bank_id] = float(record["full_accuracy"])
        empty_by_bank[bank_id] = float(record["empty_accuracy"])
    passing = [
        bank_id
        for bank_id in full_by_bank
        if full_by_bank[bank_id] >= float(config["full_accuracy_min"])
        and full_by_bank[bank_id] - empty_by_bank[bank_id]
        >= float(config["memory_gap_min"])
    ]
    fraction = len(passing) / len(full_by_bank)
    required_fraction = float(config["bank_fraction_min"])
    return {
        "mean_full_accuracy": fmean(full_by_bank.values()),
        "mean_empty_accuracy": fmean(empty_by_bank.values()),
        "mean_memory_gap": fmean(
            full_by_bank[bank] - empty_by_bank[bank] for bank in full_by_bank
        ),
        "passing_banks": passing,
        "passing_bank_fraction": fraction,
        "required_bank_fraction": required_fraction,
        "ready_for_test_unlock": fraction >= required_fraction,
    }


def create_phase2_run(
    *,
    root: Path,
    config: Mapping[str, object],
    config_path: Path,
    run_dir: Path,
    backend: LLMBackend | None = None,
) -> dict[str, object]:
    """Run discovery and validation without accessing held-out test queries."""

    if bool(config["scientific_gate_eligible"]) and (run_dir / "test_unlock.json").exists():
        raise RuntimeError("discovery artifacts are frozen after the scientific test unlock")
    _validate_config(config, root)
    backend = backend or make_backend(config["backend"])
    _validate_config(config, root, backend)
    dataset = generate_phase2_dataset(
        int(config["n_banks"]), bank_start=int(config.get("bank_start", 0))
    )
    expected_counts = config["query_counts_per_bank"]
    for split in QuerySplit:
        observed = len(dataset.view(split).queries) // len(dataset.banks)
        if observed != int(expected_counts[split.value]):
            raise RuntimeError(
                f"dataset has {observed} {split.value} queries per bank; config expects "
                f"{expected_counts[split.value]}"
            )
    discovery_view = dataset.view(QuerySplit.DISCOVERY)
    validation_view = dataset.view(QuerySplit.VALIDATION)
    provenance = runtime_provenance(root, backend)
    commit = provenance["git"]["commit"]
    code_identity = (
        commit if isinstance(commit, str) else f"tree:{provenance['source_tree_sha256']}"
    )
    config_hash = _json_hash(config)
    run_dir.mkdir(parents=True, exist_ok=True)
    _atomic_json(run_dir / "config.json", config)
    _atomic_json(run_dir / "dataset_manifest.json", dataset.public_manifest())

    cache_path = run_dir / "evaluations.sqlite3"
    with EvaluationCache(cache_path) as cache:
        evaluator = CoalitionEvaluator(
            backend=backend,
            cache=cache,
            generation_config=config["generation"],
            seed=int(config["seed"]),
            code_commit=code_identity,
            progress=True,
        )
        bank_results: list[dict[str, object]] = []
        exact_bank_count = int(config["coalitions"]["exact_bank_count"])
        sampled_budget = int(config["coalitions"]["sampled_budget"])
        for bank_index, bank in enumerate(dataset.banks):
            budget = (1 << len(bank.memories)) if bank_index < exact_bank_count else sampled_budget
            masks = size_balanced_masks(
                len(bank.memories), budget, int(config["seed"]) + bank_index * 7_919
            )
            bank_results.append(
                fit_discovery_bank(
                    bank=bank,
                    view=discovery_view,
                    masks=masks,
                    evaluator=evaluator,
                    bootstrap_resamples=int(config["stability"]["bootstrap_resamples"]),
                    bootstrap_seed=int(config["seed"]) + bank_index * 104_729,
                    top_k=int(config["stability"]["top_k"]),
                )
            )

        p2a = _p2a_gate(bank_results, config["gate_thresholds"]["p2a"])
        discovery = {
            "schema_version": 1,
            "phase": 2,
            "stage": "discovery",
            "config_sha256": config_hash,
            "dataset_sha256": dataset.sha256(),
            "prompt_template_sha256": prompt_template_hash(),
            "estimand": (
                "order-2 least-squares coefficients in a truncated binary monomial basis "
                "for discovery-query mean accuracy"
            ),
            "bank_results": bank_results,
            "p2a_candidate_gate": p2a,
        }
        _atomic_json(run_dir / "discovery.json", discovery)

        validation_records: list[dict[str, object]] = []
        deletion_ratios = [float(value) for value in config["retention"]["deletion_ratios"]]
        for bank_index, (bank, bank_result) in enumerate(
            zip(dataset.banks, bank_results, strict=True)
        ):
            validation_records.extend(
                _retention_records(
                    bank=bank,
                    view=validation_view,
                    evaluator=evaluator,
                    coefficients=_coefficients_from_result(bank_result),
                    deletion_ratios=deletion_ratios,
                    random_replicates=int(config["retention"]["random_replicates"]),
                    random_seed=int(config["seed"]) + bank_index * 1_000_003,
                )
            )
            print(
                f"validation {bank.bank_id}: retention conditions complete",
                flush=True,
            )
        validation_summary = _validation_summary(
            validation_records, config["validation_thresholds"]
        )
        validation = {
            "schema_version": 1,
            "phase": 2,
            "stage": "validation",
            "config_sha256": config_hash,
            "summary": validation_summary,
            "retention_records": validation_records,
        }
        _atomic_json(run_dir / "validation.json", validation)
        cache_stats = {
            "rows": cache.count(),
            "hits_this_stage": evaluator.cache_hits,
            "misses_this_stage": evaluator.cache_misses,
        }

    report = {
        "schema_version": 1,
        "phase": 2,
        "stage": "discovery-validation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scientific_gate_eligible": bool(config["scientific_gate_eligible"]),
        "gate_p2": None,
        "gate_note": "P2 cannot be decided before the locked test stage",
        "config_source": str(config_path.relative_to(root)),
        "config_sha256": config_hash,
        "dataset_sha256": dataset.sha256(),
        "prompt_template_sha256": prompt_template_hash(),
        "provenance": provenance,
        "p2a_candidate_gate": p2a,
        "validation": validation_summary,
        "cache": cache_stats,
        "artifacts": {
            "config": str((run_dir / "config.json").relative_to(root)),
            "dataset_manifest": str((run_dir / "dataset_manifest.json").relative_to(root)),
            "discovery": str((run_dir / "discovery.json").relative_to(root)),
            "validation": str((run_dir / "validation.json").relative_to(root)),
            "cache": str(cache_path.relative_to(root)),
        },
    }
    _atomic_json(run_dir / "report.json", report)
    return report


def unlock_phase2_test(*, run_dir: Path) -> dict[str, object]:
    """Record the one-way decision to expose the test capability."""

    unlock_path = run_dir / "test_unlock.json"
    if unlock_path.exists():
        return json.loads(unlock_path.read_text(encoding="utf-8"))
    if (run_dir / "test.json").exists():
        raise RuntimeError("test results exist without an unlock record")
    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    validation = json.loads((run_dir / "validation.json").read_text(encoding="utf-8"))
    discovery = json.loads((run_dir / "discovery.json").read_text(encoding="utf-8"))
    if validation["config_sha256"] != _json_hash(config):
        raise RuntimeError("config changed after validation; refusing test unlock")
    if not validation["summary"]["ready_for_test_unlock"]:
        raise RuntimeError("validation readiness gate did not pass")
    if not discovery["p2a_candidate_gate"]["passed"]:
        raise RuntimeError("P2-A discovery stability gate did not pass")
    unlock = {
        "schema_version": 1,
        "phase": 2,
        "decision": "test_unlocked",
        "unlocked_at_utc": datetime.now(timezone.utc).isoformat(),
        "config_sha256": validation["config_sha256"],
        "validation_summary_hash": _json_hash(validation["summary"]),
        "discovery_p2a_hash": _json_hash(discovery["p2a_candidate_gate"]),
        "discovery_artifact_hash": _json_hash(discovery),
        "validation_artifact_hash": _json_hash(validation),
        "irreversible_for_run": True,
    }
    _atomic_json(unlock_path, unlock)
    return unlock


def _one_sided_sign_flip_pvalue(differences: Sequence[float]) -> float:
    observed = fmean(differences)
    if not differences:
        raise ValueError("at least one bank-level difference is required")
    permuted = [
        fmean(sign * value for sign, value in zip(signs, differences, strict=True))
        for signs in product((-1.0, 1.0), repeat=len(differences))
    ]
    return sum(value >= observed - 1e-12 for value in permuted) / len(permuted)


def _p2b_gate(records: Sequence[Mapping[str, object]], config: Mapping[str, object]) -> dict:
    severe_ratios = {float(value) for value in config["severe_deletion_ratios"]}
    values: dict[tuple[str, str, float], list[float]] = defaultdict(list)
    for record in records:
        ratio = float(record["nominal_deletion_ratio"])
        if ratio in severe_ratios and str(record["policy"]) in {"item", "interaction"}:
            values[(str(record["bank_id"]), str(record["policy"]), ratio)].append(
                float(record["accuracy"])
            )
    bank_ids = sorted({key[0] for key in values})
    differences = []
    for bank_id in bank_ids:
        interaction = fmean(
            fmean(values[(bank_id, "interaction", ratio)]) for ratio in severe_ratios
        )
        item = fmean(
            fmean(values[(bank_id, "item", ratio)]) for ratio in severe_ratios
        )
        differences.append(interaction - item)
    mean_difference = fmean(differences)
    median_difference = median(differences)
    positive_fraction = sum(value > 0 for value in differences) / len(differences)
    pvalue = _one_sided_sign_flip_pvalue(differences)
    checks = {
        "mean_severe_accuracy_advantage": {
            "value": mean_difference,
            "operator": ">=",
            "threshold": float(config["mean_advantage_min"]),
            "passed": mean_difference >= float(config["mean_advantage_min"]),
        },
        "positive_bank_fraction": {
            "value": positive_fraction,
            "operator": ">=",
            "threshold": float(config["positive_bank_fraction_min"]),
            "passed": positive_fraction >= float(config["positive_bank_fraction_min"]),
        },
        "one_sided_sign_flip_pvalue": {
            "value": pvalue,
            "operator": "<=",
            "threshold": float(config["pvalue_max"]),
            "passed": pvalue <= float(config["pvalue_max"]),
        },
    }
    return {
        "passed": all(check["passed"] for check in checks.values()),
        "checks": checks,
        "bank_level_differences": differences,
        "median_severe_accuracy_advantage": median_difference,
    }


def _aggregate_curves(records: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, float], list[float]] = defaultdict(list)
    normalized: dict[tuple[str, float], list[float]] = defaultdict(list)
    for record in records:
        key = (str(record["policy"]), float(record["nominal_deletion_ratio"]))
        grouped[key].append(float(record["accuracy"]))
        if record["normalized_retention"] is not None:
            normalized[key].append(float(record["normalized_retention"]))
    return [
        {
            "policy": policy,
            "nominal_deletion_ratio": ratio,
            "mean_accuracy": fmean(values),
            "mean_normalized_retention": fmean(normalized[(policy, ratio)])
            if normalized[(policy, ratio)]
            else None,
            "n_records": len(values),
        }
        for (policy, ratio), values in sorted(grouped.items())
    ]


def run_phase2_test(
    *,
    root: Path,
    run_dir: Path,
    backend: LLMBackend | None = None,
) -> dict[str, object]:
    """Run the locked test stage using discovery artifacts only."""

    unlock_path = run_dir / "test_unlock.json"
    if not unlock_path.exists():
        raise RuntimeError("test split is locked; run the explicit unlock stage first")
    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    unlock = json.loads(unlock_path.read_text(encoding="utf-8"))
    if unlock["config_sha256"] != _json_hash(config):
        raise RuntimeError("config changed after test unlock")
    _validate_config(config, root)
    backend = backend or make_backend(config["backend"])
    _validate_config(config, root, backend)
    dataset: ControlledDataset = generate_phase2_dataset(
        int(config["n_banks"]), bank_start=int(config.get("bank_start", 0))
    )
    test_view = dataset.view(QuerySplit.TEST)
    discovery = json.loads((run_dir / "discovery.json").read_text(encoding="utf-8"))
    validation = json.loads((run_dir / "validation.json").read_text(encoding="utf-8"))
    if unlock.get("discovery_artifact_hash") != _json_hash(discovery):
        raise RuntimeError("discovery artifact changed after test unlock")
    if unlock.get("validation_artifact_hash") != _json_hash(validation):
        raise RuntimeError("validation artifact changed after test unlock")
    if discovery["dataset_sha256"] != dataset.sha256():
        raise RuntimeError("dataset changed after discovery")
    if discovery["prompt_template_sha256"] != prompt_template_hash():
        raise RuntimeError("prompt template changed after discovery")
    by_bank = {row["bank_id"]: row for row in discovery["bank_results"]}
    previous_report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    provenance = runtime_provenance(root, backend)
    prior_commit = previous_report["provenance"]["git"]["commit"]
    current_commit = provenance["git"]["commit"]
    if bool(config["scientific_gate_eligible"]) and current_commit != prior_commit:
        raise RuntimeError("Git commit changed between discovery and locked test")
    commit = provenance["git"]["commit"]
    code_identity = (
        commit if isinstance(commit, str) else f"tree:{provenance['source_tree_sha256']}"
    )

    cache_path = run_dir / "evaluations.sqlite3"
    with EvaluationCache(cache_path) as cache:
        evaluator = CoalitionEvaluator(
            backend=backend,
            cache=cache,
            generation_config=config["generation"],
            seed=int(config["seed"]),
            code_commit=code_identity,
            progress=True,
        )
        records: list[dict[str, object]] = []
        ratios = [float(value) for value in config["retention"]["deletion_ratios"]]
        for bank_index, bank in enumerate(dataset.banks):
            records.extend(
                _retention_records(
                    bank=bank,
                    view=test_view,
                    evaluator=evaluator,
                    coefficients=_coefficients_from_result(by_bank[bank.bank_id]),
                    deletion_ratios=ratios,
                    random_replicates=int(config["retention"]["random_replicates"]),
                    random_seed=int(config["seed"]) + bank_index * 1_000_003,
                )
            )
            print(f"test {bank.bank_id}: retention conditions complete", flush=True)
        p2b = _p2b_gate(records, config["gate_thresholds"]["p2b"])
        cache_stats = {
            "rows": cache.count(),
            "hits_this_stage": evaluator.cache_hits,
            "misses_this_stage": evaluator.cache_misses,
        }

    p2a = discovery["p2a_candidate_gate"]
    eligible = bool(config["scientific_gate_eligible"])
    gate_passed = bool(p2a["passed"] and p2b["passed"]) if eligible else None
    test_payload = {
        "schema_version": 1,
        "phase": 2,
        "stage": "test",
        "config_sha256": _json_hash(config),
        "dataset_sha256": dataset.sha256(),
        "prompt_template_sha256": prompt_template_hash(),
        "retention_records": records,
        "aggregate_curves": _aggregate_curves(records),
        "p2b_candidate_gate": p2b,
    }
    _atomic_json(run_dir / "test.json", test_payload)
    report = {
        "schema_version": 1,
        "phase": 2,
        "stage": "complete",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scientific_gate_eligible": eligible,
        "gate_p2": gate_passed,
        "gate_note": (
            "Scientific P2 decision" if eligible else "Mock smoke run; P2 is not evaluated"
        ),
        "config_sha256": _json_hash(config),
        "dataset_sha256": dataset.sha256(),
        "prompt_template_sha256": prompt_template_hash(),
        "provenance": provenance,
        "p2a_candidate_gate": p2a,
        "p2b_candidate_gate": p2b,
        "aggregate_curves": test_payload["aggregate_curves"],
        "cache": cache_stats,
        "artifacts": {
            "discovery": str((run_dir / "discovery.json").relative_to(root)),
            "validation": str((run_dir / "validation.json").relative_to(root)),
            "test_unlock": str(unlock_path.relative_to(root)),
            "test": str((run_dir / "test.json").relative_to(root)),
            "cache": str(cache_path.relative_to(root)),
        },
    }
    _atomic_json(run_dir / "report.json", report)
    return report
