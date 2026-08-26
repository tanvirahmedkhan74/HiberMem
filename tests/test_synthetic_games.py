import pytest

from hibermem.coalition.masks import index_to_mask
from hibermem.environments.synthetic import (
    PHASE1_FAMILIES,
    PolynomialGame,
    generate_phase1_benchmark,
    observe_coalitions,
)
from hibermem.interactions.mobius import mobius_coefficients


def test_polynomial_game_coefficients_are_its_mobius_truth() -> None:
    truth = {(): 0.2, (0,): 1.0, (1, 2): -2.5, (0, 2, 3): 4.0}
    game = PolynomialGame(4, truth)
    recovered = mobius_coefficients(game)
    for term, value in recovered.items():
        assert value == pytest.approx(truth.get(term, 0.0))


def test_phase1_benchmark_is_balanced_and_deterministic() -> None:
    first = generate_phase1_benchmark(28, 8, 1729)
    second = generate_phase1_benchmark(28, 8, 1729)
    assert [spec.game_id for spec in first] == [spec.game_id for spec in second]
    assert [spec.game.coefficients for spec in first] == [spec.game.coefficients for spec in second]
    assert {family: sum(spec.family == family for spec in first) for family in PHASE1_FAMILIES} == {
        family: 4 for family in PHASE1_FAMILIES
    }
    assert all(spec.game.max_order <= 3 for spec in first)


def test_noisy_observations_are_reproducible_and_seeded() -> None:
    spec = next(
        spec for spec in generate_phase1_benchmark(7, 8, 99) if spec.family == "noisy_reward"
    )
    masks = tuple(index_to_mask(index, 8) for index in range(16))
    first = observe_coalitions(spec, masks, observation_seed=7)
    second = observe_coalitions(spec, masks, observation_seed=7)
    third = observe_coalitions(spec, masks, observation_seed=8)
    assert first == second
    assert first != third


def test_distractor_family_contains_dummy_players() -> None:
    spec = next(
        spec for spec in generate_phase1_benchmark(7, 8, 41) if spec.family == "distractors"
    )
    active = {player for term in spec.game.coefficients if term for player in term}
    assert len(set(range(8)) - active) >= 2
