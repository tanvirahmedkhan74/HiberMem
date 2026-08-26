import pytest

from hibermem.coalition.sampling import size_balanced_masks
from hibermem.environments.synthetic import PolynomialGame, SyntheticGameSpec, observe_coalitions
from hibermem.interactions.polynomial import PolynomialInteractionEstimator
from hibermem.interactions.stability import residual_bootstrap_stability


def test_residual_bootstrap_is_deterministic_and_preserves_strong_signs() -> None:
    game = PolynomialGame(6, {(): 0.1, (0,): 1.0, (1, 2): 2.5, (3, 4, 5): -3.0})
    spec = SyntheticGameSpec("stable", "noisy_reward", 31, game, 0.08)
    masks = size_balanced_masks(6, 60, seed=37)
    values = observe_coalitions(spec, masks, observation_seed=41)
    estimator = PolynomialInteractionEstimator(max_order=3, n_players=6).fit(masks, values)
    first = residual_bootstrap_stability(estimator, masks, values, n_resamples=12, seed=43)
    second = residual_bootstrap_stability(estimator, masks, values, n_resamples=12, seed=43)
    assert first == second
    assert first[(1, 2)].sign_consistency == pytest.approx(1.0)
    assert first[(3, 4, 5)].sign_consistency == pytest.approx(1.0)


def test_bootstrap_rejects_too_few_resamples() -> None:
    game = PolynomialGame(3, {(): 0.0, (0,): 1.0})
    masks = size_balanced_masks(3, 8, seed=1)
    values = tuple(game.value(i for i, present in enumerate(mask) if present) for mask in masks)
    estimator = PolynomialInteractionEstimator(max_order=1, n_players=3).fit(masks, values)
    with pytest.raises(ValueError):
        residual_bootstrap_stability(estimator, masks, values, n_resamples=1, seed=1)
