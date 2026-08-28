# Phase 2-R Kaggle Model Screening and Confirmation

**Status:** implemented locally; requires publication to the correct GitHub repository

## 1. Repository audit

The supplied URL,
`https://github.com/tanvirahmedkhan74/State-Nuisance-Geometry.git`, exists on
branch `main`, but it is not this project. Its `pyproject.toml` declares
`state-geometry-video` and its tree contains `vjepa2` video code. This local
HiberMem checkout currently has no Git remote configured.

Do not point Kaggle at that repository. Both Kaggle launchers now verify that
the cloned `pyproject.toml` declares project `hibermem` and stop before package
installation if it does not.

Create or select a dedicated GitHub repository containing this HiberMem tree,
then use that repository as `HIBERMEM_REPO_URL`. No code has been pushed or
remote repository mutated automatically.

## 2. Model choice

The stable Kaggle screen uses two independent 4B-class text models:

| Candidate | Immutable revision | Reason for inclusion |
|---|---|---|
| `Qwen/Qwen3-4B-Instruct-2507` | `cdbee75f17c01a7cc42f958dc650907174af0554` | Primary stable, Apache-2.0, non-thinking 4B instruction model with strong instruction-following and reasoning results |
| `microsoft/Phi-4-mini-instruct` | `cfbefacb99257ffa30c83adab238a50856ac3083` | Independent MIT-licensed 3.8B architecture focused on constrained and reasoning-heavy use |

Official model cards:

- <https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507>
- <https://huggingface.co/microsoft/Phi-4-mini-instruct>

`Qwen/Qwen3.5-4B` is newer, but it is not used in this stable scientific path.
Its current official instructions require Transformers from the unreleased
`main` branch and a multimodal model/processor path. Introducing both a moving
library target and a different backend would confound model capability with
runtime changes. It can be evaluated later as a separately versioned
engineering candidate after stable released support is available.

Both selected candidates run in float16 without quantization. Their weights fit
a 16 GiB Kaggle GPU one at a time; the screening runner explicitly releases one
model and clears the CUDA cache before loading the next.

## 3. What the development screen measures

The previous 12-case qualification overestimated real two-hop performance. The
new screen uses ten fresh calibration banks numbered 100–109 and never obtains
a test evaluation view. For every discovery and validation query it evaluates:

- full eight-memory context;
- empty context;
- the single required memory for direct queries;
- the exact required pair for two-hop queries;
- missing-first-link and missing-second-link two-hop conditions.

This is 1,380 cached generations per model, 2,760 for the complete two-model
screen. Every raw output remains in a per-model SQLite cache; compact condition
rows and bank/model summaries are also written as JSON.

A bank passes only if:

| Check | Threshold |
|---|---:|
| Full-memory direct accuracy | >= 0.90 |
| Full-memory two-hop accuracy | >= 0.80 |
| Full-minus-empty accuracy gap | >= 0.50 |
| Full-context parse rate | >= 0.98 |

A model qualifies only if at least 80% of banks pass and its mean missing-link
false-positive rate is at most 0.25. Among qualified candidates, selection is
locked to full two-hop accuracy, then memory gap, then full direct accuracy.

The screen is marked `scientific_gate_eligible: false`. It selects a development
candidate; it cannot pass P2-A, P2-B, or Gate P2.

## 4. Kaggle environment

Create a Kaggle notebook with:

- a GPU accelerator enabled (T4 or better is appropriate);
- Internet enabled for GitHub and Hugging Face downloads;
- at least 30 GiB free working storage;
- optional `HF_TOKEN` Kaggle secret for higher Hub download limits.

The launcher preserves Kaggle's CUDA-enabled PyTorch instead of replacing it.
It pins Transformers 5.16.1, Accelerate 1.14.0, Hugging Face Hub 1.28.0, and
Safetensors 0.8.0, installs HiberMem editable, verifies CUDA and repository
identity, runs all tests, executes the screen, and packages the reports and
caches.

## 5. Publish HiberMem to GitHub

Review the local changes and create a dedicated GitHub repository first. From a
clean project-local Conda shell:

```powershell
cd D:\Coding\paper\hibermem
conda activate D:\Coding\paper\hibermem\.conda
python -m pytest -q
git status --short
git add README.md CHANGELOG.md HANDOFF.md pyproject.toml
git add src scripts tests configs docs kaggle
git commit -m "Add Kaggle Phase 2-R model screening"
git remote add origin <CORRECT_HIBERMEM_GITHUB_URL>
git push -u origin master:main
git rev-parse HEAD
```

The explicit `git add` paths leave the large untracked `results/` directory out
of the commit. If a correct HiberMem remote is already configured in the future,
do not add another `origin`; inspect `git remote -v` and use that remote.

## 6. Run the Kaggle development screen

In the first Kaggle notebook cell, substitute the correct HiberMem repository
and the commit produced above:

```python
import os
import subprocess

os.environ["HIBERMEM_REPO_URL"] = "<CORRECT_HIBERMEM_GITHUB_URL>"
os.environ["HIBERMEM_REF"] = "<SCREEN_COMMIT_OR_MAIN>"

subprocess.run(
    ["git", "clone", "--depth", "1", os.environ["HIBERMEM_REPO_URL"],
     "/kaggle/working/hibermem"],
    check=True,
)
subprocess.run(
    ["bash", "/kaggle/working/hibermem/kaggle/run_phase2r_screen.sh"],
    check=False,
    env=os.environ,
)
```

The launcher may return exit code 1 when no candidate qualifies. That is a
scientific stop condition, not an infrastructure crash. In either case,
download:

`/kaggle/working/hibermem-phase2r-screen-artifacts.tar.gz`

Inspect `results/phase2r_kaggle_screen/kaggle/report.json`. If
`selected_candidate` is null, do not run confirmation.

## 7. Freeze the selected candidate locally

If one or both candidates qualify, extract the downloaded artifact into a new
temporary directory and run:

```powershell
python scripts\freeze_phase2r_confirmation.py `
  --screen-report <EXTRACTED_ARTIFACT>\results\phase2r_kaggle_screen\kaggle\report.json
git diff -- configs\experiments\phase2r_kaggle_confirmation.json
git add configs\experiments\phase2r_kaggle_confirmation.json
git commit -m "Freeze Phase 2-R Kaggle confirmation"
git push
git rev-parse HEAD
```

The freeze tool refuses to overwrite an existing confirmation config, requires
a qualified selection, pins its 40-character model revision, retains all
existing P2 thresholds, uses seed 314159, reserves fresh banks 200–209, and
records the development-screen report hash.

## 8. Run fresh discovery/validation confirmation

Start a new Kaggle session. `HIBERMEM_REF` must be the exact 40-character commit
containing the frozen confirmation config; the confirmation launcher rejects a
branch name.

```python
import os
import subprocess

os.environ["HIBERMEM_REPO_URL"] = "<CORRECT_HIBERMEM_GITHUB_URL>"
os.environ["HIBERMEM_REF"] = "<EXACT_40_CHARACTER_CONFIRMATION_COMMIT>"

subprocess.run(
    ["git", "clone", "--depth", "1", os.environ["HIBERMEM_REPO_URL"],
     "/kaggle/working/hibermem-confirmation"],
    check=True,
)
subprocess.run(
    ["bash", "/kaggle/working/hibermem-confirmation/kaggle/"
     "run_phase2r_confirmation.sh"],
    check=False,
    env=os.environ,
)
```

Download:

`/kaggle/working/hibermem-phase2r-confirmation-artifacts.tar.gz`

The confirmation script runs discovery/validation only. It packages artifacts
even when a gate fails and never unlocks the held-out test. Review P2-A and
validation readiness locally before deciding whether the new run is eligible
for an explicit, one-way test unlock.

## 9. Decision boundary

- No screen candidate qualifies: record model/task dependence as negative and
  do not spend the full coalition budget.
- A candidate qualifies but fresh P2-A or validation fails: preserve the result,
  keep test locked, and stop/pivot.
- Fresh P2-A and validation both pass: review hashes and provenance, then unlock
  that confirmation run once and evaluate P2-B.
- Phase 3 remains prohibited until a fresh held-out P2-B result also passes.
