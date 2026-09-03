# HiberMem

HiberMem is currently a causal memory-interaction study, not a full agent-memory
framework. The repository follows the phase gates in
[`HiberMem_MASTER_RESEARCH_IMPLEMENTATION_PLAN.md`](HiberMem_MASTER_RESEARCH_IMPLEMENTATION_PLAN.md).

Current status: **Phases 0 and 1 passed. Real E3/E3c diagnostics exposed an
unresolved grounding/output-contract confound; neither E3c contract passed the
frozen readiness criteria. E4 prospective retention, E5 lesions, the historical
test, and Phase 3 therefore remain blocked.**

**2026-09-03 update:** the next scientifically eligible experiment is the
development-only **E3d grounding decomposition** on fresh banks. It must retain
`current_v1` as a paired control, test a label-only query-anchored candidate, and
keep any structured verifier as a diagnostic arm that cannot unlock E4. See the
[E3c findings](docs/E3C_OUTPUT_CONTRACT_RESULTS_2026-09-02.md) and the
[evidence-bounded scientific audit](docs/ICLR_PREPAPER_SCIENTIFIC_AUDIT_2026-09-03.md).
No readiness threshold may be relaxed and banks 350--351 may not be reused for
contract selection.

E3d Stage A is now implemented with its frozen development config, symbolic controls,
resumable evidence runner, independent validator, mock/real separation, verification
freeze gate, and Kaggle launcher. The complete ordered runbook is in
[`docs/EXPERIMENT_EXECUTION_IMPLEMENTATION_PLAN_2026-09-03.md`](docs/EXPERIMENT_EXECUTION_IMPLEMENTATION_PLAN_2026-09-03.md).
This implementation does not authorize real E4 execution.
Use [`docs/E3D_KAGGLE.md`](docs/E3D_KAGGLE.md) for the verified Windows Conda
activation sequence and the copy-paste development/verification Kaggle cells.

```powershell
conda run --prefix .\.conda python scripts\run_e3d_grounding.py --dry-run
conda run --prefix .\.conda python scripts\run_e3d_grounding.py --controls-only
conda run --prefix .\.conda python scripts\run_e3d_grounding.py --candidate mock --run-dir results\e3d_local_verification\run
conda run --prefix .\.conda python scripts\validate_e3d_report.py --report results\e3d_local_verification\run\report.json --allow-mock
```

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
conda run --prefix .\.conda python scripts\run_tests.py -q
conda run --prefix .\.conda python scripts\run_phase0.py
conda run --prefix .\.conda python scripts\run_phase1.py
```

Or activate it first:

```powershell
conda activate D:\Coding\paper\hibermem\.conda
python scripts\run_tests.py -q
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
