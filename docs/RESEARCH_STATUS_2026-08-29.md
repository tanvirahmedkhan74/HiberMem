# HiberMem Research Status and Remaining Work

**Review date:** 2026-08-29

**Lead decision:** continue only with Phase 2-R model/task qualification; do not
unlock the failed pilot and do not start Phase 3

## 1. Research goal

HiberMem asks whether external natural-language memories have stable,
behaviorally useful interaction structure for an LLM. The core hypothesis is
stronger than “two facts can be useful together.” It requires that interactions
estimated from past queries are stable enough to predict which memory subsets
preserve future behavior better than an item-value baseline under severe
deletion.

The present project is not a computer-vision project. The supplied
`State-Nuisance-Geometry` repository is a separate video/CV codebase. Its
representation-learning goals, V-JEPA2 dependencies, datasets, and evaluation
units are unrelated to HiberMem's memory-bank coalition game. It must not be
used as the Kaggle source repository for this study.

## 2. Scientific claims and gates

The evidence chain remains:

1. **P0:** mathematical interaction definitions and signs are correct.
2. **P1:** the estimator recovers known synthetic interactions.
3. **P2-A:** a real LLM produces stable interaction rankings on discovery data.
4. **Validation readiness:** the LLM reliably solves the controlled task and
   depends on the supplied memory.
5. **P2-B:** interaction-aware retention beats item-only retention on a locked
   prospective test under severe deletion.
6. **P3:** only after P2 passes, matched structural lesions test whether
   destroying interactions causes additional damage after individual utility
   is controlled.

No later engineering claim can compensate for failure at an earlier gate.

## 3. Completed work

### Mathematical and estimator validation

- Phase 0 exact mask, derivative, Möbius/Harsanyi, Shapley, pairwise, and
  higher-order tests passed.
- Phase 1 synthetic recovery passed all sign, ranking, magnitude, false-positive,
  uncertainty, and stability thresholds.
- A tracked P1 certificate now lets a clean GitHub/Kaggle clone prove this
  prerequisite without committing the large results tree.

### Phase 2 controlled experiment

- Ten banks, eight memories, four two-step chains per bank, and disjoint
  discovery/validation/test templates were implemented.
- Discovery uses exact 256-coalition enumeration for two banks and 128
  size-balanced coalitions for eight banks.
- Order-2 predictive interaction fitting, query bootstrap, split-half ranking,
  item-value and exact interaction-aware retention, random controls, matched
  storage budgets, SQLite resume, full provenance, and one-way test unlock were
  implemented.
- The mock protocol passed as an engineering test.
- The pinned local SmolLM2-1.7B backend passed the small preflight qualification.

### First real-model pilot

The scientifically eligible SmolLM2 pilot completed 30,720 discovery and 2,800
unique validation evaluations. It produced a legitimate negative result:

- P2-A top-4 overlap: 0.55 versus 0.75 required;
- margin over random: 0.4071 versus 0.50 required;
- sign consistency: 0.9705, which passed but did not stabilize membership;
- validation full-memory accuracy: 0.58;
- passing validation banks: 0/10;
- full-memory direct accuracy: 0.85;
- full-memory two-hop accuracy: 0.5125;
- validation-only severe-deletion Interaction-minus-Item advantage: 0.01.

The held-out test was not accessed. P2-B and Gate P2 remain undecided, and Phase
3 remains blocked.

### Phase 2-R Kaggle implementation

- Fresh development banks 100–109 and reserved confirmation banks 200–209 are
  supported deterministically.
- Qwen3-4B-Instruct-2507 and Phi-4-mini-instruct are pinned at immutable model
  commits as stable 4B-class candidates.
- A 2,760-generation screen now evaluates direct, two-hop, pair-only, full,
  empty, and both missing-link conditions across every public template family.
- Stronger bank-level qualification directly tests the capability that failed.
- Per-model SQLite resume, raw outputs, compact JSON diagnostics, progressive
  reports, candidate selection, CUDA cleanup, and artifact packaging are
  implemented.
- A freeze tool creates a fresh scientific config only after a candidate
  qualifies.
- A separate Kaggle confirmation launcher requires the exact committed source
  revision and never unlocks test automatically.
- The complete local suite currently passes 55 tests.

## 4. What remains

### Immediate engineering prerequisite

Publish this HiberMem tree to a dedicated GitHub repository. The local checkout
has no remote, and the supplied repository points to a different CV project.
Until a correct URL and commit exist, Kaggle execution is intentionally blocked.

### Development experiment

Run the Kaggle Phase 2-R screen and retrieve the artifact. The independent unit
is still the memory bank; individual queries and repeated conditions must not be
treated as independent replicates.

Stop if neither candidate meets all preregistered qualification checks. Do not
respond by weakening thresholds, increasing model count indefinitely, or
looking at any held-out test.

### Fresh confirmation

If a model qualifies:

1. freeze the selected backend and development-report hash;
2. review and commit the generated confirmation config;
3. push that exact commit;
4. start a new Kaggle session at the exact 40-character commit;
5. run discovery/validation once on banks 200–209;
6. review P2-A and validation readiness.

If either confirmation prerequisite fails, preserve the negative result and
stop or pivot. If both pass, and only then, authorize a one-way unlock for that
new run and evaluate P2-B exactly once.

### Later work, still unauthorized

- P2-B held-out retention for the failed pilot;
- Phase 3 matched structural lesions;
- graph retrieval, RL, regrowth, or full HiberMem system construction;
- any attempt to merge the unrelated State-Nuisance-Geometry CV experiment into
  HiberMem provenance.

## 5. Research risks to monitor

- **Model/task confounding:** better results from a larger model may reflect
  basic two-hop competence rather than more meaningful memory interactions.
- **Context interference:** deletion improved some validation conditions in the
  first pilot, so fitted interactions may partly capture distractor removal.
- **Selection optimism:** the development screen selects a model; therefore the
  scientific conclusion must come from fresh banks and a newly locked test.
- **Template dependence:** a model can pass a few handpicked prompts and fail
  the full template distribution. Qualification is now bank- and template-level.
- **Compute temptation:** spending more coalition evaluations cannot repair a
  model that fails exact full-context two-hop behavior.
- **Cross-project contamination:** using the CV repository would break source,
  dependency, and artifact provenance even if Kaggle commands happened to run.

## 6. Current go/no-go status

| Decision | Status |
|---|---|
| Publish HiberMem to a correct GitHub repository | Required |
| Run Phase 2-R Kaggle development screen | Authorized |
| Freeze a confirmation model before screen passes | Prohibited |
| Run fresh discovery/validation confirmation after qualification | Conditionally authorized |
| Unlock any held-out test now | Prohibited |
| Begin Phase 3 | Prohibited |

The exact GitHub and Kaggle command sequence is in
`docs/PHASE2R_KAGGLE_EXECUTION.md`.
