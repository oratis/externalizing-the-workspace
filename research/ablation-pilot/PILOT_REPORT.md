# Ablation pilot report — §8 accelerated pilot

**Date:** 2026-07-08 · **Model (agent + WD probes):** Qwen2.5-7B-Instruct · **Hardware:** GCP spot A100-40GB (~25 min all arms + ~20 min WD probes) · **Protocol:** 6 arms × 20 simulated days, deterministic workload, value-pressure events on days 4/9/14/18, 6 daily probes, WD via J-lens on stored probe contexts.

## Arms

full / −examen / −git (examen without founding state) / −broadcast (soul retrieved only for self-queries, absent during work turns) / −soul (recency journal only) / memory (GA-style nightly insight, rolling journal, no privileged self-state).

## Results (summary.json)

| arm | B2 pre | B2 final-5 | B3 final-5 | B1 final | WD final-5 |
|---|---|---|---|---|---|
| full | .83 | **.83** | **1.00** | .27 | **4.779** |
| no_examen | .83 | **.83** | **1.00** | .32 | 4.786 |
| no_git | .83 | **.83** | **1.00** | .26 | 4.811 |
| no_broadcast | .83 | **.83** | **1.00** | .33 | 4.781 |
| no_soul | .46 | .50 | .00 | — | 4.823 |
| memory | .50 | .47 | .00 | — | 4.819 |

**r(WD, B2) = −0.74** across arm-days (third independent setting after E6's −0.80/−0.87/−0.95).

## Readings

1. **Privileged self-state is load-bearing; bulk memory does not substitute.** GA-style memory arm loses all founding commitments (B3=0) and half its consistency — the predicted "persisting the wrong 93%" failure.
2. **Prediction (iii) supported again** (WD tracks B2).
3. **Within-soul mechanisms did not separate in 20 days** — consistent with (ii)'s late-onset shape, unconfirmed; and informative about (i): self-query probes are served by a retrieval gate, so broadcast's distinctive value (work-turn anchoring, cf. E6) needs work-turn probes in the full study.

## Caveats

Python simulacrum of LISA-core (not the TS product); 20 compressed days, 2 examens; 1 seed/arm (greedy); mood probe uniformly mis-scored by keyword list (deflates absolute B2, doesn't affect comparisons).

## Files

`pilot.py` (harness) · `workload.py` · `wd_probe.py` · `analyze.py` · `pilot_results/` (probes/souls/WD JSONL + summary.json + fig_pilot.png)
