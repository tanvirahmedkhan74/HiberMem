from dataclasses import replace

import numpy as np
import pytest

from hibermem.backends import MockBackend
from hibermem.coalition.cache import EvaluationCache
from hibermem.coalition.sampling import size_balanced_masks
from hibermem.environments.controlled import QuerySplit, generate_phase2_dataset
from hibermem.experiments.phase2 import CoalitionEvaluator, fit_discovery_bank, _p2a_gate


def test_cached_results_cannot_cross_split_capabilities(tmp_path):
    dataset = generate_phase2_dataset(1)
    validation = dataset.view(QuerySplit.VALIDATION)
    discovery = dataset.view(QuerySplit.DISCOVERY)
    bank, query = dataset.banks[0], validation.queries[0]
    with EvaluationCache(tmp_path / "cache.db") as cache:
        evaluator = CoalitionEvaluator(backend=MockBackend(), cache=cache,
            generation_config={"do_sample": False}, seed=1, code_commit="test")
        evaluator.evaluate(bank, query, validation, (True,) * 8)
        with pytest.raises(PermissionError):
            evaluator.evaluate(bank, query, discovery, (True,) * 8)
        with pytest.raises(PermissionError):
            evaluator.evaluate(bank, replace(query, text="forged"), validation, (True,) * 8)


def test_cache_invalidates_changed_content_and_backend(tmp_path):
    class Backend(MockBackend):
        dtype = "float16"

        def provenance(self):
            return {**super().provenance(), "dtype": self.dtype}

    dataset = generate_phase2_dataset(1)
    bank, view = dataset.banks[0], dataset.view(QuerySplit.DISCOVERY)
    backend = Backend()
    with EvaluationCache(tmp_path / "cache.db") as cache:
        def evaluator():
            return CoalitionEvaluator(backend=backend, cache=cache,
                generation_config={"do_sample": False}, seed=1, code_commit="same")
        first = evaluator()
        first.evaluate(bank, view.queries[0], view, (True,) * 8)
        first.evaluate(bank, view.queries[0], view, (True,) * 8)
        assert first.cache_hits == 1
        changed = replace(bank, memories=(replace(bank.memories[0], text=bank.memories[0].text + " Changed."), *bank.memories[1:]))
        first.evaluate(changed, view.queries[0], view, (True,) * 8)
        assert first.cache_misses == 2
        backend.dtype = "float32"
        second = evaluator()
        second.evaluate(bank, view.queries[0], view, (True,) * 8)
        assert second.cache_misses == 1


def test_null_game_cannot_pass_interaction_stability():
    class ZeroEvaluator:
        def reward_matrix(self, bank, queries, view, masks):
            return np.zeros((len(masks), len(queries)))

    dataset = generate_phase2_dataset(1)
    result = fit_discovery_bank(bank=dataset.banks[0], view=dataset.view(QuerySplit.DISCOVERY),
        masks=size_balanced_masks(8, 64, 11), evaluator=ZeroEvaluator(),
        bootstrap_resamples=10, bootstrap_seed=13, top_k=4)
    assert result["stability"]["eligible_pair_count"] == 0
    assert result["top_pairs"] == []
    assert not _p2a_gate([result], {"mean_top_k_overlap_min": .75,
        "mean_overlap_margin_min": .5, "mean_sign_consistency_min": .9})["passed"]


def test_additive_game_cannot_pass_nonzero_interaction_check():
    class AdditiveEvaluator:
        def reward_matrix(self, bank, queries, view, masks):
            return np.repeat(np.array([sum(m) / 8 for m in masks])[:, None], len(queries), axis=1)

    dataset = generate_phase2_dataset(1)
    result = fit_discovery_bank(bank=dataset.banks[0], view=dataset.view(QuerySplit.DISCOVERY),
        masks=size_balanced_masks(8, 64, 11), evaluator=AdditiveEvaluator(),
        bootstrap_resamples=10, bootstrap_seed=13, top_k=4)
    assert result["stability"]["eligible_pair_count"] == 0


def test_public_manifest_does_not_export_test_queries():
    dataset = generate_phase2_dataset(1)
    assert {q["split"] for q in dataset.public_manifest()["queries"]} == {"discovery", "validation"}
    assert any(q["split"] == "test" for q in dataset.public_manifest(include_test=True)["queries"])


def test_changed_scientific_run_is_rejected_before_model_loading(tmp_path, monkeypatch):
    import json
    import hibermem.experiments.phase2 as phase

    (tmp_path / "report.json").write_text(json.dumps({"config_sha256": "old"}))
    monkeypatch.setattr(phase, "_validate_config", lambda *_: None)
    monkeypatch.setattr(phase, "make_backend", lambda *_: pytest.fail("model loaded"))
    with pytest.raises(RuntimeError, match="preserve the old run"):
        phase.create_phase2_run(root=tmp_path, config={"scientific_gate_eligible": True},
            config_path=tmp_path / "config.json", run_dir=tmp_path)
