# Phase 2 Implementation and Execution Plan

**Plan status:** implementation complete; first discovery/validation run failed its unlock prerequisites

**Scientific status:** P2-A failed, validation readiness failed, P2-B not evaluated, Gate P2 undecided

**Prerequisite:** Gate P1 passed on 2026-08-27 local verification

## 1. Decision

The first scientifically eligible Phase 2 pilot is complete through validation.
It did not establish stable pairwise coalition structure and did not meet the
base-task threshold required to unlock its held-out test. Preserve it as a
negative result and proceed only to a separately versioned Phase 2 model/task-
dependence investigation. No Phase 3 lesion work is authorized by the current
evidence.

The full 256-coalition design for every bank would require 51,200 discovery
generations. The approved pilot therefore enumerates all 256 coalitions for two
banks and samples 128 size-balanced coalitions for eight banks, for 30,720
discovery generations. This is the compute-audit amendment recorded before
implementation.

## 2. Controlled environment

Each of ten independent banks contains eight nonce-token memories forming four
two-step routing chains. Per chain, a first-hop query is solvable from one item,
while final-destination queries require both items. This creates individual
utility and pairwise complementarity without encoding the answer in the query.

Every bank has:

- 20 discovery queries: one first-hop and four two-hop paraphrases per chain;
- 10 validation queries using separate template families;
- 20 held-out test queries using another separate template family;
- finite action tokens plus `UNKNOWN` for deterministic parsing.

The dependency groups intentionally recur across time splits because the
prospective question is whether structure learned from past tasks predicts
future uses of the same external memory. Query identifiers and surface-template
families are disjoint and audited automatically.

## 3. Experimental stages

### Stage A — Backend qualification

Load the pinned local model and evaluate twelve discovery-only prompts covering
single-item, complete-pair, and missing-link conditions. Require 1.0 parsing and
at least 0.75 accuracy on supported conditions, at least 0.80 parsing overall,
and at most 0.25 accidental correctness when a link is missing before spending
the full coalition budget. Invalid outputs are deterministic errors. This stage
is diagnostic and is not P2 evidence.

### Stage B — Discovery

For every selected coalition and discovery query:

1. serialize surviving memories in original order;
2. supply all survivors directly to the model;
3. generate greedily with at most eight new tokens;
4. parse one finite action and score it deterministically;
5. commit the evaluation to SQLite immediately;
6. fit an order-2 least-squares model in the binary monomial basis to mean
   discovery accuracy.

Stability uses discovery-query bootstrap sign consistency and a deterministic
split-half top-4 overlap. P2-A candidate thresholds, locked before the LLM test,
are mean overlap at least 0.75, mean overlap margin over random ranking at least
0.50, and mean top-pair sign consistency at least 0.90.

### Stage C — Validation

Construct all retention masks from discovery coefficients only. The item policy
uses ordinary Shapley item values derived coherently from the fitted Möbius
polynomial; the interaction policy exactly maximizes that polynomial for each
small fixed budget. Random has five seeded replicates.

Validation only checks that the model can perform the controlled task: at least
80% of banks must have full-memory accuracy of at least 0.80 and a full-minus-
empty gap of at least 0.50. Failure leaves test locked.

### Stage D — One-way test unlock

Write an immutable unlock artifact only if both the P2-A discovery criterion and
validation readiness pass. It contains hashes of the config and complete
discovery/validation artifacts. The test runner rejects changed configs,
artifacts, datasets, or Git commits. Test access is never used to fit
interactions, select masks, or tune thresholds.

### Stage E — Held-out retention test

Evaluate Random, Item, and Interaction policies at nominal deletion ratios
0, 0.25, 0.50, 0.70, and 0.80. All methods use the same direct-delivery prompt
and matched payload-token and serialized-byte budgets. Report raw accuracy, empty/full baselines,
unclamped normalized memory retention, nominal and actual deletion ratios, and
per-bank effects.

P2-B requires, across the two severe nominal ratios:

- mean Interaction-minus-Item accuracy of at least 0.10;
- a positive difference in at least 80% of banks;
- one-sided paired sign-flip p-value at most 0.05.

The memory bank is the independent unit. Random-mask repetitions are repeated
conditions, not extra independent samples.

## 4. Reproducibility and failure handling

The cache key includes model ID and revision, prompt-template hash, bank, query,
coalition, generation settings, seed, and Git commit. Stored rows include raw
output, parsed action, reward, latency, token counts, and UTC timestamp. Each run
also records the complete config, public dataset manifest, Python/package/GPU
details, source-tree hash, Git state, all masks, estimates, and the test unlock.

The scientific profile requires a committed revision with clean source and
config files; newly written artifacts under `results/` do not block a resumable
stage. Rerunning the same stage resumes the SQLite cache. A model or revision
change creates distinct cache keys. Any validation failure, unstable P2-A
ranking, or P2-B failure is a valid negative result and blocks Phase 3.

## 5. Implemented deliverables

- controlled environment and immutable public manifest;
- split capabilities and leakage tests;
- mock, local Hugging Face, and OpenAI-compatible backends;
- locked direct-survivor prompts and strict action scoring;
- resumable SQLite model-evaluation cache;
- discovery fitting and query-bootstrap stability;
- Random, Item, and Interaction retention policies;
- normalized memory-survival metrics;
- staged runner, explicit unlock, model qualification, and local 4050 config;
- full mock protocol and 55-test verification.

The mock result is an engineering acceptance test only. The first scientific
artifact using `configs/experiments/phase2_local_4050.json` is analyzed below.

## 6. Backend qualification result

The final discovery-only qualification passed on 2026-08-27. Supported
conditions had 1.0 parse rate and 1.0 accuracy; overall parse rate was 0.916667;
missing-link accidental correctness was 0.25. Earlier qualification attempts
exposed a surface suffix shortcut and insufficient two-hop instructions. Those
were corrected before any scientific discovery run or test unlock by separating
request/route/destination identifier alphabets and freezing prompt version v3.

## 7. Discovery/validation result and amended next step

The scientifically eligible run at
`results/phase2/20260826T195924.594962Z/report.json` failed P2-A and validation
readiness. Mean split-half top-4 overlap was 0.55, mean overlap margin over
random was 0.407143, and mean top-pair sign consistency was 0.9705. Full-memory
validation accuracy averaged 0.58, the memory gap averaged 0.45, and zero of ten
banks met the joint readiness thresholds. The test remains locked and P2-B was
not evaluated.

The next authorized work is Phase 2-R: preserve this negative pilot, diagnose
public-split query and coefficient behavior, expand qualification to the full
bank/template distribution, screen model/task variants on separate development
banks, and use fresh confirmation banks for any new scientific run. Thresholds
must not be relaxed based on this failure. See
`docs/PHASE2_DISCOVERY_VALIDATION_ANALYSIS.md` for the complete evidence and
implementation plan.

The development screen and fresh-confirmation handoff are now implemented for
Kaggle. They use new bank ranges, two pinned 4B-class models, stronger bank-level
two-hop qualification, a tracked P1 gate certificate, and exact-commit
launchers. See `docs/PHASE2R_KAGGLE_EXECUTION.md`. Kaggle execution remains
blocked until HiberMem is published to a correct GitHub repository; the supplied
`State-Nuisance-Geometry` URL points to another project.
