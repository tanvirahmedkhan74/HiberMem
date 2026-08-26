"""Context-specific finite differences of cooperative games."""

from __future__ import annotations

from collections.abc import Iterable
from itertools import combinations

from hibermem.coalition.game import CooperativeGame


def _player_set(players: Iterable[int], game: CooperativeGame, label: str) -> frozenset[int]:
    result = frozenset(players)
    if len(result) == 0 and label == "interaction":
        raise ValueError("interaction must contain at least one player")
    if any(isinstance(player, bool) or not isinstance(player, int) for player in result):
        raise TypeError(f"{label} players must be integers")
    if any(not 0 <= player < game.n_players for player in result):
        raise ValueError(f"{label} contains a player outside the game")
    return result


def discrete_derivative(
    game: CooperativeGame,
    interaction: Iterable[int],
    context: Iterable[int] = (),
) -> float:
    """Compute ``Delta_interaction game(context)`` exactly.

    ``interaction`` and ``context`` must be disjoint. The result is local to the
    supplied context and must not be relabeled as a context-averaged index.
    """

    target = _player_set(interaction, game, "interaction")
    base = _player_set(context, game, "context")
    if target & base:
        raise ValueError("interaction and context must be disjoint")

    ordered = tuple(sorted(target))
    result = 0.0
    for subset_size in range(len(ordered) + 1):
        sign = -1.0 if (len(ordered) - subset_size) % 2 else 1.0
        for subset in combinations(ordered, subset_size):
            result += sign * game.value(base | frozenset(subset))
    return result


def full_context_interaction(game: CooperativeGame, interaction: Iterable[int]) -> float:
    """Compute the local interaction with every non-target player present."""

    target = _player_set(interaction, game, "interaction")
    return discrete_derivative(game, target, game.grand_coalition - target)
