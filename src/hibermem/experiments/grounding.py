"""Resumable and independently validated E3d grounding experiments."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from hibermem.backends import HFLocalBackend
from hibermem.coalition.masks import mask_to_index
from hibermem.environments.controlled.grounding import (
    DEVELOPMENT_ARMS,
    PROTOCOL,
    VERIFICATION_ARMS,
    GroundingOracle,
    arm_prompt_hash,
    generate_grounding_suite,
    parse_grounding_action,
    symbolic_grounding_controls,
)
from hibermem.evaluation.grounding import summarize_grounding
from hibermem.experiments.exact_mechanism import (
    _analysis_equal,
    _file_hash,
    _read,
    _validate_trace,
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
    "retention_result": False,
    "historical_test_access": False,
}
ARTIFACTS = (
    "config.json",
    "manifest.json",
    "identity.json",
    "runtime.json",
    "controls.json",
    "evaluations.json",
)
READINESS_KEYS = {
    "min_supported_accuracy",
    "min_strict_format_rate",
    "max_generation_limit_rate",
    "max_unsupported_assertion",
    "min_full_accuracy",
    "min_exact_support_accuracy",
    "min_counterfactual_tracking",
    "max_stale_base_capture",
    "max_other_query_capture",
    "max_per_link_unsupported_assertion",
    "max_single_to_dual_drop",
}


def validate_grounding_config(config: dict):
    required = {
        "schema_version",
        "protocol",
        "stage",
        "scientific_gate_eligible",
        "confirmation_compatible",
        "retention_result",
        "historical_test_access",
        "cohort",
        "families",
        "overlap_levels",
        "worlds",
        "ledger_modes",
        "arms",
        "generation",
        "readiness",
        "candidates",
        "development_selection",
    }
    if set(config) != required or config.get("schema_version") != 1:
        raise ValueError("E3d requires the exact versioned config schema")
    if config.get("protocol") != PROTOCOL:
        raise ValueError("unexpected E3d protocol")
    if any(config.get(key) is not False for key in CAPABILITIES):
        raise ValueError("E3d cannot claim scientific, retention, confirmation, or test capability")
    stage = config["stage"]
    if stage not in ("development", "verification"):
        raise ValueError("invalid E3d stage")
    cohort = config["cohort"]
    if set(cohort) != {"base_bank_seeds", "seed"}:
        raise ValueError("invalid E3d cohort")
    expected_banks = [360, 361] if stage == "development" else [370, 371, 372, 373]
    expected_arms = list(DEVELOPMENT_ARMS if stage == "development" else VERIFICATION_ARMS)
    if cohort["base_bank_seeds"] != expected_banks or type(cohort["seed"]) is not int:
        raise ValueError(f"E3d {stage} requires its reserved fresh bank cohort")
    if config["arms"] != expected_arms:
        raise ValueError(f"E3d {stage} requires the frozen arm matrix")
    selection = config["development_selection"]
    if stage == "development" and selection is not None:
        raise ValueError("development cannot consume a selection artifact")
    if stage == "verification":
        if not isinstance(selection, dict) or set(selection) != {
            "selected_arm",
            "development_report_sha256",
            "development_identity_sha256",
            "development_config_sha256",
            "prompt_sha256",
        }:
            raise ValueError("verification requires an immutable development selection")
        if selection["selected_arm"] != "query_anchored_v1":
            raise ValueError("only the label-only A1 arm may enter verification")
        for key in (
            "development_report_sha256",
            "development_identity_sha256",
            "development_config_sha256",
            "prompt_sha256",
        ):
            if re.fullmatch(r"[0-9a-f]{64}", str(selection[key])) is None:
                raise ValueError(f"invalid E3d selection hash: {key}")
        if selection["prompt_sha256"] != arm_prompt_hash("query_anchored_v1"):
            raise ValueError("verification A1 prompt hash changed")
    generation = config["generation"]
    if generation != {"do_sample": False, "max_new_tokens": 64}:
        raise ValueError("E3d freezes deterministic 64-token generation")
    readiness = config["readiness"]
    if set(readiness) != READINESS_KEYS or any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not 0 <= value <= 1
        for value in readiness.values()
    ):
        raise ValueError("invalid E3d readiness thresholds")
    expected_thresholds = {
        "min_supported_accuracy": 0.95,
        "min_strict_format_rate": 0.95,
        "max_generation_limit_rate": 0.05,
        "max_unsupported_assertion": 0.05,
        "min_full_accuracy": 0.95,
        "min_exact_support_accuracy": 0.95,
        "min_counterfactual_tracking": 0.95,
        "max_stale_base_capture": 0.05,
        "max_other_query_capture": 0.05,
        "max_per_link_unsupported_assertion": 0.05,
        "max_single_to_dual_drop": 0.05,
    }
    if readiness != expected_thresholds:
        raise ValueError("E3d readiness thresholds are frozen")
    if set(config["candidates"]) != {"qwen"}:
        raise ValueError("E3d freezes the audited Qwen candidate")
    backend = config["candidates"]["qwen"]
    if backend != {
        "type": "hf_local",
        "model_id": "Qwen/Qwen3-4B-Instruct-2507",
        "model_revision": "cdbee75f17c01a7cc42f958dc650907174af0554",
        "device": "cuda",
        "dtype": "float16",
        "quantization": "none",
        "local_files_only": False,
        "trust_remote_code": False,
    }:
        raise ValueError("E3d backend identity differs from the preregistration")
    return generate_grounding_suite(
        stage=stage,
        base_bank_seeds=cohort["base_bank_seeds"],
        seed=cohort["seed"],
        families=config["families"],
        overlap_levels=config["overlap_levels"],
        worlds=config["worlds"],
        ledger_modes=config["ledger_modes"],
        arms=config["arms"],
    )


def _identity(config: dict, suite, candidate: str, git: dict) -> dict:
    backend = {"type": "mock"} if candidate == "mock" else config["candidates"][candidate]
    return {
        "protocol": PROTOCOL,
        "stage": config["stage"],
        "candidate": candidate,
        "backend": backend,
        "config_sha256": _json_hash(config),
        "manifest_sha256": _json_hash(suite.manifest()),
        "arm_prompt_sha256": suite.manifest()["arm_prompt_sha256"],
        "source_tree_sha256": _source_tree_sha256(Path(__file__).resolve().parents[3]),
        "git_commit": git["commit"],
    }


def _grounding_row(
    case: dict, *, generated, latency: float, engineering: bool, token_budget: int
) -> dict:
    raw = generated.text
    input_tokens = generated.input_tokens
    output_tokens = generated.output_tokens
    if not isinstance(raw, str) or not isinstance(latency, (int, float)) or not math.isfinite(latency) or latency < 0:
        raise ValueError("invalid E3d generation output or latency")
    if any(type(value) is not int or value < 0 for value in (input_tokens, output_tokens)):
        raise ValueError("E3d requires nonnegative token counts")
    _validate_trace(generated.trace, raw, input_tokens, output_tokens, engineering)
    query = case["query"]
    case["view"].authorize(query)
    parsed, strict, certificate = parse_grounding_action(
        raw, case["arm"], query, case["messages"]
    )
    row = {
        "case_id": case["case_id"],
        "query_id": query.query_id,
        "bank_id": query.bank_id,
        "split": query.split.value,
        "mask_index": mask_to_index(case["mask"]),
        "messages": case["messages"],
        "request_sha256": _json_hash(case["messages"]),
        "arm": case["arm"],
        "supported": case["supported"],
        "raw_output": raw,
        "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "parsed_action": parsed,
        "reward": case["view"].score(query, parsed),
        "abstained": parsed == "UNKNOWN",
        "parse_null": parsed is None,
        "unsupported_assertion": (
            not case["supported"] and parsed not in (None, "UNKNOWN")
        ),
        "strict_format": strict,
        "certificate_valid": certificate is not None,
        "certificate": certificate,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_seconds": latency,
        "finish_reason": (
            "token_limit_reached"
            if output_tokens >= token_budget
            else "ended_before_token_limit"
        ),
        "generation_trace": generated.trace,
    }
    for key in (
        "evidence_kind",
        "missing_link_position",
        "pairing_key",
        "base_bank_seed",
        "family",
        "overlap",
        "world",
        "query_role",
        "ledger_mode",
        "target_start",
        "target_destination",
        "stale_base_destination",
        "other_query_destination",
    ):
        row[key] = case[key]
    return row


def _validate_grounding_row(
    row: dict, case: dict, *, engineering: bool, token_budget: int
) -> None:
    class StoredGeneration:
        text = row["raw_output"]
        trace = row["generation_trace"]
        input_tokens = row["input_tokens"]
        output_tokens = row["output_tokens"]

    recomputed = _grounding_row(
        case,
        generated=StoredGeneration(),
        latency=row["latency_seconds"],
        engineering=engineering,
        token_budget=token_budget,
    )
    if row != recomputed:
        raise ValueError(f"E3d evidence mismatch: {case['case_id']}")
    if not engineering and any(
        message["content"] not in row["generation_trace"]["rendered_prompt"]
        for message in case["messages"]
    ):
        raise ValueError("E3d rendered prompt omitted an authorized message")


def _validate_verification_source(
    config: dict, development_report_path: Path | None
) -> None:
    if config["stage"] != "verification":
        if development_report_path is not None:
            raise ValueError("development runs cannot consume verification-source evidence")
        return
    if development_report_path is None:
        raise ValueError("E3d verification requires the bound development report")
    development = validate_grounding_report(development_report_path)
    if development["stage"] != "development" or development["engineering_only"]:
        raise ValueError("verification source must be real E3d development evidence")
    if not development["analysis"]["readiness"]["query_anchored_v1"]["passed"]:
        raise ValueError("verification source A1 did not pass every frozen check")
    directory = development_report_path.parent
    expected = config["development_selection"]
    observed = {
        "selected_arm": "query_anchored_v1",
        "development_report_sha256": _file_hash(development_report_path),
        "development_identity_sha256": _file_hash(directory / "identity.json"),
        "development_config_sha256": _json_hash(_read(directory / "config.json")),
        "prompt_sha256": arm_prompt_hash("query_anchored_v1"),
    }
    if expected != observed:
        raise ValueError("verification config is not bound to the supplied development evidence")


def validate_verification_source(
    config: dict, development_report_path: Path | None
) -> None:
    """Validate the external development capability required by verification."""
    _validate_verification_source(config, development_report_path)


def validate_grounding_report(
    path: Path,
    *,
    allow_mock: bool = False,
    development_report_path: Path | None = None,
) -> dict:
    report = _read(path)
    directory = path.parent
    if report.get("protocol") != PROTOCOL or report.get("status") != "complete":
        raise ValueError("a complete E3d report is required")
    if any(report.get(key) != value for key, value in CAPABILITIES.items()):
        raise ValueError("invalid E3d capability claim")
    engineering = report.get("engineering_only")
    if type(engineering) is not bool or (engineering and not allow_mock):
        raise ValueError("mock E3d evidence requires explicit authorization")
    for name in ARTIFACTS:
        if report.get("artifacts_sha256", {}).get(name) != _file_hash(directory / name):
            raise ValueError(f"E3d artifact hash mismatch: {name}")
    config = _read(directory / "config.json")
    suite = validate_grounding_config(config)
    _validate_verification_source(config, development_report_path)
    if report.get("stage") != config["stage"]:
        raise ValueError("E3d stage mismatch")
    manifest = _read(directory / "manifest.json")
    if manifest != suite.manifest():
        raise ValueError("E3d manifest mismatch")
    identity = _read(directory / "identity.json")
    if report.get("identity") != identity:
        raise ValueError("E3d identity mismatch")
    if identity["config_sha256"] != _json_hash(config) or identity["manifest_sha256"] != _json_hash(manifest):
        raise ValueError("E3d config/manifest identity mismatch")
    candidate = identity["candidate"]
    if engineering != (candidate == "mock"):
        raise ValueError("E3d mock/real label mismatch")
    expected_backend = {"type": "mock"} if engineering else config["candidates"].get(candidate)
    if identity["backend"] != expected_backend:
        raise ValueError("E3d backend identity mismatch")
    runtime = _read(directory / "runtime.json")
    if runtime["source_tree_sha256"] != identity["source_tree_sha256"]:
        raise ValueError("E3d source identity mismatch")
    if not engineering:
        if runtime["backend"].get("backend") != "HFLocalBackend":
            raise ValueError("unrecognized E3d runtime backend")
        for key in ("model_id", "model_revision", "quantization", "device", "dtype"):
            if runtime["backend"].get(key) != expected_backend[key]:
                raise ValueError(f"E3d runtime mismatch: {key}")
        for key in ("chat_template_sha256", "resolved_parameter_dtypes", "resolved_parameter_devices"):
            if not runtime["backend"].get(key):
                raise ValueError(f"missing E3d runtime provenance: {key}")
        if not report["git"]["available"] or report["git"]["source_dirty"]:
            raise ValueError("real E3d evidence requires committed source")
        if report["git"]["commit"] != identity["git_commit"]:
            raise ValueError("E3d Git identity mismatch")
    rows = _read(directory / "evaluations.json")
    conditions = list(suite.conditions())
    if len(rows) != len(conditions) or report["planned_conditions"] != len(conditions):
        raise ValueError("incomplete E3d condition table")
    budget = int(config["generation"]["max_new_tokens"])
    for row, case in zip(rows, conditions, strict=True):
        _validate_grounding_row(
            row, case, engineering=engineering, token_budget=budget
        )
    if _read(directory / "controls.json") != symbolic_grounding_controls(suite):
        raise ValueError("E3d symbolic controls mismatch")
    analysis = summarize_grounding(rows, suite, config)
    if not _analysis_equal(report["analysis"], analysis):
        raise ValueError("E3d analysis mismatch")
    return report


def run_grounding(
    *,
    root: Path,
    config: dict,
    candidate: str,
    run_dir: Path,
    development_report_path: Path | None = None,
) -> dict:
    suite = validate_grounding_config(config)
    _validate_verification_source(config, development_report_path)
    if candidate not in config["candidates"] and candidate != "mock":
        raise ValueError("candidate is not in the E3d matrix")
    git = git_provenance(root)
    if candidate != "mock" and (not git["available"] or git["source_dirty"]):
        raise RuntimeError("commit E3d source/config before real inference")
    identity = _identity(config, suite, candidate, git)
    identity_path = run_dir / "identity.json"
    if identity_path.exists() and _read(identity_path) != identity:
        raise RuntimeError("E3d identity changed; use a new run directory")
    if run_dir.exists() and any(run_dir.iterdir()) and not identity_path.exists():
        raise RuntimeError("refusing a nonempty E3d directory without identity")
    report_path = run_dir / "report.json"
    if report_path.exists() and _read(report_path).get("status") == "complete":
        return validate_grounding_report(
            report_path,
            allow_mock=candidate == "mock",
            development_report_path=development_report_path,
        )
    controls = symbolic_grounding_controls(suite)
    run_dir.mkdir(parents=True, exist_ok=True)
    for name, value in (
        ("identity.json", identity),
        ("config.json", config),
        ("manifest.json", suite.manifest()),
        ("controls.json", controls),
    ):
        target = run_dir / name
        if target.exists() and _read(target) != value:
            raise RuntimeError(f"E3d resume mismatch: {name}")
        if not target.exists():
            _atomic_json(target, value)
    previous = _read(report_path) if report_path.exists() else {}
    report = {
        "schema_version": 1,
        "protocol": PROTOCOL,
        "stage": config["stage"],
        **CAPABILITIES,
        "engineering_only": candidate == "mock",
        "scope": "E3d measurement-instrument qualification only",
        "identity": identity,
        "git": git,
        "status": "running",
        "planned_conditions": suite.manifest()["planned_conditions"],
        "started_at_utc": previous.get(
            "started_at_utc", datetime.now(timezone.utc).isoformat()
        ),
    }
    _atomic_json(report_path, report)
    backend = None
    try:
        backend_config = {"type": "mock"} if candidate == "mock" else config["candidates"][candidate]
        backend = GroundingOracle() if candidate == "mock" else make_backend(backend_config)
        if candidate != "mock" and type(backend) is not HFLocalBackend:
            raise ValueError("E3d supports the frozen HF-local backend only")
        runtime = runtime_provenance(root, backend)
        runtime = {
            key: runtime[key]
            for key in ("python", "packages", "gpu", "backend", "source_tree_sha256")
        }
        runtime_path = run_dir / "runtime.json"
        if runtime_path.exists() and _read(runtime_path) != runtime:
            raise RuntimeError("E3d runtime changed; use a new run directory")
        if not runtime_path.exists():
            _atomic_json(runtime_path, runtime)
        checkpoint = run_dir / "conditions"
        checkpoint.mkdir(exist_ok=True)
        expected_files = {
            f"{index:06d}.json" for index in range(report["planned_conditions"])
        }
        if any(path.name not in expected_files for path in checkpoint.iterdir()):
            raise ValueError("unexpected E3d checkpoint file")
        rows: list[dict] = []
        reused = 0
        budget = int(config["generation"]["max_new_tokens"])
        for index, case in enumerate(suite.conditions()):
            path = checkpoint / f"{index:06d}.json"
            if path.exists():
                row = _read(path)
                _validate_grounding_row(
                    row, case, engineering=candidate == "mock", token_budget=budget
                )
                reused += 1
            else:
                start = time.perf_counter()
                generated = backend.generate(
                    case["messages"],
                    **config["generation"],
                    seed=config["cohort"]["seed"],
                )
                row = _grounding_row(
                    case,
                    generated=generated,
                    latency=time.perf_counter() - start,
                    engineering=candidate == "mock",
                    token_budget=budget,
                )
                _atomic_json(path, row)
            rows.append(row)
            if (index + 1) % 288 == 0:
                print(
                    f"{candidate}: {index + 1}/{report['planned_conditions']} E3d conditions complete",
                    flush=True,
                )
        _atomic_json(run_dir / "evaluations.json", rows)
        report["analysis"] = summarize_grounding(rows, suite, config)
        report["checkpoint_reused"] = reused
        report["generation_calls_this_attempt"] = len(rows) - reused
        report["artifacts_sha256"] = {
            name: _file_hash(run_dir / name) for name in ARTIFACTS
        }
        report["status"] = "complete"
    except Exception as error:
        report["status"] = "runtime_error"
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        report["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
        _atomic_json(report_path, report)
        del backend
    return validate_grounding_report(
        report_path,
        allow_mock=candidate == "mock",
        development_report_path=development_report_path,
    )


def build_verification_config(development_report_path: Path) -> dict:
    report = validate_grounding_report(development_report_path)
    if report["stage"] != "development" or report["engineering_only"]:
        raise ValueError("verification requires a real E3d development report")
    if not report["analysis"]["readiness"]["query_anchored_v1"]["passed"]:
        raise ValueError("A1 did not pass every frozen development check")
    directory = development_report_path.parent
    development_config = _read(directory / "config.json")
    identity_path = directory / "identity.json"
    verification = copy.deepcopy(development_config)
    verification["stage"] = "verification"
    verification["cohort"]["base_bank_seeds"] = [370, 371, 372, 373]
    verification["arms"] = list(VERIFICATION_ARMS)
    verification["development_selection"] = {
        "selected_arm": "query_anchored_v1",
        "development_report_sha256": _file_hash(development_report_path),
        "development_identity_sha256": _file_hash(identity_path),
        "development_config_sha256": _json_hash(development_config),
        "prompt_sha256": arm_prompt_hash("query_anchored_v1"),
    }
    validate_grounding_config(verification)
    return verification


__all__ = [
    "build_verification_config",
    "run_grounding",
    "validate_grounding_config",
    "validate_grounding_report",
    "validate_verification_source",
]
