"""Deterministic synthetic coalition games."""

from .generator import (
    PHASE1_FAMILIES,
    SyntheticGameSpec,
    generate_phase1_benchmark,
    observe_coalitions,
)
from .polynomial_game import PolynomialGame

__all__ = [
    "PHASE1_FAMILIES",
    "PolynomialGame",
    "SyntheticGameSpec",
    "generate_phase1_benchmark",
    "observe_coalitions",
]
