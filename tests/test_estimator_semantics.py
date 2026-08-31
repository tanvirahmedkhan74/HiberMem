import numpy as np
import pytest

from hibermem.coalition.masks import iter_masks
from hibermem.interactions.polynomial import PolynomialInteractionEstimator
from hibermem.interactions.shapley import ExactInteractionEstimator


@pytest.mark.parametrize("n,quadratic_pair,sii_pair,surrogate_item", [(3,.5,.5,.25), (4,.25,1/3,.125)])
def test_complete_enumeration_does_not_fix_omitted_order(n, quadratic_pair, sii_pair, surrogate_item):
    masks = tuple(iter_masks(n))
    rewards = [float(all(mask)) for mask in masks]
    exact = ExactInteractionEstimator(n).fit(masks, rewards)
    fitted = PolynomialInteractionEstimator(max_order=2, n_players=n).fit(masks, rewards)
    assert list(exact.shapley_item_values().values()) == pytest.approx([1/n] * n)
    assert fitted.shapley_item_values() == pytest.approx(dict.fromkeys(range(n), surrogate_item))
    assert fitted.singleton_coefficients() == pytest.approx(dict.fromkeys(range(n), -.25))
    assert fitted.individual_values() == fitted.singleton_coefficients()
    assert all(value == pytest.approx(quadratic_pair) for value in fitted.interactions(2).values())
    assert all(value == pytest.approx(sii_pair) for value in exact.sii_values(2).values())
    assert all(value == 0 for term, value in exact.mobius_coefficients().items() if 1 <= len(term) <= 2)
    assert fitted.mobius_coefficients() == fitted.coefficients


def test_svd_standard_errors_match_well_conditioned_reference():
    masks = tuple(iter_masks(4))
    rng = np.random.default_rng(3)
    values = rng.normal(size=len(masks))
    fit = PolynomialInteractionEstimator(max_order=2).fit(masks, values)
    design = fit._design_matrix(masks, fit.terms)
    residual_variance = np.sum(fit.residuals ** 2) / fit.degrees_of_freedom
    expected = np.sqrt(np.diag(residual_variance * np.linalg.inv(design.T @ design)))
    assert list(fit.standard_errors.values()) == pytest.approx(expected)


def test_additive_null_and_redundancy_semantics():
    masks = tuple(iter_masks(3))
    # OR on players 0/1; player 2 is null.
    values = [float(mask[0] or mask[1]) for mask in masks]
    exact = ExactInteractionEstimator().fit(masks, values)
    fitted = PolynomialInteractionEstimator(max_order=2).fit(masks, values)
    assert exact.mobius_coefficients()[(0,1)] == -1
    assert exact.sii_values(2)[(0,1)] == -1
    assert exact.shapley_item_values() == pytest.approx({0:.5,1:.5,2:0})
    assert fitted.shapley_item_values() == pytest.approx(exact.shapley_item_values(), abs=1e-12)
