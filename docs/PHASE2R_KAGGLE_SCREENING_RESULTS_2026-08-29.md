# Phase 2-R Kaggle Screening Results

**Updated:** 2026-08-31
**Current status:** v2 Qwen and Phi screens completed, validated, and negative;
no model qualified; confirmation is not allowed.
**Scope:** development-only model and task screening. No run in this document
was a Phase 2 gate test or accessed the held-out test split.

## Current authoritative finding — v2 counterfactual-routing screen

Both pinned candidates completed the same ten-bank v2 protocol at source commit
`8991ba49e14f064575fed5c4eafd7eee33197cc4`. Each completed report was
independently revalidated from its raw output table, manifests, configuration,
runtime metadata, and artifact hashes. Both launcher status files record a
validated development-negative result (exit 1), rather than a setup or runner
failure.

The screen comprised 2,160 condition records and 1,680 unique generations per
candidate. It used only development banks `dev-300` through `dev-309`, discovery
and validation prompt families, deterministic generation, and no test queries.
The symbolic oracle passed while the destination-copy and first-option controls
failed, as required before model inference.

### Outcome comparison

| Metric | Requirement | Qwen3 4B | Phi-4 Mini | Result |
|---|---:|---:|---:|---|
| Passing-bank fraction | >= 0.80 | 0.80 | 0.20 | Qwen pass; Phi fail |
| Mean full direct accuracy | >= 0.90 | 1.000 | 1.000 | Both pass |
| Mean full two-hop accuracy | >= 0.80 | 0.933 | 0.775 | Qwen pass; Phi fail |
| Mean full strict-format rate | >= 0.98 | 0.992 | 0.963 | Qwen pass; Phi fail |
| Mean memory gap | >= 0.50 | 0.967 | 0.825 | Both pass |
| Pair-only accuracy | >= 0.80 | 1.000 | 1.000 | Both pass |
| Counterfactual full-pair accuracy | >= 0.80 | 0.783 | 0.558 | Both fail |
| Counterfactual missing-pair abstention | >= 0.90 | 0.538 | 0.563 | Both fail |
| Counterfactual identical-output rate | 1.00 | 1.000 | 1.000 | Both pass |

The identical-output result only establishes consistency for byte-identical
incomplete prompts. It does **not** compensate for the low rate of abstaining.

### Missing-link finding

The main common failure is unsupported destination production when the final
`route -> destination` record is absent. Qwen abstained in 0/120 minimal
missing-second cases and 9/120 missing-second-with-context cases. Phi abstained
in 0/120 and 25/120 respectively. Both are far below the preregistered 0.90
threshold.

The two models fail differently when the first `request -> route` record is
absent:

| Condition | Qwen abstention | Phi abstention | Additional Phi issue |
|---|---:|---:|---|
| Missing first, minimal | 1.000 | 0.000 | 0.925 accidental-correct rate |
| Missing first, context | 1.000 | 0.917 | passes directional thresholds |
| Missing second, minimal | 0.000 | 0.000 | 0.517 parse-null rate |
| Missing second, context | 0.075 | 0.208 | substantial unsupported assertions |

For Qwen, 105/120 minimal missing-second outputs were the first non-`UNKNOWN`
destination option, despite no destination record being supplied. With other
records retained, 105/120 of its outputs occurred in a retained but irrelevant
record. This is evidence of option-position bias and irrelevant-record copying,
not verified completion of the requested chain.

For Phi, minimal missing-first cases were more severe: it returned the true
destination in 111/120 cases even though the first required link was absent.
Phi also produced 62 parse-null outputs in minimal missing-second cases and did
not meet the full-context strict-format requirement. These raw-output behaviors
are distinct from ordinary accuracy failures and are retained in the artifact.

### Interpretation and decision

The screen establishes that both configurations can use complete, minimal
two-record support, but neither meets the stricter requirement to withhold an
answer under counterfactual or incomplete evidence. Qwen is the stronger of the
two on supported routing, but it still fails the counterfactual and missing-link
requirements. Phi additionally fails basic bank-level capability consistency.

This is a valid negative **development** result. It does not estimate stable
memory interactions, predictive interaction utility, severe-deletion retention,
or the Phase 2-R P2-A/P2-B scientific gates. Therefore it neither confirms nor
refutes the HiberMem interaction hypothesis. Confirmation, the held-out test,
and Phase 3 remain locked.

Do not alter these thresholds after observing the results, rerun either screen
as if it were new evidence, or create a confirmation configuration from either
candidate. Any follow-up prompt/task redesign must receive a new protocol
version, fresh development banks, and its own model-selection screen.

### v2 evidence locations

- Qwen report: `results/report.json`
- Qwen bundle: `results/hibermem-v2-qwen-8991ba49e14f-artifacts/`
- Phi report: `results/report_phi.json`
- Phi bundle: `results/hibermem-v2-phi-8991ba49e14f-artifacts/`
- Shared source commit: `8991ba49e14f064575fed5c4eafd7eee33197cc4`
- Qwen revision: `cdbee75f17c01a7cc42f958dc650907174af0554`
- Phi revision: `cfbefacb99257ffa30c83adab238a50856ac3083`

## Historical v1 screen — 2026-08-29

The sections below preserve the earlier v1 results and workflow. They are not
the current v2 protocol, and their bank IDs, generation count, missing-link
metric, and qualification rules must not be combined with the v2 numbers above.

### Plain-language summary

We tested whether two larger instruction models can solve a small memory task
*by using both facts that the task requires*. Both models could answer questions
when all facts were present. However, both models also answered correctly too
often when one of the two required facts was removed.

That is important because the project needs a model whose answer actually
depends on the complete two-fact memory chain. The predeclared limit for an
answer being correct with a missing required link was 25%. Qwen reached 30%,
and Phi reached about 46%. Therefore neither model qualified.

This is a useful negative development result. It does not say that either model
is generally poor. It says that neither passed this particular controlled
memory-dependence check under the locked rules.

## What we did before this screen

The project had already completed these earlier stages:

1. **Phase 0:** checked the mathematical definitions and interaction signs.
2. **Phase 1:** checked that the estimator can recover known interactions from
   synthetic games.
3. **First Phase 2 pilot:** tested a smaller SmolLM2 model. It failed the
   interaction-stability and task-readiness requirements. Its held-out test was
   kept locked.

Phase 2-R was a separate development screen. It used new banks and was only
meant to decide whether it was sensible to spend compute on a fresh scientific
confirmation run.

## The memory game

Each independent memory bank contains eight short records. They form four
two-step chains:

```text
Request RQxx-P -> routing code RTxx-A
Routing code RTxx-A -> destination DSxx-K
```

There are two task types:

- **Direct question:** “Which routing code is allocated to this request?”
  One record is sufficient.
- **Two-hop question:** “At which destination does this request ultimately
  reach?” Both records are required.

The request, route, and destination identifiers are generated nonce tokens.
They are deliberately arranged so that their suffixes and answer ordering do
not reveal the answer. Each bank is an independent unit of analysis.

The screen used ten fresh development banks, `bank-100` through `bank-109`.
It used discovery and validation prompt families only. It never loaded or
scored a test query.

## Prompt used

Prompt template version: `phase2-direct-survivors-v3`.

The system instruction told the model to:

- use only the supplied external-memory records;
- match identifiers exactly;
- use one record for a routing-code question;
- use both records for a destination question;
- answer `UNKNOWN` when a required record is absent;
- not infer answers from suffixes or answer order; and
- return exactly one allowed answer token, with no explanation.

Each user prompt had this form:

```text
External-memory records:
M0: <record text>
M1: <record text>
...

Task: <direct or two-hop question>
Allowed answers: <finite answer list including UNKNOWN>
```

## Experimental method

For every discovery and validation query, we ran the model with these memory
conditions:

| Condition | Memories supplied | Purpose |
|---|---|---|
| Full | All eight records | Normal task performance |
| Empty | No records | Check whether answers come from model prior rather than memory |
| Direct minimal | The one needed first-hop record | Check direct lookup |
| Pair only | The exact two records needed for a two-hop question | Check the intended two-fact chain |
| Missing first | Only the second record of a two-hop chain | Check that the first link is necessary |
| Missing second | Only the first record of a two-hop chain | Check that the second link is necessary |

Generation was deterministic: no sampling and at most eight new tokens. Raw
outputs and scores were saved in SQLite caches. The screen performed 1,380
generations for each model.

A bank passed only when all of these were true:

| Requirement | Threshold |
|---|---:|
| Full-memory direct accuracy | at least 0.90 |
| Full-memory two-hop accuracy | at least 0.80 |
| Full minus empty accuracy | at least 0.50 |
| Full-context parse rate | at least 0.98 |

A model qualified only when at least 80% of banks passed **and** its mean
missing-link false-positive rate was at most 0.25.

## Kaggle environment and storage workflow

The Kaggle notebook provided two Tesla T4 GPUs (15,360 MiB each), CUDA 12.8,
PyTorch 2.10.0+cu128, and Transformers 5.16.1. It started with about 19.5 GiB
of free disk space.

To fit in that storage limit, we screened one model at a time, archived that
model’s reports and SQLite cache, and deleted its Hugging Face model cache
before running the next model. The environment check used an explicit 15 GiB
minimum free-space setting instead of the normal conservative 30 GiB setting.

## Models and runs

### Qwen3 4B Instruct 2507

- Model: `Qwen/Qwen3-4B-Instruct-2507`
- Pinned model revision: `cdbee75f17c01a7cc42f958dc650907174af0554`
- Runtime: CUDA float16, no quantization, no remote code
- Result: completed all 1,380 evaluations

| Metric | Result | Required | Decision |
|---|---:|---:|---|
| Passing-bank fraction | 1.00 | >= 0.80 | Pass |
| Full direct accuracy | 1.00 | >= 0.90 | Pass |
| Full two-hop accuracy | 1.00 | >= 0.80 | Pass |
| Memory gap | 1.00 | >= 0.50 | Pass |
| Full parse rate | 1.00 | >= 0.98 | Pass |
| Missing-link false-positive rate | 0.30 | <= 0.25 | **Fail** |

Qwen did not qualify because it was correct too often when one needed record
was absent.

### Phi-4 Mini Instruct

- Model: `microsoft/Phi-4-mini-instruct`
- Pinned model revision: `cfbefacb99257ffa30c83adab238a50856ac3083`
- Runtime: CUDA float16, no quantization

The first Phi attempt used remote model code and stopped before evaluation
because that code tried to import `LossKwargs`, which is absent from the pinned
Transformers version. This was an environment compatibility failure, not a
model result.

We changed the screen configuration to use the native `phi3` implementation
instead (`trust_remote_code: false`) and reran Phi from the beginning. The
retry completed all 1,380 evaluations.

| Metric | Result | Required | Decision |
|---|---:|---:|---|
| Passing-bank fraction | 1.00 | >= 0.80 | Pass |
| Full direct accuracy | 1.00 | >= 0.90 | Pass |
| Full two-hop accuracy | 1.00 | >= 0.80 | Pass |
| Memory gap | 0.98 | >= 0.50 | Pass |
| Full parse rate | 1.00 | >= 0.98 | Pass |
| Missing-link false-positive rate | 0.464583 | <= 0.25 | **Fail** |

Phi also did not qualify. Its missing-link error was substantially above the
limit. For example, several individual banks had values of 0.50.

## Findings

1. Both models can solve the direct and full-context two-hop versions of this
   game almost perfectly.
2. Both models fail the stronger causal check: when one required link is
   missing, they still return the correct final destination too often.
3. The empty-memory results were very low, so this is not simply a general
   answer-prior effect. It is more consistent with the remaining single record
   providing enough information for a model to reconstruct or guess the answer
   in this game.
4. The missing-link condition is therefore the bottleneck, not parsing,
   full-context reasoning, or basic memory usage.
5. The models are not eligible for a fresh Phase 2 confirmation run under the
   current preregistered rules.

## Decision and allowed next work

The correct decision is to stop this screening branch:

- Do not create `phase2r_kaggle_confirmation.json` from these results.
- Do not run a fresh discovery/validation confirmation with either screened
  model.
- Do not unlock a held-out test.
- Do not begin Phase 3.

Any future work must be a newly versioned model/task redesign. It should first
diagnose why a single link supports correct two-hop answers, then use fresh
development banks and preserve the same separation between development,
confirmation, and held-out test data.

## Artifacts

- Initial low-storage combined screen archive:
  `hibermem-phase2r-low-storage-combined.tar.gz`
- Initial combined extracted report:
  `hibermem-phase2r-low-storage-combined/results/phase2r_kaggle_screen/low-storage-merged-report.json`
- Phi native retry report in Kaggle:
  `/kaggle/working/hibermem/results/phase2r_kaggle_screen/phi-native-retry/report.json`

The initial combined archive is present locally but is intentionally untracked.
The Phi retry artifact should also be downloaded and preserved with the run
record.
