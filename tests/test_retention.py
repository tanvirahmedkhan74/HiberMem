import pytest

from hibermem.retention import (
    interaction_aware_mask,
    item_value_mask,
    mobius_to_shapley_items,
    random_mask,
)


def test_item_and_interaction_policies_are_distinct() -> None:
    coefficients = {
        (): 0.0,
        (0,): 0.05,
        (1,): 0.0,
        (2,): 0.05,
        (3,): 0.0,
        (0, 1): 0.20,
        (2, 3): 0.20,
    }
    item_values = mobius_to_shapley_items(coefficients, 4)
    assert item_values == pytest.approx({0: 0.15, 1: 0.1, 2: 0.15, 3: 0.1})
    assert item_value_mask(item_values, 4, 2) == (True, False, True, False)
    assert interaction_aware_mask(coefficients, 4, 2) == (True, True, False, False)


def test_random_retention_is_seeded_and_budgeted() -> None:
    first = random_mask(8, 3, 42)
    assert first == random_mask(8, 3, 42)
    assert sum(first) == 3
