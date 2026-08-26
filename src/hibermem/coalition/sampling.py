"""Deterministic coalition samplers for controlled experiments."""

from __future__ import annotations

import random

from .masks import Mask, index_to_mask, mask_to_index


def size_balanced_masks(n_players: int, budget: int, seed: int) -> tuple[Mask, ...]:
    """Sample unique masks while balancing representation across coalition sizes.

    Empty and grand coalitions are always included when ``budget >= 2``. If the
    budget covers the full powerset, exact integer-mask enumeration is returned.
    The output is sorted by canonical mask index so downstream noise generation
    and serialization do not depend on sampling order.
    """

    if isinstance(n_players, bool) or not isinstance(n_players, int) or n_players < 1:
        raise ValueError("n_players must be a positive integer")
    total = 1 << n_players
    if isinstance(budget, bool) or not isinstance(budget, int) or not 2 <= budget <= total:
        raise ValueError(f"budget must be between 2 and {total}")
    if budget == total:
        return tuple(index_to_mask(index, n_players) for index in range(total))

    rng = random.Random(seed)
    groups: list[list[int]] = [[] for _ in range(n_players + 1)]
    for index in range(total):
        groups[index.bit_count()].append(index)
    for group in groups:
        rng.shuffle(group)

    allocation = [0] * (n_players + 1)
    allocation[0] = 1
    allocation[-1] = 1
    remaining = budget - 2

    # First give every non-extreme size a representative when the budget allows.
    for size in range(1, n_players):
        if remaining == 0:
            break
        allocation[size] += 1
        remaining -= 1

    # Then distribute capacity round-robin instead of proportional-to-bin-size;
    # this prevents middle-sized coalitions from dominating the sample.
    while remaining:
        progressed = False
        for size in range(1, n_players):
            if remaining == 0:
                break
            if allocation[size] < len(groups[size]):
                allocation[size] += 1
                remaining -= 1
                progressed = True
        if not progressed:
            raise RuntimeError("unable to allocate coalition budget")

    chosen: list[int] = []
    for size, count in enumerate(allocation):
        chosen.extend(groups[size][:count])
    chosen.sort()
    masks = tuple(index_to_mask(index, n_players) for index in chosen)
    if len(masks) != budget or len({mask_to_index(mask) for mask in masks}) != budget:
        raise RuntimeError("sampler produced an invalid coalition set")
    return masks
