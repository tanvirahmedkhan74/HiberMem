import pytest

from hibermem.evaluation import (
    memory_rho50_interval,
    normalized_memory_retention,
    normalized_survival_auc,
)


def test_zero_and_full_memory_metric() -> None:
    assert normalized_memory_retention(0.2, 0.2, 0.8) == pytest.approx(0.0)
    assert normalized_memory_retention(0.8, 0.2, 0.8) == pytest.approx(1.0)
    assert normalized_memory_retention(0.3, 0.4, 0.4) is None
    assert normalized_memory_retention(0.3, 0.5, 0.4) is None


def test_survival_curve_summaries() -> None:
    ratios = [0.0, 0.5, 0.8]
    values = [1.0, 0.6, 0.2]
    assert normalized_survival_auc(ratios, values) == pytest.approx(0.65)
    assert memory_rho50_interval(ratios, values) == (0.5, 0.8)
