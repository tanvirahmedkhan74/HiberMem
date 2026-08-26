# HiberMem Pre-Implementation Audit

**Audit date:** 2026-08-26  
**Repository state at audit:** specification only; no prior source tree or Git
repository was present.  
**Decision:** **APPROVE PHASE 0 WITH REQUIRED AMENDMENTS.** Phases 1–9 remain
gated. In particular, Phase 3 must use a sign-aware lesion objective before it
can be approved.

## 1. Theory audit

| Claim | Verdict | Audit finding |
|---|---|---|
| A memory bank and downstream reward define a coalition game | VALID WITH ASSUMPTIONS | The task distribution, prompt, model, decoding, and runtime distribution must be fixed. The estimated value is otherwise a different game across conditions. |
| The corrected full-context pairwise sign is \(\Delta_i+\Delta_j-\Delta_{ij}\) | VALID | Expanding the three deletion effects gives the stated second difference. Positive means complementarity **at the full-memory context**, not globally. |
| The general discrete derivative \(\Delta_Tv(S)\) | VALID | The inclusion–exclusion formula is the standard finite difference for disjoint \(S,T\). |
| A local derivative, Möbius coefficient, and Shapley-family interaction can be treated as the same \(I_T\) | INVALID | They are distinct estimands. A Möbius coefficient is \(\Delta_Tv(\emptyset)\); a local full-context effect is \(\Delta_Tv(N\setminus T)\); SII averages derivatives over contexts. Phase 0 exposes them separately. |
| Shapley interaction indices apply to memory coalitions | VALID WITH ASSUMPTIONS | They are appropriate descriptive/attribution functionals once the game and missing-memory intervention are well defined. Different indices encode different axioms and distribute pure higher-order effects differently. The index must be preregistered. See [Shapley–Taylor](https://proceedings.mlr.press/v119/sundararajan20a.html), [Faith-Shap](https://www.jmlr.org/beta/papers/v24/22-0202.html), and [shapiq](https://shapiq.readthedocs.io/en/stable/api/shapiq.game_theory.exact.html). |
| The displayed low-order polynomial may freely combine Shapley item values and arbitrary interaction scores | INVALID | A polynomial is coherent when its coefficients come from one decomposition (for example Möbius coefficients), a fitted regression with a stated basis, or an efficient truncated interaction scheme. Mixing ordinary Shapley values with unadjusted interaction terms can double count utility. |
| Sparse, order-2/3 structure is a safe default | QUESTIONABLE | It is a testable approximation, not a property of the game. Report held-out coalition reconstruction error and compare orders before interpreting recovered terms. |
| Magnitude plus bootstrap sign stability defines a functional engram | QUESTIONABLE | Stability is necessary but not sufficient. Multiplicity, practical effect size, estimator bias, and prospective validity are also required. “Candidate functional coalition” is the acceptable pre-P3 term. |
| Discovery/validation/test separation removes circularity | VALID WITH ASSUMPTIONS | Identifier disjointness is necessary but insufficient when templates or latent rules are duplicated. Split and audit by bank, template family, latent dependency, and generation seed as appropriate. |
| Interaction-aware retention tests structure beyond item value | VALID WITH ASSUMPTIONS | The item and interaction objectives must use discovery-only estimates, identical persistent-storage budgets, locked test tasks, and the same delivery/retrieval mechanism. Structural metadata must count. |
| Item-utility-matched lesions identify an interaction effect | VALID WITH ASSUMPTIONS | Causal interpretation requires adequate covariate overlap, discovery-only mask construction, tight balance, stable interventions, and uncertainty propagation for estimated item values. Residual content differences remain a threat and must be reported. |
| Destroyed mass \(J(D)=\sum |I_T|\) is a valid damage target | INVALID | Removing a negative interaction may improve utility. Positive and negative terms must be separated. Use \(J_+(D)=\sum_{T\cap D\ne\emptyset}\max(I_T,0)\), \(J_-(D)=\sum\max(-I_T,0)\), match \(J_-\), and maximize predicted sign-aware damage \(\hat v(M)-\hat v(M\setminus D)\). Absolute mass may remain a descriptive topology statistic only. |
| Normalized memory-dependent retention \(R\) | VALID WITH ASSUMPTIONS | It is interpretable as retention when \(A_{full}>A_{empty}\). It is undefined when equal. When \(A_{full}<A_{empty}\), memory is harmful and the ratio must not be presented as retained benefit; report raw effects separately. Do not clamp. |
| NMS-AUC and \(\rho_{50}^{mem}\) | VALID WITH ASSUMPTIONS | Prespecify the deletion grid, integration/interpolation rule, and handling of non-monotone curves. Report \(\rho_{50}\) as interval-censored or undefined when the grid does not identify a crossing. |
| The bank/environment is the independent unit | VALID | Queries share a bank and are repeated measurements. Bank-level paired effects are primary; hierarchical query-level models are secondary. Ten banks are suitable for a pilot, not a definitive claim. |

### Required mathematical conventions

1. Phase 0 uses exact set functions and no LLM dependencies.
2. Möbius/Harsanyi coefficients are the canonical exact polynomial
   decomposition.
3. SII is the first Shapley-family reference index, because its exact formula is
   compact and independently available in `shapiq`.
4. Phase 1 or later must preregister the primary interaction index; switching
   indices after test inspection is prohibited.
5. Triple-AND expectations are stated per index. A pure third-order Möbius term
   does not imply every lower-order Shapley-family score is zero.

## 2. Novelty audit (2024–2026)

The original broad novelty claims do not survive the current literature.

- Memory addition/deletion is directly studied by Xiong et al., [How Memory
  Management Impacts LLM Agents](https://aclanthology.org/2026.acl-long.27/).
- Item-level coalition valuation is now a direct overlap: [MemLens](https://arxiv.org/abs/2607.25992)
  defines a downstream memory coalition value, estimates per-memory Shapley
  values, and uses them for selective storage. HiberMem therefore cannot claim
  novelty for “Shapley-valued memories,” coalition valuation, or item-aware
  retention.
- Higher-order *representational* memory is also occupied: [HyperMem](https://aclanthology.org/2026.acl-long.1627/)
  uses hyperedges for high-order associations. [GAM](https://aclanthology.org/2026.acl-long.1600/),
  [MAGMA](https://aclanthology.org/2026.acl-long.1709/), and
  [Mnemis](https://aclanthology.org/2026.acl-long.1096/) further establish the
  crowded graph-memory space.
- Coalitional interaction analysis of LLM-agent inputs is not unprecedented:
  [CUDAnalyst](https://arxiv.org/abs/2605.26720) attributes planning outcomes to
  coalitions and interactions of feedback sources. Its players are feedback
  channels rather than persistent memory items, but the methodological overlap
  must be cited.
- Learned memory policies are covered by [Memory-R1](https://aclanthology.org/2026.acl-long.583/),
  [AgeMem](https://aclanthology.org/2026.acl-long.981/), and newer fine-grained
  credit work such as [AttriMem](https://arxiv.org/abs/2607.21106). Deferring RL
  is therefore both scientifically cleaner and important for differentiation.
- The benchmark ordering remains reasonable. Relevant external-validity targets
  include [LoCoMo](https://aclanthology.org/2024.acl-long.747/),
  [LoCoMo-Plus](https://aclanthology.org/2026.acl-long.1150/),
  [LongMemEval](https://openreview.net/revisions?id=UBvm2bIyxz), and
  [LongMemEval-V2](https://arxiv.org/abs/2605.12493).
- The neuroscience citation is real and current: Lin et al., “Artificial
  hibernation reveals synaptic engram architecture associated with memory
  retention,” *Science* 393 (2026), DOI
  [10.1126/science.aee7004](https://doi.org/10.1126/science.aee7004). Its result
  is biological motivation and association, not evidence about LLM memory.

### Narrow novelty verdict

No exact precedent was located in the audited primary sources for the complete
combination of:

1. explicit higher-order functional interaction estimation over external memory
   items;
2. discovery-only, item-utility-matched and sign-aware structural lesions;
3. prospective held-out prediction of lesion damage; and
4. normalized survival curves under controlled interaction destruction.

This is a **plausible novelty gap, not a priority guarantee**. MemLens, HyperMem,
and CUDAnalyst materially narrow it and must be treated as closest work.

## 3. Experimental audit

The design must add these controls before Phase 2/3 approval:

- group-disjoint splitting for query templates and latent dependency rules, not
  merely disjoint query IDs;
- exact, canonical memory ordering plus order-randomized sensitivity runs;
- equal serialized token/byte budgets across policies at each deletion ratio;
- direct delivery of all survivors in the primary causal experiment;
- finite action labels and a deterministic scorer; any LLM judge is secondary;
- a no-memory baseline and counterfactual labels/entities to measure model-prior
  success without memory;
- coalition sampling balanced across sizes, with held-out coalition
  reconstruction error and order-1/order-2/order-3 comparisons;
- query-stratified interaction estimates so averaging does not hide sign
  reversals across task types;
- bootstrap or cross-fit propagation of uncertainty in \(\phi_i\) into lesion
  matching;
- separate positive and negative interaction analyses and multiplicity-aware
  confidence reporting;
- immutable test artifacts and a one-way test unlock recorded in provenance.

Prompt length is part of the intervention across deletion ratios, but competing
policies at a fixed ratio must have closely matched serialized lengths. Neutral
padding is not automatically valid because padding can itself change model
behavior; if used, it needs its own control.

## 4. Compute audit

Phase 0 and Phase 1 are CPU-feasible. Phase 2 is inference-heavy rather than
memory-heavy, but the plan understates the call count:

\[
10\text{ banks}\times256\text{ coalitions}\times20\text{ discovery queries}
=51{,}200\text{ generations}.
\]

That is technically feasible with a 1.5B–2B quantized model on an RTX 4050 6 GB,
but may take many hours and is too large for the very first local smoke test.
The smallest validity-preserving pilot is:

- exact 256-coalition enumeration for 2 banks;
- 128 size-balanced sampled coalitions for the other 8 banks;
- deterministic outputs capped near 16–32 tokens;
- immediate persistent caching after every evaluation;
- expand exact enumeration only if the estimator and stability checks warrant it.

This reduces the initial discovery workload from 51,200 to 30,720 generations
without changing the locked query splits. Kaggle or Colab can run the same
resumable artifacts. Phase 3 adds relatively few test-mask evaluations compared
with coalition discovery and also fits these platforms.

## 5. Implementation-boundary audit

The proposed module boundaries are approved with two refinements:

- `coalition` owns masks and game evaluation only;
- `interactions` owns estimands and estimators, with explicit names for local,
  Möbius, and SII quantities;
- future environment generation must not import evaluators or test answers;
- future LLM backends must not be imported by theory modules;
- future retention modules select survivors but never retrieve them;
- future lesion modules consume discovery artifacts and covariates, never test
  outcomes;
- future evaluation modules own normalized survival and bank-level statistics;
- a split-capability object should make test access unavailable to discovery,
  rather than relying only on string labels.

Because the repository was empty, there were no pre-existing boundary violations
to remediate.

## 6. Approval checklist

- [x] Pairwise sign correction verified.
- [x] Exact analytical tests specified and implemented in Phase 0.
- [x] Discovery/test isolation is a hard requirement for later phases.
- [x] Item-only and interaction-aware objectives are distinguished.
- [x] Matched lesions control item utility, with the required sign-aware amendment.
- [x] Primary causal evaluation directly supplies all survivors.
- [x] Zero-memory normalization and its failure cases are specified.
- [x] Structural metadata counts toward storage.
- [x] Bank/environment is the scientific unit.
- [x] Falsification gates remain explicit.
- [x] Phase 0–3 have a practical staged compute path.
- [x] RL and regrowth remain deferred.
- [x] A narrow novelty gap remains after the current search, with material closest-work overlap recorded.

**Approved action:** implement and run Phase 0 only. Do not scaffold later agent,
retrieval, RL, regrowth, or lesion systems until their preceding gates pass.
