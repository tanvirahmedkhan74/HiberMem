"""Run staged Phase 2 discovery, validation, test unlock, and test evaluation."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from hibermem.experiments import create_phase2_run, run_phase2_test, unlock_phase2_test


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "experiments" / "phase2_mock.json"
PHASE1_REPORT = ROOT / "results" / "phase1_report.json"
PHASE1_CERTIFICATE = ROOT / "configs" / "gates" / "phase1_pass.json"
LATEST_REPORT = ROOT / "results" / "phase2_report.json"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=("discovery-validation", "unlock", "test", "smoke"),
        default="discovery-validation",
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-dir", type=Path)
    return parser


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _require_phase1() -> None:
    source = PHASE1_REPORT if PHASE1_REPORT.exists() else PHASE1_CERTIFICATE
    if not source.exists():
        raise SystemExit("Phase 1 report/certificate is missing; Phase 2 is gated")
    report = json.loads(source.read_text(encoding="utf-8"))
    if (
        report.get("phase") != 1
        or report.get("gate") != "P1"
        or not report.get("gate_passed")
    ):
        raise SystemExit("Gate P1 has not passed; refusing to run Phase 2")


def _latest(report_path: Path) -> None:
    LATEST_REPORT.parent.mkdir(parents=True, exist_ok=True)
    temporary = LATEST_REPORT.with_suffix(".json.tmp")
    shutil.copyfile(report_path, temporary)
    temporary.replace(LATEST_REPORT)


def main() -> int:
    args = _parser().parse_args()
    _require_phase1()
    config_path = _resolve(args.config)
    if not config_path.exists():
        raise SystemExit(f"config does not exist: {config_path}")
    config = json.loads(config_path.read_text(encoding="utf-8"))

    if args.run_dir is None:
        if args.stage in {"unlock", "test"}:
            raise SystemExit("--run-dir is required for unlock and test stages")
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        run_dir = ROOT / "results" / "phase2" / run_id
    else:
        run_dir = _resolve(args.run_dir)

    if args.stage in {"discovery-validation", "smoke"}:
        if args.stage == "smoke" and (
            config["backend"]["type"] != "mock" or config["scientific_gate_eligible"]
        ):
            raise SystemExit("smoke stage requires a non-scientific MockBackend config")
        report = create_phase2_run(
            root=ROOT,
            config=config,
            config_path=config_path,
            run_dir=run_dir,
        )
        print(f"Discovery/validation report: {run_dir / 'report.json'}")
        print(
            "Validation test-unlock readiness: "
            + ("PASS" if report["validation"]["ready_for_test_unlock"] else "FAIL")
        )
        if args.stage == "discovery-validation":
            _latest(run_dir / "report.json")
            if report["validation"]["ready_for_test_unlock"]:
                print(f"Resume with --stage unlock --run-dir {run_dir}")
                return 0
            print("Test remains locked; do not run the unlock or test stage")
            return 1

    if args.stage in {"unlock", "smoke"}:
        unlock = unlock_phase2_test(run_dir=run_dir)
        print(f"Test split unlocked at {unlock['unlocked_at_utc']}")
        if args.stage == "unlock":
            print(f"Continue with --stage test --run-dir {run_dir}")
            return 0

    report = run_phase2_test(root=ROOT, run_dir=run_dir)
    _latest(run_dir / "report.json")
    print(f"Phase 2 report: {run_dir / 'report.json'}")
    if report["scientific_gate_eligible"]:
        print("Gate P2: " + ("PASS" if report["gate_p2"] else "FAIL"))
        return 0 if report["gate_p2"] else 1
    print("Gate P2: NOT EVALUATED (mock smoke run)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
