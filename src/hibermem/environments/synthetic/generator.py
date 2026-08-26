"""Phase 1 benchmark generation with deterministic ground truth and noise."""

from __future__ import annotations

import random
from dataclasses import dataclass

from hibermem.coalition.masks import Mask, mask_to_coalition, mask_to_index

from .polynomial_game import PolynomialGame

PHASE1_FAMILIES = (
    "additive",
    "pair_synergy",
    "pair_redundancy",
    "triple_synergy",
    "distractors",
    "noisy_reward",
    "conflicting",
)


@dataclass(frozen=True)
class SyntheticGameSpec:
    game_id: str
    family: str
    seed: int
    game: PolynomialGame
    noise_std: float


def _magnitude(rng: random.Random, low: float, high: float) -> float:
    return round(rng.uniform(low, high), 4)


def _make_spec(family: str, replicate: int, n_players: int, seed: int) -> SyntheticGameSpec:
    rng = random.Random(seed)
    players = list(range(n_players))
    rng.shuffle(players)
    coefficients: dict[tuple[int, ...], float] = {(): round(rng.uniform(-0.3, 0.3), 4)}

    # Every non-additive family includes ordinary item effects. This makes the
    # recovery task explicitly distinguish item contribution from interactions.
    for player in players[:4]:
        sign = -1.0 if rng.random() < 0.3 else 1.0
        coefficients[(player,)] = sign * _magnitude(rng, 0.7, 1.5)

    noise_std = 0.0
    if family == "additive":
        pass
    elif family == "pair_synergy":
        coefficients[tuple(sorted(players[0:2]))] = _magnitude(rng, 2.0, 3.5)
        coefficients[tuple(sorted(players[2:4]))] = _magnitude(rng, 1.5, 3.0)
    elif family == "pair_redundancy":
        coefficients[tuple(sorted(players[0:2]))] = -_magnitude(rng, 2.0, 3.5)
        coefficients[tuple(sorted(players[2:4]))] = -_magnitude(rng, 1.5, 3.0)
    elif family == "triple_synergy":
        coefficients[tuple(sorted(players[0:3]))] = _magnitude(rng, 2.5, 4.0)
        coefficients[tuple(sorted(players[3:6]))] = _magnitude(rng, 2.0, 3.5)
    elif family == "distractors":
        # players[6:] are guaranteed dummy variables in the eight-player setup.
        coefficients[tuple(sorted(players[0:2]))] = _magnitude(rng, 2.0, 3.0)
        coefficients[tuple(sorted(players[2:5]))] = -_magnitude(rng, 2.0, 3.0)
    elif family == "noisy_reward":
        coefficients[tuple(sorted(players[0:2]))] = _magnitude(rng, 2.0, 3.0)
        coefficients[tuple(sorted(players[2:4]))] = -_magnitude(rng, 1.5, 2.5)
        coefficients[tuple(sorted(players[4:7]))] = _magnitude(rng, 2.5, 3.5)
        noise_std = 0.15
    elif family == "conflicting":
        coefficients[tuple(sorted(players[0:2]))] = _magnitude(rng, 2.0, 3.0)
        coefficients[tuple(sorted(players[1:3]))] = -_magnitude(rng, 2.0, 3.0)
        coefficients[tuple(sorted(players[3:6]))] = _magnitude(rng, 2.0, 3.0)
        noise_std = 0.05
    else:
        raise ValueError(f"unknown synthetic family: {family}")

    canonical = {tuple(sorted(term)): value for term, value in coefficients.items()}
    game_id = f"{family}-{replicate:02d}"
    return SyntheticGameSpec(
        game_id=game_id,
        family=family,
        seed=seed,
        game=PolynomialGame(n_players, canonical),
        noise_std=noise_std,
    )


def generate_phase1_benchmark(
    n_games: int = 28, n_players: int = 8, seed: int = 1729
) -> tuple[SyntheticGameSpec, ...]:
    """Generate a family-balanced Phase 1 benchmark.

    ``n_games`` must be a positive multiple of the seven preregistered families
    so aggregate metrics cannot be improved by silently changing family weights.
    """

    if n_games < len(PHASE1_FAMILIES) or n_games % len(PHASE1_FAMILIES):
        raise ValueError(f"n_games must be a positive multiple of {len(PHASE1_FAMILIES)}")
    if n_players < 8:
        raise ValueError("the Phase 1 family definitions require at least 8 players")
    specs = []
    replicates = n_games // len(PHASE1_FAMILIES)
    for replicate in range(replicates):
        for family_index, family in enumerate(PHASE1_FAMILIES):
            game_seed = seed + replicate * 10_000 + family_index * 1_003
            specs.append(_make_spec(family, replicate, n_players, game_seed))
    return tuple(specs)


def observe_coalitions(
    spec: SyntheticGameSpec, masks: tuple[Mask, ...], observation_seed: int
) -> tuple[float, ...]:
    """Evaluate masks and add deterministic coalition-specific Gaussian noise."""

    values = []
    for mask in masks:
        truth = spec.game.value(mask_to_coalition(mask))
        if spec.noise_std:
            mask_seed = observation_seed * 1_000_003 + spec.seed * 97 + mask_to_index(mask)
            truth += random.Random(mask_seed).gauss(0.0, spec.noise_std)
        values.append(truth)
    return tuple(values)
