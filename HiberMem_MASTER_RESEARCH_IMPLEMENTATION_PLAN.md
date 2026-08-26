# HiberMem Master Research & Implementation Specification
## Causal Interaction Structure for Fault-Tolerant / Turnover-Resilient LLM Agent Memory

**Document status:** Pre-implementation research specification  
**Purpose:** Theory audit, experimental design, implementation blueprint, compute plan, and falsification protocol for Codex review  
**Target audience:** Senior CS / Cognitive AI researchers, ACL/EMNLP reviewers, and agentic coding systems  
**Date:** August 2026

---

# 0. Executive Decision

The original HiberMem idea should **continue**, but the implementation must be narrower than the original concept note.

The first scientific question is not:

> Can we build a neuroscience-inspired graph memory with hibernation and regrowth?

It is:

> **Do higher-order functional interactions among external memories explain future agent behavior beyond the contribution of the individual memories themselves?**

Everything else is downstream of this question.

Therefore the implementation order is:

1. validate the mathematics;
2. validate interaction recovery on controlled games;
3. measure interactions in an LLM memory setting;
4. run item-utility-matched structural lesions;
5. test prospective validity on held-out future tasks;
6. only then build the full HiberMem graph/hypergraph memory system;
7. only later consider repeated hibernation, RL retention policies, and regrowth.

If the matched causal lesion experiment fails, the core HiberMem claim is unsupported and the project should pivot rather than expand.

---

# 1. Research Question

Let an agent have external memory

\[
M = \{m_1, m_2, \dots, m_n\}.
\]

For a task/query \(q\), define downstream reward when only subset \(S \subseteq M\) is accessible:

\[
r(q,S;\omega),
\]

where \(\omega\) captures generation/runtime randomness.

The central research question is:

\[
\boxed{
\text{Does higher-order interaction structure among memories carry predictive and causal information}
}
\]

\[
\boxed{
\text{about future behavior beyond individual memory importance?}
}
\]

Equivalently, if individual contributions are represented by \(\phi_i\) and higher-order interactions by \(I_T\), is

\[
I_T
\]

useful after conditioning on

\[
\{\phi_i\}?
\]

The paper should test this empirically rather than assume it.

---

# 2. Source-of-Inspiration Boundary

The project is inspired by recent neuroscience evidence on artificial hibernation and synaptic memory retention.

The biological observation motivates a computational hypothesis:

- extensive structural turnover may occur without proportional behavioral loss;
- some higher-order synaptic organization appears preferentially preserved;
- survival of organization may matter alongside survival of individual components.

However, HiberMem must **not** claim mechanistic equivalence between hippocampal engrams and LLM external memory.

Correct framing:

\[
\text{neuroscience observation}
\Rightarrow
\text{hypothesis generator}
\]

Incorrect framing:

\[
\text{neuroscience observation}
\Rightarrow
\text{proof that LLM external memory works the same way}.
\]

The computational contribution must stand even if the neuroscience analogy is removed from the paper.

---

# 3. Quick Validation of Core Claims

## 3.1 Claim: memory can remain behaviorally useful under severe structural turnover

**Status:** Biologically motivated; computationally unproven.

The recent hibernation study supports the biological inspiration, but not a causal theorem about artificial memory.

**Implementation consequence:** treat biological evidence as motivation only.

---

## 3.2 Claim: memory deletion is a novel evaluation setting

**Status:** False as a standalone novelty claim.

2026 LLM-agent work already studies the behavioral effects of memory addition/deletion.

**Implementation consequence:** the novelty cannot be "we delete memories."

The new contribution must instead be:

> controlled destruction of **interaction structure** while controlling for individual memory utility.

---

## 3.3 Claim: graph structure itself is novel

**Status:** False.

Graph-based long-term memory is already a mature and crowded direction.

**Implementation consequence:** do not position HiberMem as "another graph memory."

---

## 3.4 Claim: pairwise co-use is sufficient to define functional structure

**Status:** Unsupported.

Many useful dependencies can be genuinely third-order or higher-order.

Example:

\[
v(x_1,x_2,x_3)=x_1x_2x_3.
\]

All proper subsets can be insufficient even though the full coalition is essential.

**Implementation consequence:** the primary mathematical object is a coalition game / sparse interaction hypergraph, not a simple graph.

---

## 3.5 Claim: interaction-aware survival can be evaluated using the same trajectories that define interactions

**Status:** Invalid due to circularity / target leakage.

**Implementation consequence:** discovery and final test tasks must be disjoint.

---

## 3.6 Claim: regrowth is needed to prove structural memory

**Status:** False.

Regrowth introduces an additional inference/hallucination mechanism that weakens causal interpretation.

**Implementation consequence:** remove regrowth from the primary paper.

---

## 3.7 Claim: RL should be used for retention policy learning

**Status:** Not needed for the foundational test.

RL introduces another source of advantage and confounds interpretation.

**Implementation consequence:** deterministic retention/optimization first; RL only after the structural claim is established.

---

# 4. Correct Mathematical Formulation

## 4.1 Coalition value function

Define a memory coalition game:

\[
v: 2^M \rightarrow \mathbb{R}.
\]

For discovery tasks \(Q_D\):

\[
v_D(S)
=
\mathbb{E}_{q\sim Q_D,\omega}
[r(q,S;\omega)].
\]

For final held-out tasks \(Q_T\):

\[
v_T(S)
=
\mathbb{E}_{q\sim Q_T,\omega}
[r(q,S;\omega)].
\]

Requirement:

\[
Q_D \cap Q_T = \varnothing.
\]

No information from \(Q_T\) may affect interaction estimation, threshold selection, retention, lesion construction, or model selection.

---

# 5. Correction to the Original Pairwise Synergy Equation

The original concept proposed:

\[
\Delta_i
=
R(M)-R(M\setminus\{m_i\}),
\]

\[
\Delta_{ij}
=
R(M)-R(M\setminus\{m_i,m_j\}),
\]

and interpreted

\[
\Delta_{ij}-(\Delta_i+\Delta_j)
\]

as positive complementarity.

That sign is reversed.

The local second-order discrete interaction at the full-memory context is:

\[
I_{ij}
=
v(M)
-v(M\setminus\{i\})
-v(M\setminus\{j\})
+v(M\setminus\{i,j\}).
\]

Using the \(\Delta\) notation:

\[
\boxed{
I_{ij}
=
\Delta_i+\Delta_j-\Delta_{ij}
}
\]

Interpretation:

- \(I_{ij}>0\): complementarity/cooperation;
- \(I_{ij}<0\): redundancy/substitution/conflict-like behavior;
- \(I_{ij}\approx 0\): approximately additive contributions.

This sign correction is mandatory.

---

# 6. General Higher-Order Interactions

For a coalition \(T\) and context \(S\) with \(S\cap T=\varnothing\), define the discrete derivative:

\[
\Delta_T v(S)
=
\sum_{L\subseteq T}
(-1)^{|T|-|L|}
v(S\cup L).
\]

For \(|T|=1\), this is a marginal contribution.

For \(|T|=2\), it becomes the pairwise discrete interaction.

For \(|T|=3\), it captures a genuine third-order dependency.

Use a principled interaction index rather than an ad-hoc score where possible. Candidate families:

- Shapley Interaction Index;
- Shapley-Taylor Interaction Index;
- Faithful Shapley interaction formulations;
- Möbius / Harsanyi-style interaction decomposition.

For implementation, keep the theoretical API generic enough to support multiple estimators.

---

# 7. Approximate Functional Model

For implementation, approximate utility by a sparse low-order polynomial:

\[
\hat v(S)
=
\beta_0
+
\sum_i \phi_i x_i
+
\sum_{i<j} I_{ij}x_ix_j
+
\sum_{i<j<k}I_{ijk}x_ix_jx_k,
\]

where

\[
x_i=\mathbf{1}[m_i\in S].
\]

Interpretation:

\[
\phi_i = \text{individual memory contribution}
\]

and

\[
I_T = \text{interaction contribution}.
\]

The project must not assume that interactions are sparse or low-order without checking this empirically.

The working assumption is only:

> If useful functional interactions are sparse enough, they may be estimable and exploitable under realistic budgets.

---

# 8. Functional Engram Definition

Do **not** define an engram as:

- an embedding cluster;
- a semantic topic;
- a graph community;
- a set of frequently co-retrieved nodes.

Instead define a **candidate functional coalition** \(T\) only if:

\[
|I_T| > \epsilon
\]

and

\[
\operatorname{Stability}(I_T) > \gamma.
\]

Stability should be estimated across discovery subsets, bootstrap resamples, or repeated environments.

Positive and negative interaction structures must be analyzed separately.

A final graph/hypergraph can be built from stable interaction terms, but the interaction estimate is primary and the graph is secondary.

---

# 9. Circularity and Prospective Validation

The following procedure is prohibited:

1. use task behavior to discover interactions;
2. preserve the highest-interaction memories;
3. evaluate on the same tasks;
4. claim the structure predicts behavior.

This is circular.

Required procedure:

\[
Q = Q_D \cup Q_V \cup Q_T
\]

with disjoint discovery, validation, and test splits.

Suggested initial split:

\[
60\% / 20\% / 20\%.
\]

Use:

- \(Q_D\): interaction discovery;
- \(Q_V\): hyperparameters/thresholds/model selection;
- \(Q_T\): final locked evaluation only.

The final claim must be prospective:

\[
\hat{\mathcal H}(Q_D)
\rightarrow
\text{behavior on }Q_T.
\]

---

# 10. Primary Scientific Hypotheses

## H1 — Interaction-aware retention

Under identical total storage budgets:

\[
R_T(S_{\text{interaction}})
>
R_T(S_{\text{item}}).
\]

This tests whether interaction-aware memory selection improves survival beyond individual-item selection.

---

## H2 — Interaction-targeted lesion

Construct deletion masks with approximately equal individual utility but different interaction destruction.

Then:

\[
\Delta_{\text{structural lesion}}
>
\Delta_{\text{matched control lesion}}.
\]

This is the strongest causal hypothesis.

---

## H3 — Prospective validity

Interaction structure estimated from past tasks predicts future damage:

\[
I_T^{\text{discover}}
\rightarrow
\Delta Performance_T
\]

after controlling for individual contribution and relevant item-level covariates.

If H2 and H3 fail, the central structural-engram hypothesis should be considered unsupported even if H1 produces a small optimization gain.

---

# 11. Separate Retention From Retrieval

The primary causal experiment must not use custom graph retrieval.

Reason:

If HiberMem performs better, one must distinguish whether the gain comes from:

- better retained content;
- better retrieval;
- a different prompt/context;
- actual structural survival.

Primary causal experiment:

> give the model **all surviving memories directly**, provided they fit within the controlled context budget.

Thus:

\[
\text{independent variable}=\text{which memories survived}.
\]

Secondary systems experiment:

- same retained memory;
- vector retrieval;
- graph retrieval;
- structural/hypergraph retrieval.

Do not run the secondary retrieval comparison before the causal retention claim is established.

---

# 12. Correct Retention Optimization

Let \(C(S)\) be the serialized storage cost of retained memory.

Interaction-aware retention:

\[
S_B^*
=
\arg\max_{S\subseteq M}\hat v(S)
\]

subject to

\[
C(S)\le B.
\]

Item-only retention:

\[
S_{\text{item}}^*
=
\arg\max_{S\subseteq M}
\sum_{i\in S}\phi_i
\]

subject to

\[
C(S)\le B.
\]

For small \(n\):

- solve exactly by exhaustive search.

For moderate \(n\) with pairwise interactions:

- use MILP / quadratic binary optimization if practical.

For larger \(n\):

- greedy marginal gain:

\[
\Delta(i\mid S)
=
\phi_i
+
\sum_{j\in S}I_{ij}
+
\sum_{\{j,k\}\subseteq S}I_{ijk}.
\]

The first paper does not require proving the retention optimization is globally optimal at large scale.

---

# 13. Matched Structural Lesion Experiment

This is the decisive experiment.

Construct two deletion sets:

\[
D_s = \text{structure-targeted deletion}
\]

and

\[
D_c = \text{matched control deletion}.
\]

Match approximately:

\[
|D_s|=|D_c|
\]

\[
C(D_s)\approx C(D_c)
\]

\[
\sum_{i\in D_s}\phi_i
\approx
\sum_{i\in D_c}\phi_i.
\]

Also match or stratify:

- recency;
- retrieval frequency;
- semantic similarity/centrality;
- node degree where relevant;
- payload token count.

Define destroyed interaction mass:

\[
J(D)
=
\sum_{\substack{T:\\T\cap D\neq\varnothing\\|T|\ge2}}
|I_T|.
\]

Require:

\[
J(D_s)\gg J(D_c).
\]

Evaluate both on locked \(Q_T\).

Primary effect:

\[
\Delta_{\text{interaction}}
=
v_T(M\setminus D_c)
-
v_T(M\setminus D_s).
\]

Evidence for H2 requires a robust positive effect after matching individual contribution.

---

# 14. Synthetic Mechanism Validation

A synthetic benchmark is mandatory but cannot be the headline scientific result.

Purpose:

\[
\boxed{\text{validate that the estimator and lesion machinery recover known structure}}
\]

not:

\[
\boxed{\text{prove natural LLM memory contains the same structure}}.
\]

Required interaction patterns:

## Additive

\[
v(x_1,x_2)=a_1x_1+a_2x_2
\]

Expected:

\[
I_{12}=0.
\]

## AND complementarity

\[
v(x_1,x_2)=x_1x_2
\]

Expected:

\[
I_{12}>0.
\]

## Redundant OR

\[
v(x_1,x_2)=x_1+x_2-x_1x_2
\]

Expected:

\[
I_{12}<0.
\]

## Triple complementarity

\[
v(x_1,x_2,x_3)=x_1x_2x_3
\]

Expected:

- strong third-order interaction;
- lower-order behavior depends on selected interaction convention;
- the estimator must not falsely reduce the entire dependency to ordinary pairwise importance.

## Dummy memory

A variable that never changes utility must have zero contribution/interactions up to numerical tolerance.

---

# 15. Phase-0 Mathematical Unit Tests

No LLMs.

Mandatory tests:

1. additive game;
2. pair AND;
3. pair OR/redundancy;
4. triple AND;
5. dummy player;
6. permutation invariance;
7. sign correctness;
8. exact-vs-library estimator agreement for small \(n\);
9. serialization of coalition masks;
10. deterministic reproducibility.

**Gate P0:** all analytical expectations must pass before any LLM experiment.

---

# 16. Naturalistic Controlled Agent Environment

Create structured memory banks with known but linguistically expressed dependencies.

Example memories:

```text
m1: Server A has an NVIDIA GPU.
m2: Server A runs CUDA 12.1.
m3: Tool X requires CUDA >= 11.8.
m4: Tool X runs locally.
m5: Tool Y requires an external API.
m6: The user requires offline execution.
m7: Server B has no GPU.
m8: The user prioritizes minimum latency.
```

Example task:

```text
Choose the valid server/tool configuration.
```

Prefer finite action outputs:

```text
SERVER_A + TOOL_X
```

rather than free-form prose.

This enables deterministic scoring and reduces evaluator noise.

---

# 17. Coalition Sampling

Exact enumeration is feasible only for small \(n\).

Examples:

\[
2^8=256
\]

\[
2^{10}=1024
\]

\[
2^{20}\approx 1.05\times10^6.
\]

Recommended:

## \(n\le 8\)

Use exact enumeration where practical.

## \(8<n\le 30\)

Use sampled coalitions.

Initial range:

\[
128-512
\]

coalitions per bank.

Scale later to:

\[
256-1024
\]

if interaction estimates remain unstable.

Begin with:

\[
k=2
\]

pairwise interactions.

Add:

\[
k=3
\]

only after:

- phase-0 third-order tests work;
- evidence suggests pairwise approximation is insufficient;
- compute budget is acceptable.

---

# 18. Interaction Estimation

Implement a common interface:

```python
class InteractionEstimator:
    def fit(self, coalition_masks, coalition_values):
        ...

    def individual_values(self):
        ...

    def interactions(self, order: int):
        ...

    def uncertainty(self):
        ...
```

Recommended backend:

- `shapiq` or another established Shapley-interaction implementation;
- exact internal implementation for tiny verification games;
- optional sparse polynomial/Möbius estimator for controlled experiments.

Never trust a single library blindly: analytical unit tests are mandatory.

---

# 19. Stability Estimation

A high interaction estimate is insufficient if it is unstable.

Measure:

- sign consistency;
- ranking consistency;
- bootstrap confidence intervals;
- split-half correlation;
- top-\(k\) overlap.

Candidate stability criterion:

\[
P(\operatorname{sign}(I_T^{(b)})=\operatorname{sign}(\bar I_T))
\ge \gamma.
\]

Do not hard-code \(\gamma\) based on final test performance.

Choose on validation data or report a sensitivity analysis.

---

# 20. Memory Survival Metric

Raw downstream accuracy is confounded by model ability without external memory.

Let:

\[
A(\rho)
\]

be accuracy after deletion fraction \(\rho\).

Let:

\[
A_{\emptyset}
\]

be performance with no external memory.

Let:

\[
A_{\mathrm{full}}=A(0).
\]

Define normalized memory-dependent retention:

\[
\boxed{
R(\rho)
=
\frac{A(\rho)-A_{\emptyset}}
{A_{\mathrm{full}}-A_{\emptyset}}
}
\]

Do not clamp \(R\).

Interpretation:

- \(R=1\): full memory-dependent contribution remains;
- \(R=0\): no advantage beyond zero-memory baseline;
- \(R<0\): corrupted memory is worse than no memory;
- \(R>1\): possible beneficial regularization/noise effect; investigate, do not silently clip.

Define:

\[
\operatorname{NMS-AUC}
=
\int_0^{\rho_{\max}} R(\rho)d\rho
\]

or normalized by \(\rho_{\max}\).

Define:

\[
\rho_{50}^{mem}
=
\inf\{\rho:R(\rho)\le0.5\}.
\]

Report undefined/censored cases honestly.

---

# 21. Deletion Ratios

Initial pilot:

\[
\rho\in
\{0,0.25,0.50,0.70,0.80\}.
\]

Later full experiment may use:

\[
\{0,0.2,0.4,0.6,0.8,0.9\}.
\]

Avoid excessive grid resolution before establishing a signal.

---

# 22. Statistical Unit and Analysis

The independent scientific unit should be the **memory bank / environment**, not every query.

Why:

Queries within one bank share the same memories and dependency structure, so treating all queries as independent creates pseudoreplication.

For bank \(b\):

\[
d_b
=
R_b(D_c)-R_b(D_s).
\]

Primary analysis:

- paired mean difference;
- paired median;
- paired permutation/randomization test;
- hierarchical/bootstrap 95% confidence interval;
- complete per-bank effect distribution.

For later binary query-level analysis:

\[
\operatorname{logit}P(Y=1)
=
\beta_0
+
\beta_1\operatorname{LesionType}
+
\beta_2\rho
+
\beta_3(\operatorname{LesionType}\times\rho)
+
u_{\text{bank}}
+
u_{\text{template}}.
\]

Corruption seeds are repeated measurements, not fully independent biological/scientific replicates.

---

# 23. Baselines

Minimum baseline set:

1. Random retention.
2. Recency retention.
3. Retrieval-frequency retention.
4. Semantic-diversity/coreset retention.
5. Embedding-graph centrality.
6. Strong item-value retention.
7. Functional co-use graph.
8. Interaction-aware retention.

Critical comparison:

\[
\boxed{
\text{item-value retention}
\quad vs \quad
\text{interaction-aware retention}
}
\]

If interaction-aware selection cannot beat a properly estimated item-value baseline, the structural claim is weak.

---

# 24. Literature Positioning

Codex must verify each citation before using it in any paper draft.

Key literature families to review:

## Neuroscience inspiration

- Artificial hibernation / synaptic engram architecture and memory retention (2026).

Use only as biological inspiration, not mechanistic equivalence.

## Cooperative-game interactions

- Shapley Interaction Index.
- Shapley-Taylor Interaction Index.
- Faithful Shapley interactions.
- Möbius/Harsanyi decompositions.
- Sparse recovery of higher-order interactions where applicable.

## Agent memory management

- 2026 ACL work on memory addition/deletion and experience-following behavior.
- Memory-R1.
- AgeMem.

## Graph / structured agent memory

- GAM.
- MAGMA.
- Mnemis.
- StructMemEval and related structured-memory evaluations.

## Long-term memory benchmarks

- LoCoMo.
- LongMemEval.
- LoCoMo-Plus.
- LongMemEval-V2.

Important novelty statement:

> HiberMem is **not** novel because it uses graphs, deletion, consolidation, or biologically inspired terminology.

Potential novelty:

> HiberMem causally tests whether higher-order memory interaction structure explains survival beyond individually important memories under matched destructive interventions.

---

# 25. Benchmark Strategy

Do not begin with all public benchmarks.

Recommended order:

1. deterministic synthetic coalition games;
2. controlled natural-language agent memory environment;
3. LoCoMo-Plus subset;
4. LongMemEval;
5. LongMemEval-V2;
6. optional structured-memory benchmarks.

Why not start with LongMemEval-V2?

Because the first question is mathematical and causal, not scale.

Large realistic benchmarks should test external validity **after** the mechanism is established.

---

# 26. Storage Budget Accounting

Graph/hypergraph metadata is not free.

Define:

\[
C_{\text{total}}
=
C_{\text{payload}}
+
C_{\text{edges}}
+
C_{\text{weights}}
+
C_{\text{metadata}}
+
C_{\text{indexes}}.
\]

Report:

- textual token count;
- serialized bytes;
- graph/hypergraph metadata bytes;
- retrieval-index overhead;
- runtime cache separately from persistent memory;
- inference cost separately from memory cost.

Do not claim "20% memory retained" if the structural representation carries a large hidden payload.

---

# 27. Fault Tolerance vs Selective Compression

Keep these settings distinct.

## A. Survival-aware compression

The system intentionally chooses what to retain:

\[
\max_{S}
v(S)
\quad
\text{s.t. }
C(S)\le B.
\]

This studies structured compression.

## B. Fault tolerance

The system first consolidates memory, then an external corruption process acts:

\[
F_\rho(M,\mathcal H).
\]

The agent does not choose the fault.

Corruptions may be:

- random;
- bursty;
- recency-targeted;
- salience-targeted;
- interaction-targeted;
- adversarial.

Use "fault-tolerant" only if exogenous-fault experiments are actually performed.

Otherwise "turnover-resilient" or "interaction-aware memory compression" is more precise.

---

# 28. Regrowth Policy

Primary paper:

\[
\boxed{\text{NO REGROWTH}}
\]

Reason:

A language model may infer or hallucinate deleted content from parametric knowledge.

That makes it difficult to distinguish:

\[
\text{memory survival}
\]

from

\[
\text{probabilistic reconstruction}.
\]

Regrowth can become a separate later experiment with strict provenance/evidence constraints.

---

# 29. RL Policy

Primary paper:

\[
\boxed{\text{NO RL RETENTION POLICY}}
\]

Reason:

If an RL-trained system wins, improvement may come from training rather than the structural-memory principle.

Use fixed deterministic or optimization-based policies first.

Only add RL after H1-H3 are established.

---

# 30. Compute Feasibility

The core project is **not training-heavy**.

Major cost:

\[
\text{repeated LLM inference over many memory masks}.
\]

CPU-friendly components:

- coalition-mask generation;
- exact synthetic games;
- Shapley/Möbius estimation for small/moderate cases;
- graph construction;
- mask matching;
- statistics;
- optimization;
- plotting.

Therefore the project is feasible on:

- RTX 4050 laptop with 6 GB VRAM;
- Kaggle GPU notebooks;
- Google Colab;
- API inference, if desired.

The implementation must be backend-agnostic.

---

# 31. Local RTX 4050 6 GB Plan

Recommended development strategy:

- use a small instruction-tuned open model;
- target approximately 1.5B-2B parameters initially;
- use 4-bit quantization if needed;
- `batch_size=1`;
- short outputs;
- controlled context length;
- no model training.

Practical starting configuration:

```yaml
backend:
  type: hf_local
  model: configurable-small-instruct-model
  quantization: 4bit
  device: cuda

generation:
  do_sample: false
  max_new_tokens: 32

runtime:
  batch_size: 1
  checkpoint_every: 10
```

Do not hard-code the entire repository to one model family.

A 4B model may be usable in 4-bit quantization depending on implementation/context, but the research pipeline must first work on a smaller model.

---

# 32. Kaggle Plan

Use Kaggle primarily for:

- larger coalition sweeps;
- repeated inference;
- additional seeds;
- larger open models if accelerator memory permits.

Do not rely on a specific accelerator being permanently available.

At notebook startup:

1. detect accelerator;
2. print VRAM;
3. select model profile;
4. load existing cached results;
5. continue incomplete coalition evaluations.

All experiments must be resumable.

---

# 33. Google Colab Plan

Colab hardware is variable.

Therefore:

```python
if high_memory_gpu:
    use_medium_model()
elif standard_gpu:
    use_small_quantized_model()
else:
    run_symbolic_or_cpu_tests()
```

Never make experiment validity depend on receiving one particular GPU.

Colab sessions may terminate, so every expensive coalition evaluation must be checkpointed immediately.

---

# 34. Persistent Experiment Cache

Every model evaluation needs a deterministic cache key containing:

```text
model_id
model_revision
prompt_template_hash
memory_bank_id
query_id
coalition_mask
generation_config
seed
code_commit
```

Persist result:

```text
raw_output
parsed_action
reward
latency
input_tokens
output_tokens
timestamp
```

Use SQLite or Parquet.

Never keep the only copy of experiment results in notebook memory.

---

# 35. Backend Abstraction

Required interface:

```python
from abc import ABC, abstractmethod

class LLMBackend(ABC):
    @abstractmethod
    def generate(self, messages, **kwargs) -> str:
        ...
```

Backends:

```text
HFLocalBackend
OpenAICompatibleBackend
MockBackend
```

`MockBackend` is mandatory for unit/integration testing without GPU inference.

The theory code must never import a specific transformer model directly.

---

# 36. Recommended Repository

```text
hibermem/
│
├── README.md
├── pyproject.toml
├── MASTER_RESEARCH_PLAN.md
│
├── configs/
│   ├── local_4050.yaml
│   ├── kaggle.yaml
│   ├── colab.yaml
│   └── experiments/
│
├── src/hibermem/
│   ├── backends/
│   │   ├── base.py
│   │   ├── hf_local.py
│   │   ├── openai_compatible.py
│   │   └── mock.py
│   │
│   ├── memory/
│   │   ├── types.py
│   │   ├── store.py
│   │   └── budget.py
│   │
│   ├── environments/
│   │   └── synthetic/
│   │       ├── generator.py
│   │       ├── bank.py
│   │       ├── queries.py
│   │       └── evaluator.py
│   │
│   ├── coalition/
│   │   ├── game.py
│   │   ├── masks.py
│   │   └── cache.py
│   │
│   ├── interactions/
│   │   ├── discrete.py
│   │   ├── mobius.py
│   │   ├── shapley.py
│   │   └── stability.py
│   │
│   ├── retention/
│   │   ├── random.py
│   │   ├── recency.py
│   │   ├── semantic.py
│   │   ├── salience.py
│   │   ├── centrality.py
│   │   └── interaction.py
│   │
│   ├── lesions/
│   │   ├── random.py
│   │   ├── matched.py
│   │   └── structural.py
│   │
│   ├── evaluation/
│   │   ├── metrics.py
│   │   ├── survival.py
│   │   └── statistics.py
│   │
│   └── utils/
│       ├── seeds.py
│       ├── hashing.py
│       └── logging.py
│
├── scripts/
│   ├── run_phase0.py
│   ├── run_phase1.py
│   ├── run_phase2.py
│   ├── estimate_interactions.py
│   ├── run_retention.py
│   └── run_lesions.py
│
├── tests/
│   ├── test_interaction_sign.py
│   ├── test_mobius.py
│   ├── test_budget.py
│   ├── test_matching.py
│   ├── test_cache.py
│   └── test_split_leakage.py
│
├── notebooks/
│   ├── kaggle_runner.ipynb
│   └── colab_runner.ipynb
│
└── results/
```

---

# 37. Implementation Phases

# Phase 0 — Mathematical Correctness

## Goal

Verify every mathematical primitive before LLM use.

## Implement

- coalition masks;
- utility-game abstraction;
- exact discrete derivatives;
- exact Möbius coefficients for small games;
- pairwise interactions;
- third-order interactions;
- wrapper around chosen Shapley-interaction library;
- exact analytical tests.

## Deliverables

```text
src/hibermem/coalition/
src/hibermem/interactions/
tests/test_interaction_sign.py
tests/test_mobius.py
scripts/run_phase0.py
results/phase0_report.json
```

## Gate P0

All analytical interaction tests pass.

If not:

\[
\boxed{\text{STOP}}
\]

---

# Phase 1 — Deterministic Synthetic Interaction Recovery

## Goal

Validate that the estimator recovers known dependency structures.

## Dataset

20-100 synthetic coalition games.

Include:

- additive;
- pair synergy;
- pair redundancy;
- triple synergy;
- distractors;
- noisy reward;
- conflicting variables.

## Metrics

- sign accuracy;
- precision@k;
- recall@k;
- Spearman rank correlation;
- mean absolute interaction error;
- calibration of uncertainty/stability.

## Gate P1

The estimator must reliably distinguish individual contribution from interaction contribution.

This gate validates methodology, not the HiberMem hypothesis.

---

# Phase 2 — Minimal LLM Coalition Game

## Goal

Determine whether measurable interactions appear in LLM-mediated external memory use.

## Initial scale

```text
10 memory banks
8 memories per bank
20 discovery queries
10 validation queries
20 test queries
```

Use a small local model first.

## Coalition evaluation

For \(n=8\):

\[
2^8=256
\]

coalitions are feasible for selected banks.

Exact enumeration is useful for the first few banks.

## Compare

- random;
- item-value retention;
- interaction-aware retention.

## Deletion ratios

\[
0, 0.25, 0.50, 0.70, 0.80.
\]

## Gate P2-A — Interaction stability

Top interaction estimates must be more stable than random ranking.

## Gate P2-B — Preliminary survival signal

Interaction-aware retention should show a meaningful, repeatable advantage at severe deletion before scaling.

A small unstable gain is not enough.

---

# Phase 3 — Matched Structural Lesion

## Goal

Test whether interaction destruction causes extra behavioral damage after controlling individual utility.

## Implement matching on

- number of deleted memories;
- payload token count;
- estimated \(\phi_i\);
- recency;
- frequency;
- semantic centrality.

## Separation variable

\[
J(D_s)\gg J(D_c).
\]

## Test

Locked final queries only.

## Gate P3 — Core Go/No-Go

GO if:

- \(D_s\) consistently causes more damage than \(D_c\);
- effect survives matched item contribution;
- result is robust across independent memory banks;
- confidence interval/effect distribution does not suggest a one-bank artifact.

STOP/PIVOT if:

\[
\Delta_{\text{interaction}}\approx 0
\]

or reverses.

This is the most important gate in the project.

---

# Phase 4 — Scale and Strong Baselines

Only after Phase 3 passes.

Scale toward:

```text
>= 30 independent banks
20-50 memories per bank
256-1024 sampled coalitions per bank
>= 5 corruption masks per deletion ratio
```

Add baselines:

- recency;
- retrieval frequency;
- semantic coreset;
- graph centrality;
- functional co-use;
- strong item Shapley/value retention.

Evaluate:

\[
k=1
\]

vs

\[
k=2
\]

vs optionally

\[
k=3.
\]

Question:

> Does higher-order interaction complexity actually earn its computational/storage cost?

---

# Phase 5 — External Benchmark Validation

Order:

1. LoCoMo-Plus subset;
2. LongMemEval;
3. LongMemEval-V2;
4. optional structured-memory benchmark.

Important:

At first, use the **same retrieval mechanism for all retention policies**.

Do not combine new retention and new retrieval in one comparison.

---

# Phase 6 — Full HiberMem Architecture

Only now implement:

- persistent episodic memory;
- functional interaction graph/hypergraph;
- consolidation;
- structural retention;
- structural retrieval;
- turnover episodes;
- metadata accounting.

At this point the system can appropriately be called HiberMem.

Before this point the repository is fundamentally a causal memory-interaction study.

---

# Phase 7 — Repeated Hibernation / Turnover

Run cycles:

\[
\text{learn}
\rightarrow
\text{consolidate}
\rightarrow
\text{delete/compress}
\rightarrow
\text{learn}
\rightarrow
\dots
\]

Measure:

- memory-dependent retention \(R_t\);
- interaction persistence;
- interaction emergence;
- interaction disappearance;
- cumulative drift;
- reconsolidation after repeated successful reuse.

This phase evaluates lifelong memory rather than one-shot deletion.

---

# Phase 8 — Topology-Specific Intervention

If pairwise interaction graphs are meaningful, test topology directly.

Keep approximately constant:

- nodes;
- payload;
- number of edges;
- degree sequence;
- edge-weight distribution.

Use degree-preserving rewiring / double-edge swaps to destroy specific topology while preserving generic graph statistics.

Question:

> Does the identity of the interaction topology matter, not merely edge count or centrality?

---

# Phase 9 — Optional Regrowth

Only after the survival hypothesis is established.

Compare:

- no regrowth;
- generic LLM reconstruction;
- semantic-neighbor reconstruction;
- structure-conditioned reconstruction.

Require:

- provenance;
- evidence support;
- faithfulness scoring;
- separate functional and textual recovery metrics.

Do not let Phase 9 become necessary for H1-H3.

---

# 38. Experimental Leakage Rules

Codex must implement automated leakage tests.

Forbidden:

- interaction fitting on final test queries;
- tuning \(\epsilon\) or \(\gamma\) on final test;
- selecting deletion masks using final outcomes;
- selecting "good-looking" banks after observing final effects;
- changing prompts after inspecting final failures;
- using one method's retrieval budget differently from another;
- changing context length between methods.

Required unit test:

```text
tests/test_split_leakage.py
```

It should fail if test identifiers are passed to discovery/optimization modules.

---

# 39. Reproducibility Requirements

Every run records:

```text
git commit
dirty working-tree state
experiment config
Python version
package versions
CUDA version
GPU
model ID
model revision
quantization
prompt hash
dataset/bank version
seeds
coalition masks
lesion masks
timestamps
latency
token counts
```

All results must be reconstructable from saved configs + source commit.

---

# 40. Deterministic Generation Policy

For core experiments prefer:

```text
do_sample = false
short constrained output
```

Use exact action-label parsing where possible.

Even greedy model execution may not be perfectly reproducible across hardware/backends, so repeat key conditions across:

- memory banks;
- seeds where relevant;
- eventually more than one backbone.

Do not introduce stochastic generation unless the research question requires it.

---

# 41. Required Unit/Integration Tests

Minimum:

```text
test_additive_interaction_zero
test_and_interaction_positive
test_or_interaction_negative
test_triple_interaction
test_dummy_player
test_permutation_invariance
test_exact_vs_library
test_budget_counts_metadata
test_mask_roundtrip
test_cache_key_uniqueness
test_cache_resume
test_discovery_test_isolation
test_matched_lesion_constraint
test_zero_memory_metric
test_full_memory_metric
```

Expected metric checks:

\[
R(0)=1
\]

if \(A_{\mathrm{full}}\ne A_{\emptyset}\).

If:

\[
A_{\mathrm{full}}=A_{\emptyset},
\]

the external memory adds no measurable baseline value and normalized retention is undefined; report this rather than dividing by zero.

---

# 42. Codex Operating Rules

Codex must follow these rules:

1. Implement exactly one research phase at a time.
2. Do not implement later phases until current tests and scientific gate pass.
3. Never use final test data for discovery, tuning, retention optimization, or lesion construction.
4. Cache every expensive inference.
5. Keep theory/math code independent of LLM backend.
6. Every new mathematical function needs a deterministic unit test.
7. No RL before Phase 6+.
8. No regrowth before Phase 9.
9. No custom graph retrieval in the primary causal experiment.
10. Every retention method obeys the same total serialized memory budget.
11. Record full experiment provenance.
12. Never silently alter thresholds after observing final results.
13. Preserve negative results.
14. Do not delete failed experiment outputs.
15. Do not claim "engram" evidence unless H2/H3 pass.
16. Do not claim "fault tolerance" without exogenous fault experiments.
17. Do not call a graph structure causal merely because it correlates with performance.
18. Report metadata/storage overhead.
19. Prefer simple exact evaluations before complex approximation.
20. Stop when a falsification gate fails.

---

# 43. Codex Pre-Implementation Review Task

Before writing substantive code, Codex should independently review this document and produce:

## A. Theory audit

For each mathematical claim:

```text
VALID
VALID WITH ASSUMPTIONS
QUESTIONABLE
INVALID
```

Provide reasoning and references.

Check specifically:

- interaction sign;
- discrete derivative definition;
- Shapley interaction applicability;
- low-order approximation assumptions;
- matched lesion interpretation;
- normalized retention metric;
- statistical unit.

## B. Novelty audit

Search current 2024-August 2026 literature.

Determine whether any existing work already performs:

1. higher-order interaction estimation over external LLM memories;
2. item-utility-matched structural lesions;
3. prospective held-out validation of learned memory interaction structure;
4. survival curves under controlled interaction destruction.

If yes, identify exactly where HiberMem overlaps.

Do not rely on titles/abstracts alone when a claim is central.

## C. Experimental audit

Attempt to find:

- target leakage;
- circularity;
- retrieval confounds;
- storage-budget confounds;
- prompt-length confounds;
- pseudoreplication;
- synthetic-task triviality;
- interaction-estimator bias;
- model-prior confounds.

## D. Compute audit

Confirm the Phase 0-3 workloads can run on:

- local RTX 4050 6GB;
- Kaggle;
- Colab.

If not, propose the smallest modification that preserves experimental validity.

## E. Implementation audit

Review repository/module boundaries.

Flag anything that mixes:

- data generation with evaluation;
- test data with training/discovery;
- model inference with interaction math;
- retention with retrieval.

---

# 44. Codex Approval Criteria

Codex should only approve implementation if all are true:

- [ ] mathematical sign error is corrected;
- [ ] exact analytical tests are specified;
- [ ] discovery/test split prevents outcome leakage;
- [ ] interaction-aware and item-aware retention are distinctly defined;
- [ ] matched lesions control individual memory utility;
- [ ] all surviving memories can be passed directly in the primary causal experiment;
- [ ] normalized survival metric includes zero-memory baseline;
- [ ] graph metadata counts toward storage;
- [ ] independent unit is bank/environment;
- [ ] falsification gates are explicit;
- [ ] Phase 0-3 fit practical compute;
- [ ] regrowth/RL are deferred;
- [ ] literature novelty still exists after current search.

---

# 45. Initial Minimal Experiment

The first LLM experiment should be intentionally small.

```text
Memory banks:        10
Memories/bank:       8
Discovery queries:   20
Validation queries:  10
Test queries:        20
Interaction order:   2
Model:               small open instruct model
Generation:          deterministic/greedy
Retention methods:   Random / Item / Interaction
Deletion ratios:     0 / 0.25 / 0.50 / 0.70 / 0.80
```

Then immediately run an item-value-matched structural lesion.

No:

```text
graph retrieval
RL
regrowth
lifelong cycles
large benchmarks
```

until this passes.

This experiment must be capable of falsifying the central premise.

---

# 46. Go / No-Go Decision Tree

```text
P0 math tests fail?
    YES -> fix theory/implementation; do not continue
    NO
      |
P1 controlled interaction recovery fails?
    YES -> estimator/method invalid; stop or redesign
    NO
      |
P2 stable LLM interactions absent?
    YES -> structural hypothesis weak; investigate model/task dependence
    NO
      |
P3 matched structural lesion gives no extra damage?
    YES -> central HiberMem hypothesis unsupported -> pivot
    NO
      |
P4 interaction-aware retention survives strong baselines?
    NO -> causal effect may exist but system contribution weak
    YES
      |
P5 external benchmark replication?
    NO -> mechanism may be synthetic/domain-specific
    YES
      |
Build full HiberMem
```

---

# 47. What Would Falsify the Project

The following are legitimate negative outcomes:

1. Individual item value predicts survival as well as interactions.
2. Item-matched interaction lesions cause no extra damage.
3. Interactions discovered on past tasks do not generalize to future tasks.
4. Pairwise/higher-order estimates are too unstable to exploit.
5. Benefits disappear after structural metadata is counted.
6. Gains exist only in synthetic tasks explicitly constructed to require interactions.
7. Benefits disappear under a different LLM family.
8. Interaction estimation cost is larger than the practical memory-saving benefit.

Any of these should materially weaken the paper's central claim.

A good experiment is one that is allowed to fail.

---

# 48. What Would Strongly Support the Project

A high-impact result would look like:

1. Item contribution is carefully estimated.
2. Two deletion masks remove equal item utility and equal storage.
3. One destroys much more functional interaction mass.
4. The high-interaction lesion causes substantially greater held-out performance loss.
5. The effect repeats across independent banks and more than one model.
6. Interaction-aware retention preserves significantly more normalized memory-dependent behavior at severe deletion.
7. The result persists when graph metadata and inference cost are counted.
8. Similar behavior appears on at least one natural long-term-memory benchmark.

This would support the claim that:

> memory robustness depends on more than which individual memory items survive.

---

# 49. Paper Positioning if Successful

Preferred framing:

> We causally study whether higher-order interactions among external memories form an independently measurable substrate of long-term agent behavior.

Avoid framing:

> We mimic hippocampal engrams in LLMs.

Avoid framing:

> We introduce a new graph memory.

Avoid framing:

> We introduce a new forgetting mechanism.

Potential title:

**What Survives Forgetting? Causal Interaction Structure in Long-Term Agent Memory**

Alternative:

**Beyond Memory Importance: Higher-Order Interactions in Fault-Tolerant LLM Agent Memory**

System name:

**HiberMem**

---

# 50. Reference Checklist for Codex Verification

Codex must independently verify the exact bibliographic metadata before citation.

Key targets:

1. Lin et al. (2026), artificial hibernation / synaptic engram architecture and memory retention, Science.
2. Xiong et al. (ACL 2026), memory management / memory deletion and experience-following behavior.
3. Memory-R1 (ACL 2026).
4. AgeMem / Agentic Memory (ACL 2026).
5. GAM (ACL 2026).
6. MAGMA (ACL 2026).
7. Mnemis (ACL 2026).
8. LoCoMo (ACL 2024).
9. LongMemEval (ICLR 2025).
10. LoCoMo-Plus (ACL 2026).
11. LongMemEval-V2 (2026).
12. Shapley-Taylor Interaction Index.
13. Faithful Shapley interaction literature.
14. Sparse higher-order interaction recovery / Möbius representations where relevant.
15. StructMemEval or related structured-memory evaluations.

Codex should add or remove references if newer work materially changes novelty.

---

# 51. Final Instruction to Codex

**Do not begin by implementing HiberMem as a large agent framework.**

First attempt to disprove its foundational claim.

Your first responsibility is to verify:

\[
\boxed{
\text{Does higher-order memory interaction carry reproducible predictive and causal value}
}
\]

\[
\boxed{
\text{beyond individual memory importance?}
}
\]

Only after the answer is convincingly yes should you invest in:

- graph/hypergraph consolidation;
- retrieval;
- repeated hibernation;
- lifelong memory management;
- learned policies;
- regrowth.

The priority order is:

\[
\boxed{
\text{theory}
\rightarrow
\text{unit validation}
\rightarrow
\text{controlled causal evidence}
\rightarrow
\text{external validity}
\rightarrow
\text{system engineering}
}
\]

not:

\[
\boxed{
\text{system engineering first}
}
\]

This order minimizes compute waste, reduces confirmation bias, and makes the resulting study much more defensible as serious Computer Science / Cognitive AI research.

---

# 52. Current Quick-Validation Verdict

**Theory:** viable after correcting the pairwise interaction sign and replacing naive graph assumptions with a coalition-interaction formulation.

**Causal design:** viable only with strict discovery/test separation and item-value-matched structural lesions.

**Novelty:** deletion, graph memory, consolidation, and biologically inspired forgetting are individually insufficient; the strongest plausible novelty is causal higher-order interaction structure under matched destruction.

**Statistics:** use memory bank/environment as the primary independent unit; avoid query-level pseudoreplication.

**Metrics:** normalized memory-dependent survival is preferable to raw accuracy AUC.

**Compute:** Phase 0-3 is feasible on a 6 GB RTX 4050 with a small local model; Kaggle/Colab are suitable for scaling repeated inference.

**Engineering:** backend abstraction, caching, experiment provenance, and leakage tests are mandatory.

**Decision:** proceed to Phase 0 only after Codex independently audits this master specification.

