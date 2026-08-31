import hashlib
import json
import shutil
from pathlib import Path

import pytest

from hibermem.backends import MockBackend
from hibermem.environments.controlled.dataset import QuerySplit
from hibermem.evaluation.mechanism import local_v2_contrasts
from hibermem.experiments.exact_mechanism import (
    run_mechanism, symbolic_controls, validate_config, validate_mechanism_report,
)

ROOT = Path(__file__).resolve().parents[1]


def configuration():
    config = json.loads((ROOT / "configs/experiments/exact_mechanism_e1.json").read_text())
    config["calibration"]["n_banks"] = 1
    return config


@pytest.fixture(scope="module")
def completed(tmp_path_factory):
    directory = tmp_path_factory.mktemp("exact-complete")
    run_mechanism(root=ROOT, config=configuration(), candidate="mock", run_dir=directory)
    return directory


def test_budgets_and_development_scope():
    for name, count in (("e1", 2048), ("e2", 6144)):
        config = json.loads((ROOT / f"configs/experiments/exact_mechanism_{name}.json").read_text())
        suite = validate_config(config)
        assert suite.manifest()["planned_conditions"] == count
        assert {q.split for q in suite.dataset.queries} == {QuerySplit.DISCOVERY}
        assert not suite.dataset.view(QuerySplit.TEST).queries
        assert not suite.dataset.view(QuerySplit.VALIDATION).queries
        assert {m["base_bank_id"] for m in suite.game_metadata.values()} == {"dev-320", "dev-321"}
        conditions = list(suite.conditions())
        assert len(conditions) == count
        assert len({c["case_id"] for c in conditions}) == count
        assert all([m["role"] for m in c["messages"]] == ["system", "user"] for c in conditions)


@pytest.mark.parametrize("field,value", [("scientific_gate_eligible", True), ("confirmation_compatible", True),
                                          ("stage", "test"), ("variants", ["original", "conversation_history"])])
def test_reject_capability_expansion(field, value):
    config = configuration()
    config[field] = value
    with pytest.raises(ValueError):
        validate_config(config)


@pytest.mark.parametrize("start", [300, 319, 340, 400])
def test_reserved_or_reused_banks_rejected(start):
    config = configuration()
    config["calibration"]["bank_start"] = start
    with pytest.raises(ValueError, match="development banks"):
        validate_config(config)


def test_presentation_preserves_logical_players_and_symbolic_game():
    config = configuration()
    config["variants"] = ["original", "reverse_records", "reverse_options"]
    suite = validate_config(config)
    assert symbolic_controls(suite)["symbolic_complete_game_checks"] == 3072
    query = suite.dataset.queries[0]
    reverse_records, reverse_options = suite.dataset.queries[1:3]
    original_bank = suite.dataset.bank(query.bank_id)
    reversed_bank = suite.dataset.bank(reverse_records.bank_id)
    assert [m.text for m in original_bank.memories] == [m.text for m in reversed_bank.memories]
    assert [m.position for m in reversed_bank.memories] == list(range(8))
    full = [c for c in suite.conditions() if all(c["mask"])]
    original_lines = full[0]["messages"][1]["content"].partition("\n\nTask: ")[0].splitlines()[1:]
    reversed_lines = full[1]["messages"][1]["content"].partition("\n\nTask: ")[0].splitlines()[1:]
    assert original_lines == list(reversed(reversed_lines))
    assert query.options == tuple(reversed(reverse_options.options))
    assert suite.required_pairs[query.query_id] == suite.required_pairs[reverse_records.query_id]


def test_mock_exact_game_and_independent_validation(completed):
    report = validate_mechanism_report(completed / "report.json", allow_mock=True)
    assert report["qualified"] is None and report["selected_candidate"] is None
    assert report["scientific_gate_eligible"] is False and report["test_access"] is False
    assert report["analysis"]["future_queries_evaluated"] == 0
    assert report["generation_calls_this_attempt"] == 1024
    game = report["analysis"]["games"][0]
    assert game["reconstruction_max_error"] == 0
    assert game["shapley_efficiency_error"] == pytest.approx(0, abs=1e-12)
    assert list(game["exact_shapley_items"].values()) == pytest.approx([.125] * 8)
    assert game["surrogate_fits"]["2"]["prediction_metrics_in_sample"]["rmse"] < 1e-12
    assert all(row["local_pair_interaction"] == row["full_context_pair_interaction"] == 1
               for row in report["analysis"]["query_pair_contrasts"])
    assert {row["actual_deletion_ratio"] for row in game["retention_in_sample"]} == {.25, .5, .625, .75}
    assert all(row["payload_bytes"] > 0 for row in game["retention_in_sample"])
    with pytest.raises(ValueError, match="mock"):
        validate_mechanism_report(completed / "report.json")


def test_completed_resume_never_loads_or_rewrites(completed, monkeypatch):
    monkeypatch.setattr("hibermem.experiments.exact_mechanism.make_backend",
                        lambda *_: pytest.fail("completed resume loaded model"))
    before = (completed / "report.json").read_bytes()
    run_mechanism(root=ROOT, config=configuration(), candidate="mock", run_dir=completed)
    assert (completed / "report.json").read_bytes() == before
    config = configuration()
    config["generation"]["max_new_tokens"] = 17
    with pytest.raises(RuntimeError, match="identity changed"):
        run_mechanism(root=ROOT, config=config, candidate="mock", run_dir=completed)


def test_partial_resume_reuses_checked_conditions(tmp_path, monkeypatch):
    class Interrupted(MockBackend):
        calls = 0

        def generate(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 10:
                raise RuntimeError("simulated interruption")
            return super().generate(*args, **kwargs)

    interrupted = Interrupted()
    monkeypatch.setattr("hibermem.experiments.exact_mechanism.make_backend", lambda _: interrupted)
    directory = tmp_path / "partial"
    with pytest.raises(RuntimeError, match="simulated"):
        run_mechanism(root=ROOT, config=configuration(), candidate="mock", run_dir=directory)
    assert len(list((directory / "conditions").glob("*.json"))) == 9
    started = json.loads((directory / "report.json").read_text())["started_at_utc"]
    report = run_mechanism(root=ROOT, config=configuration(), candidate="mock", run_dir=directory)
    assert report["checkpoint_reused"] == 9
    assert report["generation_calls_this_attempt"] == 1015
    assert report["started_at_utc"] == started


@pytest.mark.parametrize("mutation", ["reward", "request", "analysis", "capability", "mock_label"])
def test_consistently_rehashed_corruption_rejected(completed, tmp_path, mutation):
    directory = tmp_path / "tampered"
    shutil.copytree(completed, directory, ignore=shutil.ignore_patterns("conditions"))
    report_path = directory / "report.json"
    report = json.loads(report_path.read_text())
    if mutation in ("reward", "request"):
        path = directory / "evaluations.json"
        rows = json.loads(path.read_text())
        if mutation == "reward":
            rows[0]["reward"] = 1
        else:
            rows[0]["messages"][1]["content"] += " altered"
        path.write_text(json.dumps(rows))
        report["artifacts_sha256"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    elif mutation == "analysis":
        report["analysis"]["games"][0]["full_accuracy"] = .9
    elif mutation == "capability":
        report["qualified"] = True
    else:
        report["engineering_only"] = False
    report_path.write_text(json.dumps(report))
    with pytest.raises(ValueError):
        validate_mechanism_report(report_path, allow_mock=True)


def test_real_run_rejects_dirty_source_before_model(tmp_path, monkeypatch):
    monkeypatch.setattr("hibermem.experiments.exact_mechanism.git_provenance", lambda _: {
        "available": True, "source_dirty": True, "commit": "a" * 40})
    monkeypatch.setattr("hibermem.experiments.exact_mechanism.make_backend",
                        lambda *_: pytest.fail("rejected source loaded model"))
    with pytest.raises(RuntimeError, match="commit"):
        run_mechanism(root=ROOT, config=configuration(), candidate="qwen", run_dir=tmp_path / "real")
    assert not (tmp_path / "real").exists()


def test_nonempty_unidentified_directory_is_preserved(tmp_path):
    path = tmp_path / "existing"
    path.mkdir()
    (path / "keep.txt").write_text("user data")
    with pytest.raises(RuntimeError, match="nonempty"):
        run_mechanism(root=ROOT, config=configuration(), candidate="mock", run_dir=path)
    assert (path / "keep.txt").read_text() == "user data"


def test_exact_report_cannot_enter_legacy_confirmation(completed, tmp_path):
    from scripts.freeze_phase2r_confirmation import freeze_config

    with pytest.raises((RuntimeError, ValueError)):
        freeze_config(screen_report_path=completed / "report.json", base_config_path=tmp_path / "missing",
                      output_path=tmp_path / "unauthorized.json")
    assert not (tmp_path / "unauthorized.json").exists()


def test_local_contrast_reanalysis_and_missing_corner_rejection():
    rows = []
    for bank in ("a", "b"):
        for condition, reward in (("pair_only", 1), ("missing_first_minimal", 0),
                                  ("missing_second_minimal", 0), ("empty", 0)):
            rows.append({"kind": "two_hop", "condition": condition, "reward": reward,
                         "query_id": bank + "-q", "base_bank_id": bank})
    result = local_v2_contrasts(rows)
    assert result["mean"] == 1 and result["bank_bootstrap"]["lower_95"] == 1
    with pytest.raises(ValueError, match="incomplete"):
        local_v2_contrasts(rows[:-1])
