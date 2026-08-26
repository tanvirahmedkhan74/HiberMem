"""Small-n retention policies with exact, deterministic optimization."""

from __future__ import annotations

import random
from collections.abc import Mapping
from itertools import combinations

from hibermem.coalition.masks import Mask


CoefficientMap = Mapping[tuple[int, ...], float]


def _validate_budget(n_players: int, keep_count: int) -> None:
    if not 0 <= keep_count <= n_players:
        raise ValueError("keep_count must be between zero and n_players")


def mobius_to_shapley_items(
    coefficients: CoefficientMap, n_players: int
) -> dict[int, float]:
    """Convert a Möbius polynomial to ordinary Shapley item values."""

    values = {player: 0.0 for player in range(n_players)}
    for term, coefficient in coefficients.items():
        if not term:
            continue
        share = float(coefficient) / len(term)
        for player in term:
            values[player] += share
    return values


def item_value_mask(item_values: Mapping[int, float], n_players: int, keep_count: int) -> Mask:
    _validate_budget(n_players, keep_count)
    if set(item_values) != set(range(n_players)):
        raise ValueError("item_values must cover every player exactly once")
    ranked = sorted(range(n_players), key=lambda player: (-item_values[player], player))
    selected = set(ranked[:keep_count])
    return tuple(player in selected for player in range(n_players))


def _polynomial_value(coalition: tuple[int, ...], coefficients: CoefficientMap) -> float:
    present = set(coalition)
    return sum(value for term, value in coefficients.items() if set(term) <= present)


def interaction_aware_mask(
    coefficients: CoefficientMap, n_players: int, keep_count: int
) -> Mask:
    """Exactly maximize the fitted low-order value for the small Phase 2 banks."""

    _validate_budget(n_players, keep_count)
    candidates = combinations(range(n_players), keep_count)
    best = max(candidates, key=lambda coalition: (_polynomial_value(coalition, coefficients), tuple(-x for x in coalition)))
    selected = set(best)
    return tuple(player in selected for player in range(n_players))


def random_mask(n_players: int, keep_count: int, seed: int) -> Mask:
    _validate_budget(n_players, keep_count)
    selected = set(random.Random(seed).sample(range(n_players), keep_count))
    return tuple(player in selected for player in range(n_players))
