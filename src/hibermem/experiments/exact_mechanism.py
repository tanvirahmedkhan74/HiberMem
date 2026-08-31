"""Resumable, evidence-checked development diagnostics; no qualification capability."""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from hibermem.backends import HFLocalBackend, MockBackend
from hibermem.coalition.masks import mask_to_index
from hibermem.environments.controlled.mechanism import PROTOCOL, generate_mechanism_suite
from hibermem.environments.controlled.prompts import prompt_template_hash
from hibermem.evaluation.mechanism import summarize_mechanism
from hibermem.evaluation.scoring import parse_action
from .phase2 import _atomic_json, _json_hash, _source_tree_sha256, git_provenance, make_backend, runtime_provenance

CAPABILITIES = {"scientific_gate_eligible": False, "confirmation_compatible": False,
                "selected_candidate": None, "qualified": None, "test_access": False}
ARTIFACTS = ("config.json", "manifest.json", "identity.json", "runtime.json", "controls.json", "evaluations.json")


def validate_config(config):
    expected_keys = {"schema_version", "protocol", "scientific_gate_eligible", "confirmation_compatible",
                     "calibration", "variants", "generation", "keep_counts", "random_seeds", "candidates"}
    if set(config) != expected_keys or config["schema_version"] != 1 or config["protocol"] != PROTOCOL:
        raise ValueError("exact mechanism requires its explicit versioned config fields")
    if config["scientific_gate_eligible"] is not False or config["confirmation_compatible"] is not False:
        raise ValueError("development diagnostics cannot enable scientific/confirmation capability")
    if set(config["calibration"]) != {"n_banks", "bank_start", "seed"}:
        raise ValueError("unexpected calibration setting")
    generation = config["generation"]
    if set(generation) != {"do_sample", "max_new_tokens"} or generation["do_sample"] is not False:
        raise ValueError("only stateless deterministic generation is supported")
    if type(generation["max_new_tokens"]) is not int or not 1 <= generation["max_new_tokens"] <= 128:
        raise ValueError("max_new_tokens must be an integer in [1,128]")
    for key, lower, upper in (("keep_counts", 1, 7), ("random_seeds", 0, 2**32 - 1)):
        values = config[key]
        if (not isinstance(values, list) or not values or
                any(type(value) is not int or not lower <= value <= upper for value in values)
                or len(set(values)) != len(values)):
            raise ValueError(f"invalid {key}")
    if len(config["random_seeds"]) > 100:
        raise ValueError("at most 100 development baseline seeds")
    if not isinstance(config["candidates"], dict) or not config["candidates"]:
        raise ValueError("pinned candidate matrix is required")
    for name, backend in config["candidates"].items():
        if name not in ("qwen", "phi") or backend.get("type") != "hf_local":
            raise ValueError("only the audited Qwen/Phi causal-LM backend is supported; no external adapter")
        if re.fullmatch(r"[0-9a-f]{40}", str(backend.get("model_revision", ""))) is None:
            raise ValueError("pin a full model revision")
        if backend.get("trust_remote_code") is not False or backend.get("quantization") != "none":
            raise ValueError("remote code and quantization are outside this diagnostic version")
    return generate_mechanism_suite(**config["calibration"], variants=config["variants"])


def symbolic_controls(suite):
    oracle = MockBackend()
    checked, query_outputs = 0, {}
    for case in suite.conditions():
        raw = oracle.generate(case["messages"]).text
        parsed = parse_action(raw, case["query"].options)
        reward = case["view"].score(case["query"], parsed)
        if reward != float(case["supported"]) or (not case["supported"] and parsed != "UNKNOWN"):
            raise ValueError("symbolic control failed; inference is forbidden")
        checked += 1
        index = mask_to_index(case["mask"])
        i, j = suite.required_pairs[case["query"].query_id]
        if index in (0, 1 << i, 1 << j, (1 << i) | (1 << j)):
            retained = sorted((m for m, present in zip(case["bank"].memories, case["mask"]) if present),
                              key=lambda memory: memory.position,
                              reverse=suite.game_metadata[case["bank"].bank_id]["variant"] == "reverse_records")
            labels = re.findall(r"DS[0-9]+", " ".join(m.text for m in retained))
            copied = labels[0] if labels else "UNKNOWN"
            query_outputs.setdefault(case["query"].query_id, {})[index] = (
                case["view"].score(case["query"], copied),
                case["view"].score(case["query"], case["query"].options[0]))
    for query_id, table in query_outputs.items():
        i, j = suite.required_pairs[query_id]
        pair = (1 << i) | (1 << j)
        for column in (0, 1):
            contrast = table[pair][column] - table[1 << i][column] - table[1 << j][column] + table[0][column]
            if contrast != 0:
                raise ValueError("shortcut control must have zero local pair contrast")
    return {"symbolic_complete_game_checks": checked, "symbolic_expected_local_interaction": 1.0,
            "destination_copy_expected_local_interaction": 0.0,
            "constant_option_expected_local_interaction": 0.0,
            "passed": True, "scope": "engineering controls, not model qualification"}


def _validate_trace(trace, raw, input_tokens, output_tokens, engineering):
    if engineering and trace is None:
        return
    if not isinstance(trace, dict):
        raise ValueError("real inference requires a captured generation trace")
    required = {"rendered_prompt", "rendered_prompt_sha256", "input_token_ids", "generated_token_ids",
                "decoded_with_special_tokens", "decoded_without_special_tokens", "text_transform"}
    if set(trace) != required:
        raise ValueError("incomplete generation trace")
    if not all(isinstance(trace[key], str) for key in required - {"input_token_ids", "generated_token_ids"}):
        raise ValueError("invalid trace text")
    if hashlib.sha256(trace["rendered_prompt"].encode()).hexdigest() != trace["rendered_prompt_sha256"]:
        raise ValueError("rendered prompt hash mismatch")
    for key, count in (("input_token_ids", input_tokens), ("generated_token_ids", output_tokens)):
        if not isinstance(trace[key], list) or len(trace[key]) != count or any(type(i) is not int or i < 0 for i in trace[key]):
            raise ValueError("token trace/count mismatch")
    if trace["text_transform"] != "decode_skip_special_tokens_then_strip" or trace["decoded_without_special_tokens"].strip() != raw:
        raise ValueError("text transformation mismatch")


def evidence_row(case, *, raw, trace, input_tokens, output_tokens, latency_seconds, engineering):
    if not isinstance(raw, str) or not isinstance(latency_seconds, (float, int)) or not 0 <= latency_seconds < float("inf"):
        raise ValueError("invalid generation output or latency")
    if any(type(count) is not int or count < 0 for count in (input_tokens, output_tokens)):
        raise ValueError("nonnegative token counts required")
    _validate_trace(trace, raw, input_tokens, output_tokens, engineering)
    query, view = case["query"], case["view"]
    view.authorize(query)
    parsed = parse_action(raw, query.options)
    return {
        "case_id": case["case_id"], "query_id": query.query_id, "bank_id": query.bank_id,
        "split": query.split.value, "mask_index": mask_to_index(case["mask"]),
        "messages": case["messages"], "request_sha256": _json_hash(case["messages"]),
        "supported": case["supported"], "raw_output": raw,
        "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "parsed_action": parsed, "reward": view.score(query, parsed),
        "abstained": parsed == "UNKNOWN", "parse_null": parsed is None,
        "unsupported_assertion": not case["supported"] and parsed not in (None, "UNKNOWN"),
        "strict_format": parsed is not None and raw.strip() == parsed,
        "input_tokens": input_tokens, "output_tokens": output_tokens,
        "latency_seconds": latency_seconds, "generation_trace": trace,
    }


def validate_row(row, case, engineering):
    recomputed = evidence_row(case, raw=row["raw_output"], trace=row["generation_trace"],
                              input_tokens=row["input_tokens"], output_tokens=row["output_tokens"],
                              latency_seconds=row["latency_seconds"], engineering=engineering)
    if row != recomputed:
        raise ValueError(f"evidence mismatch: {case['case_id']}")
    if not engineering and any(message["content"] not in row["generation_trace"]["rendered_prompt"]
                               for message in case["messages"]):
        raise ValueError("rendered prompt does not contain the authorized messages")


def _analysis_equal(left, right):
    """Permit numerical roundoff across LAPACK builds, never changed masks/fields."""
    if type(left) is not type(right):
        return False
    if isinstance(right, float):
        return math.isfinite(left) and math.isclose(left, right, rel_tol=1e-8, abs_tol=1e-9)
    if isinstance(right, dict):
        return left.keys() == right.keys() and all(_analysis_equal(left[k], right[k]) for k in right)
    if isinstance(right, list):
        return len(left) == len(right) and all(_analysis_equal(a, b) for a, b in zip(left, right))
    return left == right


def _file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_mechanism_report(path: Path, *, allow_mock=False):
    report, directory = _read(path), path.parent
    if report.get("protocol") != PROTOCOL or report.get("status") != "complete":
        raise ValueError("a complete exact-mechanism report is required")
    if any(type(report.get(key, "missing")) is not type(value) or report[key] != value
           for key, value in CAPABILITIES.items()):
        raise ValueError("invalid capability claim")
    if type(report.get("engineering_only")) is not bool:
        raise ValueError("engineering evidence label required")
    if report["engineering_only"] and not allow_mock:
        raise ValueError("mock evidence requires --allow-mock")
    for name in ARTIFACTS:
        if report.get("artifacts_sha256", {}).get(name) != _file_hash(directory / name):
            raise ValueError(f"artifact hash mismatch: {name}")
    config, identity = _read(directory / "config.json"), _read(directory / "identity.json")
    suite = validate_config(config)
    if report["identity"] != identity or identity["config_sha256"] != _json_hash(config):
        raise ValueError("config/run identity mismatch")
    if identity["prompt_template_sha256"] != prompt_template_hash():
        raise ValueError("prompt template mismatch; use the archived source version")
    if _read(directory / "manifest.json") != suite.manifest() or identity["suite_sha256"] != _json_hash(suite.manifest()):
        raise ValueError("suite identity mismatch")
    candidate = identity["candidate"]
    if report["engineering_only"] != (candidate == "mock"):
        raise ValueError("candidate evidence label mismatch")
    backend = {"type": "mock"} if candidate == "mock" else config["candidates"][candidate]
    if identity["backend"] != backend or identity["protocol"] != PROTOCOL:
        raise ValueError("backend identity mismatch")
    runtime = _read(directory / "runtime.json")
    if runtime["source_tree_sha256"] != identity["source_tree_sha256"]:
        raise ValueError("runtime/source identity mismatch")
    if candidate != "mock":
        if runtime["backend"].get("backend") != "HFLocalBackend":
            raise ValueError("unrecognized runtime adapter")
        for key in ("model_id", "model_revision", "quantization", "device", "dtype"):
            if runtime["backend"].get(key) != backend[key]:
                raise ValueError(f"runtime backend mismatch: {key}")
        for key in ("chat_template_sha256", "resolved_parameter_dtypes", "resolved_parameter_devices"):
            if not runtime["backend"].get(key):
                raise ValueError(f"missing runtime provenance: {key}")
        if not report["git"]["available"] or report["git"]["source_dirty"] or report["git"]["commit"] != identity["git_commit"]:
            raise ValueError("real evidence requires clean source identity")
    rows = _read(directory / "evaluations.json")
    conditions = list(suite.conditions())
    if len(rows) != len(conditions) or report["planned_conditions"] != len(conditions):
        raise ValueError("incomplete condition table")
    for row, case in zip(rows, conditions, strict=True):
        validate_row(row, case, report["engineering_only"])
    if _read(directory / "controls.json") != symbolic_controls(suite):
        raise ValueError("control mismatch")
    analysis = summarize_mechanism(rows, suite, config)
    if not _analysis_equal(report["analysis"], analysis):
        raise ValueError("analysis mismatch")
    return report


def run_mechanism(*, root: Path, config: dict, candidate: str, run_dir: Path):
    suite = validate_config(config)
    if candidate not in config["candidates"] and candidate != "mock":
        raise ValueError("candidate is not in the frozen matrix")
    backend_config = {"type": "mock"} if candidate == "mock" else config["candidates"][candidate]
    git = git_provenance(root)
    if candidate != "mock" and (not git["available"] or git["source_dirty"]):
        raise RuntimeError("commit source/config before real inference")
    identity = {"protocol": PROTOCOL, "candidate": candidate, "backend": backend_config,
                "config_sha256": _json_hash(config), "suite_sha256": _json_hash(suite.manifest()),
                "source_tree_sha256": _source_tree_sha256(root), "git_commit": git["commit"],
                "prompt_template_sha256": prompt_template_hash()}
    identity_path = run_dir / "identity.json"
    if identity_path.exists() and _read(identity_path) != identity:
        raise RuntimeError("run identity changed; preserve old artifacts and use a new directory")
    if run_dir.exists() and any(run_dir.iterdir()) and not identity_path.exists():
        raise RuntimeError("refusing nonempty run directory without identity")
    report_path = run_dir / "report.json"
    if report_path.exists() and _read(report_path).get("status") == "complete":
        return validate_mechanism_report(report_path, allow_mock=candidate == "mock")
    controls = symbolic_controls(suite)  # Fails before loading any real model.
    run_dir.mkdir(parents=True, exist_ok=True)
    for name, value in (("identity.json", identity), ("config.json", config),
                        ("manifest.json", suite.manifest()), ("controls.json", controls)):
        target = run_dir / name
        if target.exists() and _read(target) != value:
            raise ValueError(f"resume artifact mismatch: {name}")
        if not target.exists():
            _atomic_json(target, value)
    previous = _read(report_path) if report_path.exists() else {}
    report = {"schema_version": 1, "protocol": PROTOCOL, **CAPABILITIES,
              "engineering_only": candidate == "mock", "scope": "development diagnostics only; no qualification",
              "identity": identity, "git": git, "status": "running",
              "planned_conditions": suite.manifest()["planned_conditions"],
              "started_at_utc": previous.get("started_at_utc", datetime.now(timezone.utc).isoformat())}
    _atomic_json(report_path, report)
    backend = None
    try:
        backend = make_backend(backend_config)
        if candidate != "mock" and type(backend) is not HFLocalBackend:
            raise ValueError("external backend adapters are not supported")
        runtime = runtime_provenance(root, backend)
        runtime = {key: runtime[key] for key in ("python", "packages", "gpu", "backend", "source_tree_sha256")}
        runtime_path = run_dir / "runtime.json"
        if runtime_path.exists() and _read(runtime_path) != runtime:
            raise RuntimeError("runtime changed; use a new run directory")
        if not runtime_path.exists():
            _atomic_json(runtime_path, runtime)
        checkpoint = run_dir / "conditions"
        checkpoint.mkdir(exist_ok=True)
        expected_files = {f"{index:06d}.json" for index in range(report["planned_conditions"])}
        if any(path.name not in expected_files for path in checkpoint.iterdir()):
            raise ValueError("unexpected checkpoint files; preserve run and inspect before resuming")
        rows, reused = [], 0
        for index, case in enumerate(suite.conditions()):
            path = checkpoint / f"{index:06d}.json"
            if path.exists():
                row = _read(path)
                validate_row(row, case, candidate == "mock")
                reused += 1
            else:
                case["view"].authorize(case["query"])
                start = time.perf_counter()
                generated = backend.generate(case["messages"], **config["generation"], seed=config["calibration"]["seed"])
                row = evidence_row(case, raw=generated.text, trace=generated.trace,
                                   input_tokens=generated.input_tokens, output_tokens=generated.output_tokens,
                                   latency_seconds=time.perf_counter() - start, engineering=candidate == "mock")
                _atomic_json(path, row)
            rows.append(row)
            if (index + 1) % 256 == 0:
                print(f"{candidate}: {index + 1}/{report['planned_conditions']} conditions complete", flush=True)
        _atomic_json(run_dir / "evaluations.json", rows)
        report["analysis"] = summarize_mechanism(rows, suite, config)
        report["checkpoint_reused"] = reused
        report["generation_calls_this_attempt"] = len(rows) - reused
        report["artifacts_sha256"] = {name: _file_hash(run_dir / name) for name in ARTIFACTS}
        report["status"] = "complete"
    except Exception as error:
        report["status"] = "runtime_error"
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        report["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
        _atomic_json(report_path, report)
        del backend
    return validate_mechanism_report(report_path, allow_mock=candidate == "mock")
