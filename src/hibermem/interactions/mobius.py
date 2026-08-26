"""Exact Möbius/Harsanyi decomposition of complete coalition tables."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from math import isfinite, log2

from hibermem.coalition.game import CooperativeGame
from hibermem.coalition.masks import index_to_mask, mask_to_coalition


def _validated_table(values: Sequence[float]) -> list[float]:
    table = [float(value) for value in values]
    if not table:
        raise ValueError("values cannot be empty")
    n_players = int(log2(len(table)))
    if 1 << n_players != len(table):
        raise ValueError("value count must be a power of two")
    if any(not isfinite(value) for value in table):
        raise ValueError("values must be finite")
    return table


def mobius_transform(values: Sequence[float]) -> tuple[float, ...]:
    """Return exact polynomial coefficients in integer mask order."""

    coefficients = _validated_table(values)
    n_players = int(log2(len(coefficients)))
    for player in range(n_players):
        bit = 1 << player
        for mask in range(1 << n_players):
            if mask & bit:
                coefficients[mask] -= coefficients[mask ^ bit]
    return tuple(coefficients)


def inverse_mobius_transform(coefficients: Sequence[float]) -> tuple[float, ...]:
    """Reconstruct a complete game table from Möbius coefficients."""

    values = _validated_table(coefficients)
    n_players = int(log2(len(values)))
    for player in range(n_players):
        bit = 1 << player
        for mask in range(1 << n_players):
            if mask & bit:
                values[mask] += values[mask ^ bit]
    return tuple(values)


def mobius_coefficients(game: CooperativeGame) -> dict[tuple[int, ...], float]:
    """Return coalition-keyed Möbius/Harsanyi coefficients."""

    values = []
    for index in range(1 << game.n_players):
        coalition = mask_to_coalition(index_to_mask(index, game.n_players))
        values.append(game.value(coalition))
    transformed = mobius_transform(values)
    return {
        mask_to_coalition(index_to_mask(index, game.n_players)): coefficient
        for index, coefficient in enumerate(transformed)
    }


def evaluate_mobius(
    coefficients: Mapping[tuple[int, ...], float], coalition: Iterable[int]
) -> float:
    """Evaluate a coalition from a sparse or complete Möbius mapping."""

    present = frozenset(coalition)
    result = 0.0
    for term, coefficient in coefficients.items():
        if frozenset(term) <= present:
            result += float(coefficient)
    return result
