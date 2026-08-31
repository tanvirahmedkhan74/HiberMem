# E3 revision and prospective roadmap — 2026-08-31

Status update: real E3 core is complete and independently validated; the large
presentation run is on hold. The [core findings and revised next step](E3_CORE_RESULTS_AND_NEXT_STEP_2026-08-31.md)
take precedence over the original sequencing below. A matched decode64 diagnostic
is prepared; real execution remains pending. This document
supersedes E3–E4 details in the earlier E0–E6 plan, not any historical outcome.

## Evidence motivating the revision

Real Qwen E1 (2,048 conditions) and E2 (6,144) at commit
`aa97b3aa9b93c5ee7b6e0b3a685395442b2d220c` independently validated. E2's 2,048
original requests/outputs/rewards reproduce E1 exactly. There are only two
independent banks; presentations, coalitions, and counterfactuals are not extra banks.

Original mean additive/quadratic/cubic in-sample R2: 0.611685/0.923723/0.952570.
These do not measure future-query prediction. Required-pair-only and full accuracy
are 1; empty accuracy is 0; mean local pair contrast is 0.875. Quadratic versus
exact Shapley accuracy is .25 versus .125 at 75% deletion and .25 versus .375 at
62.5% deletion: the equally weighted severe-budget average is tied at .25.
At 62.5% deletion, Shapley's .375 decomposes into .125 supported-correct plus
.25 unsupported-correct; quadratic's .25 is entirely supported. Keep the original
correctness outcome, and report this decomposition rather than redefining success.

Reversing records lowers full accuracy from 1 to .75. Supported-coalition accuracy
is .953125 original, .863281 reversed records, .902344 reversed options. Original
unsupported abstention is 1039/1536; 497/1536 are unsupported assertions. The E1/E2
primary score can therefore reward guesses, and stable identical reruns do not
establish presentation invariance. Raw artifacts remain under `results/E_results`.

## Theory check and estimands

For a fixed query q, presentation p, world w, frozen model and decoding stack, use
the observed game v(S) = 1[answer(S) = full-world target]. Average queries only
after defining this game. Abstention is a separate behavior, not a correct answer
to the full-world task when information is missing.

Let a(T) = sum_{U subset T} (-1)^(|T|-|U|) v(U). Then

- v(S) = sum_{T subset S} a(T), exactly for a complete table.
- phi_i = sum_{T containing i} a(T)/|T|.
- I_ij = sum_{T containing i,j} a(T)/(|T|-1).
- Equivalently I_ij averages the four-corner difference over contexts with weight
  |S|!(n-|S|-2)!/(n-1)!, not uniform weight over all subsets.

These distinctions follow the [primary set-function representation paper,
equations 2, 5 and 7](https://orbilu.uni.lu/bitstream/10993/10979/1/EquivalentRepresentationsLGS99.pdf).
The implementation must cross-check the two exact SII expressions independently.

Analytic unit-amplitude reference games (other items are null):

| Family | Game | Exact pair SII | Important distinction |
|---|---|---|---|
| Direct/independent | x_i | 0 for every pair | Shared words do not create symbolic dependence |
| AND2 | x_i x_j | I_ij = 1 | Positive complementarity |
| OR2 redundancy | x_i + x_j - x_i x_j | I_ij = -1 | Either item is sufficient; a flat required-pair flag is wrong |
| AND3 | x_i x_j x_k | Each within-triple pair = 1/2 | Pair Mobius terms are zero, triple term is 1 |

Positive pair SII is not proof of an irreducible two-item mechanism. A quadratic
surrogate can absorb higher-order effects. Exact quantities describe the observed
model game; departure from a symbolic oracle is behavioral deviation, not error
in an exact estimator. Numerical tolerances are not practical-effect thresholds.

AND2 violates submodularity: v({i})+v({j}) = 0 < v({i,j})+v(empty) = 1. Therefore
the classic [monotone-submodular cardinality greedy guarantee](https://thibaut.horel.org/submodularity/papers/nemhauser1978.pdf)
does not apply to arbitrary mixed-sign interaction objectives. Enumerate all
subsets for these eight-item diagnostics. No approximation guarantee is claimed.

Support is a disjunction of minimal sufficient sets, h_q(S). Secondary diagnostic
scores are supported_correct = v*h and unsupported_correct = v*(1-h); their sum
must equal original accuracy. Report conditional abstention and unsupported-answer
rates with denominators. Support labels may annotate selected masks but must never
enter operational policy fitting/selection. Do not select masks on this diagnostic
score or call it a preregistered new primary endpoint.

## E3a implemented scope

- New protocol `phase2r-factorial-mechanism-v1`, development banks [340,360).
- Eight records per bank, two independent query motifs, all 256 coalitions.
- Families: direct, AND2, OR2, AND3. Explicit query-role/support metadata.
- Cross each family with low/high shared **lexical theme overlap**, base/paired
  counterfactual world, and selected presentation variants.
- Use identical link grammar across families. Theme words are explicitly
  non-operative metadata; report measured record-token Jaccard overlap. This is a
  narrow lexical-nuisance manipulation, not validated embedding-level semantics.
- Randomize opaque identifiers, player positions and option order by bank seed.
  Keep positions, options and question fixed across counterfactual worlds; apply
  a fixed-point-free destination reassignment to every destination-bearing record.
- Store new prompts and fingerprints; never mix with E1/E2/v2 caches. Fresh
  system/user messages every condition; no cross-coalition conversational history.
- A text-reading graph oracle must independently match the minimal-support logic
  on every coalition, including duplicates, nulls, worlds, and presentations.
- Destination-copy and first-option controls are reported as shortcuts, never
  assumed to have zero interactions in every family/context.

Core config: 2 banks * 4 families * 2 overlap levels * 2 worlds * 1 presentation *
2 queries * 256 masks = **16,384 generations**.
Presentation config: same matrix * 3 presentations = **49,152 generations**.
Both include originals; do not pool repeated conditions as independent evidence.
Original sequence (now superseded by the decoding diagnostic): start with core;
presentation is a separate, larger follow-up. Prior Qwen latency
of about .46 seconds/generation suggests roughly 2.1/6.3 inference-hours before
overhead, but the new prompt may change this substantially. Dry-run counts are
exact; time estimates are not guarantees. No inference is launched by this work.

## Analysis and implementation work packages

1. Preserve legacy E1/E2 outputs and validator compatibility. Add an explicitly
   whitelisted protocol to the existing resumable runner, not arbitrary adapters.
2. Add deterministic factorial generator, support antichains, lexical-overlap
   audit, stateless renderer, and independent prompt-reading symbolic backend.
3. Compute complete per-query Mobius/SII references, null-player/contextual
   deviations, and per-bank original-score additive/quadratic/cubic fits.
4. Retain exact Shapley, surrogate Shapley, additive, LOO, budget-conditioned item,
   random, quadratic, shuffled-interaction, and labeled in-sample oracle policies.
   Add cubic selection and seeded tie sensitivity. All fit/select on original
   correctness only. Annotate every retained subset with support decomposition.
5. Compare paired worlds, report same-prompt output consistency and both-world
   correctness on supported coalitions. Report overlap and presentation differences
   by base-bank/family; do not rank models or introduce a pass threshold.
6. For presentation variants, evaluate original-presentation frozen selections
   and predictions on variant tables without refitting. Label these presentation
   transfers, not future-query validation. Keep variant-refit descriptions separate.
7. Reuse source/config/runtime pinning, atomic checkpoints, independent raw-evidence
   validation, no-model tests, and the proven Kaggle pip-less bootstrap. Test
   tampering, interrupted resume, dirty-source rejection and gate denial.

Acceptance: analytic formulas and oracle tables agree; all dimensions preserve
their intended identities; no support/answers reach prompts as diagnostic metadata;
support decomposition is exact; frozen transfer really uses the original masks;
corrupted records/reports fail validation; mock reports remain engineering-only;
all historical tests pass. These are engineering criteria, not model qualification.

## E3b and E4–E6: explicitly not implemented in this tranche

E3b: controlled semantic paraphrases with an independent manipulation check;
conflicting sources and timestamped updates. Define authority, as-of time and
whether a stale answer counts as unsupported or wrong BEFORE generation. These
are distinct truth/utility models, not extra AND/OR templates. Preserve any E3a
negatives and use fresh development groups when changing prompts or scores.

E4: freeze the chosen protocol after development review. Separate past/future
query streams and independent bank cohorts; freeze selections before future
scoring. Specify paraphrase, compositional, dependency-frequency and temporal
shifts separately. Future R2 must use past-fitted predictions (negative allowed;
constant targets undefined). Primary endpoint: bank-level paired original-score
advantage averaged over prespecified actual >50% deletion budgets. Include
support decomposition as secondary and budget-conditioned baselines. Match
estimation calls and retained tokenizer cost; report total-system cost separately.
Set a practical effect size, power/variance pilot, multiplicity rules and clustered
uncertainty before confirmation. Two development banks cannot supply reliable
power estimates or establish a universal sample-size requirement.

Repeated adaptive examination of a holdout is a validity risk; see the
[authors' explanation of adaptive holdout reuse](https://research.google/blog/the-reusable-holdout-preserving-validity-in-adaptive-data-analysis/).
We are NOT implementing the reusable-holdout algorithm: our safeguard is fresh,
untouched future evidence after protocol freezing. E3 has no future/test capability.

E5 matched lesions require prospective evidence and separately reserved outcomes.
E6 natural conversational memory/scale follows mechanism and lesion evidence.
No hyperbolic geometry or biological engram claim is established by E3.

## Historical initial implementation verification

- 163 tests passed in the project Conda environment, including independent
  analytic SII definitions, OR support, higher-order effects, counterfactual
  identity, lexical manipulation, frozen transfer, tie repeatability, support
  isolation, corruption rejection, partial resume and gate denial.
- Full core mock run: 16,384 conditions, independently validated.
- Full presentation mock run: 49,152 conditions, independently validated.
- Both symbolic runs match the functional oracle, with zero null-player effects,
  zero lexical/presentation reward changes and perfect supported counterfactual
  correctness. These are engineering checks, not Qwen outcomes.
- Reports: `results/factorial_mechanism_local_verification/e3-core/report.json`
  and `results/factorial_mechanism_local_verification/e3-presentation/report.json`.
- Both old real Qwen E1/E2 bundles still independently validate after the runner
  extension; original artifacts were not modified. Bash syntax and diff whitespace
  checks passed.
- Source/config must be reviewed, committed and published before real E3a use;
  no commit, push, package installation, real-model inference or gate unlock was
  performed. See [E3 Kaggle instructions](E3_KAGGLE.md).

## Post-core update

The user published e98cf871877b and supplied all 16,384 real core records. Direct
and OR2 supported accuracy is above 99.9%, but AND2 is 50.49% and AND3 16.21%.
There are 2,168 outputs at the 16-token cap; 2,096 of 2,185 parse-null outputs hit
that cap. All AND3 correct answers at keep=2 are unsupported. These are valid
development outcomes under the original config, not infrastructure errors.

Before presentation, run the new `exact_mechanism_e3_decode64.json`: same complete
matrix, only max_new_tokens changes to 64. The original core and presentation
configs stay unchanged. A read-only audit/comparator checks design identity,
runtime and token prefixes and preserves all old artifacts. No output rescue,
prompt change, history carryover or gate relaxation is included. See the linked
findings for decision branches; no automatic numerical pass threshold is created.
