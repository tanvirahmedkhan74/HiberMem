import copy
import json
from pathlib import Path

import pytest

from hibermem.environments.controlled.grounding import (
    DEVELOPMENT_ARMS,
    VERIFICATION_ARMS,
    GroundingOracle,
    generate_grounding_suite,
    parse_grounding_action,
    symbolic_grounding_controls,
)
from hibermem.evaluation.grounding import summarize_grounding
from hibermem.experiments.grounding import (
    _grounding_row,
    build_verification_config,
    run_grounding,
    validate_grounding_config,
    validate_grounding_report,
)


ROOT = Path(__file__).resolve().parents[1]


def _config() -> dict:
    return json.loads(
        (ROOT / "configs/experiments/e3d_grounding_development.json").read_text()
    )


def _small_suite():
    config = _config()
    return generate_grounding_suite(
        stage="development",
        base_bank_seeds=[360],
        seed=config["cohort"]["seed"],
        families=config["families"],
        overlap_levels=config["overlap_levels"],
        worlds=config["worlds"],
        ledger_modes=config["ledger_modes"],
        arms=config["arms"],
    )


def _oracle_rows(suite, config):
    oracle = GroundingOracle()
    rows = []
    for case in suite.conditions():
        generated = oracle.generate(case["messages"])
        rows.append(
            _grounding_row(
                case,
                generated=generated,
                latency=0.0,
                engineering=True,
                token_budget=config["generation"]["max_new_tokens"],
            )
        )
    return rows


def test_e3d_manifest_matches_preregistered_budget_and_capabilities() -> None:
    suite = validate_grounding_config(_config())
    manifest = suite.manifest()
    assert manifest["planned_conditions"] == 1_728
    assert manifest["conditions_per_base_bank_per_arm"] == 288
    assert manifest["independent_base_banks"] == 2
    assert manifest["arms"] == list(DEVELOPMENT_ARMS)
    assert manifest["future_queries_evaluated"] == 0
    assert manifest["historical_test_access"] is False
    assert manifest["structured_verifier_e4_eligible"] is False
    launcher = (ROOT / "kaggle/run_e3d_grounding.sh").read_text()
    assert 'HIBERMEM_MIN_FREE_STORAGE_GIB:-15' in launcher
    assert "run_e4" not in launcher


def test_e3d_generation_is_deterministic_and_world_answers_are_isolated() -> None:
    first = _small_suite()
    second = _small_suite()
    assert first.manifest() == second.manifest()
    grouped = {}
    for query in first.dataset.queries:
        meta = first.query_metadata[query.query_id]
        key = (
            meta["base_bank_seed"],
            meta["family"],
            meta["overlap"],
            meta["query_role"],
            meta["ledger_mode"],
        )
        grouped.setdefault(key, {})[meta["world"]] = (query, meta)
    assert grouped
    for worlds in grouped.values():
        base_query, base = worlds["base"]
        counter_query, counter = worlds["counterfactual"]
        assert base["target_start"] == counter["target_start"]
        assert base["target_destination"] != counter["target_destination"]
        assert counter["stale_base_destination"] == base["target_destination"]
        assert set(base_query.options) == set(counter_query.options)


def test_e3d_panels_support_truth_payload_and_prompt_parsers() -> None:
    suite = _small_suite()
    controls = symbolic_grounding_controls(suite)
    assert controls["passed"]
    assert controls["conditions_by_arm"] == {
        "current_v1": 288,
        "query_anchored_v1": 288,
        "structured_verifier_v1": 288,
    }
    assert controls["single_dual_payload_matched"]
    assert controls["prompt_parser_round_trip"]
    for case in suite.conditions():
        support = set(suite.minimal_supports[case["query"].query_id])
        present = {index for index, value in enumerate(case["mask"]) if value}
        assert case["supported"] == support.issubset(present)


def test_e3d_oracle_summary_passes_without_unlocking_science() -> None:
    config = _config()
    suite = _small_suite()
    summary = summarize_grounding(_oracle_rows(suite, config), suite, config)
    assert summary["query_anchored_passed"]
    assert summary["verification_config_eligible"] is None
    assert summary["e4_design_eligible"] is None
    assert summary["automatic_selection"] is None
    assert summary["future_queries_evaluated"] == 0
    assert summary["historical_test_access"] is False
    for readiness in summary["readiness"].values():
        assert readiness["passed"]
        assert not readiness["failed_checks"]
    assert summary["readiness"]["structured_verifier_v1"][
        "structured_verifier_e4_eligible"
    ] is False


def test_e3d_structured_certificate_rejects_wrong_start() -> None:
    suite = _small_suite()
    case = next(
        case
        for case in suite.conditions()
        if case["arm"] == "structured_verifier_v1"
        and case["evidence_kind"] == "full"
    )
    raw = GroundingOracle().generate(case["messages"]).text
    certificate = json.loads(raw)
    certificate["start"] = "RQ000000"
    changed = json.dumps(certificate, separators=(",", ":"))
    parsed, strict, stored = parse_grounding_action(
        changed, case["arm"], case["query"], case["messages"]
    )
    assert parsed is None
    assert strict is False
    assert stored is None


def test_e3d_config_rejects_bank_reuse_threshold_changes_and_manual_verification() -> None:
    config = _config()
    changed = copy.deepcopy(config)
    changed["cohort"]["base_bank_seeds"] = [350, 351]
    with pytest.raises(ValueError, match="reserved fresh bank"):
        validate_grounding_config(changed)
    changed = copy.deepcopy(config)
    changed["readiness"]["max_unsupported_assertion"] = 0.10
    with pytest.raises(ValueError, match="thresholds are frozen"):
        validate_grounding_config(changed)
    manual = copy.deepcopy(config)
    manual["stage"] = "verification"
    manual["cohort"]["base_bank_seeds"] = [370, 371, 372, 373]
    manual["arms"] = list(VERIFICATION_ARMS)
    manual["development_selection"] = {
        "selected_arm": "query_anchored_v1",
        "development_report_sha256": "0" * 64,
        "development_identity_sha256": "0" * 64,
        "development_config_sha256": "0" * 64,
        "prompt_sha256": "0" * 64,
    }
    with pytest.raises(ValueError, match="prompt hash"):
        validate_grounding_config(manual)


def test_e3d_mock_artifact_resumes_validates_and_cannot_freeze(tmp_path) -> None:
    config = _config()
    run_dir = tmp_path / "e3d"
    first = run_grounding(root=ROOT, config=config, candidate="mock", run_dir=run_dir)
    assert first["analysis"]["query_anchored_passed"]
    second = run_grounding(root=ROOT, config=config, candidate="mock", run_dir=run_dir)
    assert second == first
    validate_grounding_report(run_dir / "report.json", allow_mock=True)
    with pytest.raises(ValueError, match="mock E3d evidence"):
        build_verification_config(run_dir / "report.json")
    evaluations = json.loads((run_dir / "evaluations.json").read_text())
    evaluations[0]["target_destination"] = "DS000000"
    (run_dir / "evaluations.json").write_text(
        json.dumps(evaluations, indent=2, sort_keys=True) + "\n"
    )
    with pytest.raises(ValueError, match="artifact hash"):
        validate_grounding_report(run_dir / "report.json", allow_mock=True)
