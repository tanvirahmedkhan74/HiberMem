"""Sampled low-order Möbius recovery by deterministic least squares."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from itertools import combinations
from math import isfinite

import numpy as np

from hibermem.coalition.masks import Mask, mask_to_index, normalize_mask

from .shapley import InteractionEstimator, InteractionMap


class PolynomialInteractionEstimator(InteractionEstimator):
    """Fit a truncated pseudo-Boolean polynomial to sampled coalition values.

    Coefficients are interpreted as Möbius/Harsanyi terms in the monomial basis
    ``prod(x_i for i in term)``. They are deliberately not labeled SII values.
    Ordinary least squares is used so analytical standard errors and recovery of
    known synthetic coefficients remain transparent.
    """

    def __init__(self, max_order: int = 3, n_players: int | None = None) -> None:
        if isinstance(max_order, bool) or not isinstance(max_order, int) or max_order < 1:
            raise ValueError("max_order must be a positive integer")
        if n_players is not None and (
            isinstance(n_players, bool) or not isinstance(n_players, int) or n_players < 1
        ):
            raise ValueError("n_players must be a positive integer")
        self.max_order = max_order
        self._configured_n_players = n_players
        self._n_players: int | None = None
        self._terms: tuple[tuple[int, ...], ...] = ()
        self._coefficients: np.ndarray | None = None
        self._standard_errors: np.ndarray | None = None
        self._design: np.ndarray | None = None
        self._observed: np.ndarray | None = None
        self._fitted: np.ndarray | None = None
        self._rank: int | None = None
        self._condition_number: float | None = None
        self._degrees_of_freedom: int | None = None

    @property
    def n_players(self) -> int:
        if self._n_players is None:
            raise RuntimeError("estimator has not been fitted")
        return self._n_players

    @property
    def terms(self) -> tuple[tuple[int, ...], ...]:
        if not self._terms:
            raise RuntimeError("estimator has not been fitted")
        return self._terms

    @property
    def coefficients(self) -> dict[tuple[int, ...], float]:
        if self._coefficients is None:
            raise RuntimeError("estimator has not been fitted")
        return {term: float(value) for term, value in zip(self.terms, self._coefficients, strict=True)}

    @property
    def standard_errors(self) -> dict[tuple[int, ...], float]:
        if self._standard_errors is None:
            raise RuntimeError("estimator has not been fitted")
        return {
            term: float(value)
            for term, value in zip(self.terms, self._standard_errors, strict=True)
        }

    @property
    def residuals(self) -> np.ndarray:
        if self._observed is None or self._fitted is None:
            raise RuntimeError("estimator has not been fitted")
        return self._observed - self._fitted

    @property
    def fitted_values(self) -> np.ndarray:
        if self._fitted is None:
            raise RuntimeError("estimator has not been fitted")
        return self._fitted.copy()

    @property
    def rank(self) -> int:
        if self._rank is None:
            raise RuntimeError("estimator has not been fitted")
        return self._rank

    @property
    def condition_number(self) -> float:
        if self._condition_number is None:
            raise RuntimeError("estimator has not been fitted")
        return self._condition_number

    @property
    def degrees_of_freedom(self) -> int:
        if self._degrees_of_freedom is None:
            raise RuntimeError("estimator has not been fitted")
        return self._degrees_of_freedom

    def _make_terms(self, n_players: int) -> tuple[tuple[int, ...], ...]:
        capped_order = min(self.max_order, n_players)
        return ((),) + tuple(
            coalition
            for order in range(1, capped_order + 1)
            for coalition in combinations(range(n_players), order)
        )

    @staticmethod
    def _design_matrix(masks: Sequence[Mask], terms: Sequence[tuple[int, ...]]) -> np.ndarray:
        design = np.empty((len(masks), len(terms)), dtype=float)
        for row_index, mask in enumerate(masks):
            for column_index, term in enumerate(terms):
                design[row_index, column_index] = float(all(mask[player] for player in term))
        return design

    def fit(
        self,
        coalition_masks: Iterable[Sequence[bool | int]],
        coalition_values: Iterable[float],
    ) -> "PolynomialInteractionEstimator":
        raw_masks = list(coalition_masks)
        values = np.asarray([float(value) for value in coalition_values], dtype=float)
        if not raw_masks:
            raise ValueError("at least one coalition is required")
        if len(raw_masks) != len(values):
            raise ValueError("coalition_masks and coalition_values must have equal length")
        if not np.all(np.isfinite(values)):
            raise ValueError("coalition values must be finite")
        n_players = self._configured_n_players or len(raw_masks[0])
        masks = tuple(normalize_mask(mask, n_players) for mask in raw_masks)
        if len({mask_to_index(mask) for mask in masks}) != len(masks):
            raise ValueError("sampled estimator requires unique coalition masks")

        terms = self._make_terms(n_players)
        design = self._design_matrix(masks, terms)
        if len(values) < len(terms):
            raise ValueError(
                f"at least {len(terms)} observations are required for {len(terms)} terms"
            )
        coefficients, _, rank, singular_values = np.linalg.lstsq(design, values, rcond=None)
        if rank != len(terms):
            raise ValueError(
                f"coalition design is rank deficient ({rank} < {len(terms)}); resample coalitions"
            )
        fitted = design @ coefficients
        degrees_of_freedom = len(values) - rank
        if degrees_of_freedom > 0:
            residual_variance = float(np.sum((values - fitted) ** 2) / degrees_of_freedom)
            covariance = residual_variance * np.linalg.pinv(design.T @ design, hermitian=True)
            standard_errors = np.sqrt(np.maximum(np.diag(covariance), 0.0))
        else:
            standard_errors = np.full(len(terms), np.nan, dtype=float)

        self._n_players = n_players
        self._terms = terms
        self._coefficients = coefficients
        self._standard_errors = standard_errors
        self._design = design
        self._observed = values
        self._fitted = fitted
        self._rank = int(rank)
        self._degrees_of_freedom = int(degrees_of_freedom)
        self._condition_number = float(singular_values[0] / singular_values[-1])
        return self

    def predict(self, coalition_masks: Iterable[Sequence[bool | int]]) -> tuple[float, ...]:
        masks = tuple(normalize_mask(mask, self.n_players) for mask in coalition_masks)
        design = self._design_matrix(masks, self.terms)
        if self._coefficients is None:
            raise RuntimeError("estimator has not been fitted")
        return tuple(float(value) for value in design @ self._coefficients)

    def individual_values(self) -> dict[int, float]:
        coefficients = self.coefficients
        return {(term[0]): value for term, value in coefficients.items() if len(term) == 1}

    def interactions(self, order: int) -> InteractionMap:
        if isinstance(order, bool) or not isinstance(order, int):
            raise TypeError("order must be an integer")
        if not 1 <= order <= min(self.max_order, self.n_players):
            raise ValueError("order must be between 1 and the fitted maximum order")
        return {term: value for term, value in self.coefficients.items() if len(term) == order}

    def uncertainty(self) -> InteractionMap:
        return {term: value for term, value in self.standard_errors.items() if term}
