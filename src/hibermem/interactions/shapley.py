"""Exact Shapley Interaction Index estimators and reference adapter."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from itertools import combinations
from math import factorial, isfinite

from hibermem.coalition.game import CooperativeGame, TabularGame
from hibermem.coalition.masks import Mask, mask_to_index, normalize_mask
from hibermem.interactions.discrete import discrete_derivative

InteractionMap = dict[tuple[int, ...], float]


def shapley_interaction_index(game: CooperativeGame, interaction: Iterable[int]) -> float:
    """Compute the Grabisch–Roubens Shapley Interaction Index exactly."""

    target = frozenset(interaction)
    if not target:
        raise ValueError("interaction must contain at least one player")
    if any(isinstance(player, bool) or not isinstance(player, int) for player in target):
        raise TypeError("interaction players must be integers")
    if any(not 0 <= player < game.n_players for player in target):
        raise ValueError("interaction contains a player outside the game")

    outside = tuple(sorted(game.grand_coalition - target))
    denominator = factorial(len(outside) + 1)
    result = 0.0
    for context_size in range(len(outside) + 1):
        weight = (
            factorial(context_size)
            * factorial(len(outside) - context_size)
            / denominator
        )
        for context in combinations(outside, context_size):
            result += weight * discrete_derivative(game, target, context)
    return result


class InteractionEstimator(ABC):
    """Common estimator interface from the master specification."""

    @abstractmethod
    def fit(
        self,
        coalition_masks: Iterable[Sequence[bool | int]],
        coalition_values: Iterable[float],
    ) -> "InteractionEstimator":
        ...

    @abstractmethod
    def individual_values(self) -> dict[int, float]:
        ...

    @abstractmethod
    def interactions(self, order: int) -> InteractionMap:
        ...

    @abstractmethod
    def uncertainty(self) -> InteractionMap:
        ...


def _complete_table(
    coalition_masks: Iterable[Sequence[bool | int]],
    coalition_values: Iterable[float],
    n_players: int | None,
) -> tuple[int, tuple[float, ...]]:
    masks = list(coalition_masks)
    values = [float(value) for value in coalition_values]
    if not masks:
        raise ValueError("at least one coalition is required")
    if len(masks) != len(values):
        raise ValueError("coalition_masks and coalition_values must have equal length")
    if any(not isfinite(value) for value in values):
        raise ValueError("coalition values must be finite")
    if n_players is None:
        n_players = len(masks[0])
    if isinstance(n_players, bool) or not isinstance(n_players, int) or n_players < 0:
        raise ValueError("n_players must be a non-negative integer")

    by_index: dict[int, float] = {}
    for mask, value in zip(masks, values, strict=True):
        normalized: Mask = normalize_mask(mask, n_players)
        index = mask_to_index(normalized)
        if index in by_index:
            raise ValueError(f"duplicate coalition mask at index {index}")
        by_index[index] = value
    expected = 1 << n_players
    if set(by_index) != set(range(expected)):
        missing = sorted(set(range(expected)) - set(by_index))
        raise ValueError(f"exact estimator requires all coalitions; missing {missing}")
    return n_players, tuple(by_index[index] for index in range(expected))


class ExactInteractionEstimator(InteractionEstimator):
    """Internal exact SII estimator for small complete games."""

    def __init__(self, n_players: int | None = None) -> None:
        self._configured_n_players = n_players
        self._game: TabularGame | None = None

    @property
    def game(self) -> TabularGame:
        if self._game is None:
            raise RuntimeError("estimator has not been fitted")
        return self._game

    def fit(
        self,
        coalition_masks: Iterable[Sequence[bool | int]],
        coalition_values: Iterable[float],
    ) -> "ExactInteractionEstimator":
        n_players, table = _complete_table(
            coalition_masks, coalition_values, self._configured_n_players
        )
        self._game = TabularGame(table, n_players)
        return self

    def individual_values(self) -> dict[int, float]:
        return {
            player: shapley_interaction_index(self.game, (player,))
            for player in range(self.game.n_players)
        }

    def interactions(self, order: int) -> InteractionMap:
        if isinstance(order, bool) or not isinstance(order, int):
            raise TypeError("order must be an integer")
        if not 1 <= order <= self.game.n_players:
            raise ValueError("order must be between 1 and n_players")
        return {
            coalition: shapley_interaction_index(self.game, coalition)
            for coalition in combinations(range(self.game.n_players), order)
        }

    def uncertainty(self) -> InteractionMap:
        return {
            coalition: 0.0
            for order in range(1, self.game.n_players + 1)
            for coalition in combinations(range(self.game.n_players), order)
        }


class ShapiqExactEstimator(InteractionEstimator):
    """Independent exact SII adapter used to cross-check the internal formula."""

    def __init__(self, n_players: int | None = None) -> None:
        self._configured_n_players = n_players
        self._n_players: int | None = None
        self._table: tuple[float, ...] | None = None
        self._computer = None

    def fit(
        self,
        coalition_masks: Iterable[Sequence[bool | int]],
        coalition_values: Iterable[float],
    ) -> "ShapiqExactEstimator":
        try:
            import numpy as np
            import shapiq
        except ImportError as error:
            raise RuntimeError(
                "ShapiqExactEstimator requires the 'reference' optional dependencies"
            ) from error

        n_players, table = _complete_table(
            coalition_masks, coalition_values, self._configured_n_players
        )

        def game_function(coalitions):
            rows = np.atleast_2d(coalitions)
            indices = np.zeros(rows.shape[0], dtype=np.int64)
            for player in range(n_players):
                indices += rows[:, player].astype(np.int64) << player
            return np.asarray([table[int(index)] for index in indices], dtype=float)

        try:
            computer = shapiq.ExactComputer(game_function, n_players=n_players)
        except TypeError:
            computer = shapiq.ExactComputer(
                n_players=n_players, game=game_function, evaluate_game=True
            )
        self._n_players = n_players
        self._table = table
        self._computer = computer
        return self

    @property
    def n_players(self) -> int:
        if self._n_players is None:
            raise RuntimeError("estimator has not been fitted")
        return self._n_players

    def _values(self, order: int) -> InteractionMap:
        if self._computer is None:
            raise RuntimeError("estimator has not been fitted")
        result = self._computer(index="SII", order=order)
        lookup = result.interaction_lookup
        values = result.values
        return {
            coalition: float(values[lookup[coalition]])
            for coalition in combinations(range(self.n_players), order)
        }

    def individual_values(self) -> dict[int, float]:
        return {
            coalition[0]: value for coalition, value in self._values(order=1).items()
        }

    def interactions(self, order: int) -> InteractionMap:
        if isinstance(order, bool) or not isinstance(order, int):
            raise TypeError("order must be an integer")
        if not 1 <= order <= self.n_players:
            raise ValueError("order must be between 1 and n_players")
        return self._values(order)

    def uncertainty(self) -> InteractionMap:
        return {
            coalition: 0.0
            for order in range(1, self.n_players + 1)
            for coalition in combinations(range(self.n_players), order)
        }
