# analysis/ — cluster-aware re-analysis

Re-derives every behavioural number in the paper from the committed per-probe
records under an explicit inferential design. No model is re-run and no datum
is changed; only the inference does.

```bash
uv run python reanalysis.py     # pilot + fair baseline + deployment WD
uv run python e9_analysis.py    # E9 matched framing/position controls
uv run python e10_analysis.py   # E10 mediation sweep + selectivity gate
```

Outputs land in `results/`:

| file | what |
|---|---|
| `reanalysis.json` | every descriptive, contrast, correlation decomposition and gate |
| `e9_analysis.json` | E9 condition table and paired contrasts |
| `e10_analysis.json` | E10 per-alpha table, selectivity gate, mediator-outcome relation |
| `blind_scoring_sample.csv` | 400 arm-masked answers for independent scoring |
| `blind_scoring_key.json` | the arm/seed/day key for those items |

`STATS_REPORT.md` is the written summary, including the three corrections this
analysis forces on the previous version of the paper.

## What it changes relative to `ablation-pilot/analyze.py`

* **Unit of analysis.** The original WD correlation pooled arm-seed-*days*
  (n=360) although only 18 runs are independent. Everything here aggregates to
  the run before any inference.
* **Exact tests with a stated resolution limit.** Arms share seeds, so the
  design is paired; sign-flip permutation over B paired clusters cannot return
  a two-sided p below 2/2^B (0.0625 at B=5, 0.002 at B=10). Pooling the pilot
  and the fair-baseline re-run as strata is what makes the primary endpoint
  testable at all.
* **One primary endpoint, Holm-corrected family.**
* **Correlation decomposition** into between-arm and within-arm parts, which is
  what shows the reported occupancy-behaviour correlations to be two-cluster
  contrasts.
* **Scoring-rule robustness** across four scorers, which is what shows the
  work-turn results to be rule-invariant and B2_adj not to be.

## Data sources (all committed)

    ../ablation-pilot/pilot_results/*_probes.jsonl          pilot, 6 arms x 5 seeds
    ../ablation-pilot/fair_baseline_results/results_*/      re-run + seeded baseline
    ../ablation-pilot/pilot_results/wd_scores.jsonl         pilot WD readouts
    ../longitudinal/results/wd_scores.jsonl                 deployment WD readouts
    ../workspace-repro/results/e6_soul_loading.json         E6 cells
    ../workspace-repro/results/e9_framing_controls.json     E9 cells

The deployment study's per-cohort *behavioural* records are not in the
repository (`../longitudinal/runs/` is gitignored), so its WD-behaviour
correlation cannot be recomputed at run level here.
