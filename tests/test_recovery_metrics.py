import pytest

from hibermem.coalition.sampling import size_balanced_masks
from hibermem.environments.synthetic import PolynomialGame
from hibermem.evaluation import recovery_metrics
from hibermem.interactions.polynomial import PolynomialInteractionEstimator
from hibermem.interactions.stability import BootstrapTermSummary


def test_perfect_recovery_metrics_distinguish_items_and_interactions() -> None:
    truth = {(): 0.2, (0,): 1.0, (3,): -0.5, (0, 1): 2.0, (2, 4, 5): -3.0}
    game = PolynomialGame(6, truth)
    masks = size_balanced_masks(6, 60, seed=101)
    values = tuple(game.value(i for i, present in enumerate(mask) if present) for mask in masks)
    estimator = PolynomialInteractionEstimator(max_order=3, n_players=6).fit(masks, values)
    stability = {
        term: BootstrapTermSummary(
            mean=estimator.coefficients[term],
            standard_deviation=0.0,
            lower=estimator.coefficients[term],
            upper=estimator.coefficients[term],
            sign_consistency=1.0,
        )
        for term in estimator.terms
    }
    metrics = recovery_metrics(
        truth,
        estimator,
        stability,
        practical_detection_threshold=0.25,
        confidence_z=1.96,
    )
    assert metrics.individual_mae == pytest.approx(0.0, abs=1e-10)
    assert metrics.interaction_mae == pytest.approx(0.0, abs=1e-10)
    assert metrics.interaction_sign_accuracy == pytest.approx(1.0)
    assert metrics.precision_at_k == pytest.approx(1.0)
    assert metrics.recall_at_k == pytest.approx(1.0)
    assert metrics.null_false_positive_rate == pytest.approx(0.0)
    assert metrics.true_interaction_sign_stability == pytest.approx(1.0)
