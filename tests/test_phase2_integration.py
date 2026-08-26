from hibermem.backends import MockBackend
from hibermem.coalition.cache import EvaluationCache
from hibermem.coalition.sampling import size_balanced_masks
from hibermem.environments.controlled import QuerySplit, generate_phase2_dataset
from hibermem.experiments.phase2 import CoalitionEvaluator, fit_discovery_bank


def test_mock_coalition_experiment_recovers_stable_pairs(tmp_path) -> None:
    dataset = generate_phase2_dataset(1)
    bank = dataset.banks[0]
    view = dataset.view(QuerySplit.DISCOVERY)
    masks = size_balanced_masks(8, 64, seed=11)
    with EvaluationCache(tmp_path / "cache.sqlite3") as cache:
        evaluator = CoalitionEvaluator(
            backend=MockBackend(),
            cache=cache,
            generation_config={"do_sample": False, "max_new_tokens": 8},
            seed=7,
            code_commit=None,
        )
        result = fit_discovery_bank(
            bank=bank,
            view=view,
            masks=masks,
            evaluator=evaluator,
            bootstrap_resamples=10,
            bootstrap_seed=13,
            top_k=4,
        )

    assert result["design_rank"] == 37
    assert result["stability"]["split_half_top_k_overlap"] == 1.0
    assert {tuple(pair) for pair in result["top_pairs"]} == {
        (0, 1),
        (2, 3),
        (4, 5),
        (6, 7),
    }
