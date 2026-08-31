import copy
import json
from pathlib import Path

import pytest

from hibermem.evaluation.factorial_audit import compare_bundles, decoding_counts, read_validated_bundle, reference_pair_summary
from hibermem.experiments.exact_mechanism import validate_config

ROOT = Path(__file__).resolve().parents[1]


def test_roundoff_is_not_a_correct_interaction_sign():
    summary = reference_pair_summary([({"sii": 5.55e-17}, {"sii": .5}),
                                      ({"sii": -.1}, {"sii": .5}),
                                      ({"sii": .2}, {"sii": .5})])
    assert summary["sign_matches_reference"] == 1
    assert summary["numerically_zero"] == 1
    assert reference_pair_summary([])["mean"] is None


def test_decode64_changes_only_generation_cap_and_preserves_requests():
    original = json.loads((ROOT / "configs/experiments/exact_mechanism_e3_core.json").read_text())
    longer = json.loads((ROOT / "configs/experiments/exact_mechanism_e3_decode64.json").read_text())
    assert original["generation"]["max_new_tokens"] == 16
    assert longer["generation"]["max_new_tokens"] == 64
    original_suite, longer_suite = validate_config(original), validate_config(longer)
    assert original_suite.manifest() == longer_suite.manifest()
    assert original_suite.manifest()["planned_conditions"] == 16384
    original["generation"]["max_new_tokens"] = 64
    assert original == longer
    for a, b in zip(original_suite.conditions(), longer_suite.conditions(), strict=True):
        assert a["case_id"] == b["case_id"]
        assert a["messages"] == b["messages"]
        assert a["supported"] == b["supported"]


def test_decoding_counts_do_not_equate_all_errors_with_truncation():
    rows = [dict(output_tokens=16, parse_null=True, strict_format=False),
            dict(output_tokens=16, parse_null=False, strict_format=False),
            dict(output_tokens=8, parse_null=True, strict_format=False),
            dict(output_tokens=8, parse_null=False, strict_format=True)]
    result = decoding_counts(rows, 16)
    assert result["at_generation_limit"] == result["parse_null"] == 2
    assert result["parse_null_at_limit"] == 1
    assert result["at_limit_rate"] == .5
    assert decoding_counts([], 16)["at_limit_rate"] is None


def bundles():
    # Minimal already-validated inputs exercise the pure comparison independently
    # of the file validator; no model is downloaded or initialized.
    report = {"engineering_only": False, "identity": {
        "candidate": "qwen", "backend": {"model_id": "test"}, "suite_sha256": "s",
        "prompt_template_sha256": "p"}, "analysis": {"games": [{"bank_id": "b", "family": "and2"}]}}
    def row(i, tokens, raw, reward, support):
        return {"case_id": str(i), "bank_id": "b", "request_sha256": str(i),
                "messages": [{"role": "user", "content": str(i)}], "output_tokens": len(tokens),
                "raw_output": raw, "reward": float(reward), "supported": support,
                "generation_trace": {"input_token_ids": [10 + i], "generated_token_ids": tokens,
                                     "rendered_prompt": str(i)}}
    old = [row(0, [1, 2], "partial", 0, True), row(1, [9], "UNKNOWN", 0, False)]
    new = [row(0, [1, 2, 3], "DS123", 1, True), row(1, [9], "UNKNOWN", 0, False)]
    short = (report, old, {"generation": {"max_new_tokens": 2, "do_sample": False}},
             {"python": "same", "packages": {"torch": "same"}, "source_tree_sha256": "old"})
    long = (copy.deepcopy(report), new, {"generation": {"max_new_tokens": 4, "do_sample": False}},
            {"python": "same", "packages": {"torch": "same"}, "source_tree_sha256": "new"})
    return short, long


def test_paired_budget_comparison_requires_actual_prefix_agreement():
    short, long = bundles()
    result = compare_bundles(short, long)
    assert result["matched_decode_only_evidence"] is True
    assert result["family_changes"]["and2"]["capped_wrong_to_correct"] == 1
    assert result["family_changes"]["and2"]["supported_correct_delta"] == .5
    assert result["qualified"] is None and result["test_access"] is False
    long[1][0]["generation_trace"]["generated_token_ids"][0] = 5
    result = compare_bundles(short, long)
    assert result["matched_decode_only_evidence"] is False
    assert result["prefix_mismatches"] == ["0"]


@pytest.mark.parametrize("change", ["runtime", "input", "early_stop", "mock"])
def test_comparison_does_not_hide_other_changes(change):
    short, long = bundles()
    if change == "runtime":
        long[3]["packages"]["torch"] = "different"
    elif change == "input":
        long[1][0]["generation_trace"]["input_token_ids"] = [777]
    elif change == "early_stop":
        long[1][1]["generation_trace"]["generated_token_ids"] = [9, 10]
    else:
        short[0]["engineering_only"] = long[0]["engineering_only"] = True
    result = compare_bundles(short, long)
    assert result["matched_decode_only_evidence"] is False


@pytest.mark.parametrize("change", ["config", "cap", "prompt", "suite", "missing", "duplicate", "empty", "mixed_evidence"])
def test_unmatched_comparison_rejected(change):
    short, long = bundles()
    if change == "config":
        long[2]["other_change"] = 1
    elif change == "cap":
        long[2]["generation"]["max_new_tokens"] = 2
    elif change == "prompt":
        long[1][0]["messages"][0]["content"] = "different"
    elif change == "suite":
        long[0]["identity"]["suite_sha256"] = "different"
    elif change == "missing":
        long[1].pop()
    elif change == "duplicate":
        long[1].append(long[1][0])
    elif change == "empty":
        short[1].clear()
        long[1].clear()
    else:
        long[0]["engineering_only"] = True
    with pytest.raises(ValueError):
        compare_bundles(short, long)


def test_file_audit_cannot_bypass_independent_validation(tmp_path, monkeypatch):
    import hibermem.experiments.exact_mechanism as runner
    def reject(*args, **kwargs):
        raise ValueError("corrupt artifact")
    monkeypatch.setattr(runner, "validate_mechanism_report", reject)
    with pytest.raises(ValueError, match="corrupt artifact"):
        read_validated_bundle(tmp_path / "report.json")


def test_audit_output_refuses_overwrite(tmp_path, monkeypatch):
    import scripts.analyze_factorial_report as cli
    output = tmp_path / "preserve.json"
    output.write_text("existing audit")
    monkeypatch.setattr(cli, "read_validated_bundle", lambda *a, **k: ({}, [], {}, {}))
    monkeypatch.setattr(cli, "summarize_bundle", lambda *a: {"test": True})
    monkeypatch.setattr("sys.argv", ["audit", "--report", "unused", "--output", str(output)])
    assert cli.main() == 2
    assert output.read_text() == "existing audit"
