# Changelog

All notable research and implementation changes are recorded here. Scientific
gate status is stated separately from engineering smoke-test status.

## 2026-08-27

### CUDA 13.0 runtime selected

- Removed the previously installed unqualified `torch 2.13.0` build from the
  project-local `.conda` environment.
- Installed `torch 2.13.0+cu130` and `torchvision 0.28.0+cu130` from the official
  PyTorch CUDA 13.0 wheel index.
- Verified that PyTorch reports CUDA 13.0, detects the NVIDIA GeForce RTX 4050
  Laptop GPU, and successfully executes a CUDA tensor operation.
- Re-ran all 48 tests and `pip check`; both passed.
- Added `configs/requirements/torch-cu130.txt` to pin the verified wheel pair for
  environment reconstruction.

### Phase 2 local backend qualified

- Downloaded the pinned `HuggingFaceTB/SmolLM2-1.7B-Instruct` revision and
  loaded it successfully on the RTX 4050 in float16.
- Used discovery-only qualification failures to remove an identifier-suffix
  shortcut and make the two-hop lookup procedure explicit. No validation or
  test outcome was accessed during this protocol refinement.
- Bumped the controlled dataset to `phase2-routing-v4` and the locked prompt to
  `phase2-direct-survivors-v3`.
- Replaced the deprecated Transformers `torch_dtype` argument with `dtype`,
  retaining a compatibility fallback for older supported releases.
- Moved qualification thresholds into the scientific configuration. The final
  check passed with supported parse rate 1.0, supported accuracy 1.0, overall
  parse rate 0.916667, and missing-link false-positive rate 0.25.
- Preserved the passing report at
  `results/phase2_backend_check/20260826T195523.639127Z/report.json`.

### Phase 1 independently verified

- Recorded the user-run project-local Conda verification: 36 tests passed,
  Gate P0 passed with 21 phase-specific tests, and Gate P1 passed.
- Recorded the immutable Phase 1 run
  `results/phase1/20260826T184454.941051Z/report.json`.
- Confirmed the Phase 1 gate values: interaction sign accuracy, precision@k,
  recall@k, nonzero Spearman correlation, and true-interaction sign stability
  were 1.0; individual MAE was 0.015359; interaction MAE was 0.016337; null
  false-positive rate was 0.003086; and noisy 95% interval coverage was
  0.938172.
- Added an environment-hygiene warning: do not activate `.conda` on top of the
  already-active `.venv`; use a clean shell or deactivate the virtual
  environment first.

### Phase 2 experiment implemented

- Added a deterministic controlled natural-language environment with ten
  independent banks, eight memories per bank, and locked 20/10/20
  discovery/validation/test query counts.
- Added split-scoped scoring capabilities and automated leakage tests. Test
  queries cannot be passed to the discovery fitting entry point.
- Added backend abstractions for a local Hugging Face model, an
  OpenAI-compatible endpoint, and a deterministic mock oracle.
- Added direct-survivor prompt delivery, strict finite-action parsing, exact and
  size-balanced coalition evaluation, query bootstrap stability, and split-half
  top-k overlap.
- Added Random, Shapley item-value, and exact interaction-aware retention under
  matched payload-token budgets at the preregistered deletion grid.
- Added zero/full-memory normalization, SQLite checkpoint/resume, complete cache
  keys, runtime/model/GPU/source provenance, and a one-way validation-to-test
  unlock.
- Added a pinned RTX 4050 profile using
  `HuggingFaceTB/SmolLM2-1.7B-Instruct` and a discovery-only backend
  qualification script. Model weights and optional LLM dependencies were not
  downloaded automatically.
- Expanded the complete test suite from 36 to 48 passing tests.

### Phase 2 mock protocol validated

- Completed the full protocol-shaped mock run at
  `results/phase2/20260826T195617.239085Z/report.json` with 39,270 cached
  evaluations.
- The harness recovered all four designed pair dependencies, achieved 1.0 mean
  split-half top-4 overlap and 0.9975 mean sign consistency, and produced a
  0.15 mean severe-deletion advantage over item-only retention.
- The run is explicitly marked `scientific_gate_eligible: false` and
  `gate_p2: null`. It validates the experiment machinery, not the HiberMem LLM
  hypothesis.

## 2026-08-26

### Phase 0 and Phase 1

- Implemented and validated the exact coalition-game mathematics required by
  Gate P0.
- Implemented deterministic synthetic low-order Möbius/Harsanyi recovery,
  uncertainty estimates, and recovery metrics for Gate P1.
- Added the project-local Conda environment and immutable Phase 0/Phase 1
  artifacts.
- Documented the pre-implementation theory, leakage, compute, and experimental
  audit in `docs/PRE_IMPLEMENTATION_AUDIT.md`.
