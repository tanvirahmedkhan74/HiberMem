# E0 / E1 / E2 execution

These commands implement the first tranche of the
[next-experiment plan](NEXT_EXPERIMENT_IMPLEMENTATION_PLAN_2026-08-31.md).
E1/E2 completion is **not qualification**. All historical v2 failures stand;
confirmation and test remain locked. Gemma's notebook-side adapter is not supported
by this new runner; do not relabel it as an audited causal-LM backend.

## Local verification (project Conda environment)

From the repository directory in PowerShell:

```powershell
.\.conda\python.exe scripts\run_tests.py -q
.\.conda\python.exe scripts\run_exact_mechanism.py --config configs\experiments\exact_mechanism_e1.json --dry-run
.\.conda\python.exe scripts\run_exact_mechanism.py --config configs\experiments\exact_mechanism_e2.json --controls-only
```

E0 reads and validates the existing raw bundle, then prints bank-bootstrap local
interaction estimates without writing anything:

```powershell
.\.conda\python.exe scripts\analyze_phase2r_v2_interactions.py --report results\hibermem-v2-qwen-8991ba49e14f-artifacts\results\phase2r_v2\qwen\report.json
.\.conda\python.exe scripts\analyze_phase2r_v2_interactions.py --report results\hibermem-v2-phi-8991ba49e14f-artifacts\results\phase2r_v2\phi\report.json
```

Review, commit and push the intended changes yourself; no commit/push is performed
by these instructions. Obtain the exact published revision with `git rev-parse HEAD`.
Do not reuse 8991ba49e14f: it does not contain this implementation.

## Fresh Kaggle notebook

Enable Internet and GPU acceleration. Start with E1 and Qwen. The launcher preserves
Kaggle's existing CUDA torch, uses the prior tested `--without-pip` bootstrap, and
does not reinstall torch. It runs the unit suite with real model loading blocked.
The new launcher itself still requires an actual Kaggle run for cloud verification.

Cell 1:

```python
import os, re
os.environ["HIBERMEM_REF"] = "PASTE_THE_NEW_FULL_40_CHARACTER_COMMIT_HASH"
os.environ["HIBERMEM_CANDIDATE"] = "qwen"  # alternatively: phi
os.environ["HIBERMEM_EXPERIMENT"] = "e1"
assert re.fullmatch(r"[0-9a-f]{40}", os.environ["HIBERMEM_REF"])
```

Cell 2, in a fresh notebook without an existing checkout:

```bash
%%bash
set -euo pipefail
git clone --filter=blob:none --no-checkout \
  https://github.com/tanvirahmedkhan74/HiberMem.git /kaggle/working/hibermem
cd /kaggle/working/hibermem
git fetch --depth 1 origin "${HIBERMEM_REF}"
git checkout --detach FETCH_HEAD
```

Cell 3:

```bash
%%bash
set -euo pipefail
cd /kaggle/working/hibermem
bash kaggle/run_exact_mechanism.sh
```

Cell 4, artifact links:

```python
from pathlib import Path
from IPython.display import FileLink, display
for artifact in sorted(Path("/kaggle/working").glob("hibermem-exact-*-artifacts.tar.gz")):
    display(FileLink(str(artifact)))
```

## E2: presentation sensitivity, after reviewing E1

Use the same committed source and environment. E2 has **6,144** conditions:
original + reversed record presentation + reversed answer-option order on the same
two development banks. This is paired sensitivity, not six independent banks.
E1 has **2,048** conditions. E2 deliberately has a separate identity/cache and repeats
its original condition; it does not silently import E1 checkpoints.

```python
os.environ["HIBERMEM_EXPERIMENT"] = "e2"
```

Then rerun cells 3 and 4. A complete run can be resumed without loading a model;
an interrupted run rechecks completed condition records and its source/runtime
identity. Do not edit source/config or change runtime to resume an old run.

## Reading the result

`report.json` contains exact game quantities, local/full-context contrasts,
order-1/2/3 surrogate diagnostics, descriptive same-query retention, and paired
presentation sensitivity. No prospective query was evaluated. No automatic
positive/negative scientific gate is assigned: `qualified` is null.

- Exit 0: independently validated completed development diagnostic, regardless
  of whether the measured interaction is positive, zero, or negative.
- Exit 2: setup, test, runtime, provenance, or artifact-validation error.

Archive contents include raw messages, decoded outputs, HF input/output token IDs,
per-condition checkpoints, runtime/template fingerprints, controls, test logs,
package versions, and launcher status. Artifact checks verify internal consistency;
they are not a proof against fabricated model execution.

Selection scores are rounded to 12 decimals before deterministic canonical tie
breaking to avoid platform-level numerical tie flips. Validator floating-point
tolerance is 1e-9 absolute / 1e-8 relative; IDs, masks, capabilities, and raw scoring
must match exactly. Randomized tie sensitivity and future generalization are deferred.

Download and preserve the bundle even when a run fails. Never unlock test based on
these diagnostics or describe the mock oracle as an LLM result.
