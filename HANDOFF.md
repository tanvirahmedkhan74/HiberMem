# HiberMem Handoff

**Updated:** 2026-08-30

**Current scientific state:** P0/P1 passed; SmolLM2 pilot and reported Qwen/Phi v1 qualification failed; no validated full v2 screen yet (accidental two-bank inference occurred inside a failed unit test)

**Locked state:** P2-B not evaluated; Gate P2 undecided; Phase 3 blocked

## Current next action — Phase 2-R v2

### Test-isolation recovery after commit 3f2c74f (current)

Kaggle successfully installed the environment and detected two Tesla T4 GPUs.
The source-rejection test incorrectly assumed that its temporary folder was
outside Git. The workspace-local folder inherited the clean checkout, so it
loaded Qwen and completed 432 condition records on development banks 300/301.
Then pytest failed because the expected rejection never occurred: 88 passed,
1 failed. The launcher correctly stopped at stage `tests`, exit 2, without
reaching its intended controls/full-screen stages. There is no reported model
qualification decision, and no confirmation/test access occurred.

The previous repair's dirty local checkout masked this test assumption. It is
now replaced by explicit unavailable/dirty source states plus clean-state tests
that stop at a stubbed backend. An automatic fixture prohibits real backend
construction throughout the unit suite and sets Hugging Face offline variables
within test scope only. The separate screen process remains enabled. Launcher
test logs and JUnit output now enter the normal artifact archive.

Verification: 95 local tests passed; the actual clean-parent behavior was safely
reproduced before edits with model construction intercepted. Bash syntax and
diff checks passed. No production inference, thresholds, or gate code changed.

Next: preserve both the old normal archive and
`results/pytest-runs/run-dqyjld4b` on Kaggle before updating the checkout. The old
archive excludes that scratch folder. Publish this repair and rerun using its
new full commit hash; reuse cached weights but never copy the accidental test
cache into the intended run. The execution guide has the exact recovery steps.

### Setup recovery after commit 5813a28 (historical)

The user successfully published `5813a282e05b2c34aa37dc515bf532876e4ca245`.
The first Kaggle attempt failed during ensurepip, before Qwen evaluation; its
exit 1 was not a negative model result. Separately, local base-Anaconda pytest
encountered 23 shared-temp permission errors (57 tests passed).

The repair uses a pip-less Kaggle venv and base pip's explicit --python target,
preserving the partial old environment. Stage-aware exit reporting reserves 1
for validated negative screens; setup/test failures become 2. Use
`.\.conda\python.exe scripts\run_tests.py` locally for a fresh workspace-owned
temp directory. Publish this repair and use its new commit hash to update the
existing Kaggle clone; the execution guide includes exact recovery cells.
Repair verification: 89 tests passed using workspace-local test scratch;
pip-less environment targeting and Bash syntax checked locally. The subsequent
3f2c74f attempt verified this bootstrap on Kaggle and exposed the separate test
defect documented above. No model conclusion follows from the setup failure.

Use `docs/PHASE2R_V2_IMPLEMENTATION_AND_KAGGLE.md`. The dedicated remote is now
`git@github.com:tanvirahmedkhan74/HiberMem.git`. Source must be reviewed, committed,
and pushed by the user before real-model inference. No push was performed here.

The 2026-08-30 audit reproduced a zero-game stability pass, cached split bypass,
and question-blind missing-link copying shortcut. Repairs add authorization
before cache access, content/runtime cache fingerprints, nonzero balanced
stability, reserved-bank checks, public-manifest filtering, and v2 paired
counterfactual development banks 300–309 with no test queries. The screen has
2,160 condition records / 1,680 unique generations per model.

The v1 model outcomes (Qwen missing-link 0.30; Phi 0.464583; both failed) are in
`docs/PHASE2R_KAGGLE_SCREENING_RESULTS_2026-08-29.md`. Raw Kaggle artifacts still
need preservation/independent verification in this checkout. Do not describe
the v1 screen as pending or the old wrong-repository blocker as current.

Local verification: 80 tests passed; Bash syntax check passed; full 10-bank mock
v2 screen passed with a qualifying symbolic oracle and failing shortcut controls.
These are engineering checks, not real-model evidence. The public-pilot analyzer
wrote `results/audits/20260830-public-pilot-v2.json` without altering the old run.

The old freeze route is retired. A v2 qualification pass leads to exact-coalition
mechanism-feasibility work, not automatic confirmation. Semantic/dependency
factorial controls, prospective prediction panels, group-aware uncertainty, and
a compatible frozen confirmation/test protocol remain to be implemented.

## Historical record below

The following sections preserve the earlier handoff and are superseded where
they say screening has not run or the GitHub remote is absent.

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
