# HiberMem

HiberMem is currently a causal memory-interaction study, not a full agent-memory
framework. The repository follows the phase gates in
[`HiberMem_MASTER_RESEARCH_IMPLEMENTATION_PLAN.md`](HiberMem_MASTER_RESEARCH_IMPLEMENTATION_PLAN.md).

Current status: **Phase 1 passed; Phase 2 is implemented and awaiting the real-model run**.

The independent pre-implementation review is in
[`docs/PRE_IMPLEMENTATION_AUDIT.md`](docs/PRE_IMPLEMENTATION_AUDIT.md). It approves
Phase 0 with explicit amendments and leaves every later phase gated.

## Conda environment

```powershell
cd D:\Coding\paper\hibermem
conda create --prefix .\.conda python=3.11 pip -y
conda run --prefix .\.conda python -m pip install -e ".[dev,reference]"
```

Run without activating the environment:

```powershell
conda run --prefix .\.conda python -m pytest -q
conda run --prefix .\.conda python scripts\run_phase0.py
conda run --prefix .\.conda python scripts\run_phase1.py
```

Or activate it first:

```powershell
conda activate D:\Coding\paper\hibermem\.conda
python -m pytest -q
python scripts\run_phase1.py
```

Do not activate `.conda` on top of `.venv`. Use a fresh shell, or deactivate the
virtual environment first, so `python` and installed packages come from one
environment only.

If PowerShell has not been initialized for Conda, run `conda init powershell`
once and open a new terminal, or keep using the activation-free `conda run`
commands above.

The Phase 0 runner writes `results/phase0_report.json`. The Phase 1 runner
preserves each run under `results/phase1/<run-id>/` and updates
`results/phase1_report.json` as the latest report. Neither phase uses an LLM or
GPU.

The Phase 1 protocol and interpretation are recorded in
[`docs/PHASE1_VALIDATION.md`](docs/PHASE1_VALIDATION.md).

## Phase 2

The Phase 2 implementation and locked gate criteria are in
[`docs/PHASE2_IMPLEMENTATION_PLAN.md`](docs/PHASE2_IMPLEMENTATION_PLAN.md). The
full mock protocol has passed as an engineering check, but it is explicitly not
scientific evidence and does not pass Gate P2.

The pinned SmolLM2 backend has also passed the discovery-only qualification on
the local RTX 4050. The next scientific action is the separately gated
discovery/validation run after committing the frozen source revision.

Install the optional local-model runtime and qualify the model on discovery-only
prompts before the long run:

```powershell
python -m pip uninstall -y torch torchvision
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130
python -m pip install -e ".[dev,reference,llm]"
python scripts\check_phase2_backend.py --config configs\experiments\phase2_local_4050.json
python scripts\run_phase2.py --stage discovery-validation --config configs\experiments\phase2_local_4050.json
```

The scientific profile requires a clean Git commit. Test remains inaccessible
until validation passes and an explicit unlock is recorded. See
[`HANDOFF.md`](HANDOFF.md) for the exact continuation commands.

## Mathematical conventions

The code intentionally keeps these objects separate:

- a context-specific discrete derivative;
- the full-context local interaction;
- a Möbius/Harsanyi coefficient;
- a Shapley Interaction Index (SII) value.

They agree for some small games but are not interchangeable in general.
