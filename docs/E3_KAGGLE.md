# E3a: matched decoding diagnostic and Kaggle execution

Read the [revised theory and implementation plan](E3_REVISED_IMPLEMENTATION_PLAN_2026-08-31.md).
E1/E2 and the real E3 core Qwen run are complete and independently validated.
Read the [E3 core findings and next-step decision](E3_CORE_RESULTS_AND_NEXT_STEP_2026-08-31.md).
The current next run is **e3_decode64**, not the large presentation matrix. It
changes only the generation cap from 16 to 64, preserving all prompts and scoring.
Use the same pinned Qwen model; no model search or Gemma adapter.

## Before Kaggle

From the repository, use the project Conda interpreter:

```powershell
.\.conda\python.exe scripts\run_tests.py -q
.\.conda\python.exe scripts\run_exact_mechanism.py --config configs\experiments\exact_mechanism_e3_decode64.json --dry-run
.\.conda\python.exe scripts\run_exact_mechanism.py --config configs\experiments\exact_mechanism_e3_decode64.json --controls-only
```

The decode64 plan is **16,384 conditions**, exactly matching the completed core
matrix. The existing **49,152**-condition presentation config is still 16-token and
is on hold. Both are two-bank development diagnostics, never independent test sets.
Review the intended changes, then commit and push them yourself. Use that new
published full hash from `git rev-parse HEAD`; `e98cf871877b` predates decode64
preparation. No commit, push, package installation or real-model run was performed
locally. Preserve the original core bundle for comparison; never resume it using
the changed cap.

## Fresh Kaggle notebook: matched decode64 experiment

Enable Internet and GPU acceleration. The existing launcher retains Kaggle's CUDA
torch and installs the existing experiment requirements in a pip-less environment.
The unit suite blocks real-model initialization. Decode64 still needs a real run;
local symbolic success cannot establish that a larger cap improves Qwen.

Cell 1:

```python
import os
import re

os.environ["HIBERMEM_REF"] = "PASTE_NEW_PUBLISHED_FULL_40_CHARACTER_COMMIT_HASH"
os.environ["HIBERMEM_CANDIDATE"] = "qwen"
os.environ["HIBERMEM_EXPERIMENT"] = "e3_decode64"
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

## Presentation follow-up — on hold after core review

Do not run `e3_presentation` as the automatic next step. It remains the original
16-token configuration, useful only if that historical sensitivity is explicitly
desired. After decoding review, any presentation experiment under a changed cap
needs a separately frozen config. Do not silently edit the old config or reuse its
checkpoints. Different presentations/worlds are paired interventions, not new banks.

## Compare the two downloaded bundles locally

After extracting the new archive, run the read-only comparator. Replace the second
path with the actual decode64 report path; each report must retain its sibling
config, manifest, runtime and evaluations files.

```powershell
.\.conda\python.exe scripts\analyze_factorial_report.py --report results\E_results\hibermem-exact-e3_core-qwen-e98cf871877b-20260831T081831Z-73\results\exact_mechanism\e3_core-qwen\run\report.json --compare PATH_TO_DECODE64_RUN\report.json --output results\E_results\e3_decode_comparison.json
```

The comparator validates both bundles and checks input tokens, rendered prompts,
short-output token prefixes, early-stop completion identity and runtime equality.
Its top-level summary describes the short-budget `--report`; paired changes appear
under `decoding_comparison`. Audit the longer report separately to summarize all
of its refitted retention policies.
It records source identity differences. `matched_decode_only_evidence=false` means
other differences or missing real evidence prevent a clean paired interpretation;
it is never a qualification verdict. A matching comparison still evaluates only
development queries. The output must be a new filename: existing audit files are
never overwritten. Do not extract the last DS label or alter the original parser.

For single-report auditing omit `--compare`. The saved core audit is
`results/E_results/e3_core_e98cf871877b_audit_20260831_v2.json` (roundoff-aware sign counts).

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
