# Phase 1 Validation: Deterministic Synthetic Interaction Recovery

**Status:** Gate P1 passed  
**Date:** 2026-08-26  
**Runtime:** project-local Conda environment, Python 3.11  
**Scientific scope:** method validation only; this phase provides no evidence
that natural LLM external memories contain useful interaction structure.

## Prerequisite verification

The user-provided terminal transcript showed repeated Phase 0 success, including
the independent `shapiq` comparison. Phase 0 was rerun inside the new Conda
environment and passed again with 21 tests.

The earlier pytest cache warning was unrelated to the implementation. Pytest's
optional cache provider is now disabled so read-only or unusual directory ACLs
do not produce warnings.

## Preregistered protocol

The frozen configuration is
[`configs/experiments/phase1.json`](../configs/experiments/phase1.json).

- 28 games: four replicates from each of seven equally weighted families;
- 8 players per game;
- 192 unique coalitions sampled with constrained balance across coalition size;
- polynomial order at most 3;
- known Möbius/Harsanyi ground-truth coefficients;
- additive, positive pair, negative pair, triple, distractor/dummy, noisy, and
  conflicting-interaction families;
- ordinary least squares in the explicit binary monomial basis;
- analytical standard errors;
- 20 deterministic fixed-design residual-bootstrap replicates;
- a practical detection floor of 0.25 plus a 95% interval excluding zero.

This phase uses Möbius coefficients because the synthetic games are generated in
that exact basis. It does not relabel them as Shapley Interaction Index values.

## Gate criteria and observed results

| Metric | Criterion | Result | Verdict |
|---|---:|---:|---|
| Interaction sign accuracy | ≥ 0.97 | 1.000000 | PASS |
| Precision@k | ≥ 0.90 | 1.000000 | PASS |
| Recall@k | ≥ 0.90 | 1.000000 | PASS |
| Spearman on nonzero interactions | ≥ 0.90 | 1.000000 | PASS |
| Individual-term MAE | ≤ 0.20 | 0.015359 | PASS |
| Interaction-term MAE | ≤ 0.20 | 0.016337 | PASS |
| Null interaction false-positive rate | ≤ 0.05 | 0.003086 | PASS |
| Noisy-game 95% interval coverage | ≥ 0.90 | 0.938172 | PASS |
| True-interaction sign stability | ≥ 0.90 | 1.000000 | PASS |

The complete test suite contains 36 passing tests. `pip check` reports no broken
environment requirements.

## Reproducibility

Two complete Phase 1 executions produced identical artifact hashes:

```text
observations.jsonl  F293CAC09CBF8DF5B2704ADECAF6D6A5B6E3CC501634565E84762F4E26493B5B
estimates.jsonl     ADD4A0EFD21E9E77F069746347C5F21BA7E8FF8D7A66274AE27550C4D114FB5D
```

Every run is preserved in a timestamped directory. The latest summary is
[`results/phase1_report.json`](../results/phase1_report.json); it points to the
immutable observations, estimates, and report for that run.

## Gate interpretation

P1 demonstrates that the selected sampling, estimator, uncertainty, and metric
pipeline can recover controlled low-order structure while separating item terms
from pair/triple interactions. It validates the machinery required before an LLM
experiment.

It does **not** establish H1, H2, or H3, does not justify the word “engram,” and
does not authorize graph retrieval, RL, regrowth, or later system architecture.
The next permissible work item is Phase 2: a locked, controlled natural-language
LLM coalition game.
