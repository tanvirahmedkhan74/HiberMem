# E4 prospective retention implementation plan — 2026-09-02

**Status:** E3c and E4 engineering/design code implemented and mock-validated; real
E3c/E4 inference, variance planning, and confirmation have not run.

**Authority:** the [master research plan](../HiberMem_MASTER_RESEARCH_IMPLEMENTATION_PLAN.md),
the [adversarial audit](ADVERSARIAL_RESEARCH_AUDIT_2026-08-31.md), and the
[validated E3 core findings](E3_CORE_RESULTS_AND_NEXT_STEP_2026-08-31.md).

## 1. Decision and phase mapping

The master plan's central question remains unchanged: do memory interactions learned
from past behavior predict and preserve future behavior beyond individual memory
importance? The repository's experiment labels map to the master phases as follows:

| Repository set | Scientific role | Master-plan role |
|---|---|---|
| E0–E3 | Mathematical, estimator, capability, and exact-game development | Phases 0–2 diagnostics |
| E4 | Prospective interaction-aware retention, H1/H3 | Prospective part of Phase 2 and prerequisite to the core lesion |
| E5 | Item-value-matched structural lesions, H2 | Phase 3 and Gate P3 |
| E6 | Natural conversational memory and scale | Phases 4–5 |
| Later system work | Retrieval, consolidation, turnover, topology, regrowth | Phases 6–9 |

E3 establishes that the selected Qwen model can express the designed direct, AND2,
OR2, and AND3 games when enough decoding budget is available. It does not establish
future-query stability. E4 must use new banks and freeze every selection before any
future-query outcome is available. It must not access or unlock the historical Phase-2
test split.

## 2. Preconditions and the E3c output-contract diagnostic

Decode64 recovered 880 supported answers that the 16-token run missed, but all 885
newly correct answers violated the requested label-only format; 852 still terminated
at the 64-token limit. Unsupported assertions also remain material for AND2/AND3.
Launching a large prospective study with this unresolved behavior would mix memory
selection with formatting and guessing.

Before real E4 execution, run the implemented, separately versioned **E3c development
diagnostic** on fresh banks. It compares the current decoder with a reinforced
answer-slot contract. It may be extended only under a new reviewed version to compare
other predeclared contracts, including a closed choice among the action labels
and `UNKNOWN`. It must:

- use fresh development banks and the same validated AND2/AND3 support logic;
- change one output-contract factor at a time;
- retain original correctness as the capability outcome;
- report strict format, cap hits, supported accuracy, unsupported assertion,
  abstention, latency, and token cost separately;
- choose a contract only by predeclared capability/grounding criteria, never by a
  retention-policy advantage;
- create a new protocol/config identity if prompts, parsing, generation, or constrained
  decoding change; and
- preserve the E3 core and decode64 reports unchanged.

Recommended readiness targets for a contract pilot are at least .95 supported
accuracy on AND2 and AND3, at least .95 strict-format rate, at most .05 cap-hit rate,
and at most .05 unsupported-assertion rate. These are engineering readiness criteria,
not scientific gates and may not be relaxed after looking at failures. If no contract
meets them, stop and repair capability/grounding before E4.

## 3. E4 estimands and hypotheses

For bank \(b\), let \(Q^P_b\) be past/discovery queries and \(Q^F_b\) be disjoint
future queries. For coalition \(S\):

\[
v^P_b(S)=\frac{1}{|Q^P_b|}\sum_{q\in Q^P_b}r(q,S),
\qquad
v^F_b(S)=\frac{1}{|Q^F_b|}\sum_{q\in Q^F_b}r(q,S).
\]

Fit all item and interaction quantities to \(v^P_b\) only. For method \(m\) and
budget \(k\), freeze \(S_{bmk}\) before opening the future view, then compute
\(A^F_{bmk}\) on future queries.

The primary bank-level effect is

\[
D_b=\frac{1}{2}\sum_{k\in\{2,3\}}
\left(A^F_{b,\mathrm{quadratic},k}
-A^F_{b,\mathrm{exact\ Shapley},k}\right).
\]

Keep-2 and keep-3 delete 75% and 62.5% of an eight-record bank. The primary endpoint
is the mean paired original-correctness difference across independent banks. It is
not support-filtered and cannot reward abstention as correctness. Support decomposition
is a secondary diagnostic.

Secondary estimands:

- normalized memory-dependent retention
  \(R=(A-A_\emptyset)/(A_\mathrm{full}-A_\emptyset)\), left undefined when the
  denominator is nonpositive;
- past-fitted prediction \(R^2\), RMSE, and MAE on future coalition outcomes, with
  negative \(R^2\) retained and constant targets marked undefined; these use a
  method-independent future coalition probe panel fixed before past fitting, not only
  the masks selected by a policy;
- sign/rank stability and top-coalition overlap from past to future;
- full/empty capability, support, abstention, unsupported assertion, and strict format;
- retained serialized bytes/tokens, estimation calls, inference tokens, latency, and
  peak memory; and
- exploratory keep-4/keep-6 results, labeled as 50%/25% deletion rather than severe.

E4 supports H1/H3 only if the prospective effect is practically meaningful and
replicates across banks. It cannot establish H2; that requires E5 lesions.

## 4. Dataset and query-shift design

Use eight records per bank so the past game can be enumerated exactly over 256 masks.
Every bank is one independent unit. Worlds, queries, paraphrases, presentations,
coalitions, and random seeds are repeated measures—not additional banks.

Each bank manifest must be generated before inference and contain:

- opaque bank, memory, role, and query identifiers;
- exactly eight immutable memory records with canonical positions and cost metadata;
- latent dependency/support antichains used only by the generator, symbolic controls,
  and diagnostic annotations;
- separate past and future query IDs and seeds;
- a declared shift stratum; and
- hashes of the public past view and sealed future view.

Do not pool distinct forms of shift into one unqualified claim. Implement and report
them as strata:

1. **Paraphrase/presentation:** same latent target, independently generated wording;
2. **Compositional:** new targets or paths formed from the same bank rules;
3. **Dependency-frequency:** a declared change in the mixture of direct, AND2, OR2,
   and AND3 query mechanisms; and
4. **Temporal/authority:** only after E3b defines source precedence, as-of-time truth,
   and stale-answer scoring.

The primary E4 confirmation should use one frozen shift mixture. Other strata are
secondary or separately multiplicity-controlled. Semantic overlap, counterfactual
worlds, and query variants must not be presented as independent replications.

Recommended development scale is 8–12 past and 12–20 future queries per bank. The
exact count and bank count are frozen after engineering and variance pilots, not
selected from confirmation effects. A complete past table costs
`past_queries * 256` generations per bank. Primary future retention generates the
deduplicated full, empty, and frozen policy masks. A separate diagnostic prediction
panel is fixed before past fitting and may enumerate all 256 masks for a declared
future-query subset or use a fixed balanced sample when compute requires it. Never
choose its masks from past coefficients or future outcomes.

## 5. Cohorts, freezing, and power

Use nonoverlapping cohorts:

1. **Engineering cohort:** symbolic/mock and a few fresh real development banks for
   output contract, schemas, and runtime checks. No scientific inference.
2. **Design cohort:** fresh development banks for choosing the query mixture,
   estimator order, tie policy, and feasibility thresholds.
3. **Variance-only pilot:** execute the already frozen design on fresh banks to
   estimate bank-level variance and determine confirmation sample size. Do not change
   the effect direction, endpoint, baseline, or practical effect after this pilot.
4. **Confirmation cohort:** fresh bank seeds and sealed future queries; one planned
   analysis after all evidence passes validation.

Record the practical difference \(\delta\) before confirmation. The current planning
value of .03 is illustrative, not a discovered effect. A normal approximation

\[
B\approx((1.96+0.84)\sigma_D/\delta)^2
\]

may size the paired bank study, followed by simulation using the pilot's bounded
outcome distribution. Enforce a prespecified minimum number of independent banks,
report the calculation, and never count within-bank queries as extra sample size.

## 6. Frozen methods and fair budgets

All operational methods receive the identical past coalition table and future query
budget. Required-support metadata and future answers are forbidden inputs.

Primary methods:

- **Exact Shapley item retention:** ordinary item values from the complete past game;
- **Quadratic interaction retention:** exact exhaustive subset optimization of the
  past-fitted order-2 surrogate.

Required secondary baselines:

- random retention with prespecified seeds;
- additive/singleton surrogate;
- leave-one-out item values;
- budget-conditioned item marginals;
- cubic surrogate selection;
- shuffled-interaction negative control;
- applicable recency, frequency, and semantic/embedding rankings; and
- a clearly labeled past-game oracle ceiling.

Use deterministic exhaustive selection for eight items. Round only for stable tie
comparison, then apply a frozen canonical tie rule; report randomized tie sensitivity.
Match exact retained count and serialized payload cost. If record lengths differ,
optimize under a tokenizer-cost cap shared by all methods rather than silently giving
one method more context. Report index/model metadata and estimation compute separately.
All surviving memories are supplied directly in canonical order; retrieval is not an
E4 variable.

## 7. Leakage-safe execution state machine

Implement a new protocol such as `phase2r-prospective-retention-v1`; do not extend the
E3 report schema in place.

```text
prepare -> past -> fit -> freeze -> future -> analyze -> validate
```

- `prepare` materializes immutable bank/split manifests and hashes.
- `past` exposes only authorized past queries and evaluates the complete game.
- `fit` derives all methods from past rows and records estimator/tie/cost details.
- `freeze` writes an exclusive-create selection artifact containing bank, method,
  budget, mask, score source, and hashes. It contains no future outcome.
- `future` requires the valid frozen artifact and exposes only the selected masks,
  full/empty controls, and the method-independent prediction probe declared in the
  manifest. It must refuse changed source, config, model, prompt, contract, tokenizer,
  bank manifest, probe, or selection hashes.
- `analyze` computes paired bank outcomes without refitting.
- `validate` independently reconstructs evidence and lineage without loading a model.

Future rows must be a different type/capability from past rows. Fitting and selection
APIs accept only a `PastEvidence` object. Future scoring accepts frozen masks but cannot
return data through a fitting interface. Do not rely on string-valued split checks alone.

## 8. Implemented repository changes

```text
src/hibermem/environments/controlled/contract.py
src/hibermem/environments/controlled/prospective.py
src/hibermem/evaluation/contract.py
src/hibermem/evaluation/prospective.py
src/hibermem/experiments/contract.py
src/hibermem/experiments/prospective.py
src/hibermem/retention/costs.py
scripts/run_e3c_contract.py
scripts/validate_e3c_report.py
scripts/run_e4_prospective.py
scripts/freeze_e4_protocol.py
scripts/validate_e4_report.py
configs/experiments/e3c_output_contract.json
configs/experiments/e4_engineering_mock.json
configs/experiments/e4_design_template.json
kaggle/run_e3c_contract.sh
kaggle/run_e4_prospective.sh
docs/E4_KAGGLE.md
```

Do not create a confirmation config until the contract, design, variance estimate,
sample size, primary endpoint, multiplicity policy, and model revision are frozen in
a reviewed source commit.

## 9. Required tests and acceptance checks

Implemented tests cover:

- deterministic bank/query generation and disjoint IDs/content;
- no future object accepted by fitting, ranking, thresholding, or mask selection;
- future stage denied before an immutable freeze artifact exists;
- freeze artifact overwrite, tampering, reordering, or identity drift rejected;
- support/answer metadata absent from model prompts and policy inputs;
- all methods share past calls, future queries, tokenizer budget, and memory order;
- exact Shapley/Mobius/SII reconstruction on past tables;
- quadratic/cubic predictions generated solely from past coefficients;
- prediction probes fixed before fitting and excluded from selection/primary retention;
- frozen masks remain unchanged during future scoring;
- correct severe-deletion ratios and token/byte accounting;
- normalized retention undefined cases, negative values, and future \(R^2<0\);
- bank-level intervals/permutation tests and no query-level pseudoreplication;
- resume equivalence, duplicate-row rejection, partial/corrupt artifact rejection;
- mock reports labeled engineering-only and real reports pinned to clean source; and
- E4 cannot modify historical P2 unlock/test state or claim P2/P3 qualification.

Engineering acceptance requires symbolic-oracle agreement, exact evidence
reconstruction, stage isolation, deterministic resume, and the full regression suite.
It is not evidence for HiberMem.

## 10. Statistical analysis and decision rule

Report every bank's \(D_b\), the paired mean and median, positive-bank fraction,
bank bootstrap 95% interval, and a paired sign-flip/randomization test. Queries and
seeds stay nested within bank. Stratified results and interaction-by-shift analyses are
secondary and multiplicity-controlled.

Before confirmation, freeze one of these decision rules with a practical margin:

- **advance to E5:** the prospective interaction method exceeds exact Shapley by the
  prespecified margin, uncertainty excludes a negligible/reversed effect, and the
  pattern is not a one-bank, guessing, formatting, or cost artifact;
- **replicate without expansion:** direction is promising but uncertainty is too wide;
- **stop/pivot:** item retention matches or exceeds interaction retention, past-to-future
  structure is unstable, or benefits disappear under cost/support diagnostics.

No E4 result unlocks the historical P2 test. E4 confirmation is a new, separately
versioned prospective study.

## 11. Experiments after E4

### E5 — matched structural lesion (decisive causal test)

On a separately reserved future cohort, construct deletion pairs matched on count,
token/byte cost, past-estimated item utility, recency/frequency, semantic centrality,
and relevant position metadata, but separated on destroyed past interaction mass
\(J(D)\). Freeze lesions before outcomes. Gate P3 advances only if high-interaction
destruction produces greater held-out damage across independent banks.

### E6 — natural memory and strong systems baselines

Only after E5 passes, move to a controlled subset of LoCoMo/LongMemEval-style data.
Use source-level deletion, answer-key auditing, identical retrieval for all retention
policies, and matched storage/context budgets. Report indexing and interaction-estimation
cost, cold/warm latency, tokens, and VRAM. Synthetic-only gains are a legitimate
falsification outcome.

### Replication and full HiberMem

Replicate the frozen mechanism on another model family before broad claims. Only after
prospective retention, matched lesions, and at least one external benchmark should the
project add structural retrieval, consolidation, repeated turnover, topology-specific
rewiring, RL, or regrowth. These components must remain separate ablations rather than
requirements for H1–H3.

## 12. Immediate implementation order

1. **Implemented:** E3c output-contract/grounding protocol, controls, resumable runner,
   independent validator, configuration, and Kaggle launcher.
2. **Implemented:** E4 protocol semantics, typed split capabilities, endpoints,
   past-only policies, cost checks, artifact schemas, and fail-closed stage machine.
3. **Implemented:** prospective generator, fixed prediction probe, analysis,
   independent validator, tests, frozen-config tool, and Kaggle launcher.
4. **Verified locally:** complete 16,384-condition E3c mock artifact and E4 mock
   past/freeze/future artifact independently validate; all are engineering-only.
5. **Next:** review, commit, and run real E3c on Kaggle. Stop if no contract passes.
6. Freeze one passing contract into a new committed E4 design config, then run only
   the fresh E4 design cohort.
7. Review development evidence; separately implement/freeze a variance cohort and
   preregister confirmation size/rules. These configs do not yet exist.
8. Run a fresh confirmation cohort once, then decide E5 advance/replicate/pivot from
   the frozen rule.
