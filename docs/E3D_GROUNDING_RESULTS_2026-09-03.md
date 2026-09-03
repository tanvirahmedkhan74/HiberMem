# E3d grounding decomposition results — 2026-09-03

## Scientific verdict

The real E3d development run is a valid, complete **negative measurement-instrument
result**. The predeclared A1 `query_anchored_v1` label-only reader passed the output
format and generation-limit checks but failed 16 frozen readiness checks. It cannot
be frozen for verification, substituted with A2, or used to unlock E4.

This result falsifies the claim that the frozen query-anchored prompt makes
`Qwen/Qwen3-4B-Instruct-2507` a sufficiently grounded reader for the controlled
AND2/AND3 retention task. It does not test retention, invalidate the exact
cooperative-game mathematics, establish a P2/P3 result, or access historical test
data.

## Artifact and independent validation

| Field | Observed value |
|---|---|
| Protocol/stage | `phase2r-grounding-decomposition-v1` / `development` |
| Source commit | `73b439204988d5ba6c06ef72373ae8ad8a629e64` |
| Git state recorded by run | clean; zero changed paths |
| Model | `Qwen/Qwen3-4B-Instruct-2507` |
| Model revision | `cdbee75f17c01a7cc42f958dc650907174af0554` |
| Conditions | 1,728/1,728; zero checkpoint reuse |
| Independent banks | 2 (`360`, `361`) |
| Runtime | Python 3.12.13, Torch 2.10.0+cu128, Transformers 5.16.1, CUDA FP16 on `cuda:0`; two Tesla T4 devices were visible |
| Run interval | 2026-09-03 08:01:00–08:40:49 UTC |
| Test record | 208 passed in 64.81 seconds |
| Launcher outcome | `validated_measurement_diagnostic`, exit 0 |
| Report SHA-256 | `a567625abcab8a3aaa406a77f5b2edbb21d101579bc519b73a5b8b026cef3c3a` |
| Evaluations SHA-256 | `133068e69fa53306a15e2f281ab2e7768a257085fb24f594e91b4a14784b2d0a` |

Canonical report:

```text
results/hibermem-e3d-development-qwen-73b439204988-20260903T075851Z-75/results/e3d_grounding/development/qwen/run/report.json
```

The model-free validator independently reconstructed the artifact and returned:

```text
Artifact validation: PASS. E3d development measurement-only evidence.
No retention result, confirmation capability, or historical-test access.
```

The original bundle is immutable evidence. Do not edit its report, rows, manifest,
identity, traces, or per-condition checkpoints.

## Primary A1 readiness result

| Frozen check | Required | Observed | Decision |
|---|---:|---:|---|
| AND2 supported accuracy | >= .95 | .875000 | Fail |
| AND3 supported accuracy | >= .95 | .890625 | Fail |
| AND2 exact-support accuracy | >= .95 | 1.000000 | Pass |
| AND3 exact-support accuracy | >= .95 | 1.000000 | Pass |
| AND2 full accuracy | >= .95 | .750000 | Fail |
| AND3 full accuracy | >= .95 | .781250 | Fail |
| AND2 unsupported assertion | <= .05 | .260417 | Fail |
| AND3 unsupported assertion | <= .05 | .402344 | Fail |
| Counterfactual tracking | >= .95 | .859375 | Fail |
| Stale-base capture | <= .05 | .062500 | Fail |
| Other-query capture | <= .05 | .218750 | Fail |
| Single-to-dual supported drop | <= .05 | .234375 | Fail |
| Strict format | >= .95 | .954861 | Pass |
| Generation-limit rate | <= .05 | 0 | Pass |

The failure replicates across both independent development banks rather than coming
from one bank: supported accuracy is .890625/.875000 and unsupported assertion is
.316964/.366071 on banks 360/361.

## Failure decomposition

### Competing-path interference

The same A1 reader is perfect on both exact support and full single-path ledgers, but
fails when the full ledger contains a second valid query path:

| Family and condition | Accuracy | Competing-query destination capture |
|---|---:|---:|
| AND2, full single-path | 1.0000 | 0 |
| AND2, full dual-path | .5000 | .5000 |
| AND3, full single-path | 1.0000 | 0 |
| AND3, full dual-path | .5625 | .4375 |

Across families, full dual-path accuracy is .53125 versus 1.0 for full single-path;
the competing destination is emitted in .46875 of full dual-path cases. The frozen
query-anchoring instruction therefore did not reliably bind the requested start
identifier when both paths were present.

### Positional partial-path completion

A1 safely abstains whenever the first required edge is removed, but it often asserts
a destination when a later edge is missing:

| Evidence condition | Missing position 0 | Missing position 1 | Missing position 2 |
|---|---:|---:|---:|
| AND2 exact support | 0 | 1.0000 | — |
| AND2 full ledger | 0 | .5625 | — |
| AND3 exact support | 0 | 1.0000 | 1.0000 |
| AND3 full ledger | 0 | .59375 | .6250 |

These are unsupported-assertion rates. The sharp dependence on link position is
mechanistically important: the model recognizes the absence of an initiating edge,
but treats an observed path prefix as sufficient evidence to complete a missing
downstream transition. In dual-path missing-full cases, the competing path is often
copied instead.

### Arm comparison

- A0 `current_v1` retains better aggregate supported accuracy (.921875 AND2,
  .984375 AND3) but fails grounding, strict format (.791667), and the generation
  limit (.194444). It is a diagnostic control and is not selectable.
- A1 fixes presentation—the strict-format rate is .954861 and no response reaches
  the generation cap—but worsens dual-path binding and unsupported completion. This
  rules out a formatting-only explanation.
- A2 `structured_verifier_v1` records zero parsed unsupported assertions, but only
  .640625 of outputs satisfy its strict certificate format and its parse-null rate is
  .359375. Supported accuracy is .921875 for AND2 and .843750 for AND3. It fails
  seven configured checks and is explicitly ineligible for E4.

The report's aggregate `accuracy` should not be interpreted as an abstention metric:
the original task reward scores unsupported conditions separately from the grounding
diagnostics. Scientific interpretation should use supported accuracy, unsupported
assertion, capture, and strict-parser measures.

## Gate decision and downstream consequences

The preregistered Stage-B rule is deterministic: if A1 fails any readiness check,
verification must not run and A2 must not be substituted. Therefore:

1. do not create `configs/experiments/e3d_grounding_verification.json`;
2. do not run reserved v1 verification banks 370–373;
3. do not run E4, E5, E6, confirmation, or the historical Phase-2 test;
4. do not resume the 49,152-condition E3 presentation sweep;
5. do not relax thresholds, edit A1, or reinterpret A2 as a pass; and
6. preserve this result as model/task-dependent negative evidence.

The most important downstream invalidation is measurement validity: without a reader
that distinguishes complete support from partial-path completion, any apparent
retention-policy advantage can be driven by unsupported guessing or competing-path
capture. E4 would therefore be uninterpretable under this model/task pair.

## Recommended next research branch

The current synthetic Qwen-4B sequence stops here. The smallest defensible follow-up
is a separately named and preregistered **E3d v2 stronger-reader qualification**, not
v1 verification:

1. Freeze one stronger reader before observing new rows. Do not screen a model list
   and select the best outcome.
2. Keep the task generator, A1 label-only prompt, deterministic decoding, metrics,
   and readiness thresholds unchanged so reader capacity is the primary intervention.
3. Run the one stronger reader on newly reserved development banks. Proposed
   reservations are 380–381 for development and 390–393 for conditional verification;
   commit these reservations before generating any condition.
4. Add multi-GPU sharding only if required by the preselected model. The current HF
   backend moves the whole model to one device and supports no quantization, so a
   14B-class FP16 run is not currently executable on a single T4.
5. If the stronger reader fails any development readiness check, stop the prospective
   retention path. Reframe the work around the grounded-evaluation confound or move
   to a fundamentally different task/interface under a new hypothesis.
6. If every development check passes, freeze that exact reader once and run one
   fresh verification cohort. Only a complete verification pass can motivate the
   separately reserved E4 variance pilot and later E4 design freeze.

If the scientific claim is model-capacity dependence rather than absolute reader
qualification, also run the frozen 4B reader on the same v2 banks and preregister a
paired comparison. That is a distinct estimand and an additional compute cost.

A deterministic symbolic graph executor would trivially solve these machine-readable
link records. It is useful as an oracle, not evidence that an LLM memory controller
works. Any hybrid executor experiment must be a separately named neuro-symbolic
study with correspondingly narrower claims.
