"""Predictive diagnostics; these metrics never select retention masks."""

from __future__ import annotations

import numpy as np


def prediction_metrics(observed, predicted) -> dict[str, float | None]:
    actual, prediction = np.asarray(observed, dtype=float), np.asarray(predicted, dtype=float)
    if actual.ndim != 1 or actual.shape != prediction.shape or actual.size == 0:
        raise ValueError("matching nonempty one-dimensional arrays are required")
    if not np.all(np.isfinite(actual)) or not np.all(np.isfinite(prediction)):
        raise ValueError("prediction metrics require finite values")
    error = actual - prediction
    denominator = float(np.sum((actual - actual.mean()) ** 2))
    return {"r2": 1.0 - float(np.sum(error ** 2)) / denominator if denominator > 0 else None,
            "rmse": float(np.sqrt(np.mean(error ** 2))), "mae": float(np.mean(abs(error)))}


def paired_bank_interval(differences, *, seed: int = 20260830, resamples: int = 10000) -> dict:
    values = np.asarray(differences, dtype=float)
    if values.ndim != 1 or len(values) < 2 or not np.all(np.isfinite(values)) or resamples < 2:
        raise ValueError("at least two finite bank differences and resamples are required")
    rng = np.random.default_rng(seed)
    means = rng.choice(values, size=(resamples, len(values)), replace=True).mean(axis=1)
    return {"mean": float(values.mean()), "median": float(np.median(values)),
            "lower_95": float(np.quantile(means, .025)), "upper_95": float(np.quantile(means, .975)),
            "positive_bank_fraction": float(np.mean(values > 0)),
            "unit": "memory bank", "n_banks": len(values), "resamples": resamples, "seed": seed}
