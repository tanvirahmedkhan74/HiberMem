from collections import Counter

import pytest

from hibermem.coalition.masks import mask_to_index
from hibermem.coalition.sampling import size_balanced_masks


def test_size_balanced_sampling_is_unique_deterministic_and_covers_extremes() -> None:
    first = size_balanced_masks(8, 192, seed=123)
    second = size_balanced_masks(8, 192, seed=123)
    assert first == second
    assert len(first) == len({mask_to_index(mask) for mask in first}) == 192
    assert (False,) * 8 in first
    assert (True,) * 8 in first
    size_counts = Counter(sum(mask) for mask in first)
    assert set(size_counts) == set(range(9))
    # Bins of sizes 1 and 7 contain only eight coalitions, so a large budget
    # necessarily saturates them before allocating the remainder to middle bins.
    assert size_counts[0] == size_counts[8] == 1
    assert all(abs(size_counts[size] - size_counts[8 - size]) <= 1 for size in range(1, 4))
    assert abs(size_counts[3] - size_counts[4]) <= 1


def test_full_budget_returns_exact_mask_order() -> None:
    masks = size_balanced_masks(4, 16, seed=999)
    assert [mask_to_index(mask) for mask in masks] == list(range(16))


@pytest.mark.parametrize("budget", [0, 1, 17])
def test_invalid_sampling_budget_is_rejected(budget: int) -> None:
    with pytest.raises(ValueError):
        size_balanced_masks(4, budget, seed=1)
