# HiberMem adversarial research audit — 2026-08-31

Archived audit and correction roadmap. This is a point-in-time assessment made
before the implementation described in [the next-experiment plan](NEXT_EXPERIMENT_IMPLEMENTATION_PLAN_2026-08-31.md).
Historical results and qualification decisions are not changed by later code work.

## 1. Executive Summary & Audit Verdict

**ACL readiness: 3/10.** This is an assessment of the current evidence, not an
acceptance probability.

HiberMem has a credible experimental foundation, but its central claim remains
unverified:

> Do interactions estimated from past queries improve future behavior under severe
> memory deletion, beyond strong individual-memory baselines?

The [master plan](../HiberMem_MASTER_RESEARCH_IMPLEMENTATION_PLAN.md) asks this
question. It does not currently implement the hyperbolic retrieval architecture
assumed in the audit request. No Poincare/Lorentz embedding pipeline, geometric
optimizer, hierarchical consolidation system, or FAISS–graph fusion implementation
was found to certify. These are absent components, not demonstrated defects.

The consequential findings are:

- Exact discrete derivatives, Mobius decomposition, and Shapley interaction
  weighting are mathematically consistent.
- Quadratic regression coefficients are not generally exact interactions of the
  underlying game. A counterexample was reproduced with the actual estimator.
- All three v2 model screens remain negative. Gemma's supported-answer accuracy
  does not overcome its missing-link failures.
- Qwen nevertheless exhibits strong local complementarity: mean two-link
  interaction **0.933**, versus **0.017** for Phi. Screen failure must not be
  interpreted as absence of interactions.
- Useful retention remains unproven: the earlier pilot's severe-deletion advantage
  over its item-value baseline is **1 percentage point**, with an exploratory
  bank-bootstrap interval of **−3 to +5 points**.
- The decisive matched structural-lesion experiment has not been completed.

The Qwen/Phi artifacts were independently revalidated and statistics recomputed.
Gemma was assessed from the pasted report; its raw bundle was unavailable locally.
The audit itself changed no files or gates and did not rerun GPU inference.

## 2. Mathematical & Geometric Proofs & Instability Analysis

### 2.1 Correct discrete interaction definition

For a fixed model, rendering protocol, and query distribution D, define

\[
v_D(S)=\mathbb E_{q\sim D}[r(q,S)],
\]

with every evaluation starting without information from other coalitions. Then

\[
\Delta_{ij}v(S)=v(S\cup\{i,j\})-v(S\cup\{i\})-v(S\cup\{j\})+v(S).
\]

[discrete.py](../src/hibermem/interactions/discrete.py) implements this definition.
At the full-memory context:

\[
\Delta_{ij}v(N\setminus\{i,j\})=v(N)-v(N-i)-v(N-j)+v(N-i-j).
\]

AND gives +1, OR gives −1, and an additive game gives 0. These are behavioral
properties of the reward. Positive interaction is not semantic similarity;
negative interaction does not uniquely distinguish redundancy from interference.

### 2.2 Distinguish exact Mobius, SII, and surrogate coefficients

\[
m(T)=\sum_{U\subseteq T}(-1)^{|T|-|U|}v(U),\qquad
v(S)=\sum_{T\subseteq S}m(T),\qquad
\phi_i(v)=\sum_{T\ni i}\frac{m(T)}{|T|}.
\]

The implemented Shapley interaction index is

\[
I_T^{\mathrm{SII}}=\sum_{S\subseteq N\setminus T}
\frac{|S|!(n-|T|-|S|)!}{(n-|T|+1)!}\Delta_Tv(S).
\]

The total weight at each context size is 1/(n−|T|+1), so the weighting is
normalized. However,

\[
I_T^{\mathrm{SII}}=\sum_{U\supseteq T}\frac{m(U)}{|U|-|T|+1}.
\]

SII and Mobius coefficients are not interchangeable, and neither should be casually
identified with [Shapley–Taylor](https://proceedings.mlr.press/v119/sundararajan20a.html)
or [Faith-Shap](https://jmlr.org/papers/v24/22-0202.html).

### 2.3 Principal mathematical risk: truncated quadratic approximation

The estimator fits

\[
\widehat v(S)=\beta_\emptyset+\sum_i\beta_i x_i+\sum_{i<j}\beta_{ij}x_ix_j.
\]

If the true game is v=X_2 beta+X_{>2} gamma, full-rank least squares gives

\[
\widehat\beta=\beta+(X_2^\top X_2)^{-1}X_2^\top X_{>2}\gamma.
\]

The second term is omitted-order contamination. Evaluating every coalition does
not remove it. For v=x1*x2*x3, fitting all eight coalitions gives

\[
\widehat v=\frac18-\frac14(x_1+x_2+x_3)
+\frac12(x_1x_2+x_1x_3+x_2x_3).
\]

True singleton/pair Mobius coefficients are zero, but fitted singleton terms are
−1/4 and fitted pair terms are 1/2. True Shapley values are 1/3 per item; surrogate
Shapley values are 1/4. For a four-way AND, fitted pairs are 1/4 while exact pair SII
is 1/3. These were verified using the repository estimator.

The current retention code correctly computes Shapley values **of the fitted
surrogate**. The error would be interpreting them as exact values of the observed
LLM game. There is also an API hazard: `individual_values()` means singleton
coefficients for the polynomial estimator but Shapley values for the exact one.

### 2.4 Selection is combinatorial, not generally submodular

The policy exhaustively maximizes the fitted polynomial over fixed-size subsets.
For a quadratic function,

\[
f(S\cup\{i\})-f(S)=\beta_i+\sum_{j\in S}\beta_{ij}.
\]

Submodularity requires decreasing marginal gains, hence all pair coefficients
must be nonpositive. Positive synergy violates this condition. No generic
submodular greedy approximation guarantee follows for signed interactions.
Describe the method as exact small-bank combinatorial optimization of a surrogate.

### 2.5 Query-shift stability is conditional

For rewards in [0,1], g(q)=Delta_ij r(q,S) lies in [−2,2]. Thus, for a fixed model
and rendering protocol,

\[
|I_{ij}(D)-I_{ij}(D')|\leq4\,\mathrm{TV}(D,D').
\]

Large query shifts permit large interaction changes. Switching from an AND task
to an OR task changes interaction from +1 to −1. Paraphrase agreement alone cannot
establish stability across future dependency or task shifts.

### 2.6 Conditional geometric requirements, not observed geometric defects

No relevant geometric implementation exists in the inspected project. If added,
curvature −c, c>0, defines the ball c||x||^2<1. Under the standard conformal convention,

\[
\exp_0^c(v)=\frac{\tanh(\sqrt c\|v\|)}{\sqrt c\|v\|}v,\qquad
\log_0^c(x)=\frac{\operatorname{artanh}(\sqrt c\|x\|)}{\sqrt c\|x\|}x.
\]

Use continuous limits at zero. General maps and parallel transport must respect
the position-dependent metric. [Hyperbolic Neural Networks](https://arxiv.org/abs/1805.09112).

For x=alpha*u, y=alpha*v and unit u,v,

\[
d_c(x,y)=\frac1{\sqrt c}\operatorname{arcosh}
\left(1+\frac{4c\alpha^2(1-u^\top v)}{(1-c\alpha^2)^2}\right).
\]

This is monotonic in cosine distance. Mapping equal-norm embeddings to an
equal-radius hyperbolic shell does not change nearest-neighbor ranking.

Boundary sensitivity follows from

\[
d_c(0,x)=\frac2{\sqrt c}\operatorname{artanh}(\sqrt c r),\qquad
\frac{\partial d_c(0,x)}{\partial r}=\frac2{1-cr^2}.
\]

Float64 increases numerical headroom, not immunity to the singularity. Lorentz
coordinates instead require <X,X>_L=−1/c, X0>0, with

\[
d_L(X,Y)=\frac1{\sqrt c}\operatorname{arcosh}(-c\langle X,Y\rangle_L).
\]

Large-coordinate cancellation and invalid inverse-hyperbolic arguments still need
tests. [Nickel and Kiela, 2018](https://proceedings.mlr.press/v80/nickel18a.html).
Symmetric distance cannot itself encode directed parent–child or temporal relations;
directional constraints or explicit labels are needed.
[Hyperbolic Entailment Cones](https://proceedings.mlr.press/v80/ganea18a.html).

## 3. Methodology & Architecture Critique (Failure Modes & Flaws)

### 3.1 Consolidation and catastrophic forgetting are untested

The experiments delete external records; they do not train a continual-learning
model or consolidate episodes into learned nodes. They demonstrate neither
catastrophic forgetting nor successful consolidation.

If a future compressor C maps M1 and M2 to the same summary but a future query
requires different answers, no decoder given only C(M) and that query can answer
both correctly. Probe preservation of rare relations, timestamps, negations,
corrections, and other task-relevant information—not generic summary quality.

Deleting a source while retaining its answer in a summary is not deletion of that
information. Summaries, graph attributes, embeddings, and recovery stores must
count toward retained storage.

### 3.2 Documentwise ranking does not guarantee complementary selection

No RRF/geometric retrieval code exists to audit. The prospective limitation is
constructive:

\[
v(S)=\mathbf1[\{a,b\}\subseteq S]+0.4\mathbf1[c\in S]+0.4\mathbf1[d\in S].
\]

With two slots, singleton ranking selects c,d for 0.8; a,b yield 1. Documentwise
rank fusion has no general guarantee for interacting set rewards. Measure both
complete-evidence candidate recall and subsequent subset selection. A selector
cannot recover a required item excluded from its candidate pool.

### 3.3 Deletion changes presentation too

The observed game depends on retained facts, token positions, length, and format.
Deletion effects can therefore combine informational dependency and presentation.
Order and identifier permutations, plus separately reported fixed-layout versus
actual-deletion experiments, are needed. Padding is itself an intervention.
[Lost in the Middle](https://aclanthology.org/2024.tacl-1.9/) documents position
sensitivity in long contexts, not a proven explanation of these short-ledger failures.

### 3.4 Current complexity is small-bank, not production-scale evidence

For B banks, Q queries and n memories, exact evaluation costs B*Q*2^n calls.
Quadratic fitting has p=1+n+n(n−1)/2 terms; current selection enumerates C(n,k)
subsets. This is suitable for eight-item mechanism tests, not an O(N) architecture.

`MemoryItem.storage_tokens` is explicitly a whitespace proxy. Real inference token
counts are also logged, but total budget claims must include payload, index,
interaction representation, summaries, and permitted recovery state. GPU accounting
must include weights, activations, and KV cache. Loading on two T4s does not certify
latency or throughput.

## 4. Empirical Verification of Kaggle Execution Results

### 4.1 Revalidated v2 evidence

Local Qwen and Phi bundles passed independent artifact validation. Gemma below
comes from the pasted report, not an independently checked local bundle.

| Metric | Qwen | Phi | Gemma |
|---|---:|---:|---:|
| Full direct accuracy | 100% | 100% | 100% |
| Full two-hop accuracy | 93.33% | 77.50% | 97.50% |
| Pair-only accuracy | 100% | 100% | 100% |
| Full overall accuracy | 96.67% | 88.75% | 98.75% |
| Passing-bank fraction | 80% | 20% | 90% |
| Counterfactual full-pair success | 78.33% | 55.83% | 96.25% |
| Counterfactual missing-pair abstention | 53.75% | 56.25% | 50.42% |
| Development qualification | FAIL | FAIL | FAIL |

Full-pair success requires correct answers in both worlds. The locked missing-pair
abstention threshold is 90%; all models miss it substantially. Scientific negative
screens are not crashed inference runs. Artifact consistency and qualification are
different properties.

### 4.2 New local-complementarity finding

Matched base two-hop queries permit

\[
I_{local}=v(\{a,b\})-v(\{a\})-v(\{b\})+v(\emptyset).
\]

For Qwen/Phi, 120 queries were grouped into ten banks, then bank means were
bootstrapped with 10,000 resamples (seed 20260830).

| Model | Mean local interaction | Exploratory 95% bank-bootstrap interval |
|---|---:|---:|
| Qwen | 0.9333 | [0.8667, 1.0000] |
| Phi | 0.0167 | [−0.0333, 0.0667] |
| Gemma, implied by aggregate metrics | 0.1167 | Unavailable without raw rows |

Gemma's implied contrast is 1−0.78333−0.10+0=0.11667. Qwen generally needs both
links for correctness, whereas Phi/Gemma often answer correctly without the first
link. In that minimal condition the second record contains the target destination;
copying it can succeed without recovering the missing relation.

These screens contain local interaction evidence, but no evidence of stable global
rankings or superior prospective retention. Intervals are exploratory and not
adjusted for adaptive experiment/model selection.

### 4.3 Gemma: high supported accuracy, weak missing-evidence behavior

- Missing-first minimal accidental correctness: 78.33%.
- Missing-second minimal abstention: 0%.
- Missing-second contextual abstention: 0.83%; parse-null: 24.17%; unsupported
  assertion: 75%.

For counterfactual worlds with X(w1)=X(w2) but y(w1)!=y(w2), a deterministic model
must give the same output and can be correct in at most one world: average accuracy
is at most 1/2. This proves non-identifiability from the missing input, not that a
useful model necessarily abstains or that all interactions vanish. Analyze
answerability and interaction strength separately without rewriting v2 gates.

### 4.4 Pilot severe-deletion result

Recomputed with `scripts/analyze_phase2_public.py` from the public pilot:

| Actual deletion | Interaction | Item | Difference |
|---|---:|---:|---:|
| 62.5% | 28% | 28% | 0 points |
| 75% | 28% | 26% | +2 points |

Mean within-bank severe effect is 0.01, 95% exploratory interval [−0.03,0.05]. Four
banks improve, three tie, three worsen. Nominal 70%/80% become actual 62.5%/75%.
The comparator uses surrogate Shapley; exact values can be reconstructed for only
two pilot banks with complete discovery tables. This is not a demonstrated win
against exact Shapley.

### 4.5 In-sample R-squared is not future stability

Mean discovery R2 is 0.4818 additive versus 0.6812 quadratic. The designs are nested,
so SSE_quadratic<=SSE_additive mechanically. Future-query coalition utilities must
be collected independently and predicted with frozen discovery fits.

### 4.6 Leakage, uncertainty, provenance, and metrics

Query authorization precedes cache access; requests and scoring are fingerprinted.
These protect against accidental split misuse, not all contamination:

1. Prefix/paraphrase splits reuse underlying facts and chains.
2. Repeated model/prompt selection makes inspected banks development data.
3. Shared conversation history across coalitions can preserve deleted facts;
   evaluations must reset between conditions.
4. Random identifiers reduce memorization shortcuts but cannot certify absence of
   all pretraining contamination.

The individual-query bootstrap ignores grouping by dependency when estimating
generalization to new facts. For m equally correlated observations,

\[
\operatorname{Var}(\bar X)=\frac{\sigma^2}{m}[1+(m-1)\rho].
\]

2,160 condition rows and repeated cache hits are not 2,160 independent observations.
Use paired bank/dependency-aware inference.
[Dror et al., 2018](https://aclanthology.org/P18-1128/).

The source fingerprint covers repository code and selected metadata, not arbitrary
notebook-side adapters. Preserve Gemma's runner, processor/chat template, settings,
and unprocessed outputs. A consistent report does not prove which executable made
the outputs. Macro-F1 over randomized destination IDs does not solve this. Report
accuracy alongside answerability, abstention, unsupported assertions, formatting,
and per-bank effects.

## 5. ACL Novelty & Related Work Positioning

| Prior work | Established contribution | Required HiberMem distinction |
|---|---|---|
| [Shapley–Taylor](https://proceedings.mlr.press/v119/sundararajan20a.html), [Faith-Shap](https://jmlr.org/papers/v24/22-0202.html) | Interaction attribution | New memory evidence, not renamed mathematics |
| [ContextCite](https://arxiv.org/abs/2409.00729) | Context attribution | Prospective usefulness under deletion |
| [Source Attribution in RAG](https://arxiv.org/abs/2507.04480) | Shapley, removal effects, inter-document dependencies | Stable past-to-future structure and matched retention benefit |
| [RAPTOR](https://arxiv.org/abs/2401.18059) | Recursive clustering and multilevel summaries | Robustness at matched retained-information cost |
| [GraphRAG](https://arxiv.org/abs/2404.16130) | Entity graph/community-summary QA | Functional interactions rather than another KG |
| [Contextual Retrieval](https://www.anthropic.com/engineering/contextual-retrieval) | Context-enriched lexical/dense retrieval | Benefit beyond retrieval and extra context |
| [HELM](https://arxiv.org/abs/2505.24722) | Hyperbolic LM architecture | Separate topic; pretrained readers are not geometric innovation |

No reliable primary publication was identified under the exact acronym HiAGRN.
Do not conflate it with another system without a title/reference.

The strongest prospective contribution is that past-query interactions predict
which combinations must survive future deletion, with benefits after controlling
individual contributions and storage. Interaction existence does not imply
persistence, which does not imply improved selection. Only the first has restricted
positive evidence. This targeted search does not establish priority for the narrow
prospective claim. First-use-of-Shapley, graph memory, and hyperbolic representation
claims are not supported novelty positions.

## 6. Concrete Corrections & Mathematical/Implementation Plan

### Priority 0 — Preserve negatives and complete provenance

Keep v2 outcomes unchanged and confirmation/test locked. Archive Gemma's runner,
model/processor revisions, rendered template hash, actual dtypes/devices, token IDs,
decoded output, processed output, and explicit thinking settings. Unsupported
settings must not silently fall back. New benchmark/gate policies require new
versions and fresh evidence.

### Priority 1 — Explicit estimator semantics

Separate Mobius coefficients, SII, singleton coefficients, and Shapley item values.
Label surrogate quantities. Add three-/four-way AND counterexamples and exact
reconstruction/null/additive/redundancy tests. For X=U Sigma V^T use

\[
\widehat{Cov}(\hat\beta)=\hat\sigma^2 V\Sigma^{-2}V^\top
\]

instead of forming X^T X, whose condition number is squared. The coefficient solve
already uses `lstsq`. For scientific uncertainty bootstrap banks/dependencies; use
a preregistered meaningful effect size and address multiplicity. 1e−8 is numerical,
not a practically meaningful interaction threshold.

### Priority 2 — Bounded exact-coalition mechanism experiment

Start development-only with two fresh eight-item banks and four distinct two-hop
queries each: 2*4*256=2,048 conditions before cache reuse. Compute exact Mobius,
Shapley, SII and surrogate errors from the same table. Qwen is a reasonable diagnostic
candidate because of its local contrast, not because it passed qualification.
Then vary context, memory order, option order, identifiers, unrelated destinations,
and independent chains/query forms.

### Priority 3 — Semantic overlap versus dependency

Cross low/high semantic overlap with absent/present functional dependency. Add
OR duplicates, AND dependencies, three-way chains, conflict, temporal updates,
null items, and misleading overlap. A similarity detector must not be mistaken
for a functional-interaction estimator.

### Priority 4 — Freeze prospective evaluation

```python
protocol = freeze_protocol_on_development_data()
for bank in fresh_confirmation_banks:
    past, future = construct_preregistered_query_streams(bank)
    rewards = evaluate_coalitions(bank, past, reset_history_between_conditions=True)
    exact_game = aggregate_past_rewards(rewards)
    exact_items = exact_shapley(exact_game)
    interaction_model = fit_locked_interaction_model(rewards)
    selections = build_all_baseline_and_interaction_masks(
        exact_items, interaction_model, budgets=protocol.budgets)
    freeze(selections)
    outcomes = evaluate_frozen_masks(bank, future, selections)
analyze_paired_bank_effects(outcomes)
```

Distinguish paraphrase, compositional, dependency-family, and temporal shifts. Use
frozen past fits to compute future R2; allow negative R2 and mark constant-target
cases undefined. Do not refit on future queries.

### Priority 5 — Strong baselines and primary endpoint

Compare exact Shapley, additive regression, leave-one-out, budget-conditioned item
utility, multiple random seeds, applicable semantic/retrieval ranking, interaction
selection, shuffled interactions, and a labeled oracle upper bound. Operational
methods use past information and comparable estimation budgets; test tie-breaking.

For actual rho>0.5 define a preregistered average paired bank difference D_b across
budgets. Use bank-level inference and meaningful effects. An illustrative normal
power approximation is B=((1.96+0.84)*sigma_D/delta)^2: sigma_D=.10 and delta=.03
suggest about 88 banks, not ten. Estimate variance before confirmation; this is not
a guarantee or a fixed required sample size.

### Priority 6 — Matched structural lesions

Match deleted/retained count, payload cost, individual utility, recency/frequency,
and relevant semantic properties. Separate sets by predicted interaction destruction
using past information only. Evaluate a separately reserved future cohort. Do not
select lesions using future outcomes. Reproducible failure requires narrowing or
rejecting the structural claim.

### Priority 7 — Scale after mechanism and lesion evidence

Then extend to [LongMemEval](https://arxiv.org/abs/2410.10813) and
[LoCoMo](https://aclanthology.org/2024.acl-long.747/) with source-level deletion,
answer-key checks, and matched information costs. Add lexical/dense, long-context,
summary, and graph baselines, plus indexing/estimation cost, peak VRAM, cold/warm
latency. Geometry is an optional separate ablation; test map round trips, manifold
constraints, transport norms, curvature changes, and float32/float64 references.

The next milestone is a reproducible prospective effect surviving exact item-value
baselines and matched deletion—not another high full-memory score. No checklist
guarantees ACL acceptance.
