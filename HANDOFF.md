# HiberMem research handoff

**Updated:** 2026-09-03

**Repository:** `D:\Coding\paper\hibermem`

**Latest real-evidence commit:** `90ef285bae7f866cc416c1cfb24da75cc1b0ee5e`

**Current code state:** experiment source at the evidence commit; documentation updates
listed below are not yet committed

## 0. Fresh-conversation bootstrap

Read these first, in order:

1. [This handoff](HANDOFF.md) for current state, paths, and restrictions.
2. [Latest E3c findings](docs/E3C_OUTPUT_CONTRACT_RESULTS_2026-09-02.md) for the
   evidence that determines the next action.
3. [Master research plan](HiberMem_MASTER_RESEARCH_IMPLEMENTATION_PLAN.md) for the
   hypotheses, estimands, gates, and stop rules.
4. [E4 prospective plan](docs/E4_PROSPECTIVE_IMPLEMENTATION_PLAN_2026-09-02.md) for
   the implemented but currently blocked past/freeze/future design.
5. [Adversarial audit](docs/ADVERSARIAL_RESEARCH_AUDIT_2026-08-31.md) for the main
   mathematical, leakage, baseline, and claim-validity constraints.

The current decision is **STOP before E4**. Real E3c completed, but neither output
contract passed the frozen capability/grounding criteria. The next permitted
experiment is a separately versioned, fresh-bank **E3d grounding decomposition**.

A useful opening request for a new conversation is:

```text
Read HANDOFF.md and the documents in its fresh-conversation bootstrap. Audit the
current Git state and independently verify the cited E3c artifact. Then implement
only the planned E3d grounding decomposition on fresh development/verification
banks. Do not run or unlock E4, E5, confirmation, or historical test data unless a
label-only contract passes every predeclared E3d verification criterion.
```

## 1. Current scientific state

| Stage | Status | Meaning |
|---|---|---|
| P0 mathematics | PASS | Exact interaction definitions and identities validated. |
| P1 synthetic recovery | PASS | Estimators recover controlled synthetic effects. This validates methodology, not HiberMem. |
| Historical Phase-2 pilot | NEGATIVE | SmolLM2 stability/readiness failed; test stayed locked. |
| Phase-2R Qwen/Phi/Gemma screens | NEGATIVE development evidence | No candidate qualified for confirmation/test. |
| E1 exact game | COMPLETE development evidence | Qwen expresses local pair complementarity; no prospective result. |
| E2 presentation sensitivity | COMPLETE development evidence | Behavior changes under record/option reordering. |
| E3 factorial core | COMPLETE development evidence | Interaction signs appear, but 16-token decoding confounded chains. |
| E3 decode64 | COMPLETE development evidence | Longer decoding recovered chain performance but not clean output/grounding. |
| E3c output contract | **NEGATIVE readiness screen** | Both contracts failed; no contract can be frozen. |
| E4 prospective retention | IMPLEMENTED, BLOCKED | Mock-valid code exists; real execution is prohibited after E3c failure. |
| E5 matched lesions / P3 | BLOCKED | Requires valid prospective evidence first. |
| E6 natural-memory/scale | BLOCKED | Requires prior controlled evidence. |
| Historical test | LOCKED | No valid unlock occurred. |

Gate P2 remains undecided because no compatible confirmation/test was reached. Do not
describe E1–E3c as a P2 pass or failure: they are development diagnostics. No
past-to-future interaction stability, future-query retention advantage, or causal
lesion effect has yet been measured.

## 2. Headline findings

### P0/P1

- Phase 0 passed its 21 phase-specific tests.
- Phase 1 passed with interaction sign accuracy, precision@k, recall@k, nonzero
  Spearman, and sign stability equal to 1.0.
- Phase-1 item MAE was .015359, interaction MAE .016337, null false-positive rate
  .003086, and noisy interval coverage .938172.

### Historical Phase-2 and Phase-2R

- SmolLM2 P2-A split-half top-4 overlap was .55 versus .75 required. Full-memory
  validation accuracy was .58, two-hop accuracy .5125, and 0/10 banks passed.
- Its interaction-aware versus item-policy severe-deletion advantage was only .01
  with the previously reported interval spanning zero.
- Qwen and Phi Phase-2R v2 artifacts independently validate as negative screens.
- The supplied Gemma summary is also negative: strong supported/full behavior but
  missing-pair abstention only .504167. Its raw bundle is not locally validated.

### E1/E2/E3

- E1 Qwen has strong local complementarity but quadratic and exact-Shapley severe-
  deletion accuracy are tied on average at .25. This is not a baseline victory.
- E2 full accuracy falls from 1.0 to .75 when records are reversed, establishing
  presentation sensitivity.
- E3 decode64 raises AND2/AND3 supported accuracy from .5049/.1621 to approximately
  .959/.973 and full accuracy from .375/0 to 1/.9375.
- All 885 decode64 recoveries are non-strict and 852 still hit the 64-token cap.
  The run demonstrates parser-scored chain access, not a clean response contract.

### Latest result: E3c Qwen

The real `phase2r-output-contract-v1` run used fresh banks 350–351, two paired
contracts, AND2/AND3, low/high lexical nuisance, base/counterfactual worlds, two
queries, and all 256 coalitions: 16,384 conditions with zero checkpoint reuse.

| Frozen readiness check | Required | `current_v1` | `answer_slot_v1` |
|---|---:|---:|---:|
| AND2 supported accuracy | >= .95 | .917969 — fail | .843750 — fail |
| AND3 supported accuracy | >= .95 | .935547 — fail | .880859 — fail |
| AND2 unsupported assertion | <= .05 | .243815 — fail | .331380 — fail |
| AND3 unsupported assertion | <= .05 | .220145 — fail | .433594 — fail |
| Global strict format | >= .95 | .776001 — fail | .997070 — pass |
| Global generation-limit rate | <= .05 | .187012 — fail | .000366 — pass |

`passing_contracts` is empty. The answer-slot intervention fixes formatting and cap
behavior but loses 104 net supported answers and adds 1,034 unsupported assertions.
Its unsupported-assertion rate increases as incomplete coalitions approach full size,
reaching .50 for AND2 and .667 for AND3 at cardinality seven. The primary problems
are partial-evidence completion, query/competing-path binding, and counterfactual
tracking—not merely decoding length.

The independent E3c validator passes. The E4 freeze tool rejects the result with exit
2 and creates no file. Thresholds may not be relaxed and banks 350–351 may not be
reused to select a repair.

## 3. Research document index

### Current authority and latest decisions

| Document | Purpose and status |
|---|---|
| [HANDOFF.md](HANDOFF.md) | Entry point for a new conversation: current decision, evidence/code map, and immediate plan. |
| [HiberMem_MASTER_RESEARCH_IMPLEMENTATION_PLAN.md](HiberMem_MASTER_RESEARCH_IMPLEMENTATION_PLAN.md) | Normative research specification: hypotheses H1–H3, mathematics, gates, leakage rules, baselines, phases, and falsification tree. |
| [CHANGELOG.md](CHANGELOG.md) | Chronological record of implementation, experiments, repairs, and gate-preserving decisions. |
| [README.md](README.md) | Package overview, installation, and basic project usage. It is not the authoritative research decision log. |
| [docs/E3C_OUTPUT_CONTRACT_RESULTS_2026-09-02.md](docs/E3C_OUTPUT_CONTRACT_RESULTS_2026-09-02.md) | Latest authoritative empirical finding: validated negative E3c screen, detailed failure decomposition, and proposed E3d design. |
| [docs/E4_PROSPECTIVE_IMPLEMENTATION_PLAN_2026-09-02.md](docs/E4_PROSPECTIVE_IMPLEMENTATION_PLAN_2026-09-02.md) | Leakage-safe E4 estimands, cohorts, baselines, cost matching, uncertainty, state machine, and code plan. Implemented in mock form but blocked by E3c. |
| [docs/ADVERSARIAL_RESEARCH_AUDIT_2026-08-31.md](docs/ADVERSARIAL_RESEARCH_AUDIT_2026-08-31.md) | Critical audit of interaction definitions, higher-order confounding, submodularity claims, leakage, baselines, statistical units, and necessary experiments. |

### Phase and experiment findings

| Document | Purpose and status |
|---|---|
| [docs/PRE_IMPLEMENTATION_AUDIT.md](docs/PRE_IMPLEMENTATION_AUDIT.md) | Initial theory/novelty/experimental/compute audit; approved Phase 0 with required amendments. Historical foundation. |
| [docs/PHASE1_VALIDATION.md](docs/PHASE1_VALIDATION.md) | Preregistered synthetic-recovery protocol, thresholds, observed P1 metrics, and gate interpretation. |
| [docs/PHASE2_DISCOVERY_VALIDATION_ANALYSIS.md](docs/PHASE2_DISCOVERY_VALIDATION_ANALYSIS.md) | Full analysis of the negative SmolLM2 discovery/validation pilot and why the historical test stayed locked. |
| [docs/PHASE2R_KAGGLE_SCREENING_RESULTS_2026-08-29.md](docs/PHASE2R_KAGGLE_SCREENING_RESULTS_2026-08-29.md) | Authoritative Qwen/Phi v1/v2 screen results and Gemma summary interpretation; all are development-negative. |
| [docs/E3_CORE_RESULTS_AND_NEXT_STEP_2026-08-31.md](docs/E3_CORE_RESULTS_AND_NEXT_STEP_2026-08-31.md) | Real E3 core findings: family behavior, output-length confound, retention cautions, and decision to run matched decode64. |
| [docs/E3_REVISED_IMPLEMENTATION_PLAN_2026-08-31.md](docs/E3_REVISED_IMPLEMENTATION_PLAN_2026-08-31.md) | Revised E3 factorial theory, support antichains, counterfactual/lexical controls, exact estimands, and later roadmap. Partly superseded by real E3/E3c findings. |
| [docs/NEXT_EXPERIMENT_IMPLEMENTATION_PLAN_2026-08-31.md](docs/NEXT_EXPERIMENT_IMPLEMENTATION_PLAN_2026-08-31.md) | E0–E6 experiment matrix and original implementation tranche. Use as historical sequencing context; later E3c/E4 decisions take precedence. |
| [docs/RESEARCH_STATUS_2026-08-29.md](docs/RESEARCH_STATUS_2026-08-29.md) | Historical status snapshot before E1–E3c. Useful for chronology, not current decisions. |

### Execution and recovery guides

| Document | Purpose and status |
|---|---|
| [docs/EXACT_MECHANISM_KAGGLE.md](docs/EXACT_MECHANISM_KAGGLE.md) | Local/Kaggle commands for E0, E1, and E2 plus result-reading guidance. Historical execution guide. |
| [docs/E3_KAGGLE.md](docs/E3_KAGGLE.md) | Matched E3 decode64 Kaggle cells, bundle comparison, and recovery instructions. Presentation follow-up remains on hold. |
| [docs/E4_KAGGLE.md](docs/E4_KAGGLE.md) | Fresh-notebook cells for E3c and conditional E4 execution. E3c section has run; E4 cells must not run because no contract passed. |
| [docs/PHASE2_IMPLEMENTATION_PLAN.md](docs/PHASE2_IMPLEMENTATION_PLAN.md) | Original controlled Phase-2 backend/discovery/validation/unlock design. Historical; later validity repairs supersede it. |
| [docs/PHASE2R_KAGGLE_EXECUTION.md](docs/PHASE2R_KAGGLE_EXECUTION.md) | Original Phase-2R screening/confirmation and publication workflow. Historical. |
| [docs/PHASE2R_V2_IMPLEMENTATION_AND_KAGGLE.md](docs/PHASE2R_V2_IMPLEMENTATION_AND_KAGGLE.md) | Phase-2R v2 safeguards plus Kaggle setup/test recovery history, including pip-less environment handling. |

When documents disagree, use this priority: master plan and frozen protocol rules;
latest validated findings; this handoff; then older plans/guides. Historical documents
must not be read as authorization to bypass a newer stop decision.

## 4. Evidence, reports, and logs

The `results/` tree is intentionally ignored by Git. Preserve it; never edit original
reports or raw evidence. Generated variants, presentations, queries, and coalitions
are repeated measurements, not independent replications.

### Canonical evidence locations

| Evidence | Canonical local location | Finding |
|---|---|---|
| Phase 0 | `results/phase0_report.json` | P0 passed. |
| Phase 1 | `results/phase1/20260826T184454.941051Z/report.json` and `results/phase1_report.json` | P1 passed. |
| SmolLM2 Phase-2 pilot | `results/phase2/20260826T195924.594962Z/report.json` | Negative pilot; test locked. |
| Qualified local backend check | `results/phase2_backend_check/20260826T195523.639127Z/report.json` | Backend engineering check passed before the negative pilot. |
| Qwen Phase-2R v2 | `results/hibermem-v2-qwen-8991ba49e14f-artifacts/results/phase2r_v2/qwen/report.json` | Independently validated negative screen. |
| Phi Phase-2R v2 | `results/hibermem-v2-phi-8991ba49e14f-artifacts/results/phase2r_v2/phi/report.json` | Independently validated negative screen. |
| Convenience Qwen/Phi copies | `results/report.json`, `results/report_phi.json` | Copies for inspection; canonical bundles above contain full lineage. |
| E1 Qwen | `results/hibermem-exact-e1-qwen-aa97b3aa9b93-20260831T040814Z-118/results/exact_mechanism/e1-qwen/run/report.json` | Local complementarity; no severe-budget mean advantage over exact Shapley. |
| E2 Qwen | `results/hibermem-exact-e2-qwen-aa97b3aa9b93-20260831T042831Z-168/results/exact_mechanism/e2-qwen/run/report.json` | Presentation sensitivity. |
| E3 core Qwen | `results/E_results/hibermem-exact-e3_core-qwen-e98cf871877b-20260831T081831Z-73/results/exact_mechanism/e3_core-qwen/run/report.json` | Real 16-token factorial core. |
| E3 core audit | `results/E_results/e3_core_e98cf871877b_audit_20260831_v2.json` | Read-only corrected audit; preferred over the earlier non-roundoff-aware audit. |
| E3 decode64 Qwen | `results/hibermem-exact-e3_decode64-qwen-518c28d5b441-20260831T124653Z-74/results/exact_mechanism/e3_decode64-qwen/run/report.json` | Real matched longer-decoding result. |
| E3c Qwen | `results/hibermem-e3c-qwen-90ef285bae7f-20260902T054005Z-75/results/e3c_output_contract/qwen/run/report.json` | Latest real result; complete, validated, no passing contract. |
| E3c mock verification | `results/e3c_local_verification/run/report.json` | Engineering-only full mock artifact. |
| E4 mock verification | `results/e4_local_verification/run/report.json` | Engineering-only past/freeze/future validation; not model evidence. |

`results/E_results/` also contains consolidated copies of E1/E2 and the E3 core. Do
not count duplicate copies as additional runs. The supplied Gemma aggregate is
recorded in the screening-results document; no independently validated raw Gemma
bundle is currently present.

### Bundle log convention

For the exact-mechanism and E3c Kaggle bundles, inspect files in this order:

| File | Purpose |
|---|---|
| `launcher-status.json` | Stage, raw exit, normalized outcome, and explicit non-qualification/test capability. |
| `environment.json` | Git commit, Python/packages, CUDA devices/runtime, and free-storage check. |
| `tests.log` / `tests.xml` | Test interpreter, scratch directory, pass/fail output, and JUnit record. |
| `controls.log` and `run/controls.json` | Symbolic grammar/support checks; never model qualification. |
| `run/identity.json` | Candidate, pinned model revision, protocol/config/prompt/source hashes. |
| `run/runtime.json` | Resolved model class/device/dtype, tokenizer/chat template, packages, and GPU. |
| `run/manifest.json` | Immutable planned banks, queries, variants, and condition commitments. |
| `run/report.json` | Independently reconstructable aggregate result and decision capabilities. |
| `run/evaluations.json` | Complete row-level evidence. Large; analyze read-only. |
| `run/conditions/*.json` | Resumable per-condition checkpoints and raw token traces. Never edit or merge manually. |
| `run.log` | Progress and runner messages. It is supporting evidence, not the decision source. |

The `f137b55f72f3` and `349b2a132412` E3c attempts stopped at the old 30 GiB
environment check before tests/controls/inference. They are infrastructure logs only.
The real `90ef285` run used the committed 15 GiB floor, had 18.92 GiB free, ran 197
tests, completed 16,384 calls, and exited 0 after independent validation.

## 5. Code map

### Mathematical and game core

| Path | Purpose |
|---|---|
| `src/hibermem/memory/types.py` | Immutable memory-item representation and storage metadata. |
| `src/hibermem/coalition/masks.py` | Coalition masks, indices, iteration, and conversions. |
| `src/hibermem/coalition/game.py` | Utility-game abstractions and evaluation. |
| `src/hibermem/coalition/cache.py` | Deterministic coalition cache and fingerprints. |
| `src/hibermem/coalition/sampling.py` | Coalition sampling utilities for non-exhaustive settings. |
| `src/hibermem/interactions/discrete.py` | Discrete derivatives and local interaction quantities. |
| `src/hibermem/interactions/mobius.py` | Exact Mobius transform and reconstruction. |
| `src/hibermem/interactions/shapley.py` | Exact Shapley item values and Shapley Interaction Index. |
| `src/hibermem/interactions/polynomial.py` | Additive/quadratic/cubic surrogate fitting. |
| `src/hibermem/interactions/stability.py` | Residual-bootstrap/sign/rank stability utilities. |
| `src/hibermem/retention/policies.py` | Item-value, interaction-aware, and random retention selection. |
| `src/hibermem/retention/costs.py` | Equal payload/token cost audits and retained-cost accounting. |

### Backends and controlled environments

| Path | Purpose |
|---|---|
| `src/hibermem/backends/base.py` | Backend interface. |
| `src/hibermem/backends/hf_local.py` | Pinned Hugging Face local inference and raw generation provenance. |
| `src/hibermem/backends/mock.py` | Deterministic engineering backend; never scientific evidence. |
| `src/hibermem/backends/openai_compatible.py` | OpenAI-compatible backend adapter. |
| `src/hibermem/environments/synthetic/` | Synthetic polynomial games used in P0/P1. |
| `src/hibermem/environments/controlled/dataset.py` | Split-scoped queries, banks, answer capabilities, and leakage boundaries. |
| `src/hibermem/environments/controlled/calibration.py` | Phase-2 calibration/readiness datasets. |
| `src/hibermem/environments/controlled/prompts.py` | Historical controlled routing prompts. |
| `src/hibermem/environments/controlled/mechanism.py` | E1/E2 exact-mechanism construction. |
| `src/hibermem/environments/controlled/factorial.py` | E3 direct/AND2/OR2/AND3 factorial banks, support antichains, and controls. |
| `src/hibermem/environments/controlled/contract.py` | E3c paired output-contract rendering and symbolic controls. |
| `src/hibermem/environments/controlled/prospective.py` | E4 fresh past/future banks, commitments, and distinct query capabilities. |

### Evaluation and experiment orchestration

| Path | Purpose |
|---|---|
| `src/hibermem/evaluation/scoring.py` | Allowed-label parsing and original correctness scoring. |
| `src/hibermem/evaluation/qualification.py` | Historical Phase-2 readiness/gate checks. |
| `src/hibermem/evaluation/survival.py` | Deletion survival and normalized retention metrics. |
| `src/hibermem/evaluation/predictive.py` | Prediction metrics, paired bank intervals, and uncertainty. |
| `src/hibermem/evaluation/recovery.py` | Matched decode-budget recovery analysis. |
| `src/hibermem/evaluation/mechanism.py` | E1/E2 exact-game and policy analysis. |
| `src/hibermem/evaluation/factorial.py` | E3 factorial interaction/retention summaries. |
| `src/hibermem/evaluation/factorial_audit.py` | Independent E3 validation and matched-report comparison. |
| `src/hibermem/evaluation/contract.py` | E3c readiness aggregation and paired contract changes. |
| `src/hibermem/evaluation/prospective.py` | Past-only E4 fitting, frozen policies, future metrics, and bank inference. |
| `src/hibermem/evaluation/artifacts.py` | Shared artifact helpers. |
| `src/hibermem/experiments/phase2.py` | Historical Phase-2 state machine, provenance, caching, and unlock protection. |
| `src/hibermem/experiments/exact_mechanism.py` | Resumable E1–E3 runs and independent artifact validation. |
| `src/hibermem/experiments/contract.py` | Resumable E3c runner, identity checks, report construction, and validator. |
| `src/hibermem/experiments/prospective.py` | Fail-closed E4 `past -> validate -> freeze -> future -> validate` state machine. |

### Command-line tools

| Path | Purpose |
|---|---|
| `scripts/run_phase0.py`, `scripts/run_phase1.py` | P0/P1 execution and reports. |
| `scripts/check_phase2_backend.py`, `scripts/run_phase2.py` | Historical Phase-2 backend qualification and experiment. |
| `scripts/run_phase2r_screen.py` | Historical Phase-2R v1 development screen. |
| `scripts/run_phase2r_v2.py`, `scripts/validate_phase2r_v2_report.py` | Counterfactual-routing v2 screen and independent validator. |
| `scripts/analyze_phase2_public.py`, `scripts/analyze_phase2r_v2_interactions.py` | Read-only public Phase-2/Phase-2R diagnostics. |
| `scripts/freeze_phase2r_confirmation.py` | Historical confirmation freezer; no current run is authorized. |
| `scripts/run_exact_mechanism.py`, `scripts/validate_exact_mechanism.py` | E1–E3 execution and independent validation. |
| `scripts/analyze_factorial_report.py` | Read-only E3 audit and matched decode comparison. |
| `scripts/run_e3c_contract.py`, `scripts/validate_e3c_report.py` | E3c paired-contract runner and validator. |
| `scripts/freeze_e4_protocol.py` | Accepts only a passing real E3c report; currently rejects both contracts. |
| `scripts/run_e4_prospective.py`, `scripts/validate_e4_report.py` | E4 stage runner and independent validator; real execution currently blocked. |
| `scripts/verify_kaggle_environment.py` | Repository, package, CUDA, Git, and storage preflight. |
| `scripts/run_tests.py` | Runs pytest with a unique workspace-local scratch directory. |
| `scripts/kaggle_launch_status.py` | Distinguishes setup failure from validated model outcomes. |

### Configurations and Kaggle launchers

| Path | Purpose/status |
|---|---|
| `configs/experiments/phase1.json` | Frozen P1 synthetic recovery protocol. |
| `configs/experiments/phase2_local_4050.json`, `phase2_mock.json` | Historical local/mock Phase-2 configs. |
| `configs/experiments/phase2r_kaggle_screen.json`, `phase2r_v2_screen.json` | Historical Phase-2R screen configs. |
| `configs/experiments/exact_mechanism_e1.json`, `exact_mechanism_e2.json` | E1/E2 real exact-game configs. |
| `configs/experiments/exact_mechanism_e3_core.json` | E3 16-token core config. |
| `configs/experiments/exact_mechanism_e3_decode64.json` | E3 matched 64-token config. |
| `configs/experiments/exact_mechanism_e3_presentation.json` | Large presentation follow-up; deliberately on hold. |
| `configs/experiments/e3c_output_contract.json` | Frozen E3c real contract screen that completed negative. |
| `configs/experiments/e4_engineering_mock.json` | Mock-only E4 end-to-end validation. |
| `configs/experiments/e4_design_template.json` | Intentionally incomplete E4 template; cannot run real inference without a passing contract freeze. |
| `kaggle/run_phase2r_v2.sh` | Historical Qwen/Phi v2 screen launcher. |
| `kaggle/run_exact_mechanism.sh` | E1–E3 Kaggle launcher. |
| `kaggle/run_e3c_contract.sh` | E3c launcher; successful at commit `90ef285`. |
| `kaggle/run_e4_prospective.sh` | Conditional E4 launcher; do not run now. |
| `kaggle/run_phase2r_screen.sh`, `run_phase2r_confirmation.sh` | Historical screen/confirmation launchers; not current authorization. |

### Tests most relevant to current safeguards

| Path | Purpose |
|---|---|
| `tests/test_estimators.py`, `test_mobius.py`, `test_shapiq_reference.py` | Mathematical identity and independent reference checks. |
| `tests/test_split_leakage.py`, `test_audit_safeguards.py` | Query-split isolation and adversarial safeguard tests. |
| `tests/test_phase2_unlock.py`, `test_phase2r_freeze.py` | Fail-closed historical gate/freeze behavior. |
| `tests/test_exact_mechanism.py`, `test_factorial_mechanism.py`, `test_factorial_audit.py` | E1–E3 construction, analysis, and corruption rejection. |
| `tests/test_generation_trace.py` | Raw token/input/output provenance and deterministic trace checks. |
| `tests/test_output_contract.py` | E3c pairing, controls, readiness, and launcher constraints. |
| `tests/test_prospective_e4.py` | E4 capabilities, support stripping, immutable freeze, and future-before-freeze denial. |
| `tests/test_launcher_recovery.py`, `test_kaggle_environment.py`, `test_unit_test_isolation.py` | Setup/result classification, storage validation, and prohibition on model loading in tests. |
| `tests/test_cli_entrypoints.py` | Import/path smoke tests for all command-line entry points. |

The full suite contained 197 tests at the latest real E3c commit and passed locally
and on Kaggle.

## 6. Methodological invariants

- The behavioral game is \(v_q(S)=r(q,S)\); original destination correctness is the
  primary outcome.
- Exact Mobius coefficients, exact Shapley item values, exact SII, and fitted
  polynomial coefficients are different quantities and must be labeled separately.
- Positive pair SII can arise from a third-order mechanism; pair signs alone do not
  prove irreducible pair structure.
- Mixed-sign interaction objectives are not generally submodular. Eight-item policy
  selection uses exact enumeration; do not claim a generic greedy guarantee.
- Support antichains are diagnostic ground truth. Support labels and future outcomes
  are unavailable to retention policies.
- The independent unit is the bank/environment. Queries, masks, worlds, orderings,
  and seeds are repeated measurements, not independent samples.
- E4 must fit only past games, freeze selections before opening the future capability,
  and compare methods at identical cardinality and serialized payload budgets.
- Preserve negative results and raw artifacts. Never tune prompts, thresholds,
  margins, masks, or model choice on confirmation/test outcomes.
- Do not claim an engram, causal lesion, fault tolerance, future-query R2, robust
  Shapley-baseline win, natural-memory benefit, or full HiberMem architecture without
  the corresponding planned evidence.

## 7. Immediate plan: E3d before E4

E3d is planned but **not implemented**. It must receive a new protocol/config/prompt
identity and must not mutate E3c artifacts.

### Design and implementation order

1. Preserve and independently revalidate the real E3c bundle before coding.
2. Freeze a targeted E3d condition matrix that distinguishes:
   - one query path versus two competing query paths;
   - base versus counterfactual destinations;
   - empty, exact minimal support, and full memory;
   - each missing required-link position;
   - each missing link with all distractors present; and
   - contexts containing only the other query's path.
3. Reserve fresh cohorts: `dev-360`–`dev-361` for diagnosis/contract development and
   `dev-370`–`dev-373` for one frozen verification run. Never reuse 350–351.
4. Keep `current_v1` as a paired control. Add one predeclared query-anchored,
   label-only candidate that forces exact start-identifier/path checking.
5. A structured support/path response may be included only as a diagnostic arm. It
   cannot silently become the original E4 outcome contract or evidence for the same
   hypothesis.
6. Report full and supported accuracy, missing-link assertion by position,
   counterfactual tracking, other-query destination capture, strict format, cap hits,
   tokens, and latency. Include bank-level results rather than treating rows as
   replication.
7. Keep the E3c criteria unchanged and predeclare additional full-memory,
   query-binding, counterfactual, and per-link requirements before inference.
8. Implement symbolic controls, a mock end-to-end run, independent reconstruction,
   corruption/leakage tests, a clean-commit Kaggle launcher, and a result archive.
9. Run the diagnostic cohort, explicitly freeze at most one label-only contract, and
   run that frozen contract once on the separate verification cohort.

### Decision after E3d

- **All label-only verification checks pass:** generate a new committed E4 design
  config from the independent E3d verification report, then run E4 past/freeze/future.
- **Single-query passes but dual-query fails:** revise the bank/query interface and
  repeat on another fresh cohort before E4.
- **Formatting passes but grounding fails:** stop this Qwen/task pairing; evaluate a
  separately pinned stronger model or narrow the claim.
- **Only a structured verifier passes:** branch to a separately named hybrid
  neuro-symbolic hypothesis; do not count it as support for the original interface.
- **All arms fail:** preserve the negative result and stop synthetic exact-game
  expansion.

Until a label-only E3d verification pass exists: do not create an E4 frozen config,
run E4, run E5, unlock confirmation/test, or resume the 49,152-condition E3
presentation experiment.

## 8. Environment and operational notes

Use only the repository-local Conda environment:

```powershell
cd D:\Coding\paper\hibermem
conda activate D:\Coding\paper\hibermem\.conda
python -m pytest -q
```

Do not activate `.venv` and `.conda` together. The verified local environment used
Python 3.11.15, PyTorch 2.13.0+cu130, torchvision 0.28.0+cu130, Transformers 5.16.1,
and accelerate 1.14.0 on an RTX 4050 Laptop GPU. The real E3c run used Kaggle Python
3.12.13, Torch 2.10.0+cu128, Transformers 5.16.1, and Tesla T4 GPUs.

Before any new real run:

1. run the full local suite and the protocol's symbolic controls;
2. independently validate all mock artifacts;
3. run `git diff --check`;
4. review and commit every source/config/launcher/test change;
5. push and use the exact 40-character commit in a fresh Kaggle checkout; and
6. verify clean Git state, pinned model revision, environment, and artifact identity.

Current uncommitted documentation work should consist only of:

```text
CHANGELOG.md
HANDOFF.md
docs/E3C_OUTPUT_CONTRACT_RESULTS_2026-09-02.md
docs/E4_PROSPECTIVE_IMPLEMENTATION_PLAN_2026-09-02.md
```

No experiment source, model inference, gate, or original result artifact was modified
while preparing this handoff.
