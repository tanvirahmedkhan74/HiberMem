import copy
import json
from pathlib import Path

import pytest

from hibermem.coalition.masks import mask_to_index
from hibermem.coalition.sampling import size_balanced_masks
from hibermem.environments.controlled.prospective import (
    FutureQueryCapability,
    PastQueryCapability,
    generate_prospective_suite,
    symbolic_prospective_controls,
)
from hibermem.evaluation.prospective import (
    PastEvidence,
    freeze_past_policies,
    future_mask_indices,
    summarize_future,
)
from hibermem.experiments.prospective import (
    freeze_prospective_policies,
    run_prospective_past,
    run_prospective_future,
    validate_prospective_config,
)
from hibermem.retention.costs import equal_length_bank_audit


ROOT = Path(__file__).resolve().parents[1]


def _config():
    return json.loads(
        (ROOT / "configs/experiments/e4_engineering_mock.json").read_text()
    )


def _past_rows(suite):
    return [
        {
            "case_id": case["case_id"],
            "query_id": case["query"].query_id,
            "bank_id": case["bank"].bank_id,
            "split": "past",
            "mask_index": mask_to_index(case["mask"]),
            "reward": float(case["supported"]),
            # Present in stored diagnostics but intentionally stripped by PastEvidence.
            "supported": case["supported"],
        }
        for case in suite.past_conditions()
    ]


def _future_rows(suite, mask_map):
    rows = []
    for case in suite.future_conditions(mask_map):
        supported = case["supported"]
        rows.append(
            {
                "case_id": case["case_id"],
                "query_id": case["query"].query_id,
                "bank_id": case["bank"].bank_id,
                "split": "future",
                "mask_index": mask_to_index(case["mask"]),
                "family": case["family"],
                "supported": supported,
                "reward": float(supported),
                "abstained": not supported,
                "parse_null": False,
                "unsupported_assertion": False,
                "strict_format": True,
            }
        )
    return rows


def test_e4_manifest_commits_but_does_not_expose_future_content() -> None:
    suite, probe = validate_prospective_config(_config())
    public = suite.public_manifest()
    rendered = json.dumps(public)
    assert public["past_planned_conditions"] == 4096
    assert public["n_future_queries"] == 24
    assert len(probe) == 64
    assert public["future_content_exposed"] is False
    assert "Future dispatch" not in rendered
    assert "Future dispatch" in json.dumps(suite.sealed_future_manifest())
    assert set(public["future_query_commitments"][0]) == {
        "query_id",
        "commitment_sha256",
    }
    launcher = (ROOT / "kaggle/run_e4_prospective.sh").read_text()
    assert 'HIBERMEM_MIN_FREE_STORAGE_GIB:-15' in launcher


def test_e4_capabilities_are_distinct_and_future_cannot_fit() -> None:
    suite, _ = validate_prospective_config(_config())
    assert isinstance(suite.past_view(), PastQueryCapability)
    assert isinstance(suite.future_view(), FutureQueryCapability)
    rows = _past_rows(suite)
    evidence = PastEvidence.from_rows(rows, suite.past_view())
    assert len(evidence.records) == 4096
    assert all(len(record) == 4 for record in evidence.records)
    with pytest.raises(TypeError, match="PastQueryCapability"):
        PastEvidence.from_rows(rows, suite.future_view())  # type: ignore[arg-type]


def test_support_labels_do_not_change_policy_safe_evidence() -> None:
    suite, _ = validate_prospective_config(_config())
    rows = _past_rows(suite)
    changed = copy.deepcopy(rows)
    for row in changed:
        row["supported"] = not row["supported"]
    first = PastEvidence.from_rows(rows, suite.past_view())
    second = PastEvidence.from_rows(changed, suite.past_view())
    assert first == second


def test_e4_freeze_and_future_analysis_are_bank_level_and_nonqualifying() -> None:
    config = _config()
    suite, probe = validate_prospective_config(config)
    controls = symbolic_prospective_controls(suite)
    assert controls["passed"]
    assert controls["support_available_to_policy"] is False
    evidence = PastEvidence.from_rows(_past_rows(suite), suite.past_view())
    frozen = freeze_past_policies(evidence, suite, config)
    assert frozen["future_data_used"] is False
    assert frozen["support_metadata_used"] is False
    assert frozen["primary_policy"] == "quadratic"
    assert frozen["primary_item_baseline"] == "exact_shapley"
    for bank in suite.dataset.banks:
        audit = equal_length_bank_audit(bank)
        assert audit["equal_payload_bytes"]
        assert audit["equal_whitespace_tokens"]
    mask_map = future_mask_indices(frozen, probe)
    rows = _future_rows(suite, mask_map)
    analysis = summarize_future(rows, suite, config, frozen, probe)
    assert analysis["independent_base_banks"] == 2
    assert len(analysis["primary_bank_differences"]) == 2
    assert analysis["query_rows_treated_as_independent"] is False
    assert analysis["future_refit_used_for_selection"] is False
    assert analysis["decision"] is None
    assert analysis["qualified"] is None
    assert analysis["historical_test_access"] is False


def test_e4_real_config_requires_passing_e3c_freeze() -> None:
    config = _config()
    with pytest.raises(ValueError, match="cannot run real"):
        validate_prospective_config(config, real=True)
    template = json.loads(
        (ROOT / "configs/experiments/e4_design_template.json").read_text()
    )
    with pytest.raises(ValueError, match="hash mismatch|status|unknown"):
        validate_prospective_config(template, real=True)


def test_e4_future_is_denied_before_past_and_freeze(tmp_path) -> None:
    with pytest.raises((FileNotFoundError, ValueError)):
        run_prospective_future(
            root=ROOT,
            config=_config(),
            candidate="mock",
            run_dir=tmp_path / "unfrozen",
        )
    assert not (tmp_path / "unfrozen" / "sealed_future_manifest.json").exists()
    assert not (tmp_path / "unfrozen" / "future_evaluations.json").exists()


def test_e4_frozen_selection_tampering_is_fail_closed(tmp_path) -> None:
    config = _config()
    run_dir = tmp_path / "tamper"
    run_prospective_past(
        root=ROOT, config=config, candidate="mock", run_dir=run_dir
    )
    changed_config = copy.deepcopy(config)
    changed_config["analysis"]["practical_margin"] = 0.04
    with pytest.raises(ValueError, match="freeze config differs"):
        freeze_prospective_policies(
            root=ROOT,
            config=changed_config,
            candidate="mock",
            run_dir=run_dir,
        )

    past_report_path = run_dir / "past_report.json"
    past_report = json.loads(past_report_path.read_text())
    changed_report = copy.deepcopy(past_report)
    changed_report["future_rows_generated"] = 1
    past_report_path.write_text(
        json.dumps(changed_report, indent=2, sort_keys=True) + "\n"
    )
    with pytest.raises(ValueError, match="future rows"):
        freeze_prospective_policies(
            root=ROOT, config=config, candidate="mock", run_dir=run_dir
        )
    past_report_path.write_text(
        json.dumps(past_report, indent=2, sort_keys=True) + "\n"
    )

    freeze_prospective_policies(
        root=ROOT, config=config, candidate="mock", run_dir=run_dir
    )
    path = run_dir / "frozen_selections.json"
    frozen = json.loads(path.read_text())
    frozen["bank_results"][0]["selections"][0]["mask_index"] ^= 1
    path.write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n")
    with pytest.raises((RuntimeError, ValueError), match="frozen|selection"):
        freeze_prospective_policies(
            root=ROOT, config=config, candidate="mock", run_dir=run_dir
        )
    with pytest.raises((RuntimeError, ValueError), match="frozen|selection"):
        run_prospective_future(
            root=ROOT, config=config, candidate="mock", run_dir=run_dir
        )
    assert not (run_dir / "sealed_future_manifest.json").exists()
    assert not (run_dir / "future_evaluations.json").exists()
