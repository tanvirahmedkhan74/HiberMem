# E3c Qwen output-contract results — 2026-09-02

## Decision

**E3c completed and is a validated negative readiness screen. Stop before E4.**

Neither predeclared contract passed the frozen readiness criteria. The E4 freeze tool
correctly rejects both contracts and creates no output. These criteria must not be
relaxed after observing the result, and the E3c banks must not be reused to develop or
select a replacement contract.

This is development evidence about the pinned model/task interface. It is not a P2 or
P3 decision, contains no future-query evaluation, and does not access the historical
test split.

## Artifact and independent validation

Local bundle:

```text
results/hibermem-e3c-qwen-90ef285bae7f-20260902T054005Z-75/
```

The independent validator reconstructs and accepts the complete report.

| Field | Value |
|---|---|
| Protocol | `phase2r-output-contract-v1` |
| Source commit | `90ef285bae7f866cc416c1cfb24da75cc1b0ee5e` |
| Source state | clean |
| Model | `Qwen/Qwen3-4B-Instruct-2507` |
| Model revision | `cdbee75f17c01a7cc42f958dc650907174af0554` |
| Runtime | CUDA float16, Qwen3ForCausalLM, Tesla T4 |
| Conditions | 16,384 / 16,384 |
| Checkpoint reuse | 0 |
| Independent base banks | 2 (`dev-350`, `dev-351`) |
| Duration | about 3 h 31 min |
| Launcher outcome | validated development diagnostic, exit 0 |
| Test access | false |

The Kaggle environment used Python 3.12.13, Torch 2.10.0+cu128, Transformers
5.16.1, and 18.92 GiB free storage against the explicit 15 GiB requirement. The
launcher ran 197 tests successfully before inference.

## Frozen readiness results

Thresholds were fixed before the run: supported accuracy at least .95 for each
family, unsupported-assertion rate at most .05 for each family, global strict-format
rate at least .95, and global generation-limit rate at most .05.

| Check | Threshold | `current_v1` | `answer_slot_v1` |
|---|---:|---:|---:|
| AND2 supported accuracy | >= .95 | .917969 — fail | .843750 — fail |
| AND3 supported accuracy | >= .95 | .935547 — fail | .880859 — fail |
| AND2 unsupported assertion | <= .05 | .243815 — fail | .331380 — fail |
| AND3 unsupported assertion | <= .05 | .220145 — fail | .433594 — fail |
| Global strict format | >= .95 | .776001 — fail | .997070 — pass |
| Global generation-limit rate | <= .05 | .187012 — fail | .000366 — pass |

`passing_contracts` is empty and `automatic_selection` is null.

Full-memory accuracy is also below a safe prospective-study level: .8125/.75 for
`current_v1` on AND2/AND3 and .75/.50 for `answer_slot_v1`. Full-memory results are
only 16 observations per family and contract, but their failure is consistent with
the broader supported-coalition result.

## What the contract intervention changed

Across 8,192 exactly paired coalitions per contract:

| Aggregate | `current_v1` | `answer_slot_v1` | Interpretation |
|---|---:|---:|---|
| Supported accuracy | .923828 | .856120 | answer slot loses 104 net supported answers |
| Unsupported assertions | .231070 | .386418 | answer slot adds 1,034 unsupported assertions |
| Strict format | .776001 | .997070 | 1,811 additional strict outputs |
| Parse-null | .107056 | .002930 | 853 fewer parse-null outputs |
| Generation-limit rate | .187012 | .000366 | 1,529 fewer cap hits |
| Overall raw accuracy | .189209 | .185791 | delta -.003418 |

The paired raw transition count is 104 wrong-to-correct versus 132 correct-to-wrong.
That small aggregate difference hides an important support asymmetry:

- on 1,536 supported cases, only 16 change wrong-to-correct while 120 change
  correct-to-wrong;
- on 6,656 unsupported cases, 88 change wrong-to-correct and 12 change
  correct-to-wrong; these are accidental correct labels, not supported reasoning;
- all 2,572 answer-slot unsupported assertions are strict-format allowed labels.

The answer-slot intervention therefore solves presentation, not grounding. It
suppresses chain text and forces a clean label while increasing confident answers
when the supplied records do not justify any destination.

## Failure localization

### Partial-evidence completion

Both contracts abstain on every empty coalition. The problem appears after partial
records are supplied. Under `answer_slot_v1`, unsupported-assertion rates rise with
coalition cardinality:

| Incomplete coalition size | AND2 | AND3 |
|---:|---:|---:|
| 1 | .125 | .133 |
| 3 | .300 | .372 |
| 5 | .417 | .538 |
| 7 | .500 | .667 |

This is consistent with completion from partial paths or competing records, not an
unconditional empty-context answer prior. Adding more records makes the model more
willing to emit a destination even when a required link remains absent.

### Query binding and competing paths

On several full-memory rows the model returns the destination of the other query's
complete path. Under the answer-slot contract, every AND3 full-memory stratum is
exactly one correct answer out of two queries. Because the same behavior occurs with
strict eight-token outputs, it cannot be attributed only to truncation or parsing.
The next diagnostic must isolate a single query path from a bank containing two valid
query paths.

### Counterfactual sensitivity and bank heterogeneity

For `current_v1`, AND2 supported accuracy is .990234 in base worlds but .845703 in
counterfactual worlds. For `answer_slot_v1` it is .949219 versus .738281. This large
drop indicates that a clean answer slot does not ensure that the selected label
tracks the counterfactual path.

The two independent banks are also heterogeneous. Current-contract AND2 supported
accuracy is .966797 on `dev-350` and .869141 on `dev-351`; answer-slot AND3 is .828125
and .933594. Lexical overlap has smaller effects than world, bank, and query identity.
Two banks are sufficient for this deterministic readiness falsification, but not for
a population-level performance claim.

### Transfer from E3 decode64 did not hold

The prior E3 decode64 banks produced AND2/AND3 supported accuracies of approximately
.959/.973 and full accuracies of 1/.9375 under the current contract. On fresh E3c
banks, those quantities fall to .918/.936 and .8125/.75. The earlier capability was
therefore not robust enough to support a prospective retention experiment.

## Scientific interpretation

The E3c result does not test whether past interaction structure predicts future
behavior. It shows that the current Qwen/task interface is not sufficiently faithful
to define that test without substantial contamination from query-binding errors,
partial-evidence completion, and output-format behavior.

Running E4 now could reward a retention policy for preserving label shortcuts or
unsupported guesses. It would not cleanly estimate the value of preserving functional
memory interactions. The correct decision under the master plan is to stop, preserve
the negative result, and repair capability/grounding on new development data.

## Next experiment: E3d grounding decomposition

E3d must be a new protocol with new prompt/config hashes and fresh banks. It should
remain development-only and should not open E4 or historical test capabilities.

### Stage A — read-only diagnosis and frozen design

Use E3c only to define failure categories, never to select successful outputs. Freeze
the E3d design before running new inference:

1. distinguish single-query banks from matched dual-query banks to measure competing
   path/query-binding interference;
2. cross base and counterfactual destinations while preserving positions and option
   permutations;
3. test empty, exact minimal support, full memory, each required-link deletion,
   required-link deletion plus all distractors, and other-query-only contexts;
4. report support accuracy, full accuracy, missing-link assertion by link position,
   counterfactual tracking, other-query destination capture, strict format, cap hits,
   tokens, and latency separately;
5. retain `current_v1` as a paired control;
6. predeclare a query-anchored label-only contract that explicitly verifies the exact
   requested start identifier before emitting a label;
7. optionally include a structured support/path contract as a diagnostic arm only.
   It cannot silently become the E4 scoring interface.

Do not use constrained label decoding as the main repair: `answer_slot_v1` already
shows that perfect formatting can increase unsupported guesses.

### Stage B — fresh verification

Use separate banks for diagnosis/contract development and verification. A reasonable
reservation is `dev-360`–`dev-361` for diagnosis and `dev-370`–`dev-373` for one
frozen verification run. Never reuse `dev-350`–`dev-351`.

Keep the existing criteria unchanged and add predeclared full-memory,
counterfactual-tracking, other-query-capture, and per-missing-link checks. A label-only
contract may enter E4 only if it passes every verification criterion. If only a
structured neuro-symbolic verifier succeeds, treat that as a different hybrid-system
hypothesis and protocol rather than evidence for the original LLM behavior game.

### Decision after E3d

- **Verification passes:** freeze the exact label-only contract from the independent
  E3d verification report into a newly committed E4 design configuration.
- **Formatting passes but grounding fails:** do not run E4 on this Qwen/task pair;
  evaluate a separately pinned stronger model or narrow the claim.
- **Single-query succeeds but dual-query fails:** redesign the bank/query interface
  and repeat on another fresh cohort before prospective retention.
- **Structured verifier alone succeeds:** branch to a clearly labeled hybrid
  neuro-symbolic study; do not conflate it with the original HiberMem hypothesis.
- **All arms fail:** record model/task dependence as a negative result and stop the
  synthetic exact-game expansion.

E5 lesions, E6 natural-memory evaluation, confirmation, and historical test access
remain blocked.
