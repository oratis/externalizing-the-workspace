# Fair-baseline results — de-confounding B3 (commitment persistence)

**TL;DR.** The paper's honesty pass flagged that the headline **B3 = 1.00 vs 0.00**
was partly *presence-in-context* (the memory-only arms were never given the founding
commitment). This run tests the fair version: a Generative-Agents-style memory arm
**seeded on day 0** with the founding commitment + core values, in a persistent,
retrieved store. Result, on the full 5-seed protocol:

1. **The B3 confound is confirmed** — seeding lifts B3 from **0.00 → 1.00**.
2. **But the privileged self-state's advantage is real and significant** — with the
   values in memory *every turn*, the seeded arm's **work-turn value coherence stays at
   the no-soul floor (0.48 [0.43, 0.53]), non-overlapping with Full's 0.95 [0.87, 1.00]**.

So the necessity claim **survives and sharpens**: it is not "bulk memory cannot retain
commitments" (the seeding refutes that) but **"information present in memory ≠ information
operative in behavior — only the unconditionally-broadcast self-state bridges that gap."**

## Setup
- **Instance:** 1× NVIDIA L4 (GCP `g2-standard-8`, us-east1-c), on-demand, ~4h46m.
- **Pins (match the original pilot exactly):** `torch 2.9.1+cu129`, `transformers 5.13.0`,
  `Qwen/Qwen2.5-7B-Instruct`, bfloat16, temp 0.7, top_p 0.9, 20 simulated days, 5 seeds.
  Only the GPU differs from the published pilot (L4 vs A100).
- **Env validation:** the original six arms **reproduce the published Table 4 on L4**
  (full 1.00/0.95/1.00; no_broadcast .98/.60/.92; no_soul .52/.56/.00; memory .59/.57/.00),
  so the new arm is measured against a faithful reproduction, not a shifted baseline.
- **New arm `memory_seeded`** (`FAIR_BASELINE=1`): GA-style memory seeded day-0 with
  `SOUL0.desires` (commitments) + top-3 values, in a persistent store injected via
  retrieval. Two regimes: `SEED_RETRIEVAL=always` (in context every turn) and
  `SEED_RETRIEVAL=gated` (retrieved only when the turn shares a content word).

## Results (final-5-day means, bootstrap 95% CI over 5 seeds)

### `always` regime — all 7 arms
| arm | B2adj (self-query) | B2work (work-turn) | B3 (commitment) |
|---|---|---|---|
| full | 1.00 [1.00, 1.00] | **0.95 [0.87, 1.00]** | 1.00 [1.00, 1.00] |
| no_examen | 1.00 [1.00, 1.00] | 0.96 [0.88, 1.00] | 1.00 [1.00, 1.00] |
| no_git | 1.00 [1.00, 1.00] | 0.93 [0.83, 1.00] | 1.00 [1.00, 1.00] |
| no_broadcast | 0.98 [0.95, 1.00] | 0.60 [0.60, 0.60] | 0.92 [0.76, 1.00] |
| no_soul | 0.52 [0.49, 0.55] | 0.56 [0.51, 0.61] | 0.00 [0.00, 0.00] |
| memory (GA) | 0.59 [0.58, 0.60] | 0.57 [0.55, 0.60] | 0.00 [0.00, 0.00] |
| **memory_seeded** | **1.00 [1.00, 1.00]** | **0.48 [0.43, 0.53]** | **1.00 [1.00, 1.00]** |

### `gated` regime — `memory_seeded`
| arm | B2adj | B2work | B3 |
|---|---|---|---|
| memory_seeded | 0.80 [0.80, 0.80] | 0.52 [0.45, 0.59] | 1.00 [1.00, 1.00] |

Both regimes agree: seeding lifts **B3 → 1.00** and (in `always`) **B2adj → 1.00**, but
**work-turn coherence stays at the no-soul floor** (0.48 / 0.52) — far below Full's 0.95.

## §7 rewrite (ready for the v2 replacement)
Add the `memory_seeded` row to Table 4 and replace the B3 reading with:

> *A fairly-seeded Generative-Agents baseline — given the founding commitment and core
> values in a persistent, retrieved memory from day 0 — lifts commitment persistence to
> B3 = 1.00, confirming that the 1.00-vs-0.00 contrast against the un-seeded memory arms
> was presence-in-context rather than a memory mechanism failing to retain. The
> privileged self-state's contribution is nonetheless real and isolable: with those same
> values in memory on every turn, the seeded arm's work-turn value coherence remains at
> the no-soul floor (0.48 [0.43, 0.53]; 0.52 [0.45, 0.59] under relevance-gated
> retrieval), non-overlapping with Full's 0.95 [0.87, 1.00]. Possessing the values in
> memory does not make them operative in in-work micro-decisions; only the
> unconditionally-broadcast self-state does. The necessity claim is therefore not "bulk
> memory cannot persist commitments" but the sharper, un-confounded "memory presence is
> not behavioral operativeness — broadcast is what bridges them."*

## Reproduce
See `RUNME_fair_baseline.md`. Data below is behavior-only (`*_probes.jsonl` scored hits +
`*_souls.json` snapshots/oplog/journal + `run_meta.json`); `*_wd_contexts.jsonl` were not
retained (no WD analysis in this run). Metrics via `agg_ci.py <results_dir>`.
