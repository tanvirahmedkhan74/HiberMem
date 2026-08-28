# HiberMem Research and Phase 2 Discovery/Validation Report

**Report date:** 2026-08-27

**Run:** `results/phase2/20260826T195924.594962Z`

**Decision:** negative Phase 2 pilot; test remains locked; Phase 3 is blocked

## 1. Executive conclusion

Phases 0 and 1 passed, and the Phase 2 implementation and local-model backend
qualification passed their engineering checks. The first scientifically
eligible Phase 2 discovery/validation run did not pass either prerequisite for
opening the held-out test:

1. P2-A interaction ranking stability failed. Mean split-half top-4 overlap
   was 0.55 against a threshold of 0.75, and its margin over random ranking was
   0.4071 against a threshold of 0.50.
2. Validation task readiness failed. Full-memory accuracy averaged 0.58, no
   bank reached the joint full-accuracy and memory-gap requirements, and the
   required passing-bank fraction was therefore 0.0 rather than 0.8.

The test split was not unlocked or evaluated. Consequently, Gate P2 is
**undecided**, not passed, and P2-B has not been tested. The correct next step
under the master plan is a separately declared Phase 2 model/task-dependence
investigation using development-only banks, followed—only if justified—by a
fresh preregistered confirmation. Phase 3 must not begin.

The runner originally printed a generic `--stage unlock` resume instruction
even when readiness failed. The unlock implementation would still have refused
the request, but the message was misleading and has been corrected.

## 2. Evidence and implementation completed so far

### 2.1 Phase 0 — mathematical correctness

Phase 0 implemented and tested the mathematical substrate before any LLM was
used:

- canonical coalition-mask serialization and validation;
- exact coalition games and discrete derivatives;
- exact Möbius/Harsanyi coefficients;
- pairwise and third-order interaction signs;
- exact Shapley and interaction reference checks;
- analytical unit tests for additive, synergistic, redundant, and higher-order
  games.

Gate P0 passed with all 21 phase-specific tests. This established that the
mathematical definitions and signs are internally correct.

### 2.2 Phase 1 — synthetic recovery

Phase 1 generated deterministic low-order polynomial coalition games with
known individual effects, pair interactions, distractors, noise, and null
terms. It fitted the estimator and measured sign, ranking, magnitude, false
positive, uncertainty, and bootstrap-stability behavior.

The verified artifact is
`results/phase1/20260826T184454.941051Z/report.json`. Gate P1 passed with:

| Metric | Result | Gate |
|---|---:|---:|
| Interaction sign accuracy | 1.000000 | >= 0.970000 |
| Precision@k | 1.000000 | >= 0.900000 |
| Recall@k | 1.000000 | >= 0.900000 |
| Nonzero Spearman correlation | 1.000000 | >= 0.900000 |
| Individual MAE | 0.015359 | <= 0.200000 |
| Interaction MAE | 0.016337 | <= 0.200000 |
| Null false-positive rate | 0.003086 | <= 0.050000 |
| Noisy 95% interval coverage | 0.938172 | >= 0.900000 |
| True-interaction sign stability | 1.000000 | >= 0.900000 |

This validated the estimator on known games. It did not establish that a real
LLM exposes stable or useful memory interactions.

### 2.3 Phase 2 — implemented controlled experiment

The Phase 2 environment contains ten independent memory banks with eight
natural-language memory items per bank. Each bank encodes four two-step routing
chains, with disjoint discovery, validation, and test surface templates and
20/10/20 queries respectively.

The implemented method is:

1. Supply every surviving memory directly in original order. There is no
   retrieval, graph search, training, regrowth, or RL component.
2. Generate greedily from a pinned model and revision with at most eight new
   tokens, parse one finite action, and score exact correctness.
3. Evaluate all 256 coalitions for two banks and 128 deterministic
   size-balanced coalitions for each of eight banks. This produces 30,720
   discovery generations rather than 51,200 for full enumeration everywhere.
4. Fit, per bank, an order-2 least-squares model in the binary monomial basis:

   `v(S) = beta_0 + sum_i beta_i x_i + sum_{i<j} beta_ij x_i x_j`.

   Because the LLM game can contain higher-order behavior, these fitted
   coefficients are a truncated predictive approximation, not an assertion
   that the real game is exactly pairwise.
5. Measure interaction stability with 100 discovery-query bootstrap resamples
   and a deterministic split-half top-4 comparison.
6. Construct retention masks from discovery only. The Item policy ranks
   ordinary Shapley item values coherently derived from the fitted polynomial;
   the Interaction policy exactly maximizes the fitted polynomial at each fixed
   keep count; Random uses five seeded replicates.
7. Match keep count, payload whitespace-token count, and serialized payload
   bytes across policies. For eight memories, nominal deletion 0.70 and 0.80
   become actual deletion 0.625 and 0.75 after integer rounding, and both values
   are recorded.
8. Store every unique evaluation in resumable SQLite with the model revision,
   prompt hash, bank, query, mask, generation settings, seed, Git commit, raw
   output, parsed action, reward, latency, token counts, and timestamp.
9. Keep test access behind a one-way artifact-hash and source/config integrity
   check. Validation and P2-A must both pass before an unlock artifact can be
   written.

The full mock protocol recovered all four designed dependencies, but it is
marked `scientific_gate_eligible: false` and is engineering evidence only.

### 2.4 Local backend qualification

The verified runtime used PyTorch 2.13.0+cu130 on an NVIDIA GeForce RTX 4050
Laptop GPU. The pinned backend is
`HuggingFaceTB/SmolLM2-1.7B-Instruct` at revision
`d1bb90bcfbe0f211109880f4da18da66f229c4f6`, loaded on CUDA in float16.

Discovery-only qualification initially exposed an identifier-suffix shortcut
and weak two-hop instructions. Before any scientific discovery or test access,
the environment was revised to dataset `phase2-routing-v4`, prompt
`phase2-direct-survivors-v3`, disjoint request/route/destination alphabets, and
explicit two-hop directions. The final qualification passed with 1.0 supported
parse rate, 1.0 supported accuracy, 0.916667 overall parse rate, and 0.25
missing-link accidental correctness.

## 3. Current run integrity and workload

The current run is scientifically eligible and reproducible:

| Property | Recorded value |
|---|---|
| Git commit | `3b13934c3215f921c6757276728467bdb9d4d851` |
| Source/config dirty | No |
| Config SHA-256 | `79241d11be57b7294a70252998650d8270b0064c657d5fb726342f403f3948c7` |
| Dataset SHA-256 | `756e0de54ab21640ab3d92e771a0518cde60c4df84935bfdbbfc333c31a4c8af` |
| Prompt SHA-256 | `53b10e3d9ba35ea6f975d69329e914188d16ea50177bd237ea2daad7a4a220bc` |
| Unique cache rows | 33,520 |
| Discovery evaluations | 30,720 |
| Unique validation evaluations | 2,800 |
| Cache reuses during validation | 900 |
| Invalid/unparsed responses | 782 / 33,520 (2.33%) |
| Evaluation time span | 2 h 58 m 52 s |
| Summed model latency | 10,624.97 s |

The cache count reconciles exactly with the planned discovery workload plus
the unique validation conditions. The repository was globally dirty because
research outputs were being written, but the recorded scientific source and
configuration paths were clean.

No `test_unlock.json` or `test.json` exists in the run directory. This is the
correct locked state.

## 4. P2-A discovery findings

### 4.1 Preregistered gate result

| Check | Result | Threshold | Decision |
|---|---:|---:|---|
| Mean split-half top-4 overlap | 0.5500 | >= 0.7500 | FAIL |
| Mean margin over random overlap | 0.4071 | >= 0.5000 | FAIL |
| Mean top-pair sign consistency | 0.9705 | >= 0.9000 | PASS |

P2-A requires all checks, so the candidate gate failed. High conditional sign
consistency does not rescue unstable top-k membership: a coefficient can keep
its sign while several similarly sized terms exchange rank across query
halves.

### 4.2 Per-bank interaction stability

The designed chain pairs are `(0,1)`, `(2,3)`, `(4,5)`, and `(6,7)`.

| Bank | Coalition design | Top-4 overlap | Top-pair sign consistency | Designed pairs in top 4 |
|---|---|---:|---:|---:|
| bank-00 | exact 256 | 0.50 | 0.9975 | 3 |
| bank-01 | exact 256 | 0.75 | 0.9325 | 2 |
| bank-02 | sampled 128 | 0.75 | 0.9800 | 2 |
| bank-03 | sampled 128 | 0.50 | 0.9800 | 2 |
| bank-04 | sampled 128 | 0.50 | 0.9525 | 1 |
| bank-05 | sampled 128 | 0.50 | 0.9500 | 2 |
| bank-06 | sampled 128 | 0.75 | 0.9950 | 2 |
| bank-07 | sampled 128 | 0.50 | 0.9550 | 1 |
| bank-08 | sampled 128 | 0.25 | 0.9825 | 3 |
| bank-09 | sampled 128 | 0.50 | 0.9800 | 1 |

Only three of ten banks reached the 0.75 overlap target. Across the 40 top-pair
slots, 19 were designed pairs (47.5%). The first designed pair `(0,1)` appeared
eight times, but `(2,3)` appeared only twice. Repeated non-designed top pairs
included `(1,5)` four times and `(1,2)` and `(1,3)` three times each.

The exact-enumeration banks also had overlaps of only 0.50 and 0.75. Therefore,
the main failure cannot be attributed solely to the 128-coalition sampling
budget. Query/template behavior and model task performance are more plausible
drivers.

## 5. Validation readiness findings

### 5.1 Bank-level readiness

Each bank needed full-memory accuracy at least 0.80 and a full-minus-empty gap
at least 0.50. At least eight of ten banks had to pass.

| Bank | Full accuracy | Empty accuracy | Memory gap | Joint pass |
|---|---:|---:|---:|---|
| bank-00 | 0.60 | 0.00 | 0.60 | No |
| bank-01 | 0.60 | 0.20 | 0.40 | No |
| bank-02 | 0.50 | 0.10 | 0.40 | No |
| bank-03 | 0.50 | 0.10 | 0.40 | No |
| bank-04 | 0.70 | 0.30 | 0.40 | No |
| bank-05 | 0.60 | 0.10 | 0.50 | No |
| bank-06 | 0.60 | 0.10 | 0.50 | No |
| bank-07 | 0.60 | 0.20 | 0.40 | No |
| bank-08 | 0.50 | 0.10 | 0.40 | No |
| bank-09 | 0.60 | 0.10 | 0.50 | No |
| **Mean / fraction** | **0.58** | **0.13** | **0.45** | **0.0** |

No bank met the full-memory accuracy requirement. This is a base-task
readiness failure before it is a retention-policy comparison.

### 5.2 Direct versus two-hop diagnosis

The cache permits a public-split diagnostic without touching the held-out test:

| Split and context | Query type | Correct / total | Accuracy | Parse nulls |
|---|---|---:|---:|---:|
| Discovery, full memory | Direct | 35 / 40 | 0.8750 | 0 |
| Discovery, full memory | Two-hop | 75 / 160 | 0.4688 | 0 |
| Validation, full memory | Direct | 17 / 20 | 0.8500 | 0 |
| Validation, full memory | Two-hop | 41 / 80 | 0.5125 | 0 |
| Validation, empty memory | Direct | 2 / 20 | 0.1000 | 0 |
| Validation, empty memory | Two-hop | 11 / 80 | 0.1375 | 0 |

Direct lookup transfers well, but full-memory two-hop routing is only about
0.47–0.51 accurate. There are no parser failures in the full or empty
conditions, so the main readiness problem is incorrect reasoning under the
complete memory context rather than output-format rejection. Of all 782 parse
nulls, 760 occurred on partial two-hop conditions.

The narrow 12-case backend qualification was therefore necessary but not
sufficient: it overestimated performance on the diverse bank/template
distribution used by the real experiment.

### 5.3 Validation retention curves

Mean raw accuracy across banks was:

| Policy | Delete 0.00 | Delete 0.25 | Delete 0.50 | Delete 0.70 | Delete 0.80 |
|---|---:|---:|---:|---:|---:|
| Interaction | 0.580 | 0.670 | 0.460 | 0.280 | 0.280 |
| Item | 0.580 | 0.510 | 0.320 | 0.280 | 0.260 |
| Random | 0.580 | 0.414 | 0.302 | 0.256 | 0.226 |

These are validation diagnostics, not P2-B results. At nominal deletion 0.70
and 0.80, Interaction-minus-Item was 0.00 and 0.02 respectively, for a mean
severe-deletion advantage of 0.01. Averaged over the two severe points, four
banks were positive, three tied, and three were negative. This is far below the
preregistered P2-B effect-size and prevalence targets if it were to persist,
but no confirmatory p-value or P2-B decision is valid because the test remains
locked.

Interaction accuracy increasing from 0.58 at full memory to 0.67 after deleting
two memories is non-monotonic. The most plausible interpretation is context
interference or distractor removal: the small model sometimes performs better
with less irrelevant routing material. This is scientifically interesting, but
it also means the fitted coefficients can reflect confusion control as well as
the intended memory dependencies.

## 6. Interpretation and limitations

The defensible result is:

- the estimator and harness work on exact and synthetic references;
- this SmolLM2-1.7B task/model pairing did not yield sufficiently stable
  pairwise rankings;
- the same pairing did not meet the full-memory task-readiness floor;
- validation shows only a negligible severe-deletion Interaction-over-Item
  difference;
- no held-out claim about P2-B is available.

This does not distinguish conclusively between “LLM memory interactions are
not useful” and “this model/task construction does not expose them cleanly.”
The current evidence specifically rejects advancing this configuration to the
locked test or to Phase 3. It also weakens the near-term HiberMem premise,
because designed pair dependencies alone were not enough to make the estimated
rankings robust.

The next investigation must not silently tune on this validation set. The
current discovery and validation splits are now development evidence. Any
revised prompt, task, bank generator, model, coalition design, or threshold
must receive a new version and use fresh confirmatory banks and a new locked
test.

## 7. Results-driven next plan — Phase 2-R

The master plan says that absent stable P2 interactions should trigger a
model/task-dependence investigation. Phase 2-R is that investigation; it is not
Phase 3 and cannot convert the current run into a pass.

### Step 1 — Freeze and diagnose the negative pilot

- Preserve the current config, report, discovery, validation, manifest, and
  cache as an immutable negative-pilot artifact.
- Do not create a test-unlock artifact and do not inspect the current test.
- Add a deterministic public-split analyzer for query family, chain position,
  template, action-confusion, parser failure, coefficient magnitude, designed
  pair enrichment, and exact-versus-sampled sensitivity.
- Treat all results from the current discovery/validation data as exploratory.

### Step 2 — Create a separate development calibration suite

- Generate new calibration-only banks with new nonce identifiers and template
  instances; do not reuse the current validation or test examples.
- Expand qualification from 12 handpicked cases to bank-level direct,
  complete-pair, missing-first-link, missing-second-link, distractor, and full
  eight-memory conditions.
- Diagnose at least the current pinned 1.7B model and one feasible stronger
  local model or quantized configuration. Candidate selection belongs only to
  development and must be recorded.
- Require, before another full coalition run, parse rate at least 0.98, direct
  full-memory accuracy at least 0.90, two-hop full-memory accuracy at least
  0.80, missing-link accidental correctness at most 0.25, and the existing
  bank-level memory-gap requirement on at least 80% of calibration banks.

These qualification additions make the expensive experiment conditional on
the exact capability that failed, rather than on a small supported-case sample.

### Step 3 — Run an interaction-feasibility development pilot

- Use four fresh development banks with exact 256-coalition enumeration.
- Keep the current order-2 estimator and stability definitions so model/task
  changes are not confounded with estimator changes.
- Report the existing P2-A checks plus diagnostic designed-pair enrichment and
  coefficient effect sizes/intervals.
- If exact-bank top-k stability still fails, stop that candidate rather than
  increasing the sampled-bank budget.

### Step 4 — Freeze a new confirmatory protocol

Only after development qualification and feasibility pass:

- assign new dataset and prompt versions;
- select and pin one model revision and runtime;
- predeclare fresh generation seeds, ten confirmation banks, split templates,
  coalition budgets, and all hashes;
- retain the existing P2-A, validation-readiness, and P2-B thresholds rather
  than relaxing them after this failure;
- commit the source and config before inference.

### Step 5 — Execute fresh Phase 2 confirmation

Run discovery and validation on the fresh confirmation banks. Branch only on
the preregistered result:

- If P2-A or readiness fails again, keep test locked and report Phase 2 as a
  negative/model-dependent result.
- If both pass, write the new run's unlock artifact and evaluate its held-out
  test exactly once.
- Gate P2 passes only if that held-out test also passes P2-B: severe-deletion
  mean advantage at least 0.10, positive effects in at least 80% of banks, and
  one-sided paired sign-flip `p <= 0.05`.

### Step 6 — Phase boundary

Phase 3 matched structural lesions are authorized only after a fresh run passes
both P2-A and P2-B. If no qualified model/task candidate produces stable
interactions, stop or pivot as required by the master decision tree. Do not
build lesion, graph, retrieval, RL, or regrowth machinery in advance of that
evidence.

## 8. Immediate implementation order

The next code work should be narrowly scoped to Phase 2-R:

1. implement and test the deterministic public-split diagnostic analyzer;
2. add a calibration-only dataset capability that cannot access confirmation
   or test queries;
3. expand backend qualification to bank-level direct/two-hop and missing-link
   metrics;
4. add development and confirmation configs with new dataset/prompt versions;
5. add leakage and provenance tests for the new development/confirmation
   boundary;
6. run the cheap calibration matrix before authorizing another 30,720-query
   coalition experiment.

This sequence addresses the observed failure directly while preserving the
current negative result and the integrity of future confirmatory evidence.

## 9. Kaggle implementation update — 2026-08-29

Phase 2-R steps 1–5 now have a Kaggle-ready implementation:

- fresh calibration banks 100–109 and reserved confirmation banks 200–209;
- a 2,760-generation development screen across Qwen3-4B-Instruct-2507 and
  Phi-4-mini-instruct;
- full/direct/two-hop/pair-only/empty/missing-link bank-level diagnostics;
- immutable model revisions, stable released package pins, SQLite resume, and
  artifact packaging;
- automatic candidate selection only after the stronger readiness thresholds;
- a freeze tool that converts a qualified screen into a new scientific config;
- an exact-commit Kaggle confirmation launcher that runs discovery/validation
  but never unlocks test;
- a tracked P1 certificate so a clean GitHub clone can verify the prerequisite
  without committing the large results directory.

The supplied `State-Nuisance-Geometry` GitHub repository was audited and is a
different `state-geometry-video` project. Actual Kaggle execution is blocked
until this HiberMem tree is committed and pushed to the correct dedicated
repository. See `docs/PHASE2R_KAGGLE_EXECUTION.md` for the complete sequence.
