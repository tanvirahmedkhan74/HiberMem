# HiberMem

HiberMem is currently a causal memory-interaction study, not a full agent-memory
framework. The repository follows the phase gates in
[`HiberMem_MASTER_RESEARCH_IMPLEMENTATION_PLAN.md`](HiberMem_MASTER_RESEARCH_IMPLEMENTATION_PLAN.md).

Current status: **Phases 0 and 1 passed; the first scientifically eligible
Phase 2 discovery/validation pilot failed its unlock prerequisites. The held-out
test remains locked and Phase 3 is blocked.**

**2026-08-30 update:** the reported Qwen/Phi v1 screens also failed qualification.
The next runnable experiment is the audited, development-only **Phase 2-R v2**
counterfactual screen. Follow
[the current implementation and Kaggle guide](docs/PHASE2R_V2_IMPLEMENTATION_AND_KAGGLE.md).
It uses the dedicated `tanvirahmedkhan74/HiberMem` repository, not the CV project.
Legacy confirmation freezing is retired; a capability-screen pass does not unlock test.

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

The current goal, completed evidence, remaining gates, and cross-project
boundary are summarized in
[`docs/RESEARCH_STATUS_2026-08-29.md`](docs/RESEARCH_STATUS_2026-08-29.md).

## Phase 2

The Phase 2 implementation and locked gate criteria are in
[`docs/PHASE2_IMPLEMENTATION_PLAN.md`](docs/PHASE2_IMPLEMENTATION_PLAN.md). The
full mock protocol has passed as an engineering check, but it is explicitly not
scientific evidence and does not pass Gate P2.

The pinned SmolLM2 backend passed discovery-only qualification on the local RTX
4050. The subsequent scientific pilot failed P2-A interaction stability and
validation task readiness. Gate P2 is undecided because the held-out P2-B test
was correctly left locked. The complete evidence and the next Phase 2-R
model/task-dependence plan are in
[`docs/PHASE2_DISCOVERY_VALIDATION_ANALYSIS.md`](docs/PHASE2_DISCOVERY_VALIDATION_ANALYSIS.md).

The optional local-model runtime was installed and qualified with:

```powershell
python -m pip uninstall -y torch torchvision
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130
python -m pip install -e ".[dev,reference,llm]"
python scripts\check_phase2_backend.py --config configs\experiments\phase2_local_4050.json
```

Do not unlock or test the completed negative pilot. A revised experiment must
use a new version, fresh confirmation banks, a clean Git commit, and the same
predeclared gates. See [`HANDOFF.md`](HANDOFF.md) for the exact current boundary.

The Phase 2-R Kaggle workflow is implemented in
[`docs/PHASE2R_KAGGLE_EXECUTION.md`](docs/PHASE2R_KAGGLE_EXECUTION.md). It first
screens pinned Qwen3-4B-Instruct-2507 and Phi-4-mini-instruct models on fresh
development banks, then freezes a separate fresh-bank confirmation config only
when a candidate qualifies. The supplied `State-Nuisance-Geometry` GitHub URL
is a different video project and must not be used; publish this HiberMem tree to
a dedicated GitHub repository before launching Kaggle.

## Mathematical conventions

The code intentionally keeps these objects separate:

- a context-specific discrete derivative;
- the full-context local interaction;
- a Möbius/Harsanyi coefficient;
- a Shapley Interaction Index (SII) value.

They agree for some small games but are not interchangeable in general.
