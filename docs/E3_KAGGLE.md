# E3a: local checks and Kaggle execution

Read the [revised theory and implementation plan](E3_REVISED_IMPLEMENTATION_PLAN_2026-08-31.md).
E1/E2 real Qwen diagnostics are complete. E3a is implemented but has not run on a
real model. Use Qwen only in this initial matrix; no model search or Gemma adapter.

## Before Kaggle

From the repository, use the project Conda interpreter:

```powershell
.\.conda\python.exe scripts\run_tests.py -q
.\.conda\python.exe scripts\run_exact_mechanism.py --config configs\experiments\exact_mechanism_e3_core.json --dry-run
.\.conda\python.exe scripts\run_exact_mechanism.py --config configs\experiments\exact_mechanism_e3_core.json --controls-only
```

The core plan is **16,384 conditions**. The presentation follow-up is **49,152**,
including a repeat of the originals. Both are two-bank development diagnostics.
Review the intended changes, then commit and push them yourself. Use that new
published full hash from `git rev-parse HEAD`; `aa97b3aa9b93` predates E3a.
No commit, push, package installation or real-model run was performed locally.

## Fresh Kaggle notebook: core experiment

Enable Internet and GPU acceleration. The existing launcher retains Kaggle's CUDA
torch and installs the existing experiment requirements in a pip-less environment.
The unit suite blocks real-model initialization. E3a itself still needs cloud
verification; local symbolic success is not evidence of Qwen performance.

Cell 1:

```python
import os
import re

os.environ["HIBERMEM_REF"] = "PASTE_NEW_PUBLISHED_FULL_40_CHARACTER_COMMIT_HASH"
os.environ["HIBERMEM_CANDIDATE"] = "qwen"
os.environ["HIBERMEM_EXPERIMENT"] = "e3_core"
assert re.fullmatch(r"[0-9a-f]{40}", os.environ["HIBERMEM_REF"])
```

Cell 2 (fresh checkout only; preserves any existing directory by failing):

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

Cell 4 (download even after an interrupted/failed run):

```python
from pathlib import Path
from IPython.display import FileLink, display

archives = sorted(Path("/kaggle/working").glob("hibermem-exact-e3*-qwen-*.tar.gz"))
for archive in archives:
    display(FileLink(str(archive)))
if not archives:
    print("No archive found. Preserve /kaggle/working/hibermem/results/exact_mechanism manually.")
```

Cell 5, compact descriptive summary:

```python
import json
from pathlib import Path

report_path = Path("/kaggle/working/hibermem/results/exact_mechanism") / (
    os.environ["HIBERMEM_EXPERIMENT"] + "-qwen/run/report.json"
)
report = json.loads(report_path.read_text())
print({k: report[k] for k in ("status", "planned_conditions", "engineering_only", "qualified", "test_access")})
if report["status"] == "complete":
    analysis = report["analysis"]
    print("Independent base banks:", analysis["independent_base_banks"])
    for game in analysis["games"]:
        print(game["bank_id"], game["outcomes"])
    print("Development only; no qualification or future-query result.")
```

## Presentation follow-up, after reviewing core

Keep the exact same source and environment. Do not tune the prompt or endpoint
using core outputs and silently call a changed run the same experiment.

```python
os.environ["HIBERMEM_EXPERIMENT"] = "e3_presentation"
```

Then rerun cells 3–5. This independently runs original/reversed-record/reversed-option
conditions; it does not import core checkpoints. Record IDs and logical player
indices remain fixed under record-order reversal. Different presentations/worlds
are paired interventions on the same banks, not new independent samples.

## Report interpretation and recovery

- `per_query`: exact observed SII and Mobius diagnostics versus symbolic references;
  AND3 has positive pair SII despite zero pair Mobius terms.
- `games`: same-query fits and retention, with original accuracy decomposed into
  supported-correct and unsupported-correct contributions for every selection.
- `randomized_tie_sensitivity` inside each game: fixed-seed draws among maximal-score
  subsets, not new statistical replicates.
- `paired_counterfactuals`: both-world supported correctness and output agreement
  when prompts are identical despite different hidden full-world targets.
- `paired_lexical_overlap`: paired theme-word manipulation; not general semantics.
- `paired_presentation`: frozen original masks/predictions evaluated against changed
  presentations. This is NOT future-query validation; variant-refit results are
  separately reported in `games`.

Exit 0 means completed and independently validated, even for negative behavioral
findings. Exit 2 means setup/test/runtime/validation error. `qualified` stays null;
confirmation and test remain locked. Do not treat UNKNOWN rates as ordinary task
accuracy, or use support labels to choose a supposedly operational policy.

For an interrupted run, rerun cell 3 with identical source, configuration and
runtime; checkpoints are checked before reuse. Preserve old artifacts and use a
fresh checkout/run location if any identity component changes. Do not delete or
rewrite existing results to force a resume. Downloaded report validation needs
the full run bundle, not only `report.json`:

```powershell
.\.conda\python.exe scripts\validate_exact_mechanism.py --report PATH_TO_EXTRACTED_RUN\report.json
```

Validation verifies internal consistency, not cryptographic proof that an external
machine truly ran the model. No transcript/history from prior coalitions is used.
