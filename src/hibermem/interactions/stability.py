"""Deterministic stability estimates for sampled interaction models."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np

from .polynomial import PolynomialInteractionEstimator


@dataclass(frozen=True)
class BootstrapTermSummary:
    mean: float
    standard_deviation: float
    lower: float
    upper: float
    sign_consistency: float


def residual_bootstrap_stability(
    estimator: PolynomialInteractionEstimator,
    coalition_masks: Iterable[Sequence[bool | int]],
    coalition_values: Iterable[float],
    *,
    n_resamples: int,
    seed: int,
    alpha: float = 0.05,
) -> dict[tuple[int, ...], BootstrapTermSummary]:
    """Estimate coefficient stability with a fixed-design residual bootstrap."""

    if isinstance(n_resamples, bool) or not isinstance(n_resamples, int) or n_resamples < 2:
        raise ValueError("n_resamples must be an integer of at least 2")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be between zero and one")
    masks = tuple(tuple(mask) for mask in coalition_masks)
    observed = np.asarray(tuple(float(value) for value in coalition_values), dtype=float)
    if len(masks) != len(observed):
        raise ValueError("coalition_masks and coalition_values must have equal length")

    fitted = np.asarray(estimator.predict(masks), dtype=float)
    centered_residuals = observed - fitted
    centered_residuals -= np.mean(centered_residuals)
    rng = np.random.default_rng(seed)
    terms = estimator.terms
    samples = np.empty((n_resamples, len(terms)), dtype=float)

    for replicate in range(n_resamples):
        boot_values = fitted + rng.choice(centered_residuals, size=len(observed), replace=True)
        boot = PolynomialInteractionEstimator(
            max_order=estimator.max_order, n_players=estimator.n_players
        ).fit(masks, boot_values)
        samples[replicate] = [boot.coefficients[term] for term in terms]

    lower_quantile = alpha / 2.0
    upper_quantile = 1.0 - lower_quantile
    base = estimator.coefficients
    summaries: dict[tuple[int, ...], BootstrapTermSummary] = {}
    for term_index, term in enumerate(terms):
        term_samples = samples[:, term_index]
        reference_sign = np.sign(base[term])
        if reference_sign == 0:
            sign_consistency = float(np.mean(np.sign(term_samples) == 0))
        else:
            sign_consistency = float(np.mean(np.sign(term_samples) == reference_sign))
        summaries[term] = BootstrapTermSummary(
            mean=float(np.mean(term_samples)),
            standard_deviation=float(np.std(term_samples, ddof=1)),
            lower=float(np.quantile(term_samples, lower_quantile)),
            upper=float(np.quantile(term_samples, upper_quantile)),
            sign_consistency=sign_consistency,
        )
    return summaries
