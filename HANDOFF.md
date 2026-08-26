# HiberMem Handoff

**Updated:** 2026-08-27  
**Current scientific gate:** P1 passed; P2 not yet evaluated with an LLM  
**Current engineering state:** Phase 2 implemented; mock protocol and local backend qualification passed

## Verified state

The user independently ran the project-local Conda environment and observed:

```text
python -m pytest -q              36 passed
python scripts\run_phase0.py     21 passed; Gate P0 PASS
python scripts\run_phase1.py     Gate P1 PASS
```

The verified Phase 1 artifact is
`results/phase1/20260826T184454.941051Z/report.json`. Its reported metrics agree
with `docs/PHASE1_VALIDATION.md`.

After Phase 2 implementation, the current suite has 48 passing tests and
`pip check` reports no broken requirements. The full mock artifact is
`results/phase2/20260826T195617.239085Z/report.json`; it contains 39,270 cached
evaluations and deliberately records `gate_p2: null`.

The local SmolLM2 backend qualification passed at
`results/phase2_backend_check/20260826T195523.639127Z/report.json` with 1.0
supported parse rate, 1.0 supported accuracy, 0.916667 overall parse rate, and
0.25 missing-link false-positive rate. It used discovery queries only and is not
P2 evidence.

## Plan verification and next gate

Phase 2 is the correct next scientific step because P0 and P1 passed. Phase 3
remains prohibited until a real small instruction model passes both P2-A
(stable interaction ranking) and P2-B (repeatable held-out severe-deletion
advantage).

The implemented Phase 2 protocol satisfies the approved boundary:

- 10 banks, 8 memories each, and 20/10/20 split queries;
- exact 256-coalition enumeration for 2 banks and 128 size-balanced coalitions
  for the remaining 8, reducing discovery inference from 51,200 to 30,720;
- discovery-only interaction fitting and retention-mask construction;
- P2-A discovery stability and validation readiness before a separately
  recorded one-way test unlock;
- all surviving memories supplied directly, with no retrieval system;
- deterministic greedy output capped at 8 tokens and strict option parsing;
- Random, ordinary-Shapley item-value, and interaction-aware policies;
- payload-token and serialized-byte budgets matched exactly across policies;
- bank-level P2 decisions and a paired sign-flip test;
- no graph retrieval, lesion system, RL, regrowth, training, or later-phase
  scaffolding.

The nominal 0.70 and 0.80 deletion points are discrete for eight memories. The
runner keeps 3 and 2 memories respectively and records the actual deletion
ratios (0.625 and 0.75) instead of hiding the rounding.

## Environment hygiene

The pasted prompt showed both `.venv` and `.conda` active. Do not keep both
active. Open a clean shell for future scientific runs, or deactivate `.venv`
before activating the Conda prefix. The verified interpreter is:

```text
D:\Coding\paper\hibermem\.conda\python.exe
Python 3.11.15
```

The detected GPU is an NVIDIA GeForce RTX 4050 Laptop GPU with 6141 MiB VRAM.
The project environment now contains the verified CUDA wheel pair:

```text
torch       2.13.0+cu130
torchvision 0.28.0+cu130
CUDA        13.0
transformers 5.16.1
accelerate   1.14.0
```

PyTorch reports `cuda available: True` and completed a CUDA tensor operation on
the RTX 4050. The pinned reconstruction file is
`configs/requirements/torch-cu130.txt`.

## Blocking prerequisites for the real Phase 2 run

1. The Git repository has no commits yet. The scientific profile intentionally
   refuses to start without a committed revision and clean source/config files.
   Research outputs under `results/` may be uncommitted during a resumable run.
   Review and create the initial commit before discovery.
2. The expected scientific workload is long: 30,720 discovery generations plus
   validation/test retention conditions. Every result is immediately cached,
   so the same command resumes safely.

## Exact next sequence

Run from a fresh PowerShell window:

```powershell
cd D:\Coding\paper\hibermem
conda activate D:\Coding\paper\hibermem\.conda
python -m pytest -q
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO CUDA')"
```

To reconstruct the verified CUDA runtime in a fresh project environment, use:

```powershell
python -m pip uninstall -y torch torchvision
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130
python -m pip install -e ".[dev,reference,llm]"
```

The backend check has passed. Commit the reviewed source and start only the
discovery/validation stage:

```powershell
git status --short
git add -- . ':(exclude)results/**'
git commit -m "Implement gated Phase 2 coalition experiment"
python scripts\run_phase2.py --stage discovery-validation --config configs\experiments\phase2_local_4050.json
```

The exclusion keeps large resumable caches out of the initial source commit;
untracked files under `results/` are expected and do not count as source/config
changes in the scientific preflight.

The command prints the run directory. Review that run's `report.json` and
`validation.json`. If and only if validation reports
`ready_for_test_unlock: true`, continue with that exact directory:

```powershell
python scripts\run_phase2.py --stage unlock --run-dir results\phase2\<RUN_ID>
python scripts\run_phase2.py --stage test --run-dir results\phase2\<RUN_ID>
```

Do not edit the config, dataset, prompt, or source between discovery and test;
the runner checks the config hash, dataset hash, and Git commit.
