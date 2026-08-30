# Phase 2-R v2: validity repair and Kaggle execution

**Date:** 2026-08-30  
**Scientific state:** P0/P1 passed; no scientific P2 pass; test locked; Phase 3 blocked.  
**Delivery:** safeguards, a fresh development capability screen, symbolic/shortcut
controls, an artifact validator, public-pilot diagnostics, and a Kaggle launcher.

## Recovery from the 5813a28 setup failure

The reported Kaggle attempt failed inside venv's `ensurepip` bootstrap, before
installing dependencies or evaluating Qwen. Its raw exit 1 is an infrastructure
failure, not a negative screen. The commit/push succeeded; the local pytest log
instead showed 57 passing tests and 23 temporary-directory setup errors, with
pytest loaded from base Anaconda rather than the verified project environment.

The repaired launcher creates `hibermem-v2-env-nopip` using `--without-pip` and
installs through the base interpreter's `pip --python <environment-python>`.
This is the [documented pip workflow for pip-less environments](https://pip.pypa.io/en/stable/topics/python-option/).
It leaves the partial old environment untouched, retains Kaggle's torch, and
uses explicit interpreter paths. Setup/test failures now return 2 and record
their stage in `<candidate>-launcher-status.json`; only a completed, validated
screen can return 0 or 1. Bootstrap/install logs are included in the archive.

On Windows use `.\.conda\python.exe scripts\run_tests.py`. This helper creates a
unique empty directory under `results/pytest-runs/` and never accesses or deletes
the inaccessible shared `AppData/Local/Temp/pytest-of-tanvi` directory. No admin
privileges or permission changes are needed. The scratch directories remain for
debugging. Pytest clears its basetemp, so do not manually set it to a directory
containing files you want to retain.

After testing, commit/push the repair and use its NEW commit hash on Kaggle.
The existing clone from the failed attempt can be reused without cloning again:

```python
import os
os.environ["HIBERMEM_REF"] = "PASTE_NEW_FULL_40_CHARACTER_REPAIR_COMMIT"
os.environ["HIBERMEM_CANDIDATE"] = "qwen"
os.environ["HIBERMEM_MIN_FREE_STORAGE_GIB"] = "15"
```

```bash
%%bash
set -euo pipefail
[[ "${HIBERMEM_REF}" =~ ^[0-9a-f]{40}$ ]] || { echo "Set the repair commit first"; exit 2; }
cd /kaggle/working/hibermem
[[ -z "$(git status --porcelain)" ]] || { echo "Preserve checkout changes before updating"; exit 2; }
git fetch --depth 1 origin "${HIBERMEM_REF}"
git checkout --detach FETCH_HEAD
bash kaggle/run_phase2r_v2.sh
```

This recovery is appropriate for the reported pre-inference failure. Do not mix
completed model runs from different commits: use fresh run directories/sessions
if any inference already occurred.

## 1. Decision and scope

The first SmolLM2 pilot failed stability and task readiness. The subsequently
reported Qwen/Phi v1 screens failed missing-link qualification (0.30/0.464583
against 0.25). Preserve these as negative results. Do not rerun or overwrite
them with this implementation. The v1 Kaggle results are documented in
`PHASE2R_KAGGLE_SCREENING_RESULTS_2026-08-29.md`; their raw artifacts should be
preserved separately for independent verification.

The audit reproduced a zero-game P2-A pass, a cached split-capability bypass,
and a question-blind copying shortcut. Those defects motivate this new protocol;
they do not retroactively change the recorded decisions.

This delivery implements the first repair/qualification increment, not the full
remaining master plan. It deliberately cannot freeze a scientific confirmation
config. Passing task qualification is not evidence of stable useful interactions.

## 2. Implemented changes

- Query identity and split authorization are checked before cache access.
- Cache v2 fingerprints the actual prompt, scoring identity, backend settings,
  relevant package versions, and source contents. Old cache entries are not
  silently reused. Scientific runs reject changed source/config identity.
- Public manifests omit test queries. The new development suite does not even
  generate test queries. The legacy generator remains an in-process research
  utility, not a cryptographic test-data vault.
- Legacy calibration is confined to banks [100,200); v2 uses [300,400).
  Banks [400,500) are reserved for future v2 confirmation.
- Stability protocol `nonzero-balanced-v2` rejects zero/near-zero effects and
  requires bootstrap intervals excluding zero. Its repeated-query halves are
  balanced within dependency and direct/two-hop kind; singleton strata are
  excluded and counted. The default 1e-8 floor is numerical, not a scientifically
  calibrated practical-effect threshold. A meaningful floor still needs
  development calibration before confirmation.
- A v2 report validator reconstructs cases, scores raw outputs, recomputes
  qualification and controls, and checks artifact hashes. This checks internal
  consistency, not authenticity against deliberate fabrication.
- Legacy confirmation freezing is retired. A v2 capability pass also cannot
  freeze confirmation before a reviewed interaction-feasibility protocol exists.
- `analyze_phase2_public.py` reports additive/quadratic in-sample fit, exact versus
  surrogate Shapley retention, sampled-coalition sensitivity on exact banks, actual
  deletion fractions, and bank-bootstrap intervals. It reads no test artifact.

## 3. New development benchmark

Protocol: `phase2r-counterfactual-routing-v2`. Ten base banks, 300–309, contain
eight records each. Identifiers are independently sampled, option order is
shuffled, and record positions are independent of chain membership. There are
four two-hop chains and three public question templates per query kind.

For each chain, alternate worlds change either the request-to-route assignment
or route-to-destination assignment. The omitted changed record makes the two
incomplete prompts byte-for-byte identical, while their underlying correct
answers differ. Full prompts must distinguish the worlds. All alternate worlds
are repeated conditions of their base bank, not additional independent banks.

Conditions:

| Condition | Purpose |
|---|---|
| Full and empty | Competence and memory dependence |
| Direct minimal and pair only | Sufficient support without distractors |
| Missing first/second, minimal | Abstention despite a tempting answer-copy shortcut |
| Missing first/second, full context | Required-link removal with competing records retained |
| Counterfactual full pairs | Both changed answers must be correct |
| Counterfactual missing pairs | Identical ambiguous evidence must produce consistent abstention |

Each model has **2,160 condition records, 1,680 unique generations**. The extra
480 records are intentional cache reuse. Both models together need 3,360 unique
generations. Generation is greedy, maximum 16 new tokens. More output tokens than
v1 are allowed for the new random identifiers; this is declared before inference.

The screen records final-answer accuracy separately from abstention, unsupported
assertions, parse failures, and exact-format compliance. Returning UNKNOWN under
insufficient evidence is correct abstention but earns zero on the original
downstream destination-accuracy metric; these two metrics must not be conflated.

### Locked development qualification rules

At least 80% of base banks must meet all of:

- full/direct-minimal accuracy >=0.90;
- full two-hop and pair-only accuracy >=0.80;
- full-minus-empty gap >=0.50;
- full strict-format rate >=0.98.

Each of the four missing-link direction/context conditions must separately have
mean accidental correctness <=0.25 and abstention >=0.90. Counterfactual full-pair
accuracy must be >=0.80, missing-pair abstention >=0.90, and identical-prompt output
consistency 1.0. These are new development diagnostics, not a relaxation or
replacement of any old reported gate. Do not change them after seeing v2 results.

Before inference, the symbolic chain-following oracle must qualify; destination
copying and first-option controls must not qualify. Controls alone are engineering
acceptance checks, not evidence about an LLM.

## 4. Local checks and publication

Use the existing Conda environment in a fresh terminal:

```powershell
cd D:\Coding\paper\hibermem
.\.conda\python.exe scripts\run_tests.py
.\.conda\python.exe scripts\run_phase2r_v2.py --candidate mock --run-dir results\phase2r_v2\prepublish-smoke
.\.conda\python.exe scripts\validate_phase2r_v2_report.py --report results\phase2r_v2\prepublish-smoke\report.json --allow-mock
git diff --check
git status --short
```

If source/config changed after a smoke run, choose a new run-directory name.
Resuming a different protocol in an existing directory is intentionally rejected.

Review the diff before staging. The existing remote is the dedicated HiberMem
repository, not State-Nuisance-Geometry. No commit or push was performed by the
implementation agent. Publish the reviewed source and record the full commit:

```powershell
git diff
git add src scripts tests configs kaggle docs README.md HANDOFF.md CHANGELOG.md
git diff --cached --stat
git commit -m "Add Phase 2-R v2 validity safeguards and counterfactual screen"
git push origin HEAD
git rev-parse HEAD
git status --short
```

The last status must be clean. Review the previously untracked v1 screening
summary as part of the docs being staged. Do not add `results/`, model weights,
credentials, or environments. Kaggle must be able to read the GitHub repository;
if it is private, configure authentication via Kaggle Secrets, never a token
embedded in notebook source or a clone URL.

Optional old-pilot analysis, without modifying the original run:

```powershell
python scripts\analyze_phase2_public.py --run-dir results\phase2\20260826T195924.594962Z --output results\audits\pilot-public-review.json
```

This analysis is exploratory. Its R2 is in-sample discovery fit, not prospective
R2. Choose a new output name if the file already exists.

## 5. Kaggle sequence — Qwen first

Create a fresh Kaggle notebook/session, enable Internet and a GPU accelerator.
One 16 GB-class GPU is intended; two T4s do not pool memory in this backend.
Keep at least 15 GiB free working storage before downloading this single model.
Do not reinstall torch or use the local Windows CUDA-13 wheel command on Kaggle.

In the first notebook cell, replace the commit placeholder with the exact
40-character commit printed locally:

```python
import os
os.environ["HIBERMEM_REF"] = "PASTE_THE_FULL_40_CHARACTER_COMMIT"
os.environ["HIBERMEM_CANDIDATE"] = "qwen"
os.environ["HIBERMEM_MIN_FREE_STORAGE_GIB"] = "15"
```

HF authentication is optional for these public models. If used, create a Kaggle
secret named HF_TOKEN and load it without printing it:

```python
from kaggle_secrets import UserSecretsClient
os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")
```

In the next cell:

```bash
%%bash
set -euo pipefail
[[ "${HIBERMEM_REF}" =~ ^[0-9a-f]{40}$ ]] || { echo "Set the exact commit first"; exit 2; }
REPO_URL="https://github.com/tanvirahmedkhan74/HiberMem.git"
WORKDIR="/kaggle/working/hibermem"
if [[ ! -e "${WORKDIR}" ]]; then
  git clone --filter=blob:none --no-checkout "${REPO_URL}" "${WORKDIR}"
else
  [[ -d "${WORKDIR}/.git" ]] || { echo "Existing path is not a checkout"; exit 2; }
  [[ "$(git -C "${WORKDIR}" remote get-url origin)" == "${REPO_URL}" ]] || { echo "Wrong remote"; exit 2; }
  [[ -z "$(git -C "${WORKDIR}" status --porcelain)" ]] || { echo "Existing checkout has changes"; exit 2; }
fi
git -C "${WORKDIR}" fetch --depth 1 origin "${HIBERMEM_REF}"
git -C "${WORKDIR}" checkout --detach FETCH_HEAD
bash "${WORKDIR}/kaggle/run_phase2r_v2.sh"
```

The launcher:

1. verifies project identity, exact commit, and clean checkout;
2. creates a pip-less Python environment inheriting Kaggle's CUDA torch, bypassing ensurepip;
3. installs the pinned model runtime and test dependencies using base pip's --python target;
4. checks that torch was not replaced, checks GPU/storage, and saves package/runtime records;
5. runs unit tests with fresh workspace-owned scratch directories, then symbolic/shortcut controls;
6. runs the selected model and verifies the completed artifact, including a negative result;
7. bundles results on exit, including failures. It never deletes model caches.

Exit codes: **0** = development qualification passed; **1** = completed negative
screen; **2** = setup/dependency/test/runner/identity/evidence error. The original
process status is preserved in the launcher-status JSON. A notebook CalledProcessError after exit 1 is an
expected negative scientific-development result, not a reason to relax thresholds.

Download the archive from Kaggle's Output/files pane:

```text
/kaggle/working/hibermem-v2-qwen-<first12commit>-artifacts.tar.gz
```

It includes reports, raw outputs, SQLite cache, manifests, config, control
results, package snapshot, and environment report. No weights or tokens are
included. Save the notebook/output version before ending the session.

## 6. Phi in a fresh session

After downloading Qwen's output, use a fresh Kaggle session to avoid storing two
model downloads simultaneously. Repeat the cells with the SAME commit and:

```python
os.environ["HIBERMEM_CANDIDATE"] = "phi"
```

Download `hibermem-v2-phi-<first12commit>-artifacts.tar.gz`. The native Phi model
implementation uses `trust_remote_code: false`. Do not change the model revision,
prompt, thresholds, or runtime between candidates.

For interrupted inference in the SAME unchanged session, rerun the launcher;
SQLite resumes completed generations. To resume from a downloaded archive, first
restore its results tree into a clean checkout of the exact commit and reproduce
the saved runtime. The identity/runtime checks reject incompatible resumption.

## 7. Review and stop conditions

- Both fail: preserve results, inspect direction-specific abstention and
  counterfactual behavior; stop this branch or preregister a separate redesign.
- One or both pass: qualification permits planning a fresh exact-coalition
  feasibility experiment, NOT a confirmation run or test unlock.
- Do not run the old confirmation launcher or freeze tool. The freeze tool now
  fails closed rather than mapping the new screen into the old benchmark.

Remaining work before scientific confirmation:

1. Implement the semantic-overlap x functional-dependency 2x2 benchmark, with
   additive, redundant-OR, conflict, distractor, and triple-AND controls.
2. Add a preregistered independent development query/coalition panel for
   prospective additive-vs-interaction R2, RMSE, retention regret, and stability.
   Include group/template-aware resampling, practical effect-size calibration,
   and exact Shapley / separately fitted additive baselines under equal budgets.
3. Demonstrate interaction feasibility on fresh development banks; do not treat
   successful full-context reasoning as interaction evidence.
4. Freeze a compatible new confirmation generator/config and a truly locked
   test capability; account for serialized payload and metadata, and report
   actual severe-deletion fractions plus paired bank-level confidence intervals.
5. Only after a prospective P2 pass, implement utility-matched, sign-separated
   structural lesions. No graph retrieval, RL, regrowth, or fault-tolerance claim
   is authorized by this development screen.

## 8. Model/runtime sources

The model matrix is intentionally unchanged so benchmark repairs can be studied
without an additional model-search confound. It is not a new SOTA ranking claim.

- [Qwen3-4B-Instruct-2507 model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
- [Phi-4-mini-instruct model card](https://huggingface.co/microsoft/Phi-4-mini-instruct)
- [Kaggle runtime image repository](https://github.com/Kaggle/docker-python)

The v2 dependency entry point is `configs/requirements/kaggle-phase2r-v2.txt`.
It includes the existing model-runtime pins and pins the direct numerical/test
dependencies to the locally verified versions. Python 3.11 or newer is required
for this Kaggle workflow. Kaggle's installed CUDA torch is retained and recorded
rather than replaced; remaining transitive versions are captured in the package
snapshot and checked where relevant to cache/runtime compatibility.
