# HiberMem experiment implementation and run plan — 2026-09-03

## 1. Governing decision

**Post-run status:** E3d v1 development completed as a validated negative result. A1
failed 16 frozen readiness checks, so steps D4–D7 and every verification command in
this document are now blocked. Do not create the v1 verification config or run banks
370–373. See [E3D_GROUNDING_RESULTS_2026-09-03.md](E3D_GROUNDING_RESULTS_2026-09-03.md).

This document preserves the preregistered implementation and execution path. E3d
qualifies the reader/output instrument; it is not a retention experiment. E4, E5,
E6, confirmation, the historical Phase-2 test, and the large E3 presentation sweep
remain blocked. Any stronger-reader follow-up is a new E3d v2 protocol requiring a
new preregistration, new identities, fresh banks, and complete engineering validation.

The execution path is fail-closed:

```text
E3d symbolic controls
  -> E3d mock artifact + independent validation
  -> clean committed source
  -> E3d real development (banks 360-361)
  -> independent validation and A1 decision
  -> [only if every A1 check passes] immutable verification config
  -> clean committed verification config
  -> one E3d real verification run (banks 370-373)
  -> [only if every A1 verification check passes] new E4 design freeze
```

No stage may pool development and verification rows, relax thresholds, reuse banks,
or substitute the structured A2 arm for the label-only A1 arm.

## 2. Implemented E3d components

| Component | Purpose | Inputs | Outputs | Validation |
|---|---|---|---|---|
| `environments/controlled/grounding.py` | Deterministic matched single/dual ledgers, evidence panels, prompts, certificate parser, symbolic oracle | Frozen cohort and factorial config | Manifest and 288 conditions per bank/arm | Exact support, payload, prompt/parser, count controls |
| `evaluation/grounding.py` | Reconstruct all aggregate, subgroup, counterfactual, interference, per-link, and bank-level metrics | Raw immutable rows | Readiness report with every failed check | Recomputed by independent validator |
| `experiments/grounding.py` | Run identity, checkpoints, resume, provenance, artifact hashes, mock/real separation | Config, backend, run directory | Complete evidence bundle | Rejects altered config, rows, source, runtime, or capability claims |
| `run_e3d_grounding.py` | Dry run, controls, mock, or real execution | Frozen config | Run artifact | Returns 2 on a stopped/invalid run |
| `validate_e3d_report.py` | Model-free independent reconstruction | Complete report path | PASS/FAIL | Reads raw rows and rebuilds all checks |
| `freeze_e3d_verification.py` | Create verification config after a passing real A1 development result | Real development artifact | Non-overwriting verification config | Rejects mock, failed, altered, or incomplete evidence |
| `run_e3d_grounding.sh` | Clean-commit Kaggle execution and archive | Commit, config, optional bound development report | Downloadable resumable archive | Full tests, controls, runner, independent validator |

## 3. Frozen E3d run matrix

### Development run D3

- Base-bank seeds: 360–361.
- Arms: A0 `current_v1`, A1 `query_anchored_v1`, A2
  `structured_verifier_v1`.
- Families: AND2 and AND3.
- Lexical overlap: low and high.
- Worlds: base and counterfactual.
- Query roles: two matched start identifiers.
- Ledgers: single path and competing dual path.
- Evidence: empty, exact support, full, every exact-support link deletion, every
  full-ledger link deletion, and other-path/nuisance-only.
- Calls: 2 banks × 3 arms × 288 = 1,728.
- Selection rule: only A1 may enter verification, and only if every frozen aggregate,
  family, per-link, counterfactual, query-binding, format, and generation check passes.

### Verification run D6

- Base-bank seeds: 370–373.
- Arms: unchanged A0 and the exact selected A1; A2 is absent.
- Calls: 4 banks × 2 arms × 288 = 2,304.
- The config must be generated from, and cryptographically bound to, the passing real
  development artifact. The run and independent validator also require that source
  development report.
- A pass permits creation of a new E4 design configuration for separate review and
  commit. It does not itself run or establish HiberMem.

## 4. Execution work breakdown

### D0 — repository preflight

**Purpose:** ensure the code and preregistration are the only authority used for the
run. **Files:** all source, config, test, launcher, and protocol documents. **Inputs:**
current checkout. **Outputs:** passing suite and reviewed diff. **Validation:** full
tests, diff check, exact 40-character commit. **Dependency:** none.

Go only if the suite, E3d controls, and working-tree review pass.

### D1 — symbolic and mock qualification

**Purpose:** prove the generator, panel, parser, resumability, artifact reconstruction,
and gates work without model inference. **Files:** E3d modules and development config.
**Inputs:** symbolic oracle. **Outputs:** `results/e3d_local_verification/run/`.
**Validation:** independent validator with `--allow-mock`; verification freeze must
reject this artifact. **Dependency:** D0 source implementation.

Go only if the mock artifact validates and the mock freeze fails closed.

### D2 — immutable source freeze

**Purpose:** bind the real run to reviewable source. **Inputs:** passing D0/D1.
**Outputs:** committed and pushed source revision. **Validation:** clean Git status and
exact remote commit. **Dependency:** human review of prompts, parser, config, and tests.

No real inference is permitted from a dirty checkout.

### D3 — real development inference

**Purpose:** determine whether A1 solves the grounding/output contract on fresh
development banks. **Inputs:** committed development config and pinned Qwen revision.
**Outputs:** raw rows, traces, runtime, manifest, controls, analysis, report, archive.
**Validation:** independent validator. **Dependency:** D2.

Stop if A1 fails any check. Do not choose A0 or A2, tune the prompt, or run banks
370–373 after observing a failure.

### D4 — development decision and archive

**Purpose:** record all failures and make the one preregistered decision. **Inputs:**
validated D3 artifact. **Outputs:** retained immutable archive and either a stopped
decision or a generated verification config. **Validation:** raw-row reconstruction,
bank-level inspection, all failed subgroups reported. **Dependency:** D3.

### D5 — verification freeze

**Purpose:** bind A1, its prompt hash, generation settings, and development evidence to
fresh verification banks. **Inputs:** passing real D3 report. **Outputs:**
`configs/experiments/e3d_grounding_verification.json`. **Validation:** config parser and
source-artifact hash checks. **Dependency:** every A1 D3 check passing.

The generated file must be reviewed, committed, and pushed before D6.

### D6 — one real verification run

**Purpose:** test the unchanged A1 once on banks 370–373. **Inputs:** committed
verification config plus the bound development artifact. **Outputs:** separate
verification archive. **Validation:** independent reconstruction using both artifacts.
**Dependency:** D5.

Stop E4 for this reader/task pairing if A1 fails any verification check.

### D7 — prospective handoff, still blocked

Only after D6 passes: implement a new E3d-to-E4 freeze that binds the verified A1
contract to the existing E4 past/freeze/future state machine. Before real E4, conduct
the separately reserved variance-only pilot needed to freeze bank count and practical
margin. E4 must retain exact Shapley as the primary item comparator and all planned
strong baselines.

### Later scientific runs

| Run | Hypothesis | Earliest gate | Primary failure condition |
|---|---|---|---|
| E4a prospective retention | H1 and surface-transfer H3a | D6 plus variance/power freeze | No practical advantage over every prespecified strong item baseline |
| E4b compositional/temporal shift | H3b/H3c | Successful E4a instrument and separately versioned generator | Low-order past predictor does not transfer under genuine shift |
| E5 matched sign-aware lesions | H2 | Positive, validated prospective evidence | Predicted positive nonlinear loss does not predict matched future damage |
| E6 second-model/natural-memory replication | External validity | Controlled H1/H2 evidence | Gains fail to replicate or cost exceeds achieved savings |

## 5. Local CLI commands

Run these from PowerShell at the repository root.

### Preflight and dry run

```powershell
cd D:\Coding\paper\hibermem
conda run --prefix .\.conda python scripts\run_tests.py -q
conda run --prefix .\.conda python scripts\run_e3d_grounding.py --dry-run
conda run --prefix .\.conda python scripts\run_e3d_grounding.py --controls-only
git diff --check
git status --short
```

### Full mock pipeline

```powershell
conda run --prefix .\.conda python scripts\run_e3d_grounding.py `
  --candidate mock `
  --run-dir results\e3d_local_verification\run

conda run --prefix .\.conda python scripts\validate_e3d_report.py `
  --report results\e3d_local_verification\run\report.json `
  --allow-mock
```

The following command must fail and create no output because mock evidence cannot
authorize verification:

```powershell
conda run --prefix .\.conda python scripts\freeze_e3d_verification.py `
  --development-report results\e3d_local_verification\run\report.json `
  --output configs\experiments\e3d_grounding_verification.json
```

### Real development run on a suitable local CUDA machine

Run only after reviewing, committing, and pushing all source/config changes.

```powershell
conda run --prefix .\.conda python scripts\run_e3d_grounding.py `
  --config configs\experiments\e3d_grounding_development.json `
  --candidate qwen `
  --run-dir results\e3d_grounding\development\qwen\run

conda run --prefix .\.conda python scripts\validate_e3d_report.py `
  --report results\e3d_grounding\development\qwen\run\report.json
```

### Freeze verification only after a real A1 development pass

```powershell
conda run --prefix .\.conda python scripts\freeze_e3d_verification.py `
  --development-report results\e3d_grounding\development\qwen\run\report.json `
  --output configs\experiments\e3d_grounding_verification.json

conda run --prefix .\.conda python scripts\run_e3d_grounding.py `
  --config configs\experiments\e3d_grounding_verification.json `
  --development-report results\e3d_grounding\development\qwen\run\report.json `
  --candidate qwen `
  --run-dir results\e3d_grounding\verification\qwen\run

conda run --prefix .\.conda python scripts\validate_e3d_report.py `
  --report results\e3d_grounding\verification\qwen\run\report.json `
  --development-report results\e3d_grounding\development\qwen\run\report.json
```

## 6. Kaggle CLI command

The full copy-paste notebook cells, artifact transfer, inspection, and stop rules are
in `docs/E3D_KAGGLE.md`.

After committing and pushing, use a fresh Kaggle checkout and set the exact revision:

```bash
export HIBERMEM_REF="$(git rev-parse HEAD)"
bash kaggle/run_e3d_grounding.sh
```

For verification, first extract the preserved development archive into
`results/e3d_grounding/development/qwen/run`, check out the commit containing the
generated verification config, and run:

```bash
export HIBERMEM_REF="$(git rev-parse HEAD)"
export HIBERMEM_E3D_CONFIG="configs/experiments/e3d_grounding_verification.json"
export HIBERMEM_E3D_DEVELOPMENT_REPORT="results/e3d_grounding/development/qwen/run/report.json"
bash kaggle/run_e3d_grounding.sh
```

## 7. Artifact and recovery rules

- Never edit a row, report, trace, manifest, or identity in place.
- Resume only into the identical run directory with the identical source/config/runtime.
- A changed prompt, parser, model, threshold, cohort, or panel is E3d v2 and needs new
  banks.
- Keep development and verification archives together; verification validation needs
  the exact bound development report.
- Treat exit 2 as a stopped/invalid run, not a negative model result, unless a complete
  independently validated report exists.
- The mock artifact is engineering-only even when every oracle check passes.
- Do not run any E4 CLI command until a real E3d verification pass and a new committed
  E4 design freeze exist.
