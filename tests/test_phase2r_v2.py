import json
from pathlib import Path

import pytest

from hibermem.environments.controlled import QuerySplit
from hibermem.environments.controlled.calibration import generate_calibration_v2, validate_counterfactual_pairs
from scripts.run_phase2r_v2 import control_results, run_v2
from scripts.validate_phase2r_v2_report import validate_report
from scripts.freeze_phase2r_confirmation import freeze_config

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def config():
    config = json.loads((ROOT / "configs/experiments/phase2r_v2_screen.json").read_text())
    config["calibration"]["n_banks"] = 2
    return config


def test_v2_has_no_test_queries_or_confirmation_banks():
    suite = generate_calibration_v2(2)
    assert len(suite.cases) == 432
    assert len({case.case_id for case in suite.cases}) == 432
    assert not suite.dataset.view(QuerySplit.TEST).queries
    assert {q.split for q in suite.dataset.queries} == {QuerySplit.DISCOVERY, QuerySplit.VALIDATION}
    validate_counterfactual_pairs(suite)
    assert suite.sha256() == generate_calibration_v2(2).sha256()
    for start, count in ((299, 1), (400, 1), (399, 2)):
        with pytest.raises(ValueError, match="confirmation"):
            generate_calibration_v2(count, bank_start=start)


def test_control_oracle_passes_and_shortcuts_fail(config):
    controls = control_results(generate_calibration_v2(**config["calibration"]), config["qualification_thresholds"])
    assert controls["symbolic_oracle"]["qualified"]
    assert not controls["destination_copy"]["qualified"]
    assert not controls["first_option"]["qualified"]
    assert controls["destination_copy"]["missing_link_conditions"]["missing_first_minimal"]["accidental_correct_rate"] == 1


def test_mock_screen_resume_identity_and_evidence_validation(tmp_path, config):
    directory = tmp_path / "screen"
    first = run_v2(root=ROOT, config=config, candidate_name="mock", run_dir=directory)
    assert first["qualified"] and first["engineering_only"]
    assert first["cache"]["rows"] == 336
    assert first["selected_candidate"] is None
    second = run_v2(root=ROOT, config=config, candidate_name="mock", run_dir=directory)
    assert second["cache"]["misses"] == 0
    assert validate_report(directory / "report.json", allow_mock=True)["qualified"]
    with pytest.raises(ValueError, match="mock"):
        validate_report(directory / "report.json")
    config["generation"]["max_new_tokens"] = 17
    with pytest.raises(RuntimeError, match="identity changed"):
        run_v2(root=ROOT, config=config, candidate_name="mock", run_dir=directory)
    evidence = directory / "evaluations.json"
    evidence.write_text("[]")
    with pytest.raises(ValueError, match="hash mismatch"):
        validate_report(directory / "report.json", allow_mock=True)


def test_real_screen_requires_clean_committed_source(tmp_path, config):
    with pytest.raises(RuntimeError, match="commit"):
        run_v2(root=tmp_path, config=config, candidate_name="qwen", run_dir=tmp_path / "screen")


def test_control_only_does_not_instantiate_real_backend(tmp_path, config, monkeypatch):
    monkeypatch.setattr("scripts.run_phase2r_v2.make_backend", lambda *_: pytest.fail("model loaded"))
    report = run_v2(root=tmp_path, config=config, candidate_name="qwen", run_dir=tmp_path / "controls", controls_only=True)
    assert report["status"] == "controls_complete"


def test_v2_capability_pass_cannot_freeze_confirmation(tmp_path, monkeypatch):
    report = tmp_path / "report.json"
    report.write_text('{"schema_version":2}')
    monkeypatch.setattr("hibermem.evaluation.artifacts.validate_report", lambda _: {"qualified": True})
    with pytest.raises(RuntimeError, match="not interaction-feasibility"):
        freeze_config(screen_report_path=report, base_config_path=tmp_path / "unused", output_path=tmp_path / "out")
    assert not (tmp_path / "out").exists()
