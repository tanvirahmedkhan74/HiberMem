"""Resumable E3c output-contract diagnostics; never a scientific gate."""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from pathlib import Path

from hibermem.backends import HFLocalBackend
from hibermem.environments.controlled.contract import (
    PROTOCOL,
    FactorialOracle,
    generate_contract_suite,
    symbolic_contract_controls,
)
from hibermem.evaluation.contract import summarize_contract
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
ARTIFACTS = (
    "config.json",
    "manifest.json",
    "identity.json",
    "runtime.json",
    "controls.json",
    "evaluations.json",
)


def validate_contract_config(config: dict):
    required = {
        "schema_version",
        "protocol",
        "scientific_gate_eligible",
        "confirmation_compatible",
        "calibration",
        "families",
        "overlap_levels",
        "worlds",
        "contracts",
        "generation",
        "readiness",
        "candidates",
    }
    if set(config) != required or config.get("schema_version") != 1:
        raise ValueError("E3c requires the exact versioned config schema")
    if config.get("protocol") != PROTOCOL:
        raise ValueError("unexpected E3c protocol")
    if config["scientific_gate_eligible"] is not False or config["confirmation_compatible"] is not False:
        raise ValueError("E3c can never authorize a scientific gate")
    calibration = config["calibration"]
    if set(calibration) != {"n_banks", "bank_start", "seed"}:
        raise ValueError("invalid E3c calibration")
    if any(type(calibration[key]) is not int for key in calibration):
        raise ValueError("E3c calibration values must be integers")
    generation = config["generation"]
    if (
        set(generation) != {"do_sample", "max_new_tokens"}
        or generation["do_sample"] is not False
        or type(generation["max_new_tokens"]) is not int
        or not 1 <= generation["max_new_tokens"] <= 64
    ):
        raise ValueError("E3c requires deterministic generation with a bounded token cap")
    readiness = config["readiness"]
    if set(readiness) != {
        "min_supported_accuracy",
        "min_strict_format_rate",
        "max_generation_limit_rate",
        "max_unsupported_assertion",
    }:
        raise ValueError("invalid E3c readiness criteria")
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1
        for value in readiness.values()
    ):
        raise ValueError("E3c readiness values must be probabilities")
    if not isinstance(config["candidates"], dict) or set(config["candidates"]) != {"qwen"}:
        raise ValueError("E3c freezes the audited Qwen candidate only")
    backend = config["candidates"]["qwen"]
    if backend.get("type") != "hf_local" or re.fullmatch(
        r"[0-9a-f]{40}", str(backend.get("model_revision", ""))
    ) is None:
        raise ValueError("E3c requires a pinned HF-local Qwen revision")
    if backend.get("trust_remote_code") is not False or backend.get("quantization") != "none":
        raise ValueError("remote code and quantization are outside E3c")
    return generate_contract_suite(
        **calibration,
        families=config["families"],
        overlap_levels=config["overlap_levels"],
        worlds=config["worlds"],
        contracts=config["contracts"],
    )


def _identity(config: dict, suite, candidate: str, git: dict) -> dict:
    backend = {"type": "mock"} if candidate == "mock" else config["candidates"][candidate]
    return {
        "protocol": PROTOCOL,
        "candidate": candidate,
        "backend": backend,
        "config_sha256": _json_hash(config),
        "manifest_sha256": _json_hash(suite.manifest()),
        "contract_prompt_sha256": suite.manifest()["contract_prompt_sha256"],
        "source_tree_sha256": _source_tree_sha256(Path(__file__).resolve().parents[3]),
        "git_commit": git["commit"],
    }


def _contract_row(case, *, generated, latency: float, engineering: bool) -> dict:
    row = evidence_row(
        case,
        raw=generated.text,
        trace=generated.trace,
        input_tokens=generated.input_tokens,
        output_tokens=generated.output_tokens,
        latency_seconds=latency,
        engineering=engineering,
    )
    row["contract"] = case["contract"]
    return row


def _validate_contract_row(row: dict, case: dict, engineering: bool) -> None:
    if row.get("contract") != case["contract"]:
        raise ValueError("contract evidence label mismatch")
    base = dict(row)
    base.pop("contract")
    validate_row(base, case, engineering)


def validate_contract_report(path: Path, *, allow_mock: bool = False) -> dict:
    report, directory = _read(path), path.parent
    if report.get("protocol") != PROTOCOL or report.get("status") != "complete":
        raise ValueError("a complete E3c report is required")
    if any(report.get(key) != value for key, value in CAPABILITIES.items()):
        raise ValueError("invalid E3c capability claim")
    engineering = report.get("engineering_only")
    if type(engineering) is not bool or (engineering and not allow_mock):
        raise ValueError("mock E3c evidence requires explicit authorization")
    for name in ARTIFACTS:
        if report.get("artifacts_sha256", {}).get(name) != _file_hash(directory / name):
            raise ValueError(f"E3c artifact hash mismatch: {name}")
    config = _read(directory / "config.json")
    suite = validate_contract_config(config)
    manifest = _read(directory / "manifest.json")
    if manifest != suite.manifest():
        raise ValueError("E3c manifest mismatch")
    identity = _read(directory / "identity.json")
    if report.get("identity") != identity:
        raise ValueError("E3c identity mismatch")
    if identity["config_sha256"] != _json_hash(config) or identity["manifest_sha256"] != _json_hash(manifest):
        raise ValueError("E3c config/manifest identity mismatch")
    candidate = identity["candidate"]
    if engineering != (candidate == "mock"):
        raise ValueError("E3c mock/real label mismatch")
    expected_backend = {"type": "mock"} if engineering else config["candidates"].get(candidate)
    if identity["backend"] != expected_backend:
        raise ValueError("E3c backend identity mismatch")
    runtime = _read(directory / "runtime.json")
    if runtime["source_tree_sha256"] != identity["source_tree_sha256"]:
        raise ValueError("E3c source identity mismatch")
    if not engineering:
        if runtime["backend"].get("backend") != "HFLocalBackend":
            raise ValueError("unrecognized E3c runtime backend")
        for key in ("model_id", "model_revision", "quantization", "device", "dtype"):
            if runtime["backend"].get(key) != expected_backend[key]:
                raise ValueError(f"E3c runtime mismatch: {key}")
        if not report["git"]["available"] or report["git"]["source_dirty"]:
            raise ValueError("real E3c evidence requires committed source")
        if report["git"]["commit"] != identity["git_commit"]:
            raise ValueError("E3c Git identity mismatch")
    rows = _read(directory / "evaluations.json")
    conditions = list(suite.conditions())
    if len(rows) != len(conditions) or report["planned_conditions"] != len(conditions):
        raise ValueError("incomplete E3c condition table")
    for row, case in zip(rows, conditions, strict=True):
        _validate_contract_row(row, case, engineering)
    if _read(directory / "controls.json") != symbolic_contract_controls(suite):
        raise ValueError("E3c symbolic controls mismatch")
    analysis = summarize_contract(rows, suite, config)
    if not _analysis_equal(report["analysis"], analysis):
        raise ValueError("E3c analysis mismatch")
    return report


def run_contract(
    *, root: Path, config: dict, candidate: str, run_dir: Path
) -> dict:
    suite = validate_contract_config(config)
    if candidate not in config["candidates"] and candidate != "mock":
        raise ValueError("candidate is not in the E3c matrix")
    git = git_provenance(root)
    if candidate != "mock" and (not git["available"] or git["source_dirty"]):
        raise RuntimeError("commit E3c source/config before real inference")
    identity = _identity(config, suite, candidate, git)
    identity_path = run_dir / "identity.json"
    if identity_path.exists() and _read(identity_path) != identity:
        raise RuntimeError("E3c identity changed; use a new run directory")
    if run_dir.exists() and any(run_dir.iterdir()) and not identity_path.exists():
        raise RuntimeError("refusing a nonempty E3c directory without identity")
    report_path = run_dir / "report.json"
    if report_path.exists() and _read(report_path).get("status") == "complete":
        return validate_contract_report(report_path, allow_mock=candidate == "mock")

    controls = symbolic_contract_controls(suite)
    run_dir.mkdir(parents=True, exist_ok=True)
    for name, value in (
        ("identity.json", identity),
        ("config.json", config),
        ("manifest.json", suite.manifest()),
        ("controls.json", controls),
    ):
        target = run_dir / name
        if target.exists() and _read(target) != value:
            raise RuntimeError(f"E3c resume mismatch: {name}")
        if not target.exists():
            _atomic_json(target, value)
    previous = _read(report_path) if report_path.exists() else {}
    report = {
        "schema_version": 1,
        "protocol": PROTOCOL,
        **CAPABILITIES,
        "engineering_only": candidate == "mock",
        "scope": "development-only output-contract diagnostic",
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
        backend = FactorialOracle() if candidate == "mock" else make_backend(backend_config)
        if candidate != "mock" and type(backend) is not HFLocalBackend:
            raise ValueError("E3c supports the audited HF-local backend only")
        runtime = runtime_provenance(root, backend)
        runtime = {
            key: runtime[key]
            for key in ("python", "packages", "gpu", "backend", "source_tree_sha256")
        }
        runtime_path = run_dir / "runtime.json"
        if runtime_path.exists() and _read(runtime_path) != runtime:
            raise RuntimeError("E3c runtime changed; use a new run directory")
        if not runtime_path.exists():
            _atomic_json(runtime_path, runtime)
        checkpoint = run_dir / "conditions"
        checkpoint.mkdir(exist_ok=True)
        expected_files = {
            f"{index:06d}.json" for index in range(report["planned_conditions"])
        }
        if any(path.name not in expected_files for path in checkpoint.iterdir()):
            raise ValueError("unexpected E3c checkpoint file")
        rows, reused = [], 0
        for index, case in enumerate(suite.conditions()):
            path = checkpoint / f"{index:06d}.json"
            if path.exists():
                row = _read(path)
                _validate_contract_row(row, case, candidate == "mock")
                reused += 1
            else:
                start = time.perf_counter()
                generated = backend.generate(
                    case["messages"],
                    **config["generation"],
                    seed=config["calibration"]["seed"],
                )
                row = _contract_row(
                    case,
                    generated=generated,
                    latency=time.perf_counter() - start,
                    engineering=candidate == "mock",
                )
                _atomic_json(path, row)
            rows.append(row)
            if (index + 1) % 256 == 0:
                print(
                    f"{candidate}: {index + 1}/{report['planned_conditions']} E3c conditions complete",
                    flush=True,
                )
        _atomic_json(run_dir / "evaluations.json", rows)
        report["analysis"] = summarize_contract(rows, suite, config)
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
    return validate_contract_report(report_path, allow_mock=candidate == "mock")


__all__ = [
    "run_contract",
    "validate_contract_config",
    "validate_contract_report",
]
