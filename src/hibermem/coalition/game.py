"""Exact cooperative-game abstractions independent of any LLM backend."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Sequence
from math import isfinite, log2

from .masks import coalition_to_mask, mask_to_index


def _validated_coalition(coalition: Iterable[int], n_players: int) -> frozenset[int]:
    mask = coalition_to_mask(coalition, n_players)
    return frozenset(index for index, present in enumerate(mask) if present)


class CooperativeGame(ABC):
    """A deterministic set function over players ``0..n_players-1``."""

    def __init__(self, n_players: int) -> None:
        if isinstance(n_players, bool) or not isinstance(n_players, int):
            raise TypeError("n_players must be an integer")
        if n_players < 0:
            raise ValueError("n_players must be non-negative")
        self._n_players = n_players

    @property
    def n_players(self) -> int:
        return self._n_players

    @property
    def grand_coalition(self) -> frozenset[int]:
        return frozenset(range(self.n_players))

    @abstractmethod
    def value(self, coalition: Iterable[int]) -> float:
        """Evaluate one coalition."""

    def values(self, coalitions: Iterable[Iterable[int]]) -> tuple[float, ...]:
        return tuple(self.value(coalition) for coalition in coalitions)


class TabularGame(CooperativeGame):
    """A complete value table in integer mask order."""

    def __init__(self, values: Sequence[float], n_players: int | None = None) -> None:
        table = tuple(float(value) for value in values)
        if not table:
            raise ValueError("a game table cannot be empty")
        if any(not isfinite(value) for value in table):
            raise ValueError("game values must be finite")
        if n_players is None:
            inferred = int(log2(len(table)))
            if 1 << inferred != len(table):
                raise ValueError("table length must be a power of two")
            n_players = inferred
        super().__init__(n_players)
        expected = 1 << self.n_players
        if len(table) != expected:
            raise ValueError(f"expected {expected} values, got {len(table)}")
        self._table = table

    @property
    def table(self) -> tuple[float, ...]:
        return self._table

    def value(self, coalition: Iterable[int]) -> float:
        validated = _validated_coalition(coalition, self.n_players)
        index = mask_to_index(coalition_to_mask(validated, self.n_players))
        return self.table[index]


class CallableGame(CooperativeGame):
    """A validated wrapper around a coalition callable."""

    def __init__(self, n_players: int, function: Callable[[frozenset[int]], float]) -> None:
        super().__init__(n_players)
        if not callable(function):
            raise TypeError("function must be callable")
        self._function = function

    def value(self, coalition: Iterable[int]) -> float:
        validated = _validated_coalition(coalition, self.n_players)
        result = float(self._function(validated))
        if not isfinite(result):
            raise ValueError("game values must be finite")
        return result

    def tabulate(self) -> TabularGame:
        values = []
        for index in range(1 << self.n_players):
            coalition = frozenset(
                player for player in range(self.n_players) if index & (1 << player)
            )
            values.append(self.value(coalition))
        return TabularGame(values, self.n_players)
