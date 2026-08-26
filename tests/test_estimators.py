from itertools import combinations

import pytest

from hibermem.coalition.game import CallableGame
from hibermem.coalition.masks import iter_masks, mask_to_coalition
from hibermem.interactions.shapley import ExactInteractionEstimator


def _mixed_game() -> CallableGame:
    return CallableGame(
        4,
        lambda s: 0.2
        + 1.1 * (0 in s)
        - 0.8 * (2 in s)
        + 2.5 * ({0, 1} <= s)
        - 1.7 * ({1, 3} <= s)
        + 3.2 * ({0, 2, 3} <= s),
    )


def _fit_internal(game: CallableGame) -> ExactInteractionEstimator:
    masks = list(iter_masks(game.n_players))
    values = [game.value(mask_to_coalition(mask)) for mask in masks]
    return ExactInteractionEstimator().fit(masks, values)


def test_estimator_is_deterministically_reproducible() -> None:
    first = _fit_internal(_mixed_game())
    second = _fit_internal(_mixed_game())
    assert first.individual_values() == second.individual_values()
    for order in range(1, 5):
        assert first.interactions(order) == second.interactions(order)
    assert first.uncertainty() == second.uncertainty()


def test_estimator_rejects_incomplete_or_duplicate_tables() -> None:
    with pytest.raises(ValueError, match="all coalitions"):
        ExactInteractionEstimator().fit([(False, False)], [0.0])
    with pytest.raises(ValueError, match="duplicate"):
        ExactInteractionEstimator().fit([(False,), (False,)], [0.0, 1.0])


def test_individual_values_match_order_one_interactions() -> None:
    estimator = _fit_internal(_mixed_game())
    order_one = estimator.interactions(1)
    assert estimator.individual_values() == {
        coalition[0]: value for coalition, value in order_one.items()
    }
    assert set(estimator.interactions(3)) == set(combinations(range(4), 3))
