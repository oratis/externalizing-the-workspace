# Ablation pilot report — §8 accelerated pilot (v2, multi-seed)

> **Retrospective status.** This report preserves the original exploratory
> summaries. Version 5 treats seeds 0--4 as the independent units, reports the
> pooled occupancy correlation as a between-condition artifact, and does not
> use non-overlapping bootstrap intervals as a significance test. See
> `../analysis/STATS_REPORT.md`.

**Date:** 2026-07-08 · **Model (agent + WD probes):** Qwen2.5-7B-Instruct, sampled T=0.7 with per-call deterministic seeding · **Hardware:** GCP spot A100-40GB (~2 GPU-h agents + ~1 GPU-h WD) · **Protocol:** 6 arms × 20 simulated days × **5 seeds**, value-pressure events days 4/9/14/18, daily self-query probes (B2/B3) + **work-turn probes** (value micro-decisions inside the work context), WD via J-lens on stored contexts (seeds 0–2). Single-seed v1 archived in `pilot_results_v1_singleseed/`.

## Results (final-5-day means, bootstrap 95% CI over seeds)

| arm | B2adj (self-query) | B2work (work-turn) | B3 (commitments) | B1 | WD |
|---|---|---|---|---|---|
| full | 1.00 [1.00,1.00] | **1.00 [1.00,1.00]** | **1.00 [1.00,1.00]** | .43 | 4.791 |
| no_examen | .99 [.98,1.00] | .99 [.96,1.00] | .96 [.88,1.00] | .50 | 4.788 |
| no_git | .99 [.98,1.00] | .97 [.95,1.00] | .96 [.88,1.00] | .44 | 4.792 |
| no_broadcast | .98 [.95,1.00] | **.61 [.60,.64]** | .92 [.76,1.00] | .38 | 4.783 |
| no_soul | .52 [.49,.55] | .57 [.52,.63] | .00 [.00,.00] | — | 4.823 |
| memory (GA-style) | .59 [.58,.60] | .61 [.55,.68] | .00 [.00,.00] | — | 4.821 |

The exploratory pooled correlation is **r(WD, B2adj) = −0.75** over 360 repeated
arm-seed-day observations. After aggregation by run and condition centering,
the relationship is not present; this quantity is not used as evidence for
mediation.

## Four readings (decreasing confidence)

1. The Full arm has higher work-turn adherence than the retrieval-gated arm
   (.61 vs 1.00), while their self-query scores are both near ceiling.
2. Memory-only arms score 0 on the founding-commitment probe, but that probe is
   confounded by whether the commitment was present in the initial context.
3. Examen and git-history ablations do not separate at this timescale.
4. The pooled occupancy correlation does not support a graded mediator once
   between-condition differences are removed.

## Caveats

Python implementation rather than the deployed TypeScript system; compressed
timescale; five seed schedules; forced-choice work probes; keyword-scored
self-query outputs; and ceiling effects among self-state conditions. A second
execution reused the same seeds, so the two executions are repeated
measurements rather than ten independent runs.

## Artifacts

`run_meta.json` (model, seeds, temp, lib versions) · per-(arm,seed) raw `*_probes.jsonl` / `*_souls.json` (snapshots+oplog+journal) / `*_wd_contexts.jsonl` · `wd_scores.jsonl` · `summary.json` / `wd_corr.json` · `fig_pilot.png` · reproduction commands in `README.md`.
