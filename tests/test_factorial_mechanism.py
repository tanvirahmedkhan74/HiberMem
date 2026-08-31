import copy
import hashlib
import json
import shutil
from dataclasses import replace
from itertools import combinations
from pathlib import Path

import pytest

from hibermem.coalition.masks import iter_masks, mask_to_index
from hibermem.environments.controlled.dataset import QuerySplit
from hibermem.environments.controlled.factorial import (
    FactorialOracle, PROTOCOL, supported_by,
)
from hibermem.evaluation.factorial import exact_pair_details, outcome_breakdown, summarize_factorial
from hibermem.experiments.exact_mechanism import (
    evidence_row, run_mechanism, symbolic_controls, validate_config, validate_mechanism_report,
)
from hibermem.interactions.mobius import mobius_transform

ROOT = Path(__file__).resolve().parents[1]


def configuration(*, families=None, variants=None):
    config = json.loads((ROOT / "configs/experiments/exact_mechanism_e3_core.json").read_text())
    config["calibration"]["n_banks"] = 1
    config["families"] = families or ["and3"]
    config["variants"] = variants or ["original"]
    return config


def symbolic_rows(suite):
    backend = FactorialOracle()
    return [evidence_row(case, raw=backend.generate(case["messages"]).text, trace=None,
                         input_tokens=0, output_tokens=1, latency_seconds=0., engineering=True)
            for case in suite.conditions()]


@pytest.fixture(scope="module")
def completed(tmp_path_factory):
    directory = tmp_path_factory.mktemp("factorial-complete")
    run_mechanism(root=ROOT, config=configuration(), candidate="mock", run_dir=directory)
    return directory


def test_factorial_counts_scope_and_prompt_controls():
    for name, count in (("core", 16384), ("presentation", 49152)):
        config = json.loads((ROOT / f"configs/experiments/exact_mechanism_e3_{name}.json").read_text())
        suite = validate_config(config)
        assert suite.manifest()["planned_conditions"] == count
        assert suite.manifest()["independent_base_banks"] == 2
        assert symbolic_controls(suite)["symbolic_complete_game_checks"] == count
        assert {q.split for q in suite.dataset.queries} == {QuerySplit.DISCOVERY}
        assert not suite.dataset.view(QuerySplit.TEST).queries
        assert not suite.dataset.view(QuerySplit.VALIDATION).queries
        assert all("answer" not in q for q in suite.manifest()["queries"])
    suite = validate_config(configuration())
    case = next(suite.conditions())
    assert [m["role"] for m in case["messages"]] == ["system", "user"]
    with pytest.raises(PermissionError):
        case["view"].score(replace(case["query"], split=QuerySplit.TEST), "UNKNOWN")


@pytest.mark.parametrize("start", [300, 320, 339, 360, 400])
def test_reserved_banks_rejected(start):
    config = configuration()
    config["calibration"]["bank_start"] = start
    with pytest.raises(ValueError, match="development banks"):
        validate_config(config)


@pytest.mark.parametrize("key,value", [
    ("worlds", ["base"]), ("overlap_levels", ["high"]), ("families", ["temporal"]),
    ("variants", ["reverse_records"]), ("variants", ["original", "conversation_history"]),
    ("confirmation_compatible", True), ("test_access", True), ("schema_version", True),
])
def test_unimplemented_or_unsafe_designs_rejected(key, value):
    config = configuration()
    config[key] = value
    with pytest.raises(ValueError):
        validate_config(config)


@pytest.mark.parametrize("family,expected_sii", [("direct", 0), ("and2", 1), ("or2", -1), ("and3", .5)])
def test_exact_analytic_references_and_nulls(family, expected_sii):
    suite = validate_config(configuration(families=[family]))
    query = suite.dataset.queries[0]
    minimal = suite.minimal_supports[query.query_id]
    table = [float(supported_by(mask, minimal)) for mask in iter_masks(8)]
    details = exact_pair_details(table)
    active = set().union(*map(set, minimal))
    for pair in details["pairs"]:
        expected = expected_sii if set(pair["players"]) <= active else 0
        assert pair["sii"] == pytest.approx(expected)
        assert pair["context_weighted_sii"] == pytest.approx(expected)
    coefficients = mobius_transform(table)
    if family == "and3":
        assert all(coefficients[(1 << i) | (1 << j)] == 0 for i, j in combinations(active, 2))
        assert coefficients[sum(1 << i for i in active)] == 1
    if family in ("and2", "and3"):
        assert details["submodularity_violating_contexts"] > 0
    else:
        assert details["submodularity_violating_contexts"] == 0
    assert details["negative_single_item_marginals"] == 0


def test_or_support_is_disjunction_and_independent_text_oracle():
    suite = validate_config(configuration(families=["or2"]))
    query = suite.dataset.queries[0]
    minimal = suite.minimal_supports[query.query_id]
    assert len(minimal) == 2 and all(len(s) == 1 for s in minimal)
    for singleton in minimal:
        index = 1 << singleton[0]
        case = next(c for c in suite.conditions() if c["query"].query_id == query.query_id
                    and mask_to_index(c["mask"]) == index)
        assert case["supported"]
        generated = FactorialOracle().generate(case["messages"])
        assert case["view"].score(query, generated.text) == 1
        altered = copy.deepcopy(case["messages"])
        altered[1]["content"] = altered[1]["content"].replace("Link RQ", "Link RZ")
        assert FactorialOracle().generate(altered).text == "UNKNOWN"


def test_paired_world_options_positions_support_and_overlap():
    suite = validate_config(configuration(families=["direct", "and2", "or2", "and3"],
                                         variants=["original", "reverse_records", "reverse_options"]))
    view = suite.dataset.view(QuerySplit.DISCOVERY)
    lookup = {(m["base_bank_id"], m["family"], m["overlap"], m["world"], m["variant"], m["chain"]): q
              for q in suite.dataset.queries for m in [suite.query_metadata[q.query_id]]}
    for key, q in lookup.items():
        base, family, overlap, world, variant, chain = key
        source = lookup[(base, family, "low", "base", "original", chain)]
        assert q.text == source.text
        assert suite.minimal_supports[q.query_id] == suite.minimal_supports[source.query_id]
        assert q.options == (source.options[::-1] if variant == "reverse_options" else source.options)
        answer = next(o for o in q.options if view.score(q, o))
        old_answer = next(o for o in source.options if view.score(source, o))
        assert (answer != old_answer) == (world == "counterfactual")
        bank = suite.dataset.bank(q.bank_id)
        assert [m.position for m in bank.memories] == list(range(8))
        if overlap == "high":
            low = lookup[(base, family, "low", world, variant, chain)]
            assert suite.game_metadata[q.bank_id]["mean_record_token_jaccard"] > suite.game_metadata[low.bank_id]["mean_record_token_jaccard"]
    full = {c["query"].query_id: c for c in suite.conditions() if all(c["mask"])}
    for key, q in lookup.items():
        if key[4] != "reverse_records":
            continue
        source = lookup[(*key[:4], "original", key[5])]
        lines = lambda query: full[query.query_id]["messages"][1]["content"].partition("\n\nTask: ")[0].splitlines()[1:]
        assert lines(q) == lines(source)[::-1]


def test_support_is_secondary_and_breakdown_handles_empty_denominators():
    rows = [dict(reward=1., supported=False, abstained=False, unsupported_assertion=True, parse_null=False)]
    result = outcome_breakdown(rows)
    assert result["accuracy"] == result["unsupported_correct"] == 1
    assert result["supported_correct"] == 0 and result["supported_accuracy"] is None
    rows[0]["supported"] = True
    rows[0]["unsupported_assertion"] = False
    result = outcome_breakdown(rows)
    assert result["unsupported_abstention"] is None
    assert result["accuracy"] == result["supported_correct"] + result["unsupported_correct"]


def test_full_report_independent_validation_and_cubic(completed):
    report = validate_mechanism_report(completed / "report.json", allow_mock=True)
    assert report["protocol"] == PROTOCOL
    assert report["qualified"] is None and report["test_access"] is False
    assert report["analysis"]["future_queries_evaluated"] == 0
    for game in report["analysis"]["games"]:
        assert game["reconstruction_max_error"] == 0
        assert game["surrogate_fits"]["3"]["prediction_metrics_in_sample"]["rmse"] < 1e-12
        assert game["surrogate_fits"]["2"]["prediction_metrics_in_sample"]["rmse"] > .01
        assert {s["policy"] for s in game["retention_in_sample"]} >= {"exact_shapley", "budget_marginal", "quadratic", "cubic"}
        for s in game["retention_in_sample"]:
            assert s["outcomes"]["unsupported_correct"] == 0
            assert s["accuracy_in_sample"] == s["outcomes"]["accuracy"] == s["outcomes"]["supported_correct"]
    assert all(r["supported_both_worlds_correct"] == 1 for r in report["analysis"]["paired_counterfactuals"])
    assert all(r["identical_prompt_output_agreement"] == 1 for r in report["analysis"]["paired_counterfactuals"])
    with pytest.raises(ValueError, match="mock"):
        validate_mechanism_report(completed / "report.json")


def test_frozen_transfer_not_target_refit_and_ties_reproducible():
    config = configuration(families=["direct"], variants=["original", "reverse_records"])
    suite = validate_config(config)
    rows = symbolic_rows(suite)
    # Deliberately change target outcomes; source selections must stay frozen.
    for row in rows:
        if row["bank_id"].endswith("reverse_records"):
            row["reward"] = float(bool(row["mask_index"] & 1))
    analysis = summarize_factorial(rows, suite, config)
    games = {g["bank_id"]: g for g in analysis["games"]}
    for transfer in analysis["paired_presentation"]:
        source = games[transfer["source_bank_id"]]
        for s, frozen in zip(source["retention_in_sample"], transfer["frozen_selection_transfer"], strict=True):
            assert frozen["mask_index"] == s["mask_index"]
            assert frozen["target_outcomes"]["accuracy"] == float(bool(s["mask_index"] & 1))
        assert "presentation" in transfer["scope"]
    assert any(t["n_tied_masks"] > 1 for g in analysis["games"] for t in g["randomized_tie_sensitivity"])
    # Flipping support annotations cannot change operational scores/selections.
    changed = copy.deepcopy(rows)
    for row in changed:
        row["supported"] = not row["supported"]
    alternate = summarize_factorial(changed, suite, config)
    for left, right in zip(analysis["games"], alternate["games"], strict=True):
        assert [(s["policy"], s["mask_index"]) for s in left["retention_in_sample"]] == [(s["policy"], s["mask_index"]) for s in right["retention_in_sample"]]
        assert [(s["seed"], s["mask_index"]) for s in left["randomized_tie_sensitivity"]] == [(s["seed"], s["mask_index"]) for s in right["randomized_tie_sensitivity"]]


@pytest.mark.parametrize("mutation", ["support", "reward", "protocol", "analysis", "capability"])
def test_rehashed_corruption_rejected(completed, tmp_path, mutation):
    directory = tmp_path / mutation
    shutil.copytree(completed, directory, ignore=shutil.ignore_patterns("conditions"))
    report_path = directory / "report.json"
    report = json.loads(report_path.read_text())
    if mutation in ("support", "reward"):
        path = directory / "evaluations.json"
        rows = json.loads(path.read_text())
        rows[0]["supported" if mutation == "support" else "reward"] = True if mutation == "support" else 1.
        path.write_text(json.dumps(rows))
        report["artifacts_sha256"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    elif mutation == "protocol":
        report["protocol"] = "phase2r-exact-mechanism-v1"
    elif mutation == "analysis":
        report["analysis"]["games"][0]["retention_in_sample"][0]["outcomes"]["supported_correct"] = .99
    else:
        report["test_access"] = True
    report_path.write_text(json.dumps(report))
    with pytest.raises(ValueError):
        validate_mechanism_report(report_path, allow_mock=True)


def test_completed_resume_preserves_report_and_loads_no_model(completed, monkeypatch):
    # Validation legitimately runs prompt-reading symbolic controls, not a real model.
    monkeypatch.setattr("hibermem.experiments.exact_mechanism.make_backend", lambda *_: pytest.fail("model loaded"))
    before = (completed / "report.json").read_bytes()
    run_mechanism(root=ROOT, config=configuration(), candidate="mock", run_dir=completed)
    assert (completed / "report.json").read_bytes() == before
    config = configuration()
    config["generation"]["max_new_tokens"] = 17
    with pytest.raises(RuntimeError, match="identity changed"):
        run_mechanism(root=ROOT, config=config, candidate="mock", run_dir=completed)


def test_interrupted_e3_resume_revalidates_and_reuses(tmp_path, monkeypatch):
    import hibermem.experiments.exact_mechanism as runner
    original = runner.evidence_row
    calls = 0

    def interrupt_once(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 10:
            raise RuntimeError("simulated E3 interruption")
        return original(*args, **kwargs)

    monkeypatch.setattr(runner, "evidence_row", interrupt_once)
    directory = tmp_path / "partial"
    with pytest.raises(RuntimeError, match="simulated E3"):
        run_mechanism(root=ROOT, config=configuration(), candidate="mock", run_dir=directory)
    assert len(list((directory / "conditions").glob("*.json"))) == 9
    report = run_mechanism(root=ROOT, config=configuration(), candidate="mock", run_dir=directory)
    assert report["checkpoint_reused"] == 9
    assert report["generation_calls_this_attempt"] == 2039


def test_real_run_rejects_dirty_source_before_model(tmp_path, monkeypatch):
    monkeypatch.setattr("hibermem.experiments.exact_mechanism.git_provenance", lambda _: {
        "available": True, "source_dirty": True, "commit": "a" * 40})
    monkeypatch.setattr("hibermem.experiments.exact_mechanism.make_backend", lambda *_: pytest.fail("model loaded"))
    with pytest.raises(RuntimeError, match="commit"):
        run_mechanism(root=ROOT, config=configuration(), candidate="qwen", run_dir=tmp_path / "real")


def test_e3_cannot_enter_confirmation(completed, tmp_path):
    from scripts.freeze_phase2r_confirmation import freeze_config
    with pytest.raises((RuntimeError, ValueError)):
        freeze_config(screen_report_path=completed / "report.json", base_config_path=tmp_path / "missing",
                      output_path=tmp_path / "not-authorized.json")
    assert not (tmp_path / "not-authorized.json").exists()


def test_kaggle_e3_uses_existing_safe_bootstrap():
    launcher = (ROOT / "kaggle/run_exact_mechanism.sh").read_text()
    assert "e3_core|e3_presentation" in launcher
    assert "--without-pip --system-site-packages" in launcher
    assert "E3a freezes Qwen only" in launcher
    assert "STAGE=\"tests\"" in launcher
    assert "scripts/validate_exact_mechanism.py" in launcher
