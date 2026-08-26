import math

import pytest

from hibermem.coalition.sampling import size_balanced_masks
from hibermem.environments.synthetic import PolynomialGame, observe_coalitions, SyntheticGameSpec
from hibermem.interactions.polynomial import PolynomialInteractionEstimator


def test_sampled_polynomial_estimator_exactly_recovers_sparse_game() -> None:
    truth = {(): 0.3, (0,): 1.2, (3,): -0.7, (0, 2): 2.5, (1, 3, 5): -3.2}
    game = PolynomialGame(6, truth)
    masks = size_balanced_masks(6, 60, seed=11)
    values = tuple(game.value(player for player, present in enumerate(mask) if present) for mask in masks)
    estimator = PolynomialInteractionEstimator(max_order=3, n_players=6).fit(masks, values)
    for term in estimator.terms:
        assert estimator.coefficients[term] == pytest.approx(truth.get(term, 0.0), abs=1e-10)
    assert estimator.predict(masks) == pytest.approx(values, abs=1e-10)
    assert estimator.rank == len(estimator.terms)


def test_estimator_reports_finite_uncertainty_for_noisy_overdetermined_fit() -> None:
    game = PolynomialGame(6, {(): 0.0, (0,): 1.0, (1, 2): 2.0, (3, 4, 5): -3.0})
    spec = SyntheticGameSpec("noise", "noisy_reward", 17, game, 0.1)
    masks = size_balanced_masks(6, 60, seed=19)
    values = observe_coalitions(spec, masks, observation_seed=23)
    estimator = PolynomialInteractionEstimator(max_order=3, n_players=6).fit(masks, values)
    assert estimator.degrees_of_freedom == 18
    assert estimator.condition_number > 1.0
    assert all(math.isfinite(value) and value >= 0 for value in estimator.standard_errors.values())
    assert any(value > 0 for value in estimator.standard_errors.values())


def test_estimator_rejects_insufficient_design() -> None:
    masks = size_balanced_masks(5, 10, seed=1)
    with pytest.raises(ValueError, match="at least"):
        PolynomialInteractionEstimator(max_order=2, n_players=5).fit(masks, [0.0] * len(masks))
