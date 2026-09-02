# E3c and E4 Kaggle execution — fresh notebooks

These experiments are development-only. Exit 0 means the artifact independently
validated; it does not mean qualification, P2/P3 passage, confirmation access, or
historical test unlock.

E3c and E4 require two source revisions. First run E3c from the implementation
commit. Download and review its report locally, freeze a passing contract into an E4
config, commit that config, and then start a second fresh Kaggle notebook from the
new commit. The E4 launcher refuses an engineering placeholder or uncommitted config.

## A. E3c output-contract diagnostic

Enable a GPU and Internet in a fresh Kaggle notebook. Replace the placeholder with
the exact 40-character implementation commit.

The launcher enforces 15 GiB of free working storage, matching the repository's
existing single-Qwen workflow. Exit 2 at an environment/setup stage is infrastructure
failure and contains no model conclusion.

### Cell 1 — immutable run settings

```python
import os
import re

HIBERMEM_REF = "REPLACE_WITH_40_CHARACTER_COMMIT"
assert re.fullmatch(r"[0-9a-f]{40}", HIBERMEM_REF)
os.environ["HIBERMEM_REF"] = HIBERMEM_REF
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
print(HIBERMEM_REF)
```

If the Hugging Face token is stored as a Kaggle secret named `HF_TOKEN`, add:

```python
from kaggle_secrets import UserSecretsClient
os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")
```

### Cell 2 — exact clean checkout

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
```

### Cell 3 — run tests, controls, inference, and validation

```bash
%%bash
set -euo pipefail
cd /kaggle/working/hibermem
bash kaggle/run_e3c_contract.sh
```

The run contains 16,384 conditions: two independent fresh banks, AND2/AND3,
low/high lexical nuisance, base/counterfactual worlds, two queries, 256 coalitions,
and two paired prompt contracts. No contract is automatically selected.

### Cell 4 — inspect readiness without changing the artifact

```python
import json
from pathlib import Path

report_path = Path(
    "/kaggle/working/hibermem/results/e3c_output_contract/qwen/run/report.json"
)
report = json.loads(report_path.read_text())
print(json.dumps({
    "status": report["status"],
    "passing_contracts": report["analysis"]["passing_contracts"],
    "readiness": report["analysis"]["readiness"],
    "automatic_selection": report["analysis"]["automatic_selection"],
    "qualified": report["qualified"],
    "test_access": report["test_access"],
}, indent=2))
```

If `passing_contracts` is empty, stop. Do not weaken thresholds and do not run E4.
If multiple contracts pass, select one explicitly based on the predeclared grounding,
format, cap, and supported-accuracy evidence—not any retention result.

### Cell 5 — download the complete E3c bundle

```python
from glob import glob
from IPython.display import FileLink, display

artifacts = sorted(glob("/kaggle/working/hibermem-e3c-qwen-*.tar.gz"))
assert artifacts
display(FileLink(artifacts[-1]))
```

## B. Freeze the E4 design locally

Extract the E3c archive into the repository's ignored `results/` folder. Use the
actual report and choose a name present in `passing_contracts`:

```powershell
cd D:\Coding\paper\hibermem
conda activate D:\Coding\paper\hibermem\.conda
python scripts\validate_e3c_report.py `
  --report results\e3c_download\results\e3c_output_contract\qwen\run\report.json
python scripts\freeze_e4_protocol.py `
  --contract-report results\e3c_download\results\e3c_output_contract\qwen\run\report.json `
  --contract answer_slot_v1 `
  --template configs\experiments\e4_design_template.json `
  --output configs\experiments\e4_design_qwen_frozen.json
python scripts\run_e4_prospective.py `
  --config configs\experiments\e4_design_qwen_frozen.json `
  --candidate qwen --dry-run
git diff --check
git status --short
```

Review the generated config. It records the E3c report SHA-256, contract prompt hash,
and the same decoding budget used by E3c. Commit and push the implementation plus the
frozen config. Do not edit the frozen config after publication; any change requires a
new name and source revision.

## C. E4 prospective design cohort

Start another fresh Kaggle notebook. Use the new commit that contains the reviewed
frozen config.

### Cell 1 — immutable E4 settings

```python
import os
import re

HIBERMEM_REF = "REPLACE_WITH_NEW_40_CHARACTER_COMMIT"
HIBERMEM_E4_CONFIG = "configs/experiments/e4_design_qwen_frozen.json"
assert re.fullmatch(r"[0-9a-f]{40}", HIBERMEM_REF)
os.environ["HIBERMEM_REF"] = HIBERMEM_REF
os.environ["HIBERMEM_E4_CONFIG"] = HIBERMEM_E4_CONFIG
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
print(HIBERMEM_REF, HIBERMEM_E4_CONFIG)
```

Add the optional `HF_TOKEN` secret cell from E3c if needed.

### Cell 2 — exact clean checkout

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
test -f "${HIBERMEM_E4_CONFIG}"
```

### Cell 3 — run the explicit E4 state machine

```bash
%%bash
set -euo pipefail
cd /kaggle/working/hibermem
bash kaggle/run_e4_prospective.sh
```

The launcher uses separate processes and artifacts for:

```text
past -> validate past -> freeze selections -> future -> validate complete report
```

The default design template has eight independent banks, 16,384 complete-game past
conditions, and approximately 9,000–11,000 deduplicated future/probe conditions. The
exact future count depends only on overlaps among already frozen policy masks; the
prediction probe is fixed at 64 masks before fitting.

Rerunning Cell 3 in the same notebook resumes validated per-condition checkpoints. A
source, runtime, config, model, prompt, future commitment, probe, or selection mismatch
stops the run.

### Cell 4 — inspect development results

```python
import json
from pathlib import Path

run_dir = Path(
    "/kaggle/working/hibermem/results/e4_prospective/qwen-design/run"
)
report = json.loads((run_dir / "report.json").read_text())
analysis = report["analysis"]
print(json.dumps({
    "status": report["status"],
    "independent_base_banks": analysis["independent_base_banks"],
    "primary_bank_differences": analysis["primary_bank_differences"],
    "primary_interval": analysis["primary_interval"],
    "primary_randomization": analysis["primary_randomization"],
    "practical_margin_declared": analysis["practical_margin_declared"],
    "decision": analysis["decision"],
    "qualified": report["qualified"],
    "test_access": report["test_access"],
}, indent=2))
```

`decision` must remain `null`; this is a design cohort, not confirmation. Inspect
per-bank support decomposition, future prediction metrics, strict format, and costs
before defining the variance-only cohort. Do not count queries as independent banks.

### Cell 5 — download the E4 bundle

```python
from glob import glob
from IPython.display import FileLink, display

artifacts = sorted(glob("/kaggle/working/hibermem-e4-qwen-*.tar.gz"))
assert artifacts
display(FileLink(artifacts[-1]))
```

## D. What does not happen automatically

- No historical Phase-2 test query is generated or unlocked.
- No E3c contract is selected automatically.
- No E4 development result authorizes E5.
- No variance or confirmation config is generated from a favorable mean.
- No prompt, threshold, policy, practical margin, or output parser is relaxed after
  viewing E4 future outcomes.
- E5 begins only after a separately reviewed variance/power and confirmation plan.
