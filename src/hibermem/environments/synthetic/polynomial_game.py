"""Synthetic games with known Möbius/pseudo-Boolean coefficients."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from math import isfinite

from hibermem.coalition.game import CooperativeGame


class PolynomialGame(CooperativeGame):
    """A complete game defined by sparse Möbius coefficients."""

    def __init__(self, n_players: int, coefficients: Mapping[tuple[int, ...], float]) -> None:
        super().__init__(n_players)
        validated: dict[tuple[int, ...], float] = {}
        for raw_term, raw_value in coefficients.items():
            term = tuple(raw_term)
            if tuple(sorted(set(term))) != term:
                raise ValueError("coefficient terms must be sorted and unique")
            if any(isinstance(player, bool) or not isinstance(player, int) for player in term):
                raise TypeError("coefficient players must be integers")
            if any(not 0 <= player < n_players for player in term):
                raise ValueError("coefficient term contains an unknown player")
            value = float(raw_value)
            if not isfinite(value):
                raise ValueError("coefficients must be finite")
            if term in validated:
                raise ValueError(f"duplicate coefficient term {term}")
            validated[term] = value
        validated.setdefault((), 0.0)
        self._coefficients = dict(sorted(validated.items(), key=lambda item: (len(item[0]), item[0])))

    @property
    def coefficients(self) -> dict[tuple[int, ...], float]:
        return self._coefficients.copy()

    @property
    def max_order(self) -> int:
        return max(map(len, self._coefficients), default=0)

    def value(self, coalition: Iterable[int]) -> float:
        present = frozenset(coalition)
        if any(isinstance(player, bool) or not isinstance(player, int) for player in present):
            raise TypeError("coalition players must be integers")
        if any(not 0 <= player < self.n_players for player in present):
            raise ValueError("coalition contains an unknown player")
        return sum(value for term, value in self._coefficients.items() if set(term) <= present)
