import pytest

from hibermem.evaluation.predictive import paired_bank_interval, prediction_metrics


def test_predictive_r2_is_not_squared_correlation_or_clipped():
    assert prediction_metrics([1, 2, 3], [1, 2, 3])["r2"] == 1
    assert prediction_metrics([1, 2, 3], [3, 2, 1])["r2"] == -3
    assert prediction_metrics([1, 1], [0, 0])["r2"] is None
    with pytest.raises(ValueError):
        prediction_metrics([1], [float("nan")])


def test_bank_bootstrap_is_paired_and_reproducible():
    first = paired_bank_interval([.1, .2, 0, -.1], seed=3)
    assert first == paired_bank_interval([.1, .2, 0, -.1], seed=3)
    assert first["n_banks"] == 4
    assert first["mean"] == pytest.approx(.05)
