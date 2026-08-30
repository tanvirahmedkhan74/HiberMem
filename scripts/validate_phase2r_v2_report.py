"""Validate raw v2 screening artifacts without running a model."""

from hibermem.evaluation.artifacts import main, validate_report

__all__ = ["validate_report"]


if __name__ == "__main__":
    raise SystemExit(main())
