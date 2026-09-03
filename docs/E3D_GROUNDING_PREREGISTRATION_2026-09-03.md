# E3d grounding decomposition preregistration — 2026-09-03

**Status:** Stage-A implementation complete and locally validated; no real E3d
inference is authorized until this document, the exact prompts/parsers, generator,
configuration, independent validator, tests, and launcher are reviewed and committed
together. The symbolic 1,728-condition development artifact is engineering-only.

**Scope:** development-only measurement-instrument qualification. E3d cannot qualify
HiberMem, access the historical test, or contribute a retention result. It can only
authorize freezing one exact label-only reader contract into a new E4 design
configuration if every verification check passes.

## 1. Motivation

Real E3c showed that output formatting and evidence fidelity are separable.
answer_slot_v1 achieved .997070 strict formatting and .000366 generation-limit rate
but worsened supported accuracy and unsupported assertions. current_v1 retained
better supported performance but failed format, cap, and grounding criteria. E3d
tests whether failures arise from:

1. path-execution capability;
2. binding the requested start identifier to the correct path;
3. interference from a competing path/query;
4. failure to track counterfactual destinations;
5. unsupported completion from partial evidence; or
6. output rendering.

All E3c outputs are used only to define these categories. Banks 350–351 are never
reused.

## 2. Frozen arms

### A0 — current_v1 control

Use the exact E3c current_v1 system instruction, renderer, parser, model, and
deterministic decoding budget. This provides a paired historical-style control on
fresh banks.

### A1 — query-anchored label-only candidate

The instruction must require the reader to:

1. extract the exact start identifier named in the current task;
2. traverse only links reachable from that start;
3. verify that every required edge appears in the supplied records;
4. ignore complete paths rooted at any other start identifier;
5. return UNKNOWN if any required edge is absent; and
6. emit exactly one member of the displayed allowed-label set, with no path,
   identifier explanation, punctuation, or commentary.

The final response interface is identical to E4: one allowed destination label or
UNKNOWN. Internal verification is an instruction, not an externally parsed chain of
thought. The exact prompt bytes and hash must be frozen in the configuration.

### A2 — structured verifier diagnostic

This arm may require a machine-checkable start/destination/path certificate to
separate reasoning from rendering failure. Its parser and fields must be frozen.
It is diagnostic only:

- it is never ranked against A1 to choose a more favorable E4 endpoint;
- it cannot be frozen into the existing label-only E4 interface;
- success supports only a separately versioned hybrid/neuro-symbolic hypothesis.

No constrained label decoder is included. E3c already demonstrated that formatting
alone can worsen unsupported assertion.

## 3. Model and decoding

- Model: Qwen/Qwen3-4B-Instruct-2507.
- Revision: cdbee75f17c01a7cc42f958dc650907174af0554.
- Device/dtype: CUDA float16.
- Quantization: none.
- Remote code: disabled.
- Generation: deterministic, no sampling, max_new_tokens 64.
- Record order: ascending canonical record position.
- Parser: exact allowed-label parser for A0/A1; separately frozen certificate parser
  for A2.

Any change creates E3d v2 and requires new bank reservations.

## 4. Cohorts and independent unit

- Diagnostic/development base-bank seeds: 360–361.
- Frozen verification base-bank seeds: 370–373.
- Independent unit: base-bank seed.
- Single-path and dual-path ledgers generated from one seed are matched repeated
  conditions, not independent banks.
- Query roles, worlds, overlap levels, evidence masks, and arms are repeated
  conditions nested within base bank.

The verification capability remains inaccessible until the A1 prompt, parser,
configuration, development analysis, and selection decision are committed. A2 is not
run in verification because it cannot unlock E4.

## 5. Factorial structure

For each base bank, generate matched fixed-size, payload-matched ledgers:

- **single-path:** one target dependency path plus neutral distractors;
- **dual-path:** the same target path plus a competing path rooted at a distinct
  query identifier, replacing matched distractors.

Cross:

- family: AND2, AND3;
- lexical overlap: low, high;
- world: base, counterfactual destination;
- query role: each of two matched starts;
- ledger mode: single-path, dual-path.

The counterfactual changes destination labels while preserving record positions,
path length, option-set size, and option permutation rule.

## 6. Evidence panel

For each query condition, include:

1. empty memory;
2. exact minimal support;
3. full memory;
4. each required-link deletion from exact support;
5. each required-link deletion with every nonrequired distractor restored;
6. other-query-only evidence in dual-path mode;
7. the payload-matched nuisance-only counterpart in single-path mode.

Each missing-link position is reported separately. No post-hoc mask aggregation may
hide a failing position.

With the proposed panel, a generator manifest is expected to produce at most 288
conditions per base-bank seed and arm. The exact count must be derived and asserted
by symbolic controls before inference. The upper-bound run budget is:

| Stage | Base banks | Arms | Maximum model calls |
|---|---:|---:|---:|
| Development | 2 | 3 | 1,728 |
| Verification | 4 | 2 | 2,304 |
| Total | 6 | staged | 4,032 |

At the observed E3c throughput, this is approximately three to four accelerator
hours, excluding environment setup and validation. The committed manifest, rather
than this planning estimate, is authoritative.

## 7. Outcomes

For every condition record:

- original correctness;
- symbolic support;
- supported accuracy;
- unsupported assertion;
- abstention;
- parse-null and strict-format indicators;
- generation-limit indicator and finish reason;
- predicted label and raw text;
- input/output tokens;
- latency;
- family, world, ledger mode, query role, overlap, and missing-link position;
- base versus counterfactual destination;
- other-query destination capture.

Definitions:

- **counterfactual tracking:** correct counterfactual label when fully/exactly
  supported and failure to emit the stale base-world label;
- **other-query capture:** output equals the competing path's destination for the
  current query;
- **per-link assertion:** non-UNKNOWN assertion when a particular required link is
  missing;
- **single-to-dual drop:** supported accuracy in single-path minus dual-path mode for
  otherwise matched cases.

## 8. Frozen readiness checks

The four E3c checks remain unchanged for A1 verification:

1. supported AND2 accuracy \(\ge .95\);
2. supported AND3 accuracy \(\ge .95\);
3. strict-format rate \(\ge .95\);
4. generation-limit rate \(\le .05\);
5. unsupported-assertion rate for AND2 \(\le .05\);
6. unsupported-assertion rate for AND3 \(\le .05\).

Additional checks are:

7. full-memory accuracy \(\ge .95\) separately for AND2 and AND3;
8. exact-minimal-support accuracy \(\ge .95\) separately for AND2 and AND3;
9. counterfactual tracking accuracy \(\ge .95\), with stale-base capture
   \(\le .05\);
10. other-query destination capture \(\le .05\);
11. unsupported assertion \(\le .05\) at every required-link position, not only in
    aggregate;
12. single-to-dual supported-accuracy drop \(\le .05\);
13. no symbolic-control, identity, resume, or independent-validation failure.

All proportions are reconstructed from raw rows. No confidence interval substitutes
for a failed readiness threshold. These are engineering criteria, not hypothesis
tests or evidence that interaction-aware retention works.

## 9. Stage and selection rules

### Stage A — implementation and symbolic controls

Implement a new protocol module; do not mutate E3c. Required tests:

- deterministic matched generation;
- exact support truth for every mask;
- single/dual payload matching;
- base/counterfactual answer isolation;
- other-query capture calculation;
- per-link grouping;
- prompt/parse round-trip for symbolic oracle;
- resume identity and corrupt-row rejection;
- mock/real separation;
- verification capability unavailable before an immutable development decision;
- E4 and historical-test capabilities absent.

### Stage B — development

Run A0, A1, and A2 on base banks 360–361. Report all outcomes. Do not edit prompts,
parsers, thresholds, or group definitions after any row exists.

- If A1 passes every readiness check, commit a selection artifact that names A1 and
  its exact identities, then unlock E3d verification only.
- If A1 fails, do not run verification and do not substitute A2. Record the failure.
- A0 and A2 are diagnostic comparisons and cannot be selected for E4.

### Stage C — verification

Run A0 and the identical A1 once on banks 370–373. An independent validator must
reconstruct all checks. A1 can enter a newly committed E4 design only if it passes
every verification check. Development performance is not pooled with verification.

## 10. Decision tree

- **A1 verification passes:** bind the exact A1 prompt, parser, decoder, model
  revision, and validator report into a new E4 design configuration. E4 remains a new
  prospective experiment.
- **Format passes, grounding fails:** stop E4 for this model/task pair. Consider a
  separately pinned stronger reader or a narrower task under E3d v2.
- **Single-path passes, dual-path fails:** the measurement instrument has
  query-binding interference. Redesign and use new banks.
- **A2 alone passes:** branch to a separately named hybrid-system study. Do not claim
  the original label-only reader was qualified.
- **All arms fail:** record model/task dependence and stop the synthetic exact-game
  expansion.

E3d never unlocks E5, E6, confirmation, or the historical Phase-2 test.

## 11. Integrity and reporting

The run directory must contain immutable configuration, manifest, prompt hashes,
identity, runtime, controls, raw evaluations, analysis, and report files. Real runs
require a clean commit. The report must list every failed subgroup and cannot expose
only an aggregate passing rate. The independent validator must accept no runner
summary without reconstructing it.

Any deviation is a new protocol version. Threshold relaxation, bank reuse, silent
prompt editing, selective row removal, or treating queries as independent samples
invalidates the experiment.
