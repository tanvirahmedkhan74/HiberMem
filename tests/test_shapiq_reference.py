from itertools import combinations

import pytest

pytest.importorskip("shapiq")

from hibermem.coalition.game import CallableGame
from hibermem.coalition.masks import iter_masks, mask_to_coalition
from hibermem.interactions.shapley import ExactInteractionEstimator, ShapiqExactEstimator


def test_exact_vs_library() -> None:
    game = CallableGame(
        4,
        lambda s: 0.3
        + 1.0 * (0 in s)
        - 0.4 * (3 in s)
        + 2.0 * ({0, 1} <= s)
        - 1.5 * ({1, 2} <= s)
        + 4.0 * ({0, 2, 3} <= s),
    )
    masks = list(iter_masks(game.n_players))
    values = [game.value(mask_to_coalition(mask)) for mask in masks]
    internal = ExactInteractionEstimator().fit(masks, values)
    reference = ShapiqExactEstimator().fit(masks, values)

    assert internal.individual_values() == pytest.approx(reference.individual_values(), abs=1e-10)
    for order in range(1, game.n_players + 1):
        expected_keys = set(combinations(range(game.n_players), order))
        assert set(internal.interactions(order)) == expected_keys
        assert internal.interactions(order) == pytest.approx(
            reference.interactions(order), abs=1e-10
        )
