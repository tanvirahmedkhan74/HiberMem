# E3d local and Kaggle execution — exact sequential workflow

> **Post-run stop notice (2026-09-03):** real E3d v1 development completed and A1
> failed 16 frozen readiness checks. The artifact independently validates, but the
> verification branch below is not authorized. Do not run the freeze command, create
> the v1 verification config, or execute the verification notebook/cells. They remain
> documented only as the original fail-closed workflow. See
> [E3D_GROUNDING_RESULTS_2026-09-03.md](E3D_GROUNDING_RESULTS_2026-09-03.md).

This is the executable companion to the E3d preregistration. E3d qualifies a
measurement instrument only. It does not test retention, authorize E5, open the
historical Phase-2 test, or establish HiberMem.

The sequence is strict:

```text
local environment -> tests -> dry run -> controls -> mock artifact -> mock validation
-> reviewed clean commit -> Kaggle development -> download -> local validation
-> stop if A1 fails
-> freeze and commit verification config only if A1 passes
-> fresh Kaggle verification -> download -> local validation -> decision
```

## 1. Correct Windows Conda activation

Open a new **PowerShell** window. Do not activate `.venv` and `.conda` together.

```powershell
cd D:\Coding\paper\hibermem

# Load Conda into this PowerShell process when `conda activate` is unavailable.
& "$env:USERPROFILE\anaconda3\shell\condabin\conda-hook.ps1"

conda activate "D:\Coding\paper\hibermem\.conda"

python -c "import sys; print('python=' + sys.executable); print('prefix=' + sys.prefix)"
```

Both printed paths must begin with:

```text
D:\Coding\paper\hibermem\.conda
```

If the hook is installed elsewhere, initialize PowerShell once and open a new shell:

```powershell
conda init powershell
```

The activation-free equivalent is also valid:

```powershell
conda run --prefix D:\Coding\paper\hibermem\.conda python -c "import sys; print(sys.executable)"
```

## 2. Correct test command for this Windows machine

Do **not** use `python -m pytest -q` here. The pasted failure came from pytest trying
to enumerate `C:\Users\tanvi\AppData\Local\Temp\pytest-of-tanvi`, which Windows
denied. Use the repository wrapper; it creates a unique workspace-owned scratch
directory and invokes pytest with the active interpreter.

```powershell
python scripts\run_tests.py -q
```

Expected preamble:

```text
Test interpreter: D:\Coding\paper\hibermem\.conda\python.exe
Test scratch directory: D:\Coding\paper\hibermem\results\pytest-runs\run-...
```

The verified current result is `208 passed`.

## 3. Local E3d Stage-A sequence

Run each command only after the preceding command succeeds.

### Step 3.1 — test and inspect the frozen design

```powershell
python scripts\run_tests.py -q
python scripts\run_e3d_grounding.py --dry-run
python scripts\run_e3d_grounding.py --controls-only
```

The dry run must report:

- stage `development`;
- banks 360 and 361;
- 1,728 planned conditions;
- 288 conditions per bank and arm;
- A0, A1, and A2;
- `model_loaded: false`.

The controls must report `passed: true`, payload matching, parser round trips, zero
future queries, and no historical-test access.

### Step 3.2 — reproduce the engineering-only mock artifact

Use a new run directory if an existing one was created by different source.

```powershell
python scripts\run_e3d_grounding.py `
  --candidate mock `
  --run-dir results\e3d_local_verification\run

python scripts\validate_e3d_report.py `
  --report results\e3d_local_verification\run\report.json `
  --allow-mock
```

Exit 0 means the artifact machinery validated. A mock A1 readiness pass is not a
reader result and does not create a verification configuration.

### Step 3.3 — verify the fail-closed mock boundary

This command is expected to exit 2 and create no output:

```powershell
python scripts\freeze_e3d_verification.py `
  --development-report results\e3d_local_verification\run\report.json `
  --output configs\experiments\e3d_grounding_verification.json
```

### Step 3.4 — source review before any real inference

```powershell
git diff --check
git status --short
```

Do not use `git add -A`: the checkout also contains external critique folders, a zip,
paper outputs, and other user artifacts. Review and selectively commit the experiment
source, config, tests, launcher, and governing documents. A real run deliberately
stops before model loading when source is dirty.

After the reviewed commit is pushed, record the exact full revision:

```powershell
git push origin HEAD
git rev-parse HEAD
```

Use that exact 40-character revision in Kaggle. A fresh Kaggle checkout avoids the
untracked local research artifacts while preserving their local copies.

## 4. Kaggle notebook A — real E3d development

Create a **fresh Kaggle notebook**, enable Internet, and select one GPU. Do not reuse
an old checkout or old result directory.

### Cell A1 — immutable settings

```python
import os
import re

HIBERMEM_REF = "REPLACE_WITH_REVIEWED_40_CHARACTER_COMMIT"
HIBERMEM_CONFIG = "configs/experiments/e3d_grounding_development.json"

assert re.fullmatch(r"[0-9a-f]{40}", HIBERMEM_REF)
os.environ["HIBERMEM_REF"] = HIBERMEM_REF
os.environ["HIBERMEM_E3D_CONFIG"] = HIBERMEM_CONFIG
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
print(HIBERMEM_REF, HIBERMEM_CONFIG)
```

If Hugging Face authentication is required and the Kaggle secret is named
`HF_TOKEN`, run this additional cell:

```python
import os
from kaggle_secrets import UserSecretsClient

os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")
```

### Cell A2 — exact clean checkout

```bash
%%bash
set -euo pipefail
test ! -e /kaggle/working/hibermem
git clone --filter=blob:none --no-checkout \
  https://github.com/tanvirahmedkhan74/HiberMem.git \
  /kaggle/working/hibermem
cd /kaggle/working/hibermem
git fetch --depth 1 origin "${HIBERMEM_REF}"
git checkout --detach FETCH_HEAD
test "$(git rev-parse HEAD)" = "${HIBERMEM_REF}"
test -z "$(git status --porcelain --untracked-files=all)"
test -f "${HIBERMEM_E3D_CONFIG}"
```

### Cell A3 — tests, controls, development inference, and validation

```bash
%%bash
set -euo pipefail
cd /kaggle/working/hibermem
bash kaggle/run_e3d_grounding.sh
```

The launcher preserves Kaggle's CUDA Torch, installs the pinned project dependencies,
runs the full suite through the workspace-owned test scratch wrapper, runs symbolic
controls, executes all 1,728 real Qwen conditions, independently validates the
artifact, and creates a resumable archive.

If Cell A3 is interrupted, rerun it only in the same notebook with identical source,
config, model, and runtime. Checkpoints are validated before reuse.

### Cell A4 — inspect the preregistered A1 decision

```python
import json
from pathlib import Path

report_path = Path(
    "/kaggle/working/hibermem/results/e3d_grounding/development/qwen/run/report.json"
)
report = json.loads(report_path.read_text())
a1 = report["analysis"]["readiness"]["query_anchored_v1"]

print(json.dumps({
    "status": report["status"],
    "engineering_only": report["engineering_only"],
    "planned_conditions": report["planned_conditions"],
    "generation_calls_this_attempt": report["generation_calls_this_attempt"],
    "a1_passed": a1["passed"],
    "a1_failed_checks": a1["failed_checks"],
    "automatic_selection": report["analysis"]["automatic_selection"],
    "historical_test_access": report["historical_test_access"],
}, indent=2))

assert report["status"] == "complete"
assert report["engineering_only"] is False
assert report["historical_test_access"] is False
```

If `a1_passed` is false, stop. Preserve the archive; do not alter prompts or
thresholds, do not run verification, and do not substitute A2.

### Cell A5 — download the complete development archive

```python
from pathlib import Path
from IPython.display import FileLink, display

archives = sorted(
    Path("/kaggle/working").glob("hibermem-e3d-development-qwen-*.tar.gz")
)
assert archives, "No archive found; preserve the results/e3d_grounding directory."
display(FileLink(str(archives[-1])))
```

## 5. Local development validation and conditional freeze

Download the archive without modifying it. Extract it into a new directory:

```powershell
cd D:\Coding\paper\hibermem
& "$env:USERPROFILE\anaconda3\shell\condabin\conda-hook.ps1"
conda activate "D:\Coding\paper\hibermem\.conda"

New-Item -ItemType Directory -Force results\e3d_download | Out-Null
tar -xzf "C:\PATH\TO\hibermem-e3d-development-qwen-....tar.gz" `
  -C results\e3d_download

$devReport = "results\e3d_download\results\e3d_grounding\development\qwen\run\report.json"
python scripts\validate_e3d_report.py --report $devReport
```

Inspect A1 without changing the artifact:

```powershell
python -c "import json,sys; r=json.load(open(sys.argv[1])); a=r['analysis']['readiness']['query_anchored_v1']; print(json.dumps({'passed':a['passed'],'failed_checks':a['failed_checks']},indent=2))" $devReport
```

Only when `passed` is `true`, create the verification config:

```powershell
python scripts\freeze_e3d_verification.py `
  --development-report $devReport `
  --output configs\experiments\e3d_grounding_verification.json

python scripts\run_e3d_grounding.py `
  --config configs\experiments\e3d_grounding_verification.json `
  --development-report $devReport `
  --dry-run

git diff --check
git status --short
```

Review, commit, and push the generated config. Use the new 40-character commit for
verification. Do not edit the generated JSON after freezing it.

## 6. Kaggle notebook B — one real E3d verification run

Start a second **fresh** GPU notebook. Upload the unchanged development `.tar.gz` as
a private Kaggle Dataset/input. The verification config must already be committed.

### Cell B1 — immutable settings and development artifact discovery

```python
import os
import re
from pathlib import Path

HIBERMEM_REF = "REPLACE_WITH_COMMIT_CONTAINING_VERIFICATION_CONFIG"
HIBERMEM_CONFIG = "configs/experiments/e3d_grounding_verification.json"
archives = sorted(
    Path("/kaggle/input").rglob("hibermem-e3d-development-qwen-*.tar.gz")
)

assert re.fullmatch(r"[0-9a-f]{40}", HIBERMEM_REF)
assert len(archives) == 1, f"Expected one development archive, found {archives}"
os.environ["HIBERMEM_REF"] = HIBERMEM_REF
os.environ["HIBERMEM_E3D_CONFIG"] = HIBERMEM_CONFIG
os.environ["HIBERMEM_E3D_DEVELOPMENT_ARCHIVE"] = str(archives[0])
os.environ["HIBERMEM_E3D_DEVELOPMENT_REPORT"] = (
    "results/e3d_grounding/development/qwen/run/report.json"
)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
print(HIBERMEM_REF, archives[0])
```

Run the optional `HF_TOKEN` cell from notebook A if needed.

### Cell B2 — exact clean checkout and development-artifact extraction

```bash
%%bash
set -euo pipefail
test ! -e /kaggle/working/hibermem
git clone --filter=blob:none --no-checkout \
  https://github.com/tanvirahmedkhan74/HiberMem.git \
  /kaggle/working/hibermem
cd /kaggle/working/hibermem
git fetch --depth 1 origin "${HIBERMEM_REF}"
git checkout --detach FETCH_HEAD
test "$(git rev-parse HEAD)" = "${HIBERMEM_REF}"
test -z "$(git status --porcelain --untracked-files=all)"
test -f "${HIBERMEM_E3D_CONFIG}"
tar -xzf "${HIBERMEM_E3D_DEVELOPMENT_ARCHIVE}" -C /kaggle/working/hibermem
test -f "${HIBERMEM_E3D_DEVELOPMENT_REPORT}"
```

The extracted files live under ignored `results/`, so the source checkout remains
clean.

### Cell B3 — tests, controls, verification inference, and dual-artifact validation

```bash
%%bash
set -euo pipefail
cd /kaggle/working/hibermem
bash kaggle/run_e3d_grounding.sh
```

The runner checks that the supplied development report is real, complete, A1-passing,
and byte-for-byte bound to the committed verification config before loading Qwen. It
then runs exactly 2,304 conditions: four fresh banks × two arms × 288.

### Cell B4 — inspect verification without claiming E4 success

```python
import json
from pathlib import Path

report_path = Path(
    "/kaggle/working/hibermem/results/e3d_grounding/verification/qwen/run/report.json"
)
report = json.loads(report_path.read_text())
a1 = report["analysis"]["readiness"]["query_anchored_v1"]

print(json.dumps({
    "status": report["status"],
    "engineering_only": report["engineering_only"],
    "independent_base_banks": report["analysis"]["independent_base_banks"],
    "a1_passed": a1["passed"],
    "a1_failed_checks": a1["failed_checks"],
    "automatic_selection": report["analysis"]["automatic_selection"],
    "historical_test_access": report["historical_test_access"],
}, indent=2))

assert report["status"] == "complete"
assert report["engineering_only"] is False
assert report["historical_test_access"] is False
```

If A1 fails any check, stop E4 for this reader/task pair. If it passes, preserve both
artifacts and perform a separate review before implementing the E3d-to-E4 design
freeze. E4 is not launched by this notebook.

### Cell B5 — download the combined development and verification archive

```python
from pathlib import Path
from IPython.display import FileLink, display

archives = sorted(
    Path("/kaggle/working").glob("hibermem-e3d-verification-qwen-*.tar.gz")
)
assert archives, "No archive found; preserve the results/e3d_grounding directory."
display(FileLink(str(archives[-1])))
```

## 7. Exit meanings and mandatory stop rules

- Exit 0: the requested stage completed and its artifact independently validated.
  It is not a retention or publication result.
- Exit 2 before a complete report: setup, test, identity, runtime, or validation
  failure. It is not a negative model result.
- A complete development report with A1 failure: valid negative development evidence;
  no verification.
- A complete verification report with A1 failure: valid measurement failure; no E4.
- A2-only success: consider a separately named hybrid-system study; it cannot qualify
  the label-only interface.
- Never relax thresholds, reuse banks, edit downloaded artifacts, or pool development
  and verification rows.
