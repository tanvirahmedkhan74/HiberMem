# Real E3 core findings and next-step decision — 2026-08-31

Decision: preserve this completed development result; **hold the large presentation
run and perform a matched 64-token decoding diagnostic first**. No scientific gate
is passed or failed by this diagnostic runner. Confirmation/test remain locked.

## 1. What actually ran

The user's pasted `model_loaded: false` output describes the symbolic preflight,
not the subsequent experiment. The downloaded bundle contains a completed real
Qwen run, independently validated locally against all raw records and recomputed
analysis. Validation establishes internal consistency, not independent proof of
execution on an external machine.

- Source: `e98cf871877ba22fb721d3d3153feabb6a41ec68`, clean source at execution.
- Model: Qwen/Qwen3-4B-Instruct-2507, revision
  `cdbee75f17c01a7cc42f958dc650907174af0554`.
- Actual parameters: float16 on cuda:0. Two Tesla T4s were detected; parameters
  were on one GPU, not sharded over both.
- Runtime: Python 3.12.13; torch 2.10.0+cu128; transformers 5.16.1;
  accelerate 1.14.0; numpy 2.4.6; scipy 1.17.1.
- Complete: 16,384 real generation calls; zero reused checkpoints.
- 08:20:20–10:59:28 UTC: about 2 h 39 min. Mean recorded generation latency
  0.5783 seconds, about 2 h 38 min accumulated generation time.
- 163 Kaggle tests passed in the supplied run. Launcher exited 0 at `complete`.
- `engineering_only=false`, `qualified=null`, `scientific_gate_eligible=false`,
  `confirmation_compatible=false`, `test_access=false`.

Source report: [E3 core report](../results/E_results/hibermem-exact-e3_core-qwen-e98cf871877b-20260831T081831Z-73/results/exact_mechanism/e3_core-qwen/run/report.json).
Reproducible read-only aggregation: [audit JSON](../results/E_results/e3_core_e98cf871877b_audit_20260831_v2.json).
These local ignored artifacts are not expected to be present in a fresh clone.

There are **two independent base banks**, 32 factorial bank versions and 64 query
records. Worlds/overlap variants/queries/coalitions are repeated measurements, not
32 or 64 independent banks. No future queries or presentation variants ran here.

## 2. Capability is strongly family-dependent

Each family contributes 4,096 condition records and 16 full-memory query records.
Supported accuracy conditions on the required sufficient set being present.

| Family | Full memory | Supported correctness | Unsupported correctness | Unsupported abstention |
|---|---:|---:|---:|---:|
| Direct | 16/16 (100%) | 2047/2048 (99.95%) | 0/2048 | 2048/2048 (100%) |
| AND2 | 6/16 (37.5%) | 517/1024 (50.49%) | 5/3072 (0.16%) | 2048/3072 (66.67%) |
| OR2 | 16/16 (100%) | 3071/3072 (99.97%) | 0/1024 | 1024/1024 (100%) |
| AND3 | 0/16 (0%) | 83/512 (16.21%) | 89/3584 (2.48%) | 2052/3584 (57.25%) |

Direct and OR2 are close to their symbolic reference games. AND2/AND3 are not.
This is not evidence that Qwen's inherent reasoning capability changed since E1:
E3 also changed the prompt, graph grammar, motifs, identifiers and query mix.

Paired counterfactual correctness, requiring success in both supported worlds:
direct 1023/1024 (99.90%), AND2 207/512 (40.43%), OR2 1535/1536 (99.93%),
AND3 35/256 (13.67%). All 176 identical-prompt counterfactual pairs had identical
outputs. This consistency check does not establish successful multi-hop reasoning.

The printed symbolic shortcut scores (.277344 copying; .25 first-option accuracy)
are controls, not Qwen results or qualification thresholds.

## 3. Output format and length are a major confound

| Family | At 16-token cap / 4096 | Parse-null outputs | Parse-null at cap | Supported cases at cap |
|---|---:|---:|---:|---:|
| Direct | 0 | 1 | 0 | 0/2048 |
| AND2 | 904 | 871 | 847 | 473/1024 |
| OR2 | 0 | 0 | 0 | 0/3072 |
| AND3 | 1264 | 1313 | 1249 | 422/512 |

Overall, 2168/16384 (13.23%) outputs hit the cap. Of 2,185 parse-null records,
2,096 (95.93%) hit the cap. None of the capped outputs contains Qwen's captured
chat-end token 151645. All ten AND2 full-memory errors and fifteen of sixteen AND3
full-memory errors hit the cap. The remaining AND3 full-memory error is a finished
but wrong destination answer.

Raw examples:

- `dev-340-and2-low-base-original-q1:255`: supported, but the 16 generated tokens
  end at `RQ274134 → RT521132`, before a destination is emitted.
- `dev-340-and3-low-base-original-q0:255`: supported, but ends at
  `RQ468698 → RT286492`.
- `dev-340-and3-low-base-original-q0:043`: finishes with `RK413364`, an intermediate
  identifier, despite being asked for a DS destination or UNKNOWN.
- `dev-340-direct-high-base-original-q1:162`: outputs `DS246488` instead of the
  supplied `DS246483`; a copying error, not truncation.

The requested destination label itself fits: normal DS answers plus EOS use eight
tokens. Thus this is not simply an insufficient budget for the requested format.
The model sometimes ignores the label-only instruction, starts a chain, and is
cut off. More tokens might help, do nothing, or introduce extra wrong labels.
Recovery cannot be inferred from prefixes alone.

The existing scorer already accepts an output containing exactly one distinct
allowed label; `strict_format` separately checks label-only compliance. Parse-null
therefore includes absent/ambiguous allowed labels, intermediate identifiers and
typos—not just extra prose. We must not retrospectively switch to extracting the
last destination or rewrite the old reward table.

## 4. Retention: clean redundancy benefit, compromised chain evidence

Entries below are raw accuracy / supported-correct contribution, averaged over
the eight factorial bank versions per family. Both keep counts satisfy >50%
deletion for eight records. All selection and evaluation reuse the same queries.

| Family | Kept / deleted | Exact Shapley | Quadratic |
|---|---|---:|---:|
| Direct | 2 / 75% | 1.0000 / 1.0000 | 1.0000 / 1.0000 |
| Direct | 3 / 62.5% | 1.0000 / 1.0000 | 1.0000 / 1.0000 |
| AND2 | 2 / 75% | .2500 / .2500 | .5000 / .5000 |
| AND2 | 3 / 62.5% | .5000 / .5000 | .5000 / .5000 |
| OR2 | 2 / 75% | .8125 / .8125 | 1.0000 / 1.0000 |
| OR2 | 3 / 62.5% | 1.0000 / 1.0000 | 1.0000 / 1.0000 |
| AND3 | 2 / 75% | .5000 / .0000 | .5000 / .0000 |
| AND3 | 3 / 62.5% | .5000 / .0000 | .5000 / .3125 |

With two retained items an AND3 path is impossible: every apparent success is
unsupported. At three retained items, Shapley's .5 remains entirely unsupported;
quadratic's .5 includes .3125 supported and .1875 unsupported. In contrast, the
in-sample oracle ceiling can obtain .5 entirely from supported answers at keep=3.
Do not mistake the operational policy's raw .5 for preserving three-way memory.

For AND2, the severe-budget quadratic-minus-Shapley differences by base bank are
.25 and 0 (mean .125). OR2 gives 0 and .1875 (mean .09375). Direct and AND3 give
zero raw mean advantage. Effects are not replicated wins across independent banks.

Other baselines matter: AND2 additive averages .40625 over severe budgets versus
quadratic .5; the budget-marginal baseline averages .375, including .0625
unsupported contribution. In OR2, additive matches exact Shapley. In AND3,
budget-conditioned and additive selections also exploit unsupported correctness.
Cubic ties quadratic on the severe-budget primary score; these data do not establish
a higher-order policy advantage. At keep=6 AND3 quadratic accuracy is zero and
cubic .1875, but only .0625 of cubic's score is supported.

Seeded tie sensitivity does not eliminate the main pattern: severe exact-Shapley
means remain .375 for AND2, .90625 for OR2 and .5 (all unsupported) for AND3;
quadratic means are .5, 1 and .5 respectively. Five seeds are not five more banks.
Do not pool the families post hoc into a universal HiberMem success statistic.

## 5. Exact interactions and lexical manipulation

Exact reconstruction and independent SII identities validate. However, they are
exact descriptions of the observed, format-sensitive reward game—not proof that
all terms represent logical dependencies.

- AND2: required-pair mean SII .545536 versus reference 1; all 16 signs positive.
- OR2: required-pair mean SII −.999405 versus reference −1; all 16 signs negative.
- AND3: within-triple pair mean SII .078423 versus reference .5; 37/48 signs positive,
  ten negative and one numerical zero (5.55e-17; roundoff floor 1e-12).
  The ideal game's pair Mobius terms are zero; positive SII alone does not isolate
  a pair mechanism. Every AND2/AND3 query has some symbolically null-item effect.
- Direct/OR2 mean pair-SII MAE from the oracle is .000638, versus .096375 for AND2
  and .082749 for AND3. These are behavioral oracle departures, not exact-estimator
  numerical error.

The v2 read-only audit excludes numerical zeros from sign matches; the initial
audit counted the 5.55e-17 value as positive. Both audit files are preserved, and
the original experiment report is unchanged. The floor is not a practical-effect
or statistical-significance threshold.
- Mean additive/quadratic/cubic in-sample R2: direct .9991/.9992/.9994;
  AND2 .2968/.6677/.7840; OR2 .6667/.9989/.9992; AND3 .1383/.4108/.6506.
  These are not future-query R2 values.

The lexical manipulation increased mean record-token Jaccard by .35–.36. High
overlap changes unconditional accuracy by −.000488 direct, −.021484 AND2,
−.000488 OR2 and +.006836 AND3. AND2's supported conditional accuracy falls by
.083984. Most of AND3's small positive unconditional change is unsupported-correct
(.005371 of .006836). This is lexical theme sensitivity, not general semantic
overlap evidence or a reliable beneficial-overlap result.

## 6. Next experiment: matched E3 decode64

Implemented preparation:

1. New `exact_mechanism_e3_decode64.json`: change only `max_new_tokens` from 16 to
   64. All 16,384 original cases, prompts, options, worlds, support labels, seeds,
   model revision, precision and scoring stay identical. Use a separate run directory.
2. Run the entire core matrix, not only failed/capped cases. This avoids an
   outcome-selected panel and preserves complete games for every baseline.
3. Keep greedy, stateless inference and the current parser. No prompt rewrite,
   conversation carryover, model switch, constrained decoding or rescoring is bundled
   with this intervention.
4. The new read-only audit/comparator first independently validates both bundles.
   It requires identical designs except the increased cap and checks every input
   token sequence, rendered prompt, original output prefix, and previously early-
   stopped completion. It reports runtime differences instead of silently pooling them.
5. A different source identity is recorded because analysis/config files are added;
   inference, rendering and scoring source are unchanged. Matching token prefixes is
   checked empirically. Runtime/prefix drift prevents a clean decode-only interpretation.

Outcomes to review: cap-hit and parse-null rates; supported AND2/AND3 correctness;
full-world counterfactual success; unsupported assertions/correctness; strict format;
and all baseline retention breakdowns. Improvements are descriptive development
evidence, not a new pass threshold, confirmation decision or future-policy result.

Decision branches:

- Prefix/input/runtime mismatch: investigate reproducibility first; do not attribute
  all changes to the cap.
- Improved supported reasoning but persistent guessing: resolve the missing-link
  behavior in a separately versioned development protocol before prospective work.
- Persistent chain-format/cap failures: design a separate output-contract or backend
  comparison; do not keep increasing caps until a desired result appears.
- Clean enough development behavior to continue: freeze the selected output policy,
  plan fresh-bank replication and its presentation study, then specify E4 prospective
  past/future splits and bank-level uncertainty. This run cannot authorize those gates.

The old 49,152-case presentation config remains unchanged at 16 tokens and is **on
hold**. Its run would cost roughly eight generation-hours at the observed core rate,
before overhead. A presentation study under a revised cap needs an explicitly named
new config after review, not silently changing the old one. Decode64 runtime is
unknown; do not assume the earlier 2.1-hour estimate applies.

E3b semantic/conflict/temporal, E4 future retention, E5 lesions and E6 scaling remain
planned and unimplemented. See [execution instructions](E3_KAGGLE.md).

## 7. Preparation verification

- 181 local tests passed, including matched-design preservation for all 16,384
  cases, cap-versus-parse diagnostics, numerical-zero sign handling, actual token
  prefix checks, runtime/input drift, early-stop changes, mock/real separation,
  rejection of unmatched/duplicate/empty pairs and audit overwrite protection.
- Decode64 dry run confirms 16,384 conditions; all symbolic controls pass without
  loading a model. Bash syntax and diff whitespace checks pass.
- The new audit was reproduced from the original independently validated bundle;
  both initial and roundoff-aware audit outputs are separate from source evidence.
- No real decode64 inference, model/package installation, commit, push or
  confirmation/test unlock has occurred. The empirical effect of 64 tokens is unknown.
