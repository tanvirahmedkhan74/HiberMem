"""Recompute a completed v2 screen's evidence without loading an LLM."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from hibermem.environments.controlled.calibration import CALIBRATION_VERSION, generate_calibration_v2
from hibermem.evaluation.qualification import summarize_v2
from hibermem.evaluation import parse_action
from hibermem.experiments.phase2 import _json_hash
from .calibration import calibration_row as _row, control_results


def validate_report(path: Path, *, allow_mock: bool = False) -> dict:
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("protocol") != CALIBRATION_VERSION or report.get("status") != "complete":
        raise ValueError("a complete v2 screen report is required")
    if (report.get("scientific_gate_eligible") is not False
            or report.get("confirmation_compatible") is not False
            or report.get("selected_candidate") is not None):
        raise ValueError("capability screening cannot authorize confirmation or scientific claims")
    if report.get("engineering_only") and not allow_mock:
        raise ValueError("mock screening is not real-model evidence")
    for name in ("evaluations.json", "manifest.json", "config.json", "controls.json", "runtime.json", "identity.json"):
        actual = hashlib.sha256((path.parent / name).read_bytes()).hexdigest()
        if report.get("artifacts_sha256", {}).get(name) != actual:
            raise ValueError(f"artifact hash mismatch: {name}")
    if report["identity"] != json.loads((path.parent / "identity.json").read_text()):
        raise ValueError("run identity mismatch")
    config = json.loads((path.parent / "config.json").read_text())
    if config.get("protocol") != CALIBRATION_VERSION or config.get("scientific_gate_eligible") is not False:
        raise ValueError("invalid protocol configuration")
    if _json_hash(config) != report["identity"]["config_sha256"]:
        raise ValueError("config identity mismatch")
    suite = generate_calibration_v2(**config["calibration"])
    manifest = json.loads((path.parent / "manifest.json").read_text())
    if manifest != suite.manifest() or report["identity"]["suite_sha256"] != suite.sha256():
        raise ValueError("dataset identity mismatch")
    candidate = report["identity"]["candidate"]
    expected_backend = {"type": "mock"} if candidate == "mock" else config["candidates"][candidate]
    if expected_backend != report["identity"]["backend"]:
        raise ValueError("candidate identity mismatch")
    runtime = json.loads((path.parent / "runtime.json").read_text())
    if runtime["source_tree_sha256"] != report["identity"]["source_tree_sha256"]:
        raise ValueError("runtime source identity mismatch")
    if candidate != "mock":
        if expected_backend.get("type") != "hf_local":
            raise ValueError("real-model evidence requires HFLocalBackend")
        for field in ("model_id", "model_revision", "quantization", "dtype", "device"):
            if runtime["backend"].get(field) != expected_backend.get(field):
                raise ValueError(f"runtime backend mismatch: {field}")
    if (candidate == "mock") != bool(report.get("engineering_only")):
        raise ValueError("mock evidence labeling mismatch")
    rows = json.loads((path.parent / "evaluations.json").read_text())
    expected = {case.case_id: case for case in suite.cases}
    if len(rows) != len(expected) or {r["case_id"] for r in rows} != set(expected):
        raise ValueError("evaluation table is incomplete or duplicated")
    for row in rows:
        case = expected[row["case_id"]]
        for field in ("base_bank_id", "condition", "kind", "supported", "counterfactual_id", "world"):
            if row.get(field) != getattr(case, field):
                raise ValueError(f"case metadata mismatch: {field}")
        if row["query_id"] != case.query.query_id or row["split"] != case.query.split.value:
            raise ValueError("query identity mismatch")
        view = suite.dataset.view(case.query.split)
        raw = row.get("raw_output")
        if not isinstance(raw, str) or row != _row(case, view, raw, parse_action(raw, case.query.options)):
            raise ValueError("stored evaluation does not match its raw output and scoring rule")
        if row["reward"] != view.score(case.query, row["parsed_action"]):
            raise ValueError("stored reward does not match the scoring rule")
        if row["abstained"] != (row["parsed_action"] == "UNKNOWN"):
            raise ValueError("abstention metric mismatch")
        if row["parse_null"] != (row["parsed_action"] is None):
            raise ValueError("parse metric mismatch")
        if row["unsupported_assertion"] != (not case.supported and row["parsed_action"] not in (None, "UNKNOWN")):
            raise ValueError("unsupported assertion metric mismatch")
    computed = summarize_v2(rows, config["qualification_thresholds"])
    if any(report.get(key) != value for key, value in computed.items()):
        raise ValueError("report qualification disagrees with its evaluation table")
    if control_results(suite, config["qualification_thresholds"]) != json.loads((path.parent / "controls.json").read_text()):
        raise ValueError("control evidence mismatch")
    return computed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--allow-mock", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_report(args.report, allow_mock=args.allow_mock)
    except (ValueError, KeyError, OSError) as error:
        print(f"Artifact consistency: FAIL ({error})")
        return 2
    print("Artifact consistency: PASS")
    print("Development qualification: " + ("PASS" if result["qualified"] else "FAIL"))
    print("Confirmation and test remain gated; no artifacts were changed.")
    return 0 if result["qualified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
