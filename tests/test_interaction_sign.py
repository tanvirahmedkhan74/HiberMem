from itertools import combinations

import pytest

from hibermem.coalition.game import CallableGame
from hibermem.interactions.discrete import discrete_derivative, full_context_interaction
from hibermem.interactions.shapley import shapley_interaction_index


def test_additive_interaction_zero() -> None:
    game = CallableGame(3, lambda s: 0.7 + 2.0 * (0 in s) - 3.0 * (1 in s) + 0.5 * (2 in s))
    for pair in combinations(range(3), 2):
        assert full_context_interaction(game, pair) == pytest.approx(0.0)
        assert shapley_interaction_index(game, pair) == pytest.approx(0.0)


def test_and_interaction_positive() -> None:
    game = CallableGame(2, lambda s: float({0, 1} <= s))
    assert discrete_derivative(game, (0, 1), ()) == pytest.approx(1.0)
    assert full_context_interaction(game, (0, 1)) == pytest.approx(1.0)
    assert shapley_interaction_index(game, (0, 1)) == pytest.approx(1.0)


def test_or_interaction_negative() -> None:
    game = CallableGame(2, lambda s: float(bool(s & {0, 1})))
    assert full_context_interaction(game, (0, 1)) == pytest.approx(-1.0)
    assert shapley_interaction_index(game, (0, 1)) == pytest.approx(-1.0)


def test_triple_interaction() -> None:
    game = CallableGame(3, lambda s: float({0, 1, 2} <= s))
    assert discrete_derivative(game, (0, 1, 2), ()) == pytest.approx(1.0)
    assert full_context_interaction(game, (0, 1, 2)) == pytest.approx(1.0)
    assert shapley_interaction_index(game, (0, 1, 2)) == pytest.approx(1.0)
    # SII averages pair derivatives over contexts, so triple AND has pair SII 1/2.
    assert shapley_interaction_index(game, (0, 1)) == pytest.approx(0.5)


def test_dummy_player() -> None:
    game = CallableGame(3, lambda s: 2.0 * (0 in s) + 3.0 * ({0, 1} <= s))
    assert shapley_interaction_index(game, (2,)) == pytest.approx(0.0)
    assert shapley_interaction_index(game, (0, 2)) == pytest.approx(0.0)
    assert shapley_interaction_index(game, (0, 1, 2)) == pytest.approx(0.0)


def test_permutation_invariance() -> None:
    original = CallableGame(
        4,
        lambda s: 1.5 * (0 in s) - 0.2 * (3 in s) + 2.3 * ({0, 2} <= s),
    )
    # New player -> old player. This is deliberately nontrivial and invertible.
    permutation = (2, 0, 3, 1)
    permuted = CallableGame(
        4,
        lambda new_s: original.value({permutation[player] for player in new_s}),
    )
    old_target = (0, 2)
    new_target = tuple(
        sorted(new_player for new_player, old_player in enumerate(permutation) if old_player in old_target)
    )
    assert shapley_interaction_index(permuted, new_target) == pytest.approx(
        shapley_interaction_index(original, old_target)
    )
    assert full_context_interaction(permuted, new_target) == pytest.approx(
        full_context_interaction(original, old_target)
    )


def test_sign_correction_matches_deletion_notation() -> None:
    game = CallableGame(
        3,
        lambda s: 0.4 + 2.0 * (0 in s) + 3.0 * (1 in s) + 5.0 * ({0, 1} <= s),
    )
    grand = game.grand_coalition
    delta_i = game.value(grand) - game.value(grand - {0})
    delta_j = game.value(grand) - game.value(grand - {1})
    delta_ij = game.value(grand) - game.value(grand - {0, 1})
    assert delta_i + delta_j - delta_ij == pytest.approx(
        full_context_interaction(game, (0, 1))
    )
