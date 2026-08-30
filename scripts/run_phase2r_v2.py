"""Run one pinned model on the v2 development-only counterfactual screen.

Exit 0: capability screen qualified (not Gate P2); 1: completed negative screen;
2: invalid configuration, failed control, provenance mismatch, or runtime error.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from hibermem.coalition.cache import EvaluationCache
from hibermem.environments.controlled.calibration import CALIBRATION_VERSION, generate_calibration_v2
from hibermem.environments.controlled.prompts import prompt_template_hash
from hibermem.evaluation.calibration import calibration_row as _row, control_results
from hibermem.evaluation.qualification import summarize_v2
from hibermem.experiments.phase2 import (
    CoalitionEvaluator, _atomic_json, _json_hash, _source_tree_sha256,
    git_provenance, make_backend, runtime_provenance,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs/experiments/phase2r_v2_screen.json"


def run_v2(*, root: Path, config: dict, candidate_name: str, run_dir: Path,
           controls_only: bool = False) -> dict:
    if config.get("protocol") != CALIBRATION_VERSION or config.get("scientific_gate_eligible") is not False:
        raise ValueError("v2 requires its versioned, development-only config")
    if config.get("generation", {}).get("do_sample") is not False:
        raise ValueError("v2 requires deterministic generation")
    if candidate_name not in config["candidates"] and candidate_name != "mock":
        raise ValueError("candidate is not in the preregistered development matrix")
    backend_config = ({"type": "mock"} if candidate_name == "mock" else config["candidates"][candidate_name])
    if candidate_name != "mock":
        if (backend_config.get("type") != "hf_local" or
                re.fullmatch(r"[0-9a-f]{40}", str(backend_config.get("model_revision", ""))) is None):
            raise ValueError("real screening requires a pinned local HF backend")
    git = git_provenance(root)
    if not controls_only and candidate_name != "mock" and (not git["available"] or git["source_dirty"]):
        raise RuntimeError("commit the implementation/config before real-model screening")
    suite = generate_calibration_v2(**config["calibration"])
    identity = {
        "protocol": CALIBRATION_VERSION, "config_sha256": _json_hash(config),
        "suite_sha256": suite.sha256(), "candidate": candidate_name, "backend": backend_config,
        "source_tree_sha256": _source_tree_sha256(root), "git_commit": git["commit"],
        "prompt_template_sha256": prompt_template_hash(), "controls_only": controls_only,
    }
    identity_path = run_dir / "identity.json"
    if identity_path.exists() and json.loads(identity_path.read_text()) != identity:
        raise RuntimeError("run identity changed; use a new run directory (old results are immutable)")
    if run_dir.exists() and any(run_dir.iterdir()) and not identity_path.exists():
        raise RuntimeError("refusing to reuse a nonempty run directory without its identity")
    run_dir.mkdir(parents=True, exist_ok=True)
    _atomic_json(identity_path, identity)
    _atomic_json(run_dir / "config.json", config)
    _atomic_json(run_dir / "manifest.json", suite.manifest())
    controls = control_results(suite, config["qualification_thresholds"])
    _atomic_json(run_dir / "controls.json", controls)
    report = {
        "schema_version": 2, "phase": "2-R", "protocol": CALIBRATION_VERSION,
        "scope": "development-only qualification; no confirmation or test capability",
        "scientific_gate_eligible": False, "confirmation_compatible": False,
        "selected_candidate": None, "identity": identity, "git": git,
        "status": "controls_complete" if controls_only else "running", "qualified": False,
        "planned_condition_records": len(suite.cases),
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "next_step": "review development evidence; exact-coalition mechanism feasibility still required",
    }
    _atomic_json(run_dir / "report.json", report)
    if controls_only:
        return report
    backend = None
    try:
        backend = make_backend(backend_config)
        runtime = runtime_provenance(root, backend)
        runtime_path = run_dir / "runtime.json"
        # Freeze all runtime metadata that can affect numerical generation.
        stable_runtime = {key: runtime[key] for key in ("python", "packages", "gpu", "backend", "source_tree_sha256")}
        if runtime_path.exists() and json.loads(runtime_path.read_text()) != stable_runtime:
            raise RuntimeError("runtime changed; use a new run directory")
        _atomic_json(runtime_path, stable_runtime)
        rows = []
        with EvaluationCache(run_dir / "evaluations.sqlite3") as cache:
            evaluator = CoalitionEvaluator(backend=backend, cache=cache,
                generation_config=config["generation"], seed=int(config["seed"]),
                code_commit=str(identity["git_commit"]) + ":" + str(identity["source_tree_sha256"]))
            for index, case in enumerate(suite.cases):
                view = suite.dataset.view(case.query.split)
                result = evaluator.evaluate(suite.dataset.bank(case.query.bank_id), case.query, view, case.mask)
                rows.append(_row(case, view, result.raw_output, result.parsed_action))
                if (index + 1) % 216 == 0:
                    print(f"{candidate_name}: {case.base_bank_id} complete ({index + 1}/{len(suite.cases)} conditions)", flush=True)
            report["cache"] = {"rows": cache.count(), "hits": evaluator.cache_hits, "misses": evaluator.cache_misses}
        _atomic_json(run_dir / "evaluations.json", rows)
        report.update(summarize_v2(rows, config["qualification_thresholds"]))
        report["status"] = "complete"
        report["engineering_only"] = candidate_name == "mock"
        report["artifacts_sha256"] = {name: hashlib.sha256((run_dir / name).read_bytes()).hexdigest()
                                      for name in ("evaluations.json", "manifest.json", "config.json", "controls.json", "runtime.json", "identity.json")}
    except Exception as error:
        report["status"] = "runtime_error"
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        report["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
        _atomic_json(run_dir / "report.json", report)
        del backend
        gc.collect()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--candidate", choices=("qwen", "phi", "mock"), required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--controls-only", action="store_true")
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else ROOT / args.config
    run_dir = args.run_dir if args.run_dir.is_absolute() else ROOT / args.run_dir
    try:
        report = run_v2(root=ROOT, config=json.loads(config_path.read_text()),
                        candidate_name=args.candidate, run_dir=run_dir, controls_only=args.controls_only)
    except Exception as error:
        print(f"Phase 2-R v2 stopped: {type(error).__name__}: {error}")
        return 2
    print(f"Development report: {run_dir / 'report.json'}")
    print("Test remains locked. This screen cannot authorize confirmation or Phase 3.")
    if args.controls_only:
        print("Symbolic and shortcut controls: PASS (no LLM inference)")
        return 0
    print("Development qualification: " + ("PASS" if report["qualified"] else "FAIL"))
    return 0 if report["qualified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
