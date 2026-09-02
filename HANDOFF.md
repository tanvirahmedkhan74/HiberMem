# HiberMem handoff

**Updated:** 2026-09-02
**Base repository revision reviewed:** `518c28d5b441f469df9135b15ff75778b88107c5`

**Working implementation:** uncommitted E3c/E4 source and documentation changes

## 1. Current decision

P0 and P1 passed. The historical Phase-2 pilot and Qwen/Phi/Gemma Phase-2R v2
screens are negative development evidence. No candidate qualified, P2-B was not
evaluated on a valid locked test, Gate P2 is undecided, and Phase 3/P3 remains
blocked.

E1–E3 are exact-game **development diagnostics** and cannot alter those gates. Real
Qwen E1, E2, E3 core, and E3 decode64 artifacts have been independently validated.
E3 decode64 shows that the 16-token cap severely understated supported multi-hop
behavior, but it also confirms persistent output-contract and missing-evidence
grounding problems. It contains no prospective future-query result.

E3c and the leakage-safe E4 development pipeline are now implemented and mock-
validated. The next action is to review/commit the source and run real E3c on Kaggle.
Only a readiness-passing contract may be explicitly frozen into a new committed E4
design config. See the [E4 implementation plan](docs/E4_PROSPECTIVE_IMPLEMENTATION_PLAN_2026-09-02.md)
and [Kaggle cells](docs/E4_KAGGLE.md). Do not run the old 49,152-condition presentation
config, unlock the historical test, or begin matched lesions.

## 2. Scientific claim and methodology

The project tests whether external-memory interactions learned from past queries are
stable and behaviorally useful under severe deletion beyond individual memory value.
It does not claim that deletion, graph memory, Shapley attribution, or biological
hibernation is itself novel.

For query \(q\) and surviving coalition \(S\), the behavioral game is

\[
v_q(S)=r(q,S).
\]

For disjoint past and future query sets, fit to

\[
v^P(S)=E_{q\in Q^P}[r(q,S)]
\]

and evaluate frozen selections against \(Q^F\). No future query, answer, reward,
support annotation, or derived statistic may enter estimation, selection, threshold
tuning, tie resolution, or model choice.

The corrected local pair interaction is

\[
I_{ij}=v(M)-v(M\setminus\{i\})-v(M\setminus\{j\})
+v(M\setminus\{i,j\}),
\]

equivalently \(I_{ij}=\Delta_i+\Delta_j-\Delta_{ij}\). Positive means
complementarity and negative means redundancy under this convention.

For complete games, exact Mobius coefficients, Shapley item values, and Shapley
Interaction Index values are separate quantities. Regression singleton/pair/triple
coefficients are surrogate Mobius terms, not exact SII. Exact estimators are
cross-checked through independent formulas and reconstruction identities.

The fitted working model is

\[
\hat v(S)=\beta_0+\sum_i\phi_i x_i+
\sum_{i<j}I_{ij}x_ix_j+
\sum_{i<j<k}I_{ijk}x_ix_jx_k.
\]

Positive pair SII does not prove an irreducible pair mechanism: an AND3 game has zero
pair Mobius coefficients, a positive triple coefficient, and positive within-triple
pair SII. Mixed-sign objectives are not generally submodular, so no generic greedy
guarantee is claimed; eight-item experiments use exact subset enumeration.

Support is represented as an antichain of minimal sufficient memory sets. Original
destination correctness remains the operational outcome. Supported-correct,
unsupported-correct, abstention, unsupported assertion, parse failure, and strict
format are diagnostic decompositions only and are never available to retention
policies.

The independent statistical unit is the memory bank/environment. Queries,
coalitions, counterfactual worlds, presentations, and random seeds are repeated
measurements. Primary inference uses paired bank effects, bank bootstrap intervals,
and paired randomization; query-level counts must not be presented as independent
replication.

## 3. Evidence ledger

### P0/P1 mathematical and synthetic validation

- Phase 0: 21 phase-specific tests passed; Gate P0 passed.
- Phase 1: Gate P1 passed at
  `results/phase1/20260826T184454.941051Z/report.json`.
- Interaction sign accuracy, precision@k, recall@k, nonzero Spearman, and true-sign
  stability were 1.0. Item MAE was .015359, interaction MAE .016337, null false
  positive rate .003086, and noisy interval coverage .938172.
- These validate the estimator implementation, not the HiberMem hypothesis.

### Historical SmolLM2 Phase-2 pilot

The real pilot is preserved at `results/phase2/20260826T195924.594962Z`.
P2-A failed: mean split-half top-4 overlap .55 versus the .75 requirement, although
top-pair sign consistency was .9705. Validation readiness also failed: full-memory
accuracy .58, empty .13, and 0/10 passing banks. Direct accuracy was .85 but two-hop
accuracy only .5125. Interaction versus item retention at nominal .70/.80 deletion
was .28/.28 and .28/.26; combined advantage .01. The test remained locked.

### Phase-2R v1/v2 screens

Qwen and Phi v1 missing-link scores were .30 and .464583; both failed. The v2 protocol
added authorization-before-cache, content/runtime cache fingerprints, nonzero balanced
stability, reserved-bank checks, public manifests, and paired counterfactual banks.
Full Qwen and Phi v2 bundles validate as negative screens. Gemma's supplied aggregate
report is also negative: 9/10 banks pass and supported full accuracy is high, but
missing-pair abstention is .504167 and unsupported assertions remain substantial.
The raw Gemma bundle has not been independently validated in this checkout.

None of these screens authorizes confirmation or test. Their strongest exploratory
finding is Qwen's local empty-context pair contrast .933333 with a bank-bootstrap
interval [.866667, 1] on development banks; Phi is .016667
[-.033333, .066667]. This is local complementarity, not global stability or future
retention.

### E1 exact coalition game

Real Qwen E1 at commit `aa97b3aa9b93c5ee7b6e0b3a685395442b2d220c`
contains 2 banks x 4 queries x 256 masks = 2,048 conditions. Required-pair-only and
full accuracy are 1, empty accuracy is 0, and the mean local pair contrast is .875.
Exact values reconstruct the observed game. Additive/quadratic/cubic mean in-sample
R2 values are .611685/.923723/.952570. They are not future-query R2.

At 75% deletion, quadratic versus exact Shapley accuracy is .25 versus .125; at
62.5% deletion it is .25 versus .375. Their equally weighted severe-budget mean is
tied at .25. Shapley's keep-3 advantage includes unsupported correct guesses, while
quadratic's .25 is supported. Therefore E1 does not establish a primary-score win.

### E2 presentation sensitivity

E2 contains 6,144 conditions: the E1 facts under original, reversed-record, and
reversed-option presentation. Its original 2,048 requests, token traces, outputs,
and rewards reproduce E1 exactly. Full accuracy drops from 1 to .75 under reversed
records. Supported-coalition accuracy is .953125 original, .863281 reversed records,
and .902344 reversed options. Presentations are paired variants, not new banks.

### E3 factorial mechanism core

Protocol `phase2r-factorial-mechanism-v1` uses two independent base banks, eight
records, two motifs/queries per bank, and all 256 coalitions. It crosses direct,
AND2, OR2, and AND3 mechanisms with low/high lexical theme overlap and base/
counterfactual worlds. The core has 16,384 conditions. There are 32 bank versions
and 64 query records, but only **two independent banks**.

OR2 uses multiple minimal sufficient sets; AND3 is an irreducible triple in its
symbolic Mobius representation. Opaque labels, positions, and option order are
randomized. Counterfactual worlds reassign destinations while preserving questions
and positions. A prompt-reading symbolic oracle validates every support table.
Inference is stateless with fresh system/user messages for every coalition.

The real 16-token run at `e98cf871877ba22fb721d3d3153feabb6a41ec68`
completed 16,384 calls with no checkpoint reuse in about 2 h 39 min. Direct/OR2
supported accuracy exceeded 99.9%, but AND2 was 50.49% and AND3 16.21%. There were
2,168 16-token cap hits and 2,185 parse-null outputs. Many chains ended before the
destination. The 49,152-condition presentation run was therefore put on hold.

### E3 matched decode64

The real artifact is
`results/hibermem-exact-e3_decode64-qwen-518c28d5b441-20260831T124653Z-74`.
It used Qwen3-4B-Instruct-2507 revision
`cdbee75f17c01a7cc42f958dc650907174af0554` at commit
`518c28d5b441f469df9135b15ff75778b88107c5` and completed in about 3 h 52 min.

Both 16- and 64-token bundles independently validate. Across all 16,384 matched
conditions there are zero prompt/input-token mismatches, runtime differences,
short-output prefix mismatches, or changes to previously early-stopped outputs.
Reward transitions are 9,687 wrong-to-wrong, 885 wrong-to-correct, 5,812
correct-to-correct, and zero correct-to-wrong. Of the recoveries, 880 are supported
and five unsupported.

| Family | Supported accuracy, 16 -> 64 | Full-memory accuracy, 16 -> 64 |
|---|---:|---:|
| Direct | 99.95% -> 99.95% | 100% -> 100% |
| AND2 | 50.49% -> 95.90% | 37.5% -> 100% |
| OR2 | 99.97% -> 99.97% | 100% -> 100% |
| AND3 | 16.21% -> 97.27% | 0% -> 93.75% |

The expected interaction structure also recovers: required-pair mean SII is +.9504
for AND2 (16/16 signs), -.9994 for OR2 (16/16 signs), and +.4919 for AND3
(48/48 within-triple signs). Mean quadratic in-sample R2 is .9614 for AND2 and
.7879 for AND3; these remain same-query descriptions.

The decode intervention does not repair the output contract. All 885 recovered
answers are non-strict, 852 still hit 64 tokens, and strict output totals do not
increase. AND2/AND3 unsupported abstention is .7044/.6155. The frozen scorer can
extract a unique allowed label from an unfinished reasoning trace, so decode64 proves
parser-scored access to the chain more strongly than clean final-answer compliance.

At severe deletion, quadratic versus exact Shapley averages .50/.4375 for AND2 and
1/.90625 for OR2, but the raw advantage is concentrated in one of two banks in each
family. AND3 raw accuracy is tied at .50. At keep-3, quadratic's .50 is entirely
supported while Shapley's .50 is entirely unsupported; at keep-2 the triple cannot
be supported by any method. This is a meaningful support-profile distinction, not a
replicated primary-score victory.

## 4. Implemented software and safeguards

Implemented components include:

- exact coalition masks, complete/sampled games, caching, and deterministic resume;
- discrete derivatives, exact Mobius transforms, exact Shapley/SII, polynomial
  estimators, stability, and analytical tests;
- survival and predictive metrics with explicit undefined cases;
- random, item, budget-marginal, LOO, additive, quadratic, cubic, shuffled-pair,
  and oracle-ceiling retention analyses for small games;
- controlled Phase-2, calibration, exact-mechanism, and factorial environments;
- support antichains, counterfactual worlds, lexical nuisance controls, symbolic
  prompt-reading oracles, and shortcut controls;
- HF-local/mock/OpenAI-compatible backend abstractions;
- clean-source/config/model/prompt/runtime fingerprints, raw requests and outputs,
  HF input/generated token IDs, rendered prompt hashes, latency and token counts;
- atomic checkpointing, interruption-safe resume, artifact hashes, independent report
  validators, corruption rejection, and mock/real separation;
- fail-closed Phase-2 unlock logic and explicit development-only capabilities for
  E1–E3; and
- Kaggle pip-less launchers that preserve the platform Torch installation and archive
  logs/evidence;
- E3c paired output-contract rendering on fresh AND2/AND3 banks, fixed readiness
  checks, resumable evidence, and an independent validator;
- explicit prospective `PastQueryCapability` and `FutureQueryCapability` types plus
  policy-safe `PastEvidence` that strips support/output fields;
- E4 mixed direct/AND2/OR2/AND3 banks, sealed future commitments, fixed prediction
  probes, exact-Shapley and interaction baselines, payload-cost validation, and
  bank-level future analysis; and
- an immutable `past -> freeze -> future` state machine, frozen-config tool, E4
  validator, and dedicated E3c/E4 Kaggle launchers.

Important current code locations:

```text
src/hibermem/interactions/
src/hibermem/retention/policies.py
src/hibermem/environments/controlled/factorial.py
src/hibermem/evaluation/factorial.py
src/hibermem/evaluation/factorial_audit.py
src/hibermem/experiments/exact_mechanism.py
scripts/run_exact_mechanism.py
scripts/validate_exact_mechanism.py
scripts/analyze_factorial_report.py
kaggle/run_exact_mechanism.sh
src/hibermem/environments/controlled/contract.py
src/hibermem/environments/controlled/prospective.py
src/hibermem/evaluation/prospective.py
src/hibermem/experiments/contract.py
src/hibermem/experiments/prospective.py
scripts/run_e3c_contract.py
scripts/run_e4_prospective.py
kaggle/run_e3c_contract.sh
kaggle/run_e4_prospective.sh
```

The current suite passes 197 local tests. E3c symbolic controls cover all 16,384
conditions; its full 16,384-condition mock artifact independently validates. The E4
mock artifact independently validates 4,096 past conditions, an immutable policy
freeze, and 2,424 deduplicated future/probe conditions. Both launchers pass Bash
syntax validation. These engineering checks do not create model evidence or
scientific qualification.

## 5. Known limitations and prohibited claims

- No past-to-future interaction stability or retention benefit has been measured.
- E1–E3 fit and evaluate policies on the same queries.
- Only two independent E1/E2/E3 banks exist; variants are not replication.
- Lexical theme overlap is not broad semantic similarity validation.
- Support-aware decomposition is secondary and cannot replace original correctness.
- Strict-format and missing-evidence behavior are unresolved for multi-hop families.
- The current policies use small-cardinality exact enumeration and do not establish
  production scalability.
- No consolidation, catastrophic-forgetting, repeated-turnover, retrieval, topology,
  hyperbolic-geometry, RL, regrowth, or natural-memory claim is supported.
- The biological hibernation analogy is motivation only, never mechanistic evidence.
- Do not claim a P2/P3 pass, a robust Shapley-baseline victory, future-query R2,
  submodular guarantees, or an implemented full HiberMem architecture.

## 6. E4 prospective implementation

E4 tests H1/H3 on new cohorts. Its primary bank effect averages, at keep-2 and
keep-3, future original-correctness differences between quadratic interaction
selection and exact Shapley item retention. Exact Shapley, quadratic, and all other
methods share the complete past coalition table. Selection is frozen before future
queries can be accessed.

The implementation must use a new protocol and state machine:

```text
prepare -> past -> fit -> freeze -> future -> analyze -> validate
```

Future data must be excluded by typed/capability-scoped interfaces, immutable split
manifests, exclusive-create selection artifacts, and independent lineage validation.
The future stage must reject any source, config, model, prompt, tokenizer, bank,
contract, or selection drift. It evaluates only deduplicated frozen masks plus
full/empty controls and a predeclared method-independent coalition probe for future
prediction metrics; probe outcomes cannot trigger refitting or enter the primary
retention endpoint.

Use separate engineering, design, variance, and confirmation bank cohorts. Freeze the
practical margin, bank count from variance/power analysis, primary shift mixture,
method/order, budgets, tie rule, output contract, and multiplicity policy before
confirmation. Report every bank effect, paired mean/median, positive-bank fraction,
bank bootstrap interval, and paired randomization test. Query rows are nested data.

The E3c/E4 source, development configs, runners, validators, tests, freeze tool, and
Kaggle launchers are implemented. Real E3c and E4 inference have not run. A design
template exists, but a real E4 config cannot be created until a real E3c contract
passes every frozen readiness check. Variance and confirmation configs deliberately
do not exist.

## 7. Later experiment sequence

1. **E3c:** fresh development-only output-contract and grounding diagnostic.
2. **E4:** prospective past-to-future retention against exact item baselines.
3. **E5:** matched structural lesions on a separately reserved cohort, matching
   deletion count, token/byte cost, item utility, recency/frequency, semantics, and
   position while separating destroyed interaction mass. This is Gate P3.
4. **E6:** controlled natural conversational-memory/scale evaluation with identical
   retrieval and storage/context budgets across retention methods.
5. **Replication:** another model family and external benchmark before broad claims.
6. **Only after success:** full graph/hypergraph retrieval, consolidation, repeated
   turnover, topology interventions, RL, and optional regrowth.

Failure of prospective stability, item-baseline improvement, matched-lesion damage,
cost-adjusted benefit, cross-model replication, or natural-benchmark transfer is a
valid reason to narrow or reject the central hypothesis.

## 8. Reproducible environment and operational notes

Use one environment only:

```powershell
cd D:\Coding\paper\hibermem
conda activate D:\Coding\paper\hibermem\.conda
python -m pytest -q
```

Do not activate `.venv` and `.conda` together. The verified local environment uses
Python 3.11.15, PyTorch 2.13.0+cu130, torchvision 0.28.0+cu130, Transformers 5.16.1,
and accelerate 1.14.0 on an RTX 4050 Laptop GPU. Real E3 cloud evidence used the
pinned Qwen model on Kaggle T4 hardware with recorded runtime provenance.

Preserve all existing result bundles and reports. Analysis tools must be read-only or
write a new exclusive artifact; never edit original evidence. Real inference requires
a clean reviewed commit and exact 40-character source/model revisions. No commit,
push, dependency installation, GPU inference, confirmation access, or test unlock is
authorized merely by this handoff.

## 9. Reading order

1. [Master research plan](HiberMem_MASTER_RESEARCH_IMPLEMENTATION_PLAN.md)
2. [Adversarial research audit](docs/ADVERSARIAL_RESEARCH_AUDIT_2026-08-31.md)
3. [E3 revised theory and implementation](docs/E3_REVISED_IMPLEMENTATION_PLAN_2026-08-31.md)
4. [E3 core findings](docs/E3_CORE_RESULTS_AND_NEXT_STEP_2026-08-31.md)
5. [E4 prospective implementation plan](docs/E4_PROSPECTIVE_IMPLEMENTATION_PLAN_2026-09-02.md)
6. [E3c/E4 Kaggle execution guide](docs/E4_KAGGLE.md)
7. [E3 Kaggle execution guide](docs/E3_KAGGLE.md)
