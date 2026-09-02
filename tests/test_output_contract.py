import copy
import json
from pathlib import Path

from hibermem.environments.controlled.contract import (
    build_contract_messages,
    generate_contract_suite,
    symbolic_contract_controls,
)
from hibermem.evaluation.contract import summarize_contract
from hibermem.experiments.contract import validate_contract_config


ROOT = Path(__file__).resolve().parents[1]


def _small_config():
    config = json.loads(
        (ROOT / "configs/experiments/e3c_output_contract.json").read_text()
    )
    config["calibration"]["n_banks"] = 1
    config["families"] = ["and2"]
    return config


def test_e3c_config_is_fresh_paired_and_development_only() -> None:
    config = json.loads(
        (ROOT / "configs/experiments/e3c_output_contract.json").read_text()
    )
    suite = validate_contract_config(config)
    manifest = suite.manifest()
    assert manifest["planned_conditions"] == 16_384
    assert manifest["independent_base_banks"] == 2
    assert manifest["scientific_gate_eligible"] is False
    assert manifest["future_queries_evaluated"] == 0
    assert config["calibration"]["bank_start"] >= 350
    launcher = (ROOT / "kaggle/run_e3c_contract.sh").read_text()
    assert 'HIBERMEM_MIN_FREE_STORAGE_GIB:-15' in launcher


def test_contract_intervention_changes_prompt_not_structural_case() -> None:
    suite = generate_contract_suite(
        n_banks=1,
        bank_start=350,
        seed=9,
        families=["and2"],
        overlap_levels=["low", "high"],
        worlds=["base", "counterfactual"],
        contracts=["current_v1", "answer_slot_v1"],
    )
    query = suite.base.dataset.queries[0]
    bank = suite.base.dataset.bank(query.bank_id)
    current = build_contract_messages(bank.memories, query, "current_v1")
    answer_slot = build_contract_messages(bank.memories, query, "answer_slot_v1")
    assert current != answer_slot
    assert "Answer (one allowed label only):" not in current[-1]["content"]
    assert answer_slot[-1]["content"].endswith("Answer (one allowed label only):")
    assert [memory.text for memory in bank.memories] == [
        memory.text for memory in suite.base.dataset.bank(query.bank_id).memories
    ]


def test_e3c_symbolic_controls_and_readiness_summary() -> None:
    config = _small_config()
    suite = validate_contract_config(config)
    controls = symbolic_contract_controls(suite)
    assert controls["passed"]
    assert controls["conditions_by_contract"] == {
        "current_v1": 2048,
        "answer_slot_v1": 2048,
    }
    rows = []
    for case in suite.conditions():
        rows.append(
            {
                "case_id": case["case_id"],
                "query_id": case["query"].query_id,
                "bank_id": case["bank"].bank_id,
                "split": "discovery",
                "mask_index": int(case["case_id"].rsplit(":", 1)[1]),
                "contract": case["contract"],
                "supported": case["supported"],
                "reward": float(case["supported"]),
                "abstained": not case["supported"],
                "parse_null": False,
                "unsupported_assertion": False,
                "strict_format": True,
                "output_tokens": 1,
            }
        )
    summary = summarize_contract(rows, suite, config)
    assert summary["passing_contracts"] == ["current_v1", "answer_slot_v1"]
    assert summary["automatic_selection"] is None
    assert summary["qualified"] is None
    assert summary["future_queries_evaluated"] == 0


def test_e3c_config_rejects_relaxed_or_scientific_mutations() -> None:
    config = _small_config()
    changed = copy.deepcopy(config)
    changed["scientific_gate_eligible"] = True
    try:
        validate_contract_config(changed)
    except ValueError:
        pass
    else:
        raise AssertionError("scientific E3c mutation was accepted")
