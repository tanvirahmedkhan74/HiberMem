"""Memory-dependent survival metrics with explicit undefined cases."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def normalized_memory_retention(
    accuracy: float, empty_accuracy: float, full_accuracy: float
) -> float | None:
    """Return R only when full memory has a strictly positive contribution."""

    denominator = full_accuracy - empty_accuracy
    if denominator <= 0:
        return None
    return (accuracy - empty_accuracy) / denominator


def normalized_survival_auc(
    deletion_ratios: Sequence[float], retention_values: Sequence[float | None]
) -> float | None:
    if len(deletion_ratios) != len(retention_values) or len(deletion_ratios) < 2:
        raise ValueError("matching metric sequences of length at least two are required")
    if any(value is None for value in retention_values):
        return None
    ratios = np.asarray(deletion_ratios, dtype=float)
    values = np.asarray(retention_values, dtype=float)
    if np.any(np.diff(ratios) <= 0):
        raise ValueError("deletion ratios must be strictly increasing")
    return float(np.trapezoid(values, ratios) / (ratios[-1] - ratios[0]))


def memory_rho50_interval(
    deletion_ratios: Sequence[float], retention_values: Sequence[float | None]
) -> tuple[float, float] | None:
    """Return the grid interval containing the first R=0.5 crossing."""

    if len(deletion_ratios) != len(retention_values):
        raise ValueError("metric sequences must have equal length")
    if any(value is None for value in retention_values):
        return None
    for index, value in enumerate(retention_values):
        assert value is not None
        if value <= 0.5:
            if index == 0:
                return (deletion_ratios[0], deletion_ratios[0])
            return (deletion_ratios[index - 1], deletion_ratios[index])
    return None
