import pytest

from hibermem.coalition.game import CallableGame
from hibermem.interactions.mobius import (
    evaluate_mobius,
    inverse_mobius_transform,
    mobius_coefficients,
    mobius_transform,
)


def test_mobius_roundtrip() -> None:
    values = (0.3, 1.0, -0.5, 2.2, 1.7, -3.0, 0.2, 4.5)
    assert inverse_mobius_transform(mobius_transform(values)) == pytest.approx(values)


def test_mobius_recovers_sparse_polynomial() -> None:
    game = CallableGame(
        4,
        lambda s: 1.25
        + 2.0 * (0 in s)
        - 0.5 * (2 in s)
        + 3.0 * ({0, 1} <= s)
        - 4.0 * ({1, 2, 3} <= s),
    )
    coefficients = mobius_coefficients(game)

    assert coefficients[()] == pytest.approx(1.25)
    assert coefficients[(0,)] == pytest.approx(2.0)
    assert coefficients[(2,)] == pytest.approx(-0.5)
    assert coefficients[(0, 1)] == pytest.approx(3.0)
    assert coefficients[(1, 2, 3)] == pytest.approx(-4.0)
    assert coefficients[(0, 2)] == pytest.approx(0.0)

    for index in range(16):
        coalition = tuple(player for player in range(4) if index & (1 << player))
        assert evaluate_mobius(coefficients, coalition) == pytest.approx(game.value(coalition))


def test_triple_and_has_only_third_order_mobius_term() -> None:
    game = CallableGame(3, lambda s: float({0, 1, 2} <= s))
    coefficients = mobius_coefficients(game)
    assert coefficients[(0, 1, 2)] == pytest.approx(1.0)
    assert all(
        value == pytest.approx(0.0)
        for coalition, value in coefficients.items()
        if coalition != (0, 1, 2)
    )
