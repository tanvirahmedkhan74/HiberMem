"""Resumable, leakage-scoped E4 past/freeze/future experiment pipeline."""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from pathlib import Path

from hibermem.backends import HFLocalBackend
from hibermem.coalition.masks import mask_to_index
from hibermem.coalition.sampling import size_balanced_masks
from hibermem.environments.controlled.contract import (
    FactorialOracle,
    contract_prompt_hash,
)
from hibermem.environments.controlled.prospective import (
    PROTOCOL,
    generate_prospective_suite,
    symbolic_prospective_controls,
)
from hibermem.evaluation.prospective import (
    PastEvidence,
    freeze_past_policies,
    future_mask_indices,
    summarize_future,
)
from hibermem.experiments.exact_mechanism import (
    _analysis_equal,
    _file_hash,
    _read,
    evidence_row,
    validate_row,
)
from hibermem.experiments.phase2 import (
    _atomic_json,
    _json_hash,
    _source_tree_sha256,
    git_provenance,
    make_backend,
    runtime_provenance,
)


CAPABILITIES = {
    "scientific_gate_eligible": False,
    "confirmation_compatible": False,
    "selected_candidate": None,
    "qualified": None,
    "test_access": False,
}
FINAL_ARTIFACTS = (
    "config.json",
    "public_manifest.json",
    "identity.json",
    "runtime.json",
    "controls.json",
    "past_evaluations.json",
    "past_report.json",
    "frozen_selections.json",
    "sealed_future_manifest.json",
    "future_evaluations.json",
)


def validate_prospective_config(config: dict, *, real: bool = False):
    expected = {
        "schema_version",
        "protocol",
        "scientific_gate_eligible",
        "confirmation_compatible",
        "cohort",
        "output_contract",
        "generation",
        "keep_counts",
        "random_seeds",
        "prediction_probe",
        "analysis",
        "candidates",
    }
    if set(config) != expected or config.get("schema_version") != 1:
        raise ValueError("E4 requires the exact versioned config schema")
    if config.get("protocol") != PROTOCOL:
        raise ValueError("unexpected E4 protocol")
    if config["scientific_gate_eligible"] is not False or config["confirmation_compatible"] is not False:
        raise ValueError("E4 development cannot authorize a scientific gate")
    cohort = config["cohort"]
    if set(cohort) != {
        "name",
        "n_banks",
        "bank_start",
        "seed",
        "past_paraphrases",
        "future_paraphrases",
    } or cohort["name"] not in ("engineering", "design"):
        raise ValueError("E4 v1 permits engineering/design cohorts only")
    if any(type(cohort[key]) is not int for key in cohort if key != "name"):
        raise ValueError("E4 cohort counts/seeds must be integers")
    contract = config["output_contract"]
    if set(contract) != {
        "name",
        "status",
        "e3c_report_sha256",
        "prompt_sha256",
    }:
        raise ValueError("invalid E4 output-contract freeze")
    if not isinstance(contract["name"], str):
        raise ValueError("E4 output-contract status is not frozen")
    expected_prompt = contract_prompt_hash(contract["name"])
    if contract["prompt_sha256"] != expected_prompt:
        raise ValueError("E4 output-contract prompt hash mismatch")
    if contract["status"] == "engineering_only":
        if contract["e3c_report_sha256"] is not None or real:
            raise ValueError("engineering-only contracts cannot run real E4 inference")
    elif contract["status"] == "frozen_development":
        if re.fullmatch(r"[0-9a-f]{64}", str(contract["e3c_report_sha256"])) is None:
            raise ValueError("real E4 requires a frozen E3c report hash")
    else:
        raise ValueError("unknown E4 output-contract status")
    generation = config["generation"]
    if (
        set(generation) != {"do_sample", "max_new_tokens"}
        or generation["do_sample"] is not False
        or type(generation["max_new_tokens"]) is not int
        or not 1 <= generation["max_new_tokens"] <= 64
    ):
        raise ValueError("E4 requires bounded deterministic generation")
    keep_counts = config["keep_counts"]
    if keep_counts != [2, 3, 4, 6]:
        raise ValueError("E4 v1 freezes keep counts [2,3,4,6]")
    seeds = config["random_seeds"]
    if not isinstance(seeds, list) or not seeds or len(set(seeds)) != len(seeds) or any(
        type(seed) is not int or not 0 <= seed < 2**32 for seed in seeds
    ):
        raise ValueError("invalid E4 random seeds")
    probe = config["prediction_probe"]
    if set(probe) != {"mode", "n_masks", "seed"} or probe["mode"] != "size_balanced":
        raise ValueError("E4 v1 requires a size-balanced prediction probe")
    if any(type(probe[key]) is not int for key in ("n_masks", "seed")):
        raise ValueError("invalid E4 prediction probe")
    probe_masks = size_balanced_masks(8, probe["n_masks"], probe["seed"])
    analysis = config["analysis"]
    if set(analysis) != {
        "practical_margin",
        "bootstrap_seed",
        "bootstrap_resamples",
        "randomization_seed",
        "randomization_resamples",
    }:
        raise ValueError("invalid E4 analysis contract")
    if (
        isinstance(analysis["practical_margin"], bool)
        or not isinstance(analysis["practical_margin"], (int, float))
        or not 0 <= analysis["practical_margin"] <= 1
    ):
        raise ValueError("invalid practical margin")
    for key in (
        "bootstrap_seed",
        "bootstrap_resamples",
        "randomization_seed",
        "randomization_resamples",
    ):
        if type(analysis[key]) is not int or analysis[key] < (2 if "resamples" in key else 0):
            raise ValueError(f"invalid E4 analysis setting: {key}")
    if not isinstance(config["candidates"], dict) or set(config["candidates"]) != {"qwen"}:
        raise ValueError("E4 v1 freezes the audited Qwen candidate")
    backend = config["candidates"]["qwen"]
    if backend.get("type") != "hf_local" or re.fullmatch(
        r"[0-9a-f]{40}", str(backend.get("model_revision", ""))
    ) is None:
        raise ValueError("E4 requires a pinned HF-local model revision")
    if backend.get("trust_remote_code") is not False or backend.get("quantization") != "none":
        raise ValueError("remote code/quantization are outside E4 v1")
    suite = generate_prospective_suite(
        n_banks=cohort["n_banks"],
        bank_start=cohort["bank_start"],
        seed=cohort["seed"],
        output_contract=contract["name"],
        past_paraphrases=cohort["past_paraphrases"],
        future_paraphrases=cohort["future_paraphrases"],
    )
    indices = tuple(mask_to_index(mask) for mask in probe_masks)
    return suite, indices


def _identity(config: dict, suite, probe_indices, candidate: str, git: dict) -> dict:
    backend = {"type": "mock"} if candidate == "mock" else config["candidates"][candidate]
    return {
        "protocol": PROTOCOL,
        "candidate": candidate,
        "backend": backend,
        "config_sha256": _json_hash(config),
        "public_manifest_sha256": _json_hash(suite.public_manifest()),
        "sealed_future_manifest_sha256": _json_hash(suite.sealed_future_manifest()),
        "prediction_probe_sha256": _json_hash(probe_indices),
        "output_contract_prompt_sha256": contract_prompt_hash(
            config["output_contract"]["name"]
        ),
        "source_tree_sha256": _source_tree_sha256(Path(__file__).resolve().parents[3]),
        "git_commit": git["commit"],
    }


def _prospective_row(case, *, generated, latency: float, engineering: bool) -> dict:
    row = evidence_row(
        case,
        raw=generated.text,
        trace=generated.trace,
        input_tokens=generated.input_tokens,
        output_tokens=generated.output_tokens,
        latency_seconds=latency,
        engineering=engineering,
    )
    row["family"] = case["family"]
    return row


def _validate_prospective_row(row: dict, case: dict, engineering: bool) -> None:
    if row.get("family") != case["family"]:
        raise ValueError("prospective family label mismatch")
    base = dict(row)
    base.pop("family")
    validate_row(base, case, engineering)


def _prepare(root: Path, config: dict, candidate: str, run_dir: Path):
    suite, probe_indices = validate_prospective_config(
        config, real=candidate != "mock"
    )
    if candidate not in config["candidates"] and candidate != "mock":
        raise ValueError("candidate is not in the E4 matrix")
    git = git_provenance(root)
    if candidate != "mock" and (not git["available"] or git["source_dirty"]):
        raise RuntimeError("commit E4 source/frozen config before real inference")
    identity = _identity(config, suite, probe_indices, candidate, git)
    identity_path = run_dir / "identity.json"
    if identity_path.exists() and _read(identity_path) != identity:
        raise RuntimeError("E4 run identity changed; use a new directory")
    if run_dir.exists() and any(run_dir.iterdir()) and not identity_path.exists():
        raise RuntimeError("refusing a nonempty E4 directory without identity")
    controls = symbolic_prospective_controls(suite)
    run_dir.mkdir(parents=True, exist_ok=True)
    for name, value in (
        ("identity.json", identity),
        ("config.json", config),
        ("public_manifest.json", suite.public_manifest()),
        ("controls.json", controls),
    ):
        path = run_dir / name
        if path.exists() and _read(path) != value:
            raise RuntimeError(f"E4 resume mismatch: {name}")
        if not path.exists():
            _atomic_json(path, value)
    return suite, probe_indices, identity, git


def _backend_and_runtime(root, config, candidate, run_dir):
    backend_config = {"type": "mock"} if candidate == "mock" else config["candidates"][candidate]
    backend = FactorialOracle() if candidate == "mock" else make_backend(backend_config)
    if candidate != "mock" and type(backend) is not HFLocalBackend:
        raise ValueError("E4 supports the audited HF-local backend only")
    runtime = runtime_provenance(root, backend)
    runtime = {
        key: runtime[key]
        for key in ("python", "packages", "gpu", "backend", "source_tree_sha256")
    }
    path = run_dir / "runtime.json"
    if path.exists() and _read(path) != runtime:
        raise RuntimeError("E4 runtime changed between stages")
    if not path.exists():
        _atomic_json(path, runtime)
    return backend, runtime


def _evaluate_conditions(
    *, conditions, backend, config, candidate, checkpoint: Path, label: str
) -> tuple[list[dict], int]:
    checkpoint.mkdir(exist_ok=True)
    conditions = list(conditions)
    expected = {f"{index:07d}.json" for index in range(len(conditions))}
    if any(path.name not in expected for path in checkpoint.iterdir()):
        raise ValueError(f"unexpected {label} checkpoint file")
    rows, reused = [], 0
    for index, case in enumerate(conditions):
        path = checkpoint / f"{index:07d}.json"
        if path.exists():
            row = _read(path)
            _validate_prospective_row(row, case, candidate == "mock")
            reused += 1
        else:
            start = time.perf_counter()
            generated = backend.generate(
                case["messages"],
                **config["generation"],
                seed=config["cohort"]["seed"],
            )
            row = _prospective_row(
                case,
                generated=generated,
                latency=time.perf_counter() - start,
                engineering=candidate == "mock",
            )
            _atomic_json(path, row)
        rows.append(row)
        if (index + 1) % 256 == 0 or index + 1 == len(conditions):
            print(
                f"{candidate}: {index + 1}/{len(conditions)} E4 {label} conditions complete",
                flush=True,
            )
    return rows, reused


def run_prospective_past(
    *, root: Path, config: dict, candidate: str, run_dir: Path
) -> dict:
    suite, probe_indices, identity, git = _prepare(
        root, config, candidate, run_dir
    )
    path = run_dir / "past_report.json"
    if path.exists() and _read(path).get("status") == "past_complete":
        return validate_prospective_past(run_dir, allow_mock=candidate == "mock")
    report = {
        "schema_version": 1,
        "protocol": PROTOCOL,
        **CAPABILITIES,
        "engineering_only": candidate == "mock",
        "status": "past_running",
        "scope": "past discovery only; future outcomes unavailable",
        "identity": identity,
        "git": git,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _atomic_json(path, report)
    backend = None
    try:
        backend, _ = _backend_and_runtime(root, config, candidate, run_dir)
        rows, reused = _evaluate_conditions(
            conditions=suite.past_conditions(),
            backend=backend,
            config=config,
            candidate=candidate,
            checkpoint=run_dir / "past_conditions",
            label="past",
        )
        _atomic_json(run_dir / "past_evaluations.json", rows)
        evidence = PastEvidence.from_rows(rows, suite.past_view())
        report.update(
            {
                "status": "past_complete",
                "planned_conditions": suite.public_manifest()["past_planned_conditions"],
                "checkpoint_reused": reused,
                "generation_calls_this_attempt": len(rows) - reused,
                "past_evidence_sha256": evidence.sha256,
                "past_evaluations_sha256": _file_hash(
                    run_dir / "past_evaluations.json"
                ),
                "future_rows_generated": 0,
                "frozen_selections_created": False,
            }
        )
    except Exception as error:
        report["status"] = "past_runtime_error"
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        report["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
        _atomic_json(path, report)
        del backend
    return validate_prospective_past(run_dir, allow_mock=candidate == "mock")


def validate_prospective_past(
    run_dir: Path, *, allow_mock: bool = False
) -> dict:
    config = _read(run_dir / "config.json")
    report = _read(run_dir / "past_report.json")
    if report.get("protocol") != PROTOCOL or report.get("status") != "past_complete":
        raise ValueError("a completed E4 past stage is required")
    if any(report.get(key) != value for key, value in CAPABILITIES.items()):
        raise ValueError("invalid E4 past capability claim")
    if report.get("future_rows_generated") != 0:
        raise ValueError("E4 past report claims future rows were generated")
    if report.get("frozen_selections_created") is not False:
        raise ValueError("E4 past report claims policies were already frozen")
    engineering = report.get("engineering_only")
    if type(engineering) is not bool or (engineering and not allow_mock):
        raise ValueError("mock E4 past evidence requires explicit authorization")
    suite, probe_indices = validate_prospective_config(config, real=not engineering)
    if _read(run_dir / "public_manifest.json") != suite.public_manifest():
        raise ValueError("E4 public manifest mismatch")
    identity = _read(run_dir / "identity.json")
    if report["identity"] != identity:
        raise ValueError("E4 past identity mismatch")
    if identity["config_sha256"] != _json_hash(config):
        raise ValueError("E4 past config identity mismatch")
    if identity["prediction_probe_sha256"] != _json_hash(probe_indices):
        raise ValueError("E4 prediction probe identity mismatch")
    if _read(run_dir / "controls.json") != symbolic_prospective_controls(suite):
        raise ValueError("E4 symbolic controls mismatch")
    runtime = _read(run_dir / "runtime.json")
    if runtime["source_tree_sha256"] != identity["source_tree_sha256"]:
        raise ValueError("E4 source identity mismatch")
    if not engineering:
        backend = config["candidates"].get(identity["candidate"])
        if backend is None or identity["backend"] != backend:
            raise ValueError("E4 backend identity mismatch")
        if runtime["backend"].get("backend") != "HFLocalBackend":
            raise ValueError("unrecognized E4 runtime backend")
        for key in ("model_id", "model_revision", "quantization", "device", "dtype"):
            if runtime["backend"].get(key) != backend[key]:
                raise ValueError(f"E4 runtime mismatch: {key}")
        if not report["git"]["available"] or report["git"]["source_dirty"]:
            raise ValueError("real E4 evidence requires clean source")
    rows = _read(run_dir / "past_evaluations.json")
    conditions = list(suite.past_conditions())
    if len(rows) != len(conditions):
        raise ValueError("incomplete E4 past rows")
    for row, case in zip(rows, conditions, strict=True):
        _validate_prospective_row(row, case, engineering)
    evidence = PastEvidence.from_rows(rows, suite.past_view())
    if report["past_evidence_sha256"] != evidence.sha256:
        raise ValueError("E4 policy-safe past evidence mismatch")
    if report["past_evaluations_sha256"] != _file_hash(
        run_dir / "past_evaluations.json"
    ):
        raise ValueError("E4 past-evaluations file mismatch")
    return report


def freeze_prospective_policies(
    *, root: Path, config: dict, candidate: str, run_dir: Path
) -> dict:
    del root
    if _read(run_dir / "config.json") != config:
        raise ValueError("E4 freeze config differs from the completed past run")
    suite, probe_indices = validate_prospective_config(
        config, real=candidate != "mock"
    )
    past_report = validate_prospective_past(
        run_dir, allow_mock=candidate == "mock"
    )
    if past_report["identity"]["candidate"] != candidate:
        raise ValueError("E4 freeze candidate mismatch")
    rows = _read(run_dir / "past_evaluations.json")
    evidence = PastEvidence.from_rows(rows, suite.past_view())
    frozen = freeze_past_policies(evidence, suite, config)
    frozen.update(
        {
            "identity_sha256": _json_hash(past_report["identity"]),
            "past_report_sha256": _file_hash(run_dir / "past_report.json"),
            "past_evaluations_sha256": _file_hash(
                run_dir / "past_evaluations.json"
            ),
            "prediction_probe_indices": list(probe_indices),
            "prediction_probe_sha256": _json_hash(probe_indices),
            "output_contract_freeze": config["output_contract"],
        }
    )
    path = run_dir / "frozen_selections.json"
    if path.exists():
        if _read(path) != frozen:
            raise RuntimeError("frozen E4 selections differ; preserve run and inspect")
        return frozen
    _atomic_json(path, frozen)
    return frozen


def _validate_frozen(run_dir, suite, config, probe_indices, engineering):
    past_report = validate_prospective_past(run_dir, allow_mock=engineering)
    frozen = _read(run_dir / "frozen_selections.json")
    rows = _read(run_dir / "past_evaluations.json")
    expected = freeze_past_policies(
        PastEvidence.from_rows(rows, suite.past_view()), suite, config
    )
    expected.update(
        {
            "identity_sha256": _json_hash(past_report["identity"]),
            "past_report_sha256": _file_hash(run_dir / "past_report.json"),
            "past_evaluations_sha256": _file_hash(
                run_dir / "past_evaluations.json"
            ),
            "prediction_probe_indices": list(probe_indices),
            "prediction_probe_sha256": _json_hash(probe_indices),
            "output_contract_freeze": config["output_contract"],
        }
    )
    if not _analysis_equal(frozen, expected):
        raise ValueError("E4 frozen-selection artifact mismatch")
    return frozen


def run_prospective_future(
    *, root: Path, config: dict, candidate: str, run_dir: Path
) -> dict:
    suite, probe_indices, identity, git = _prepare(
        root, config, candidate, run_dir
    )
    report_path = run_dir / "report.json"
    if report_path.exists() and _read(report_path).get("status") == "complete":
        return validate_prospective_report(
            report_path, allow_mock=candidate == "mock"
        )
    frozen = _validate_frozen(
        run_dir, suite, config, probe_indices, candidate == "mock"
    )
    report = {
        "schema_version": 1,
        "protocol": PROTOCOL,
        **CAPABILITIES,
        "engineering_only": candidate == "mock",
        "status": "future_running",
        "scope": "prospective development; no qualification or historical test access",
        "identity": identity,
        "git": git,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _atomic_json(report_path, report)
    backend = None
    try:
        backend, _ = _backend_and_runtime(root, config, candidate, run_dir)
        mask_map = future_mask_indices(frozen, probe_indices)
        rows, reused = _evaluate_conditions(
            conditions=suite.future_conditions(mask_map),
            backend=backend,
            config=config,
            candidate=candidate,
            checkpoint=run_dir / "future_conditions",
            label="future",
        )
        _atomic_json(run_dir / "sealed_future_manifest.json", suite.sealed_future_manifest())
        _atomic_json(run_dir / "future_evaluations.json", rows)
        report["analysis"] = summarize_future(
            rows, suite, config, frozen, probe_indices
        )
        report["planned_future_conditions"] = len(rows)
        report["checkpoint_reused"] = reused
        report["generation_calls_this_attempt"] = len(rows) - reused
        report["artifacts_sha256"] = {
            name: _file_hash(run_dir / name) for name in FINAL_ARTIFACTS
        }
        report["status"] = "complete"
    except Exception as error:
        report["status"] = "future_runtime_error"
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        report["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
        _atomic_json(report_path, report)
        del backend
    return validate_prospective_report(
        report_path, allow_mock=candidate == "mock"
    )


def validate_prospective_report(
    path: Path, *, allow_mock: bool = False
) -> dict:
    report, run_dir = _read(path), path.parent
    if report.get("protocol") != PROTOCOL or report.get("status") != "complete":
        raise ValueError("a complete E4 report is required")
    if any(report.get(key) != value for key, value in CAPABILITIES.items()):
        raise ValueError("invalid E4 capability claim")
    engineering = report.get("engineering_only")
    if type(engineering) is not bool or (engineering and not allow_mock):
        raise ValueError("mock E4 evidence requires explicit authorization")
    for name in FINAL_ARTIFACTS:
        if report.get("artifacts_sha256", {}).get(name) != _file_hash(run_dir / name):
            raise ValueError(f"E4 artifact hash mismatch: {name}")
    config = _read(run_dir / "config.json")
    suite, probe_indices = validate_prospective_config(config, real=not engineering)
    past = validate_prospective_past(run_dir, allow_mock=engineering)
    if report["identity"] != past["identity"] or report["git"] != past["git"]:
        raise ValueError("E4 identity changed after past stage")
    frozen = _validate_frozen(
        run_dir, suite, config, probe_indices, engineering
    )
    if _read(run_dir / "sealed_future_manifest.json") != suite.sealed_future_manifest():
        raise ValueError("E4 sealed future manifest mismatch")
    if report["identity"]["sealed_future_manifest_sha256"] != _json_hash(
        suite.sealed_future_manifest()
    ):
        raise ValueError("E4 future commitment mismatch")
    mask_map = future_mask_indices(frozen, probe_indices)
    conditions = list(suite.future_conditions(mask_map))
    rows = _read(run_dir / "future_evaluations.json")
    if len(rows) != len(conditions) or report["planned_future_conditions"] != len(rows):
        raise ValueError("incomplete E4 future rows")
    for row, case in zip(rows, conditions, strict=True):
        _validate_prospective_row(row, case, engineering)
    analysis = summarize_future(rows, suite, config, frozen, probe_indices)
    if not _analysis_equal(report["analysis"], analysis):
        raise ValueError("E4 analysis mismatch")
    return report


def run_prospective_all_mock(
    *, root: Path, config: dict, run_dir: Path
) -> dict:
    """Engineering convenience; real E4 must use separate explicit stages."""
    run_prospective_past(
        root=root, config=config, candidate="mock", run_dir=run_dir
    )
    freeze_prospective_policies(
        root=root, config=config, candidate="mock", run_dir=run_dir
    )
    return run_prospective_future(
        root=root, config=config, candidate="mock", run_dir=run_dir
    )


__all__ = [
    "freeze_prospective_policies",
    "run_prospective_all_mock",
    "run_prospective_future",
    "run_prospective_past",
    "validate_prospective_config",
    "validate_prospective_past",
    "validate_prospective_report",
]
