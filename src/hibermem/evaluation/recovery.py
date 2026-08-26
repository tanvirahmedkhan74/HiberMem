"""Preregistered metrics for deterministic synthetic interaction recovery."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite

import numpy as np
from scipy.stats import spearmanr

from hibermem.interactions.polynomial import PolynomialInteractionEstimator
from hibermem.interactions.stability import BootstrapTermSummary


@dataclass(frozen=True)
class RecoveryMetrics:
    individual_mae: float
    interaction_mae: float
    interaction_sign_accuracy: float | None
    precision_at_k: float | None
    recall_at_k: float | None
    nonzero_spearman: float | None
    detected_interaction_recall: float | None
    null_false_positive_rate: float
    ci_coverage: float
    true_interaction_sign_stability: float | None

    def as_dict(self) -> dict[str, float | None]:
        return asdict(self)


def _sign(value: float) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def recovery_metrics(
    truth: dict[tuple[int, ...], float],
    estimator: PolynomialInteractionEstimator,
    stability: dict[tuple[int, ...], BootstrapTermSummary],
    *,
    practical_detection_threshold: float,
    confidence_z: float,
) -> RecoveryMetrics:
    """Compare fitted Möbius coefficients with known synthetic ground truth."""

    if practical_detection_threshold < 0:
        raise ValueError("practical_detection_threshold must be non-negative")
    if confidence_z <= 0:
        raise ValueError("confidence_z must be positive")

    estimates = estimator.coefficients
    errors = {term: abs(estimates[term] - truth.get(term, 0.0)) for term in estimator.terms}
    item_terms = [term for term in estimator.terms if len(term) == 1]
    interaction_terms = [term for term in estimator.terms if len(term) >= 2]
    nonzero_interactions = [term for term in interaction_terms if abs(truth.get(term, 0.0)) > 1e-12]
    null_interactions = [term for term in interaction_terms if abs(truth.get(term, 0.0)) <= 1e-12]

    individual_mae = float(np.mean([errors[term] for term in item_terms]))
    interaction_mae = float(np.mean([errors[term] for term in interaction_terms]))

    if nonzero_interactions:
        interaction_sign_accuracy = float(
            np.mean(
                [
                    _sign(estimates[term]) == _sign(truth[term])
                    for term in nonzero_interactions
                ]
            )
        )
        k = len(nonzero_interactions)
        top_k = set(
            sorted(interaction_terms, key=lambda term: (-abs(estimates[term]), term))[:k]
        )
        true_set = set(nonzero_interactions)
        precision_at_k = len(top_k & true_set) / k
        recall_at_k = len(top_k & true_set) / len(true_set)
        if len(nonzero_interactions) >= 2:
            statistic = spearmanr(
                [truth[term] for term in nonzero_interactions],
                [estimates[term] for term in nonzero_interactions],
            ).statistic
            nonzero_spearman = float(statistic) if isfinite(float(statistic)) else None
        else:
            nonzero_spearman = None
        true_interaction_sign_stability = float(
            np.mean([stability[term].sign_consistency for term in nonzero_interactions])
        )
    else:
        interaction_sign_accuracy = None
        precision_at_k = None
        recall_at_k = None
        nonzero_spearman = None
        true_interaction_sign_stability = None

    uncertainty = estimator.standard_errors

    def detected(term: tuple[int, ...]) -> bool:
        estimate = estimates[term]
        standard_error = uncertainty[term]
        excludes_zero = (
            estimate - confidence_z * standard_error > 0
            or estimate + confidence_z * standard_error < 0
        )
        return abs(estimate) >= practical_detection_threshold and excludes_zero

    detected_interaction_recall = (
        float(np.mean([detected(term) for term in nonzero_interactions]))
        if nonzero_interactions
        else None
    )
    null_false_positive_rate = (
        float(np.mean([detected(term) for term in null_interactions]))
        if null_interactions
        else 0.0
    )

    coverage = []
    for term in estimator.terms:
        standard_error = uncertainty[term]
        if not isfinite(standard_error):
            continue
        lower = estimates[term] - confidence_z * standard_error
        upper = estimates[term] + confidence_z * standard_error
        true_value = truth.get(term, 0.0)
        coverage.append(lower - 1e-10 <= true_value <= upper + 1e-10)
    ci_coverage = float(np.mean(coverage)) if coverage else float("nan")

    return RecoveryMetrics(
        individual_mae=individual_mae,
        interaction_mae=interaction_mae,
        interaction_sign_accuracy=interaction_sign_accuracy,
        precision_at_k=precision_at_k,
        recall_at_k=recall_at_k,
        nonzero_spearman=nonzero_spearman,
        detected_interaction_recall=detected_interaction_recall,
        null_false_positive_rate=null_false_positive_rate,
        ci_coverage=ci_coverage,
        true_interaction_sign_stability=true_interaction_sign_stability,
    )
