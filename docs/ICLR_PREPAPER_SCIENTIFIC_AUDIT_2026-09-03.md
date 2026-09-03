# HiberMem pre-paper scientific audit — 2026-09-03

**Decision status:** evidence-bounded reconstruction complete. The project is not
ready to claim an interaction-aware retention advantage. E3d is the next eligible
development diagnostic; E4, E5, confirmation, and the historical Phase-2 test remain
blocked.

**Audit basis:** repository revision a6c76f20e856618506dee76a9d05fae2f4da48a5,
the independently validated artifacts referenced in HANDOFF.md, source code and
configuration, 197 passing tests before this audit, and primary literature available
through 2026-09-03. The untracked gemini_docs/ and gemini/ directories were treated
as a professional critic's report, not as an authority or a source of results.

---

# 1. Executive verdict

The scientifically defensible project is narrower than the original HiberMem vision:

> Test whether interaction structure estimated from past interventions over external
> memory records improves fixed-budget selection and predicts sign-aware lesion damage
> on genuinely held-out future tasks, beyond strong item-only methods.

This is a coherent and falsifiable question. It is not yet an empirical contribution.
The repository currently provides unusually strong auditability, exact small-game
tooling, and useful negative diagnostics, but no prospective evidence that
interaction-aware retention beats item-level selection.

| Dimension | Rating | Verdict |
|---|---:|---|
| Mathematical definitions | 6/10 | Mostly sound after separating exact games, Möbius coefficients, SII, Shapley values, and fitted coefficients |
| Theory | 4/10 | No selection guarantee; low-order transfer is an empirical hypothesis |
| Novelty | 4/10 | Narrow combination novelty; item valuation, memory deletion, hypergraphs, and Shapley interactions are established |
| Experimental design | 5/10 | Strong leakage controls, but E4's current shift is only surface paraphrase and the reader is not ready |
| Current evidence | 2/10 | Diagnostics and negative screens only; no positive prospective or lesion result |
| Reproducibility | 8/10 | Strong artifact identities, validators, locked stages, raw traces, and test coverage |
| ICLR readiness | 3/10 | Promising study design, not a submission-ready scientific result |

**Estimated probability that the core scientific hypothesis fails:** approximately
70%. This is a judgment, not a calibrated probability. The main failure modes are
reader grounding, instability across future tasks, and exact-Shapley or
budget-conditioned item methods matching the interaction selector.

**Current recommendation:** proceed to E3d only. Do not spend the larger E4 budget,
describe HiberMem as a working framework, claim biological equivalence, or claim that
Shapley valuation fails on multi-hop chains.

---

# 2. Current ground truth of the project

## 2.1 Research question and actual mechanism

For a fixed memory bank \(M_b=\{m_1,\ldots,m_n\}\), fixed reader/model
\(\theta\), renderer \(g\), output contract \(c\), and query distribution \(Q\),
the project intervenes on the records made available to the reader. It measures a
bounded task reward \(r_{\theta,g,c}(q,S)\) for each retained coalition \(S\).
This defines a finite cooperative game

\[
v_b^Q(S)=\mathbb E_{q\sim Q_b}[r_{\theta,g,c}(q,S)].
\]

The implemented proof-of-mechanism uses \(n=8\), enabling complete \(2^8\)-coalition
tables. It computes exact game-theoretic diagnostics, fits low-order polynomial
surrogates, freezes retention masks from past-query outcomes, and is designed to
evaluate those masks on sealed future queries. It is not a complete long-term-memory
architecture: there is no learned online controller, natural memory ingestion,
consolidation, regrowth, or deployed retrieval system.

## 2.2 Hypotheses currently implicit in the code

1. Low-order interaction structure can be estimated reproducibly from past
   interventions.
2. That structure transfers to future queries within a bank.
3. Optimizing a low-order set-function surrogate selects better fixed-budget
   coalitions than item-only comparators.
4. Destroying past-estimated positive nonlinear structure causes extra held-out
   damage after item utility, cost, and negative interactions are matched.
5. The reader's response is a valid measurement instrument: supported coalitions
   answer and unsupported coalitions abstain rather than guess.

Assumption 5 currently fails the frozen readiness screen, so assumptions 2–4 cannot
yet be interpreted scientifically.

## 2.3 Completed evidence

| Stage | Actual evidence | Scientific interpretation |
|---|---|---|
| P0 | 21 exact mathematical tests pass | Exact operators agree with analytic/reference cases |
| P1 | 28 synthetic games, 192 sampled coalitions per game; sign, precision, recall, rank stability all 1.0; item MAE .015359; interaction MAE .016337 | Estimator recovery works in a favorable known model class; not LLM evidence |
| SmolLM2 P2 | top-4 overlap .55 vs .75 threshold; severe advantage .01, exploratory interval [-.03,.05]; 0/10 banks | Negative discovery/validation screen; held-out test correctly stayed locked |
| Phase2R | Qwen and Phi negative; Gemma aggregate lacks the required raw bundle | No qualified candidate |
| E1 | strong local complementarity; quadratic and exact-Shapley severe accuracy both .25; two independent banks | Interaction expression exists locally; no policy advantage |
| E2 | full-memory accuracy 1.00 in original order and .75 after reversal | Presentation order is a large confound |
| E3 core | 16,384 Qwen conditions; supported AND2 .5049, AND3 .1621; extensive truncation | Reader capability/decoding inadequate for causal interpretation |
| E3 decode64 | supported approximately .959/.973; full 1.0/.9375; 885 recoveries all non-strict, 852 cap hits | More tokens recover capability but not the output contract |
| E3c | 16,384 real conditions, banks 350–351; no passing contract | Engineering readiness failed; E4 freeze correctly rejected |
| E4 | code, symbolic controls, mock pipeline, freeze/validator exist | Engineering evidence only; no real E4 result |
| E5/E6 | plans only | Blocked |

E3c details matter. For current_v1, supported AND2/AND3 accuracy is
.917969/.935547, unsupported assertion is .243815/.220145, strict-format rate is
.776001, and cap-hit rate is .187012. The answer-slot contract improves strict
format to .997070 and cap hits to .000366, but reduces supported accuracy to
.843750/.880859 and raises unsupported assertions to .331380/.433594. At
cardinality seven, answer-slot unsupported assertions reach .50 for AND2 and .667
for AND3. No contract satisfies the unchanged readiness criteria.

## 2.4 Implementation and integrity status

- The full local suite passed 197 tests before audit changes.
- The real E3c report independently validates and is development-only.
- The E4 freeze tool rejects current E3c and creates no design configuration.
- PastEvidence strips support and output metadata before policy fitting.
- Future capabilities are typed separately, committed, and unavailable during
  selection.
- Frozen masks bind source, configuration, model, prompt, runtime, evidence, and
  manifest hashes.
- Mock runs are explicitly non-scientific and cannot qualify a method.
- Historical Phase-2 test access remains locked.

These controls are a major strength. They do not compensate for a measurement
instrument that guesses under missing evidence.

## 2.5 Discrepancies found

1. README.md was stale and named Phase2R v2 rather than E3d as the next experiment.
2. The master plan mixed ordinary Shapley values and generic interactions as
   polynomial coefficients. The code is more careful than the prose.
3. The master and E4 plans used absolute destroyed interaction mass as a lesion
   target despite PRE_IMPLEMENTATION_AUDIT.md correctly rejecting it.
4. The exact branch of the E4 sign-flip test used a Monte Carlo add-one correction.
   Exact enumeration should use the enumerated tail proportion.
5. The current E4 future split changes surface phrasing while holding latent
   dependency targets fixed. It measures paraphrase stability, not broad
   compositional or temporal transfer.
6. The Gemini draft converts proposed work and negative diagnostics into completed
   contributions and contains factual bibliography and experiment-table errors.

Items 1–4 were corrected in this audit. Items 5–6 require experimental and paper
discipline, not cosmetic edits.

---

# 3. Adversarial claim audit

| Claim | Classification | Audit | If wrong, what fails downstream? |
|---|---|---|---|
| External-memory subsets define a cooperative game | VALID WITH ASSUMPTIONS | Valid only after fixing reader, renderer, contract, query distribution, scoring, order, and absence semantics | Every attribution and lesion becomes ill-defined if these change across coalitions |
| Subset deletion identifies causal availability effects | PLAUSIBLE BUT LIMITED | It identifies the effect of making records available under a fixed prompt intervention; it does not identify a substrate-independent causal memory mechanism | “Causal engram” and transfer claims become invalid |
| Ordinary Shapley assumes additive utility | INCORRECT | Shapley averages marginal contributions over all coalitions and applies to arbitrary finite games | The Gemini paper's central Shapley-failure proof, figure, and MemLens attack fail |
| A pure \(k\)-way AND gives each necessary item zero Shapley value | INCORRECT | Symmetry and efficiency give each item \(1/k\) when \(v(M)-v(\emptyset)=1\) | A pure-chain “catastrophic eviction” example is false |
| Top-\(k\) ranking by Shapley is always selection-optimal | INCORRECT | A one-score-per-item ranking discards coalition identity; mixed, overlapping, redundant, or budget-specific games can make it suboptimal | H1 remains possible, but must be shown on counterexamples and data rather than asserted |
| Positive complementarity makes the game non-submodular | VALID | Any positive second discrete derivative violates submodularity | Standard monotone-submodular greedy guarantees cannot be invoked |
| Non-submodularity proves greedy or Shapley failure | INCORRECT | Absence of a guarantee is not an empirical failure theorem | Claims of inevitable failure and superiority are invalid |
| Low-order polynomial interactions represent the LLM game | REQUIRES EMPIRICAL VALIDATION | Omitted higher orders can contaminate fitted lower orders; order-2/3 is an approximation | Estimated “edges” may be projection artifacts and fail prospectively |
| Exact past Möbius/SII is ground truth interaction | WEAK / UNDERSPECIFIED | It is exact for the observed past game, not ground truth for future tasks or a latent semantic dependency | “Recovered true engrams” is invalid |
| Absolute destroyed interaction mass predicts damage | INCORRECT | Removing negative terms can increase utility | Original E5 could reverse the intended treatment |
| Interaction-aware retention has a prospective advantage | REQUIRES EMPIRICAL VALIDATION | No real E4 has run | Framework-performance and headline claims are unsupported |
| Partial-evidence hallucination confounds raw accuracy | VALID IN THIS PROTOCOL | E3/E3c directly show unsupported correct assertions and dependence on cardinality/contract | Raw retention accuracy can reward guessing unless decomposed |
| A better format contract solves grounding | INCORRECT | E3c answer-slot improves formatting while worsening unsupported assertion | E4 cannot be unlocked by strict formatting alone |
| Hibernation biology licenses the artificial mechanism | REDUNDANT AS INSPIRATION / INCORRECT AS EVIDENCE | Lin et al. study mouse synaptic architecture; no mapping identifies records, coalitions, or LLM behavior with synapses | Biological mechanism and “engram” claims fail; at most retain motivation |
| Hypergraphs or higher-order memory are novel | REDUNDANT WITH EXISTING WORK | HyperMem explicitly models high-order associations; HippoRAG models structured associative retrieval | Novelty must be functional, interventional, prospective, and sign-aware |
| Memory deletion/importance evaluation is novel | REDUNDANT WITH EXISTING WORK | Xiong et al., OSL-MR, MemLens, RAG attribution, and KV-cache work cover adjacent ground | HiberMem cannot sell generic retention or deletion |

---

# 4. Audit of the Gemini critique and draft

## 4.1 What the critic got right

- Grounding is the immediate blocker, and partial-evidence guessing makes raw
  correctness uninterpretable.
- Möbius coefficients, local finite differences, SII, and fitted interactions should
  not be conflated.
- Low-order fits can contain omitted-order contamination.
- Positive complementarity removes ordinary submodular greedy guarantees.
- Biological analogy, hyperbolic structure, RL controllers, regrowth, and other
  unimplemented modules should not inflate the paper.
- The novelty boundary is narrow, and E3d, E4, and E5 are necessary before a systems
  claim.
- The independent unit for confirmation should be the memory bank/environment, not
  individual queries.

## 4.2 Material corrections

1. **Shapley mathematics:** the draft repeatedly says item-level Shapley assumes
   additivity and gives necessary links zero value. This is false. For the unanimity
   game \(u_T(S)=\mathbf 1[T\subseteq S]\),
   \(\phi_i(u_T)=1/|T|\) for \(i\in T\). Shapley is an additive allocation
   functional, not an assumption that the game is additive. The real limitation of
   top-\(k\) Shapley is loss of coalition identity during subset optimization.
2. **MemLens:** as of the audit date, the primary record is arXiv:2607.25992,
   “MemLens: A Value-Aware Memory Management System with Interactive Analytics for
   LLM-based Agents,” not the invented VLDB citation. MemLens itself acknowledges
   co-retained-unit dependence and uses Shapley-style marginal analysis. It must be
   implemented faithfully before being named as a baseline.
3. **HyperMem:** the correct ACL 2026 authors are Juwei Yue, Chuanrui Hu, Jiawei
   Sheng, Zuyi Zhou, Wenyuan Zhang, Tingwen Liu, Li Guo, and Yafeng Deng; pages
   35237–35254, DOI 10.18653/v1/2026.acl-long.1627.
4. **Memory-management study:** the correct ACL 2026 paper is by Zidi Xiong, Yuping
   Lin, Wenya Xie, Pengfei He, Zirui Liu, Jiliang Tang, Himabindu Lakkaraju, and
   Zhen Xiang; pages 623–645, DOI 10.18653/v1/2026.acl-long.27.
5. **CUDAnalyst:** the actual paper is “Towards Feedback-to-Plan Decisions for
   Self-Evolving LLM Agents in CUDA Kernel Generation,” by Yee Hin Chong, Jiaming
   Wu, Youhui Zhang, and Peng Qu (arXiv:2605.26720; ICML 2026), not the invented
   title/authors.
6. **shapiq:** the correct NeurIPS 2024 paper is by Maximilian Muschalik, Hubert
   Baniecki, Fabian Fumagalli, Patrick Kolpaczki, Barbara Hammer, and Eyke
   Hüllermeier.
7. **Neuroscience:** the Science paper exists, but the draft's author list is
   fabricated. It is a mouse artificial-hibernation study and offers motivation,
   not validation of an LLM memory mechanism.
8. **E3d contract:** a response of the form “VERIFIED: start -> destination” is
   structured and changes the downstream interface. It may be a diagnostic arm, but
   cannot unlock the current label-only E4 interface. A qualifying candidate must
   verify the path internally and emit exactly one allowed label or UNKNOWN.
9. **Power:** fixing \(B=12\) from a variance observed in a different failed setting
   is unjustified. Sample size must follow a frozen, variance-only pilot on fresh
   banks. If the bank-level standard deviation is .10, detecting a .03 effect can
   require far more than 12 banks.
10. **Statistics:** the implemented primary procedure is a one-sided bank-level
    sign-flip/randomization test plus a bank bootstrap interval. Adding Wilcoxon after
    seeing data creates researcher degrees of freedom.
11. **Ranges:** for \(v\in[0,1]\), order-\(k\) finite differences and Möbius terms
    can reach magnitude \(2^{k-1}\); SII is not generally restricted to [-1,1].
    Ordinary Shapley values can also be negative.
12. **Factual counts:** P1 used 28 games, not 1,000; E1 had 2,048 conditions, not
    512; E2 had 6,144, not 512. E3 and decode64 were diagnostics, not thresholded
    gates.
13. **Results discipline:** no-memory performance is unknown, not \(0\pm0\); proposed
    anchor verification is not implemented; and “all real-model evaluations were
    negative” wrongly treats development diagnostics as failed confirmatory tests.
14. **Causal language:** coalition interventions estimate effects of record
    availability conditional on the fixed prompting system. They do not reveal a
    model-independent “true downstream utility.”

The Gemini LaTeX should therefore not be edited into a submission. It is safer to
replace it with an evidence-bounded draft whose unknown results remain explicit
TODOs.

---

# 5. Mathematical reconstruction

## 5.1 Intervention and reward

Let \(A(q)\) be the allowed labels for query \(q\), including UNKNOWN. Define a
deterministic prompt

\[
p(q,S)=g(c,q,(m_i)_{i\in S}),
\]

where retained records use a predeclared canonical order. The model and decoder
produce \(y\sim P_\theta(\cdot\mid p)\). The primary reward is original task
correctness \(r\in[0,1]\); strict format, support, abstention, cap hits, latency, and
tokens are separate outcomes. Support metadata must never enter \(p\) or policy
fitting.

The game is conditional on \((\theta,g,c,Q)\). Changing record order, instructions,
decoding length, parser, or query distribution defines a different game.

## 5.2 Discrete derivatives and Möbius decomposition

For \(T\cap S=\emptyset\),

\[
\Delta_Tv(S)=\sum_{L\subseteq T}(-1)^{|T|-|L|}v(S\cup L).
\]

The Möbius/Harsanyi coefficient is the derivative at the empty background:

\[
a(T)=\Delta_Tv(\emptyset)
=\sum_{L\subseteq T}(-1)^{|T|-|L|}v(L),
\qquad
v(S)=\sum_{T\subseteq S}a(T).
\]

This is an exact basis for a complete finite game. A positive \(a(T)\) is
complementary in that basis; a negative term is redundant/inhibitory in that basis.
The sign need not agree with every context-specific derivative.

For \(v\in[0,1]\), the triangle inequality gives
\(|\Delta_Tv(S)|\le 2^{|T|-1}\) for nonempty \(T\); the same bound applies to
\(|a(T)|\). Higher-order interaction values are therefore not generally bounded by
one.

## 5.3 Ordinary Shapley value

\[
\phi_i(v)=
\sum_{S\subseteq N\setminus\{i\}}
\frac{|S|!(n-|S|-1)!}{n!}
\bigl[v(S\cup\{i\})-v(S)\bigr].
\]

Equivalently, in the Möbius basis,

\[
\phi_i(v)=\sum_{T\ni i}\frac{a(T)}{|T|}.
\]

Thus ordinary Shapley distributes every pure interaction among its participants. It
does not expose which items must be retained together. A policy that ranks items by
\(\phi_i\) solves an additive proxy
\(\max_{|S|\le k}\sum_{i\in S}\phi_i\), not the original
\(\max_{|S|\le k}v(S)\). That distinction—not an alleged additive game
assumption—is the defensible motivation for H1.

## 5.4 Shapley Interaction Index

For nonempty \(T\),

\[
I_T^{\mathrm{SII}}(v)=
\sum_{S\subseteq N\setminus T}
\frac{|S|!(n-|S|-|T|)!}{(n-|T|+1)!}\Delta_Tv(S)
=\sum_{U\supseteq T}\frac{a(U)}{|U|-|T|+1}.
\]

At \(|T|=1\), SII equals ordinary Shapley. For higher orders it is a
context-averaged derivative and differs from Möbius coefficients, Shapley–Taylor,
Faith-Shap, and local full-context effects. The estimator must always name the
quantity it estimates.

## 5.5 Low-order surrogate

Given sampled masks \(S_\ell\), fit one coherent polynomial basis:

\[
\hat v_d(S)=\sum_{\substack{T\subseteq N\\|T|\le d}}\hat a_T
\mathbf 1[T\subseteq S]
\]

by a fully specified weighted/regularized loss. These \(\hat a_T\) are projection
coefficients, not exact SII. Required diagnostics are held-out mask prediction,
coefficient stability, sign recovery where symbolic truth exists, sensitivity to
sampling weights and regularization, and comparison across \(d=1,2,3\).

Omitted high-order terms can enter lower-order coefficients because the sampled
design is not generally orthogonal. No coefficient should be called an engram or a
causal dependency solely because it is large.

## 5.6 Retention optimization

\[
S^\star_{b,d,k}
=\arg\max_{\substack{S\subseteq N_b\\|S|=k}}\hat v_{b,d}^P(S).
\]

At \(n=8\), enumerate all \(\binom nk\) masks with a deterministic tie rule. The
proof-of-mechanism cost is \(O(B|Q|2^n)\) model evaluations for complete games and
\(O(\binom nk\sum_{j=0}^d\binom nj)\) for naive selection scoring. Exact
enumeration is not scalable. For larger \(n\), sampling, sparse estimation, candidate
generation, or mixed-integer/heuristic optimization is necessary, with empirical
rather than general approximation guarantees.

## 5.7 Sign-aware lesions

For a deletion set \(D\), fitted nonlinear terms disrupted by deletion are
\(\{T:|T|\ge2,T\cap D\ne\emptyset\}\). Define

\[
J_+(D)=\sum_{T\cap D\ne\emptyset,|T|\ge2}\max(\hat a_T,0),
\quad
J_-(D)=\sum_{T\cap D\ne\emptyset,|T|\ge2}\max(-\hat a_T,0),
\]

\[
G(D)=J_+(D)-J_-(D)
=\sum_{T\cap D\ne\emptyset,|T|\ge2}\hat a_T.
\]

Pair a structural lesion \(D_s\) with control \(D_c\) on deletion count, payload,
past item scores, recency, frequency, semantic centrality, position, and
\(J_-\), while separating \(J_+\) or \(G\). The held-out causal contrast is

\[
\Delta_b=
v_b^F(M_b\setminus D_c)-v_b^F(M_b\setminus D_s).
\]

Absolute \(\sum|\hat a_T|\) may describe topology but cannot be the treatment:
destroying a negative term can improve the outcome.

---

# 6. Literature and novelty audit

| Work | What is established | Overlap with HiberMem | Defensible remaining distinction |
|---|---|---|---|
| MemLens (Wei et al., arXiv 2026) | Shapley-style record valuation, value-aware storage, interactive memory analytics | External records as players; task utility and management | Prospective comparison of coalition-aware subset optimization to a faithful MemLens-style item baseline |
| Source Attribution in RAG (Nematov et al., arXiv 2025) | Document-level cooperative games; exact/approximate Shapley; redundancy, complementarity, synergy | Nearly the same attribution unit and subset intervention | Persistent retention, past-to-future transfer, fixed-budget selection, and sign-aware lesions |
| CUDAnalyst (Chong et al., ICML 2026) | Frozen-trajectory selective feedback interventions and coalitional interaction attribution | Controlled LLM-agent component interactions | External persistent records and turnover rather than feedback-to-plan analysis |
| HyperMem (Yue et al., ACL 2026) | Hierarchical hypergraph with high-order associations and coarse-to-fine retrieval | Higher-order memory structure | Functional behavioral interactions rather than constructed structural hyperedges |
| HippoRAG (Gutiérrez et al., NeurIPS 2024) | Knowledge graph and Personalized PageRank for multi-hop associative retrieval | Structured dependencies and multi-hop memory | Interventional value estimation and deletion, not retrieval graph construction |
| Xiong et al. (ACL 2026) | Empirical effects of memory addition/deletion and experience-following behavior | Deletion and future behavioral utility | Factorial coalition effects and prospective interaction selection |
| OSL-MR (Kang et al., arXiv 2026) | Budgeted retention with explicit online/offline observability separation | Leakage-safe past supervision and constrained retention | Explicit higher-order coalition structure; OSL-MR is a required strong baseline concept |
| ContextCite (Cohen-Wang et al., arXiv 2024) | Scalable context attribution and context pruning | Black-box context removal and usefulness | Persistent bank retention and explicit interactions |
| Shapley–Taylor (Sundararajan et al., ICML 2020), Faith-Shap (Tsai et al., JMLR 2023), shapiq (Muschalik et al., NeurIPS 2024) | General interaction definitions, axioms, approximation, software | Most mathematical machinery | Application and prospective evidence only; no new interaction index |
| LongMemEval (Wu et al., ICLR 2025), LoCoMo (Maharana et al., ACL 2024) | Long-term conversational-memory benchmarks | Future multi-session reasoning targets | Appropriate later evaluation setting, not novelty |
| H2O (Zhang et al., NeurIPS 2023), StreamingLLM (Xiao et al., ICLR 2024), Scissorhands (Liu et al., NeurIPS 2023) | Token/KV retention and efficiency | Importance-based constrained retention | Different substrate: persistent external records before prompt construction |
| Lin et al. (Science 2026) | Memory persists in mice despite broad synapse loss; retained synaptic architecture is associated with memory | High-level motivation about structure under turnover | No methodological or empirical transfer; should not support novelty |

Primary records:

- MemLens: https://arxiv.org/abs/2607.25992
- Source Attribution in RAG: https://arxiv.org/abs/2507.04480
- CUDAnalyst: https://arxiv.org/abs/2605.26720
- HyperMem: https://aclanthology.org/2026.acl-long.1627/
- HippoRAG: https://proceedings.neurips.cc/paper_files/paper/2024/hash/6ddc001d07ca4f319af96a3024f6dbd1-Abstract-Conference.html
- Memory-management study: https://aclanthology.org/2026.acl-long.27/
- OSL-MR: https://arxiv.org/abs/2606.10616
- ContextCite: https://arxiv.org/abs/2409.00729
- Shapley–Taylor: https://proceedings.mlr.press/v119/sundararajan20a.html
- Faith-Shap: https://www.jmlr.org/papers/v24/22-0202.html
- shapiq: https://proceedings.neurips.cc/paper_files/paper/2024/hash/eb3a9313405e2d4175a5a3cfcd49999b-Abstract-Datasets_and_Benchmarks_Track.html
- LongMemEval: https://openreview.net/forum?id=pZiyCaVuti
- LoCoMo: https://aclanthology.org/2024.acl-long.747/
- H2O: https://proceedings.neurips.cc/paper_files/paper/2023/hash/6ceefa7b15572587b78ecfcebb2827f8-Abstract.html
- StreamingLLM: https://openreview.net/forum?id=NG7sS51zVF
- Scissorhands: https://proceedings.neurips.cc/paper_files/paper/2023/hash/a452a7c6c463e4ae8fbdc614c6e983e6-Abstract.html
- Neuroscience motivation: https://pubmed.ncbi.nlm.nih.gov/42594194/

## Novelty classification

**Already established:** memory deletion, item importance, Shapley document/record
valuation, high-order interaction indices, high-order memory structures, multi-hop
retrieval, context pruning, and long-term-memory benchmarks.

**Potential combination novelty:** a leakage-safe sequence that (i) measures a
complete or sampled external-memory game on past tasks, (ii) freezes a
coalition-aware fixed-budget policy, (iii) evaluates it on genuinely shifted future
tasks, and (iv) uses sign-aware item-matched lesions to test incremental functional
structure.

**Engineering novelty:** fail-closed capabilities, immutable freezes, independent
artifact validation, raw traces, and explicit support/guess decomposition.

**Unclear until evidence exists:** whether interactions transfer, improve selection,
or cause future damage beyond item value; whether the effect survives natural memory
and computational costs.

---

# 7. Strongest defensible methodology

## 7.1 Core contribution

The core is a falsifiable evaluation and selection protocol for external-memory
coalition structure. It is not a new Shapley index, hypergraph architecture, or
biological model.

## 7.2 Problem formulation

Inputs are a fixed reader, a bank of persistent records with sizes and metadata, a
past-query capability, a sealed future-query capability, and capacity \(C\).
Policy fitting sees only past outcomes and online-available record features. It
outputs an immutable subset \(S\) satisfying
\(\sum_{i\in S}c_i\le C\). The evaluation objective is future original
correctness, accompanied by support, abstention, formatting, and efficiency
outcomes. Updates, consolidation, retrieval, and online learning are outside the
core proof-of-mechanism and must not be implied.

## 7.3 Falsifiable hypotheses

**H1 — prospective selection.** On frozen future queries and matched budgets, the
predeclared interaction-aware selector has a positive bank-level mean accuracy
advantage over every prespecified strong item-only comparator, with exact Shapley as
the primary comparator. A practically relevant margin must be frozen before
confirmation.

**H2 — sign-aware lesion.** Among pre-outcome deletion pairs matched on cost,
past-estimated item utility, nuisance metadata, and disrupted negative nonlinear
mass, the higher predicted positive nonlinear loss causes greater held-out damage.

**H3 — incremental future prediction.** A past-only interaction predictor improves
predeclared future-mask prediction beyond an additive predictor. Report this
separately for:

- H3a: surface paraphrase shift (current E4 generator);
- H3b: compositional/dependency shift with changed targets and motif composition;
- H3c: temporal or sequential shift in later natural-memory work.

Passing H3a does not establish H3b or H3c.

## 7.4 Supporting mechanisms

- Exact small-\(n\) games as an oracle for implementation and descriptive audit.
- Low-order surrogate fits with explicit predictive validation.
- Ordinary Shapley, LOO, additive regression, budget-conditioned marginals, recency,
  lexical, query-overlap, random, and shuffled controls.
- Typed capabilities, immutable policy freezes, independent validators, and
  support/format decomposition.

## 7.5 Optional later work

Natural conversational memory, candidate retrieval, sparse interaction discovery,
online retention, consolidation, hierarchical structures, and learned policies are
separate future studies. They should be added only after H1/H2 survive controlled
tests.

---

# 8. Experimental design

## 8.1 E3d — measurement-instrument readiness

The accompanying E3D_GROUNDING_PREREGISTRATION_2026-09-03.md is authoritative for
the next experiment. In brief:

- development banks 360–361 and frozen verification banks 370–373;
- current_v1 paired control;
- one query-anchored label-only candidate that internally verifies the exact start
  and path but emits one allowed label or UNKNOWN;
- one structured verifier diagnostic that cannot unlock E4;
- single-path/dual-path, base/counterfactual, empty, minimal support, full, every
  missing-link, missing-link-plus-distractors, and other-query-only conditions;
- unchanged readiness thresholds plus full-memory, counterfactual, other-query
  capture, and per-link checks;
- no reuse of E3c banks or adaptive threshold changes.

Failure condition: no label-only candidate passes all frozen verification criteria.
Interpretation: stop E4; change reader/model/task design under a new version.

## 8.2 E4 — H1 and H3a prospective study

**Independent unit:** bank. Queries, worlds, masks, and decoding seeds are repeated
measurements nested within bank.

**Primary outcome:** original future-query accuracy.

**Primary contrast:**

\[
D_b=\frac12\sum_{k\in\{2,3\}}
\left(A^F_{b,\mathrm{interaction},k}
-A^F_{b,\mathrm{exact\ Shapley},k}\right).
\]

**Primary inference:** one-sided bank-level sign-flip/randomization test for
interaction \(>\) item plus a bank bootstrap interval and the full distribution of
\(D_b\). Report mean, median, positive-bank fraction, and sensitivity to ties.
Do not treat query rows as independent. Multiplicity-correct secondary contrasts.

**Sample size:** do not freeze \(B=12\). Run a separately frozen variance-only pilot
on fresh banks after E3d, estimate the bank-level variance without selecting an
effect direction or endpoint, and determine confirmation size for the frozen
practical margin. Report sensitivity over plausible variance.

**Required comparators:**

1. exact Shapley top-\(k\) (primary item baseline);
2. budget-conditioned item marginals;
3. leave-one-out;
4. additive regression/surrogate Shapley;
5. faithful MemLens-style implementation after specification audit;
6. OSL-MR-inspired online-observable item scorer if implementable;
7. random, recency/position, query overlap, lexical centrality;
8. cubic and quadratic interaction selection;
9. exhaustive exact past-game optimum as an in-sample ceiling, never future oracle;
10. full memory and empty memory as reference conditions, not fabricated zeros.

**Controls:** equal cardinality and report payload bytes/tokens; identical record
order, reader, renderer, contract, decoding, queries, and calls; freeze every mask
before future access.

**Failure conditions:** no practical/uncertain advantage; exact Shapley or another
item baseline matches/exceeds; future prediction does not improve over additive;
effect is unsupported guessing, format, cost, or one-bank driven.

## 8.3 H3b compositional shift

Add a new version after E4a, not an unrecorded edit. Vary target identifiers,
dependency topology, motif mixture, path overlap, distractor structure, and query
composition between past and future while preserving scoring semantics. Freeze
shift strata and test an interaction-by-shift effect. This is required before
claiming general future validity.

## 8.4 E5 — H2 matched lesions

Use a new reserved cohort. Enumerate candidate deletion pairs using past evidence
only. Match deletion count, bytes/tokens, multiple item scores, recency, frequency,
centrality, position, and \(J_-\); maximize separation in \(G\) or \(J_+\).
Freeze pair identities and all tolerances before future outcomes. Primary analysis
is the bank-level paired damage contrast. Include placebo pairs with no predicted
nonlinear separation and negative-interaction lesions as a sign check.

Failure conditions: no held-out damage gradient with \(G\), matching imbalance,
effect reversal, or dependence on unsupported outputs.

## 8.5 E6 — external validity

Only after E5 passes, test source-level deletion on a controlled subset of LoCoMo and
LongMemEval, with manually audited evidence sets and identical retrieval. Add a
second reader/model family. Report accuracy, evidence recall, abstention,
contradiction/knowledge-update behavior, latency, storage, token use, number of model
calls, GPU memory, and dollar-equivalent compute. Synthetic-only success is a
legitimate falsification of broad claims.

## 8.6 Ablations and stress tests

- polynomial order \(d=1,2,3\);
- exact versus sampled games; coalition sample budget and design;
- regularization and weighting;
- Möbius objective versus other coherent interaction bases;
- no interaction terms; positive-only versus sign-aware terms;
- canonical versus permuted memory order;
- label-only versus diagnostic structured contract;
- single versus dual support paths;
- increasing \(n\), capacity, irrelevant memories, contradictions, corruption, and
  long temporal gaps;
- lexical nuisance and semantically confusable distractors;
- model family and decoding-budget replication.

Every ablation must preserve the frozen primary analysis. Exploratory findings do
not rewrite the confirmatory rule.

## 8.7 Quality–efficiency frontier

Plot future accuracy and supported accuracy against model calls, input/output tokens,
wall time, storage, and peak accelerator memory. Exact \(2^n\) evaluation is a
scientific instrument at \(n=8\), not a deployable memory controller. A useful method
must show an approximation path whose gain exceeds its estimation cost.

---

# 9. Implementation audit and execution plan

| Component | Status | Required action |
|---|---|---|
| Exact masks, Möbius, SII, Shapley | Implemented/tested | Keep semantic names separate; retain reference tests |
| Polynomial estimator | Implemented/tested | Add prospective omitted-order and sampling sensitivity reports |
| Retention policies | Implemented; exhaustive at \(n=8\) | Add counterexample tests showing when top-\(k\) Shapley differs from subset optimum without false pure-AND claims |
| E3c runner/validator | Implemented, real negative | Preserve immutable |
| E3d | Not implemented | Implement only from the frozen preregistration |
| E4 state machine | Implemented/mock validated | Keep blocked until a label-only E3d contract passes |
| Randomization inference | Corrected in this audit | Exact tail for enumerated flips; add-one only for Monte Carlo |
| E5 lesions | Plan only | Implement sign-aware pair construction and balance diagnostics after E4 |
| Natural benchmark adapter | Not implemented | Defer until E5 |
| Paper | Evidence-bounded scaffold created | Replace TODOs only with independently validated frozen results |

Recommended execution order:

1. Review and freeze E3d design, prompt, parser, model, banks, checks, hashes, and
   compute estimate.
2. Implement E3d generator, runner, independent validator, resume checks, symbolic
   controls, tests, and launcher.
3. Run development banks once; select at most one label-only candidate by frozen
   readiness rules.
4. Run verification banks once. If it fails, stop and version a new reader/task
   intervention; do not relax criteria.
5. If it passes, create and review a new E4 design config binding the exact contract.
6. Run E4 development and the separately frozen variance-only pilot.
7. Preregister confirmation size and rule, then run confirmation once.
8. Advance to sign-aware E5 only if the frozen E4 rule passes.
9. Attempt external validity only after E5.

Compute should be estimated in model calls before each freeze. Cache only conditions
whose full identity hash matches. Never cache across prompt/contract/decoder changes.

---

# 10. Reproducibility and integrity protocol

1. Predeclare source commit, environment lock, model revision, tokenizer, precision,
   hardware, prompt bytes, parsing, decoding, seeds, bank IDs, masks, metrics, and
   stopping rules.
2. Hash every raw row and retain raw generated text, token counts, finish reason, and
   latency.
3. Use a capability object so policy code cannot receive future content or support
   labels.
4. Have a separate validator reconstruct condition counts, rewards, masks, hashes,
   and stage legality without trusting the runner summary.
5. Keep development, variance, confirmation, and historical test cohorts disjoint.
6. Never use future outcomes for model, contract, prompt, threshold, estimator,
   policy, mask, or baseline selection.
7. Report all attempted contracts/models and failed screens.
8. Mark symbolic/mock artifacts as engineering-only in both filename and report.
9. Require a clean committed source for real runs; record hardware/runtime drift.
10. Do not impute missing calls as failures or successes. A partial/corrupt run must
    resume identically or be invalidated.
11. Freeze one primary endpoint, comparator, alternative, test, margin, and
    multiplicity policy before confirmation.
12. Treat LLM-judge metrics as secondary unless blinded human validation establishes
    agreement.

---

# 11. Reviewer attack simulation

**Attack 1: “Shapley already captures interactions.”** Correct. Ordinary Shapley
allocates interaction dividends to items. The paper must argue and test the narrower
point that item scores can lose coalition identity for constrained subset selection.
Include exact-Shapley and budget-conditioned item baselines; remove the false
pure-chain theorem.

**Attack 2: “This is an eight-string toy.”** At present, yes. Exact games identify a
mechanism but do not establish practical memory management. Passing E5 plus an
external benchmark and second model is required for a broad claim.

**Attack 3: “Your utility is prompt-format behavior.”** E2 and E3c support this
concern. E3d must qualify the reader, record order must be controlled, and support,
format, and capability must be decomposed.

**Attack 4: “Past and future are paraphrases of the same generator.”** Correct for
current E4. Call it H3a only and add H3b compositional shift.

**Attack 5: “The interaction estimator is a misspecified projection.”** Report
held-out mask prediction, order sensitivity, coefficient stability, and exact-game
error. Interpret coefficients as fitted predictors unless exact.

**Attack 6: “You leaked future utility.”** Typed capabilities and frozen artifacts
are strong, but publication requires an auditable trace showing future content was
unavailable before selection.

**Attack 7: “The lesion treatment ignores antagonism.”** The original plan did. The
revised E5 matches disrupted negative mass and uses sign-aware predicted loss.

**Attack 8: “The method costs exponentially more than the memory it saves.”** True
for exact games. Report calls and a sampled scaling path; avoid deployment claims.

**Attack 9: “You chose the model/contract after failures.”** Report the full sequence
as development. A fresh verification cohort and single frozen confirmation are
mandatory.

**Attack 10: “The biological story is decorative.”** Agree. Keep it to one
motivation sentence or remove it; never claim mechanistic equivalence.

**Attack 11: “MemLens/Source Attribution already do this.”** They substantially
preempt memory/document cooperative games. The remaining contribution requires
prospective subset-selection and sign-aware lesion evidence, not terminology.

**Attack 12: “Your p-value is meaningless with few banks.”** Exact sign flips are
valid under exchangeability but coarse at small \(B\). Power and generalization come
from more independent banks, effect distributions, and a frozen variance-based
sample size—not from treating queries as replicates.

---

# 12. Paper plan

**Recommended title:** *When Do Memory Interactions Matter? A Falsifiable Study of
Coalition-Aware Retention for Language Agents*

**Current paper type:** evidence-bounded diagnostic/pre-results draft. Do not use
“we demonstrate superiority,” “framework solves,” “true engram,” or
“catastrophically fails.”

1. Introduction: constrained external memory, item scores versus subset objectives,
   falsifiable question, current evidence boundary.
2. Related work: external memory management, source attribution, interaction
   indices, structured retrieval, KV retention.
3. Formalization: fixed intervention, exact game, estimands, surrogate, selection,
   causal limits.
4. Measurement readiness: E2/E3/E3c and the grounding confound.
5. Prospective protocol: H1/H3a, leakage controls, comparators, statistics.
6. Sign-aware lesions: H2 and matching.
7. Results: completed diagnostics only; prospective rows remain TODO until validated.
8. Limitations and broader impact.
9. Reproducibility statement and AI-use statement required by ICLR 2027.

Planned figures:

1. Protocol diagram: past interventions → immutable freeze → sealed future
   evaluation.
2. Correct counterexample where top-\(k\) item ranking loses coalition identity;
   include ordinary Shapley values and exact subset utilities.
3. Grounding decomposition by evidence cardinality and contract.
4. Future quality–efficiency frontier, only after E4.

Planned tables:

1. Novelty matrix with verified citations.
2. Completed diagnostic ledger with exact condition counts and evidence type.
3. E3d readiness checks.
4. Prospective H1/H3 results with TODOs until run.
5. E5 balance and lesion effects with TODOs until run.

The official ICLR 2027 initial-submission limit is nine pages of main text, excluding
references and appendices. The template, double-blind rules, reproducibility
expectations, and required AI-use statement must follow the current author guide:
https://iclr.cc/Conferences/2027/AuthorGuidelines.

---

# 13. Risks, go/no-go rules, and immediate actions

## Highest risks

1. Reader grounding never passes without changing the task interface.
2. Interactions are query-specific and do not transfer prospectively.
3. Strong item methods match the subset selector.
4. Low-order terms are unstable projections of higher-order behavior.
5. Synthetic gains disappear in natural memory.
6. Estimation cost dominates any retention efficiency.
7. Adaptive model/contract selection consumes all credible holdout capacity.

## Go/no-go

- **E3d GO:** exactly one label-only candidate passes every frozen verification
  readiness check. Otherwise STOP E4.
- **E4 GO to confirmation:** development suggests the frozen practical effect,
  without support/format/cost artifacts; variance pilot yields feasible confirmation.
- **E4 GO to E5:** the single frozen confirmation rule passes against all required
  item comparators.
- **E5 GO to external validity:** sign-aware lesion effect is positive, balanced,
  replicated across banks, and not guessing-driven.
- **Paper GO for a positive method claim:** E4 confirmation + E5 + second
  model/external benchmark.
- **Paper GO for a diagnostic paper:** only if the venue values the grounding
  evaluation protocol and negative result as a standalone contribution; title and
  claims must reflect that.

## Immediate prioritized actions

1. Review the E3d preregistration for a label-only query-anchored contract.
2. Implement and validate E3d without touching E3c artifacts or E4 gates.
3. Add a constructive, mathematically correct top-\(k\)-Shapley counterexample to
   tests and the paper; do not use a pure unanimity chain.
4. Audit a faithful MemLens and OSL-MR-style comparator specification.
5. Extend future generation to a separately versioned compositional shift.
6. Design sign-aware E5 matching and balance diagnostics before any E5 outcomes.
7. Maintain the evidence-bounded paper; replace TODOs only from independently
   validated artifacts.

**Bottom line:** the project has a credible scientific question and strong research
integrity machinery. It does not currently have the positive result or novelty
evidence needed for an ICLR method paper. The correct next move is a disciplined
E3d measurement repair, followed by prospective falsification—not stronger prose.
