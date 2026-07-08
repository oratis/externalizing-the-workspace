# Ablation pilot report — §8 accelerated pilot (v2, multi-seed)

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

**r(WD, B2adj) = −0.75** (n = 360 arm-seed-days) — fourth setting after E6's −0.80/−0.87/−0.95.

## Four readings (decreasing confidence)

1. **Privileged self-state is load-bearing; bulk memory does not substitute.** Memory-only arms lose *all* founding commitments (B3 = .00 [.00,.00]) and half their consistency.
2. **Prediction (i) behaviorally confirmed.** Identical stored soul, gated broadcast → work-turn value coherence collapses to the no-soul level (.61 vs full's 1.00, non-overlapping CIs). Broadcast is necessary exactly where self-query retrieval does not fire — the behavioral face of E6's loading result.
3. **Prediction (iii) holds in a fourth setting** (r = −0.75, n = 360).
4. **Suggestive, not significant:** full is the only arm at ceiling on every metric; −examen shows the largest soul drift (B1 .50 vs .43) — prediction (ii)'s direction, CIs overlapping at 20 days / 2 examens.

## Caveats

Python simulacrum (not the TS product); compressed timescale; keyword scoring (mood probe excluded from B2adj — it's designed to evolve); ceiling effects compress within-soul differences on self-query metrics (the work-turn family was added for exactly this reason).

## Artifacts

`run_meta.json` (model, seeds, temp, lib versions) · per-(arm,seed) raw `*_probes.jsonl` / `*_souls.json` (snapshots+oplog+journal) / `*_wd_contexts.jsonl` · `wd_scores.jsonl` · `summary.json` / `wd_corr.json` · `fig_pilot.png` · reproduction commands in `README.md`.
