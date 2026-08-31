# Next experiment sets and implementation plan — 2026-08-31

Authority: [adversarial audit](ADVERSARIAL_RESEARCH_AUDIT_2026-08-31.md) and the
[master plan](../HiberMem_MASTER_RESEARCH_IMPLEMENTATION_PLAN.md).

## Invariants

- Preserve all historical artifacts and negative v2 qualification outcomes.
- No confirmation/test generation, scoring, unlock, or automatic candidate selection.
- Every new report explicitly distinguishes exact game quantities, surrogate
  quantities, in-sample descriptive retention, and future evidence (not yet collected).
- Stateless inference between coalitions. No removed information survives in history.
- Real inference requires committed source/config and a pinned model revision.
- No new model installation or GPU inference is performed by unit tests.

## Experiment matrix

| Set | Purpose | Data / budget | Current implementation status |
|---|---|---|---|
| E0 | Reproduce local four-corner interactions from existing v2 bundles | Read-only validated Qwen/Phi artifacts; no inference | Implemented; estimates reproduced |
| E1 | Measure full coalition games and approximation error | Fresh development banks 320–321, 8 items, 4 distinct two-hop queries each, 256 masks = 2,048 conditions | Implemented; real inference pending |
| E2 | Presentation sensitivity | Same E1 facts: original, reversed record presentation, reversed option order = 6,144 conditions in a separate run | Implemented; real inference pending |
| E3 | Semantic overlap × functional dependency | New development generator: independent/AND/OR/three-way/conflict/temporal controls | Planned; not implemented in this tranche |
| E4 | Prospective retention | Freeze protocol on development; independent bank cohorts and past/future streams; exact and budget-conditioned baselines | Blocked on development review and preregistration |
| E5 | Matched structural lesion | Separate future cohort; match count/cost/item utility and nuisance factors | Blocked on prospective evidence |
| E6 | Natural conversational memory / scale | LongMemEval/LoCoMo; retrieval and total storage/latency baselines | Only after mechanism/lesion evidence |

E1/E2 are a **new development diagnostic**, not a relaxed replacement for v2.
Completing them has no qualification meaning. E2 reuses E1 facts intentionally;
its variants are paired conditions, never extra independent banks. Banks 320–321
are fresh relative to the supplied 300–309 screens, not a permanently reusable test.

## Implementation tranche

1. Archive the audit, preserving exact empirical numbers and evidence limitations.
2. Add explicit estimator APIs with backward-compatible legacy methods. Compute
   model-based standard errors from an SVD; document iid/misspecification limits.
3. Implement E0 reanalysis after full v2 artifact validation; bank-bootstrap local
   contrasts only. Never infer a scientific gate from them.
4. Implement a strictly development-scoped E1/E2 suite and complete-game analyzer.
   Expose exact Mobius, exact SII, exact Shapley, local/full-context contrasts,
   order-1/2/3 fits, and endpoint/reconstruction errors.
5. Compare exact Shapley, additive, surrogate Shapley, leave-one-out, budget-specific
   marginals, random, shuffled pairs, quadratic selection, and an oracle ceiling.
   These selections/evaluations reuse the same development queries and must be
   labeled **in-sample descriptions**, not policy validation.
6. Add a resumable runner with immutable run identity, request/response evidence,
   source/runtime/model fingerprints, symbolic controls, and an independent
   report validator. Completed reports must be validated without loading a model.
7. Add captured HF token IDs and rendered prompts without changing legacy text
   scoring. Gemma support is deferred until its external adapter can be audited;
   do not pretend the ordinary causal-LM backend supports it.
8. Add a Kaggle launcher using the proven no-ensurepip environment approach.
   Exit 0 means a validated completed diagnostic, **not qualification**; 2 means error.
9. Test reconstruction, higher-order contamination, presentation identity, gate
   denial, corruption rejection, resume safety, source pinning, and no-model controls.

## E1/E2 analysis contract

The utility remains destination correctness, with support/abstention scored
separately. The generator's required pair is available only to diagnostic scoring
and symbolic controls, never to operational subset baselines.

For each query report both empty-context and full-context pair contrasts. For each
bank/variant compute all exact quantities from the complete mean game. Label
regression coefficients as Mobius terms of the fitted surrogate, not exact SII.
All regression R2 is in-sample. No confidence claim is made from the two-bank pilot.

Fixed keep counts 2, 3, 4, 6 correspond to actual deletion 75%, 62.5%, 50%, 25%.
Retained payload bytes and whitespace tokens are audited; total-system and
tokenizer-budget matching are deferred, not claimed. Ties use canonical player order
and are explicitly labeled; randomized tie sensitivity remains an E3/E4 requirement.

## Decision after E1/E2

Review exact versus surrogate disagreement, actual local/contextual interactions,
unsupported-answer behavior, and sensitivity to presentation. No automatic pass
threshold or candidate-selection rule is introduced post hoc. Preserve negative
results. Before E4, specify practical effect sizes, clustered uncertainty,
multiplicity, power, full baseline costs, and the independent future cohorts.

## Verification and execution

See [execution instructions and notebook cells](EXACT_MECHANISM_KAGGLE.md).

- 130 tests passed locally in the project Conda environment.
- Bash syntax passed for the new Kaggle launcher.
- E1 dry run confirms 2,048 conditions; E2 symbolic/shortcut controls checked all
  6,144 conditions without model loading.
- Full E1 (2,048) and E2 (6,144) mock runs completed and passed independent
  artifact validation. The symbolic oracle's coalition utilities were unchanged
  under both presentation variants, as expected. Engineering-only reports are in
  `results/exact_mechanism_local_verification/20260831-e1/report.json` and
  `results/exact_mechanism_local_verification/20260831-e2/report.json`.
- E0 independently validated the existing raw bundles and reproduced Qwen
  0.933333 [0.866667,1] and Phi 0.016667 [−0.033333,0.066667] local interactions.
- Token-trace capture was tested using CPU model/tokenizer stubs, not downloaded
  weights. Actual new cloud inference has not been executed.
- Completed report validation tolerates only numerical analysis roundoff
  (absolute 1e-9, relative 1e-8); raw scoring, IDs, masks, and capability claims
  must match exactly. Selection scores use 12 decimal places before canonical
  tie breaking. Randomized tie sensitivity remains deferred.

Real Kaggle runs require committing and pushing these changes first. No commit,
push, historical-result overwrite, confirmation unlock, or real-model execution
was performed during this implementation.
