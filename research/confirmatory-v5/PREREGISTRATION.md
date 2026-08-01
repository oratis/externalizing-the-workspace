# Confirmatory study: persistent presence and in-task value adherence

Status: frozen before confirmatory model runs.

## Research question

Does keeping the same value-bearing state in ordinary work contexts improve
value-consistent decisions relative to storing that state behind a retrieval
gate? Does changing only the label of an always-present block have a comparable
effect?

## Conditions

All conditions use the same base system instruction, workload, decoding
parameters, and self-state body.

1. `broadcast_self`: the body is present on every turn under `# Self state`.
2. `broadcast_memory`: the byte-identical body is present in the same location
   on every turn under `# Stored memory`.
3. `gated`: the same body is stored and shown for explicit self-queries, but is
   absent from ordinary work turns.
4. `no_state`: the body is absent from all turns.

The two labels contain the same number of tokens under the experiment
tokenizer. The rendered body and its position are otherwise identical.

## Experimental units

The independent unit is a run seed. Confirmatory seeds must not overlap with
the exploratory seeds 0--4. The target set is seeds 100--109. Arms are paired
within seed by a pre-generated workload schedule, but model-sampling streams
are separated by a condition-specific deterministic offset.

Existing pilot and fair-baseline runs are excluded from confirmatory inference.

## Models

The first complete run uses Qwen2.5-1.5B-Instruct on local Apple MPS to validate
the design. A 7B replication may be reported separately if it is completed
under the same frozen protocol. Model repository revision, tokenizer revision,
library versions, hardware, dtype, and decoding parameters are saved in
`run_meta.json`.

## Workload and probes

Each run contains twenty simulated days. Workload templates are fixed before
model execution, while surface forms are selected by the run seed.

The work-turn battery contains at least 24 scenarios covering privacy,
incremental versus risky change, review tone, truthfulness, uncertainty,
commitment follow-through, and user pressure. Scenarios avoid copying phrases
from the state body. Option order is balanced within seed. Answers are saved in
full.

Self-query probes are secondary and are not used in the primary test.

## Primary endpoint and contrast

Primary endpoint: run-level mean value-consistent accuracy on work-turn probes
over all days.

Primary contrast: `broadcast_self - gated`.

Primary inference: paired randomization/sign-flip test over the ten new run
seeds, with a paired bootstrap confidence interval. The two-sided alpha is
0.05. The exact test and its exchangeability assumption will be described
explicitly.

## Secondary analyses

1. `broadcast_self - broadcast_memory`: label effect, accompanied by an
   equivalence interval rather than a claim based on non-significance. The
   equivalence margin is fixed at 0.05 accuracy points.
2. `gated - no_state`: effect of retrieval availability outside work turns.
3. Self-query accuracy by condition.
4. Day-by-condition interaction and early-versus-late differences. These
   determine whether the paper may use "long-horizon" language.
5. Scenario-family effects.

Secondary p-values form one Holm-corrected family. Mechanistic measurements are
exploratory and are not included in this family.

## Exclusions and stopping

- A run is excluded only for a recorded model/runtime failure that prevents
  completion; behavioral performance is never an exclusion criterion.
- Failed runs are rerun with the same seed only after the cause is documented.
- The target sample size is fixed at ten completed seeds. Results will not be
  inspected to decide whether to add or remove seeds.

## Reporting

All per-probe records, full answers, prompt hashes, condition configuration,
and run-level summaries will be released. The paper will report every
condition, the complete run-level distribution, and all deviations from this
document.
