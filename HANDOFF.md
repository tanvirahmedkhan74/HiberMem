# HiberMem Handoff

**Updated:** 2026-08-27

**Current scientific state:** P0 and P1 passed; first Phase 2 pilot failed P2-A and validation readiness

**Locked state:** P2-B not evaluated; Gate P2 undecided; Phase 3 blocked

## Verified evidence

- Phase 0: 21 phase-specific tests passed; Gate P0 passed.
- Phase 1: Gate P1 passed at
  `results/phase1/20260826T184454.941051Z/report.json`. Interaction sign
  accuracy, precision@k, recall@k, nonzero Spearman, and sign stability were
  1.0; item MAE was 0.015359, interaction MAE 0.016337, null false-positive
  rate 0.003086, and noisy interval coverage 0.938172.
- Engineering: 48 tests passed before the scientific run; the current suite has
  55 tests after the locked-output and Kaggle workflow additions. The full mock
  protocol at `results/phase2/20260826T195617.239085Z/report.json` exercised the
  complete runner but is explicitly ineligible for scientific claims.
- Backend: the pinned SmolLM2-1.7B CUDA backend passed qualification at
  `results/phase2_backend_check/20260826T195523.639127Z/report.json`.

## Phase 2 scientific pilot

Run directory:

`results/phase2/20260826T195924.594962Z`

The run used the committed revision
`3b13934c3215f921c6757276728467bdb9d4d851`, clean scientific source/config,
dataset `phase2-routing-v4`, prompt `phase2-direct-survivors-v3`, and pinned
`HuggingFaceTB/SmolLM2-1.7B-Instruct` revision
`d1bb90bcfbe0f211109880f4da18da66f229c4f6` in CUDA float16.

The 33,520-row SQLite cache contains the planned 30,720 discovery evaluations
and 2,800 unique validation evaluations. There were 900 legitimate cache reuses
for duplicate retention conditions. No test-unlock or test artifact exists.

### P2-A result

- mean split-half top-4 overlap: 0.55, below 0.75;
- mean overlap margin over random: 0.407143, below 0.50;
- mean top-pair sign consistency: 0.9705, above 0.90;
- decision: **FAIL**, because all checks are required.

Only three of ten banks reached 0.75 top-4 overlap. Designed chain pairs filled
19 of the 40 top-pair positions. The two exact-enumeration banks reached only
0.50 and 0.75 overlap, so sampled-coalition budget alone does not explain the
failure.

### Validation result

- mean full-memory accuracy: 0.58;
- mean empty-memory accuracy: 0.13;
- mean memory gap: 0.45;
- passing banks: 0/10; required: 8/10;
- decision: **FAIL** and test remains locked.

The main capability gap is two-hop routing. Full-memory validation accuracy was
0.85 on direct queries but only 0.5125 on two-hop queries. Full-context outputs
had no parser failures, so incorrect reasoning, not strict parsing, caused the
readiness failure.

Validation retention accuracy for Interaction versus Item at nominal deletion
0.70 and 0.80 was 0.28 versus 0.28 and 0.28 versus 0.26. The combined diagnostic
advantage was only 0.01, with four positive, three tied, and three negative
banks. This is not a P2-B result because validation cannot substitute for the
locked test.

The runner previously printed a generic unlock resume command after a failed
validation. The unlock function was already fail-closed, and the runner message
has now been corrected to say that the test remains locked.

## Decision and next work

Do not run either of these stages against the current run:

```powershell
python scripts\run_phase2.py --stage unlock --run-dir results\phase2\20260826T195924.594962Z
python scripts\run_phase2.py --stage test --run-dir results\phase2\20260826T195924.594962Z
```

Do not begin Phase 3. The master decision tree requires a Phase 2 model/task-
dependence investigation:

1. preserve this run as a negative pilot and analyze only its public splits;
2. implement a deterministic diagnostic analyzer;
3. create fresh calibration-only banks and expand qualification to full-bank
   direct, two-hop, missing-link, and distractor conditions;
4. screen the current model and a feasible stronger model/configuration only on
   development banks;
5. require robust two-hop full-memory behavior before spending another full
   coalition budget;
6. freeze one revised protocol without relaxing P2 thresholds;
7. use fresh confirmation banks and a new locked test;
8. unlock that new test only if both P2-A and validation readiness pass.

The full evidence, methods, tables, interpretation, and Phase 2-R plan are in
`docs/PHASE2_DISCOVERY_VALIDATION_ANALYSIS.md`.

## Kaggle Phase 2-R implementation

The next development experiment is implemented but has not been run. It screens
two immutable 4B-class candidates on fresh banks 100–109:

- `Qwen/Qwen3-4B-Instruct-2507` at
  `cdbee75f17c01a7cc42f958dc650907174af0554`;
- `microsoft/Phi-4-mini-instruct` at
  `cfbefacb99257ffa30c83adab238a50856ac3083`.

The screen uses 1,380 generations per model and evaluates full/empty context,
minimal direct support, exact two-hop pairs, both missing-link directions, all
public template families, parse behavior, and per-bank readiness. It is
development-only and cannot pass Gate P2.

The supplied GitHub repository,
`https://github.com/tanvirahmedkhan74/State-Nuisance-Geometry.git`, is not
HiberMem; it declares project `state-geometry-video` and contains `vjepa2` code.
This local HiberMem checkout has no remote configured. The Kaggle launchers
therefore require a configurable repository URL and verify project identity
before installation. Publish this tree to a dedicated HiberMem repository
before running Kaggle.

If a screen candidate qualifies, the freeze tool writes a new confirmation
config using banks 200–209 and unchanged P2 thresholds. That config must be
reviewed, committed, and pushed. The confirmation launcher accepts only an
exact 40-character commit and runs discovery/validation only; test remains
locked. Full commands are in `docs/PHASE2R_KAGGLE_EXECUTION.md`.

## Environment

Use a fresh shell with only the project-local Conda prefix active:

```powershell
cd D:\Coding\paper\hibermem
conda activate D:\Coding\paper\hibermem\.conda
python -m pytest -q
```

The verified environment uses Python 3.11.15, PyTorch 2.13.0+cu130,
torchvision 0.28.0+cu130, Transformers 5.16.1, and accelerate 1.14.0 on the
NVIDIA GeForce RTX 4050 Laptop GPU. Do not activate `.venv` and `.conda`
simultaneously.
