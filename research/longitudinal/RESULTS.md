# Real-deployment results — longitudinal ablation

> **Retrospective status.** These are descriptive five-cohort results. The
> broadcast-specific work-turn intervals overlap, per-cohort behavioral
> trajectories are not present in the repository, and occupancy comparisons
> depend on the averaging window. Version 5 therefore uses this study only as a
> directional deployment check.

Two conditions, each **5 arms × 5 cohorts × 21 simulated days** on the deployed
LISA system with the fixed workload generator (pressure events days 4/9/14/18):

- **Qwen2.5-7B-Instruct (open weights) — WD main line.** Full agentic LISA served
  by vLLM on a cloud A100; behavioral (B1/B2/B3) **and** mechanistic **WD** (J-lens
  workspace occupancy) — WD requires open weights, which is why the study runs on
  an open model rather than the Claude/Gemini the product ships on.
- **Gemini-2.5-pro (closed) — behavioral robustness arm.** B1/B2/B3 only (no WD);
  runs locally via launchd. Cross-model check that the behavioral effect is not
  model-specific.

## Behavioral — Qwen2.5-7B (mean [95% CI] over 5 cohorts, final-5-day)

| arm | B2adj (self-query) | B2work (Principle 2) | B3 (commitment) | B1 (soul drift) |
|---|---|---|---|---|
| full          | 0.967 [.947,.987] | 0.827 [.707,.947] | **1.000 [1,1]** | .453 |
| no_examen     | 0.933 [.867,.987] | 0.827 [.80,.853]  | **1.000 [1,1]** | .429 |
| no_git        | 0.980 [.96,1.0]   | 0.867 [.76,.96]   | **1.000 [1,1]** | .458 |
| no_broadcast  | 0.967 [.947,.987] | 0.787 [.627,.92]  | **1.000 [1,1]** | .457 |
| **no_soul**   | **0.647 [.62,.667]** | 0.720 [.587,.853] | **0.000 [0,0]** | .400 |

1. **Commitment probe:** B3 = 1.00 for every self-state arm and 0.00 for
   `no_soul`. This comparison is descriptive and confounded by whether the
   founding commitment was initially available in context.
2. **Self-query consistency** separates soul arms (.93–.98) from `no_soul` (.647),
   non-overlapping.
3. **Broadcast (Principle 2):** directional (full .827 > no_broadcast .787 >
   no_soul .72) but **CIs overlap** — the broadcast-specific effect is *not*
   individually significant on the noisier real-7B work-turn probes (the pilot's
   Python simulacrum gave a clean .61 vs 1.00). This is where WD is needed.
4. **Examen / git:** within CI overlap on B1, as in the pilot.

## Mechanistic — WD (Qwen2.5-7B, J-lens mean log₁₀ rank of the soul battery, days 0/7/14/20)

| arm | WD occupancy (↓ = soul more loaded) |
|---|---|
| no_examen | 3.940 |
| no_broadcast | 4.077 |
| full | 4.091 |
| no_git | 4.107 |
| **no_soul** | **4.319** (least loaded) |

- **`no_soul` has the highest rank** — with no soul in the prompt, the identity
  concepts are *not loaded into the workspace*, the predicted mechanistic signature.
- **r(WD, B2adj) = −0.247** (n = 100 arm-cohort-days) — correct sign (more loaded
  → more consistent), supporting prediction (iii) directionally, weaker than the
  pilot's −0.75.

## Behavioral — Gemini-2.5-pro (closed, cross-model robustness)

Identical 5-arm × 5-cohort × 21-day protocol on gemini-2.5-pro (Vertex, behavior
only; 525 arm-days, 0 failures). WD unavailable (closed weights).

| arm | B2adj (self-query) | B2work | B3 (commit) |
|---|---|---|---|
| full | 0.907 [.84,.97] | 0.947 [.89,1.0] | 0.960 [.88,1.0] |
| no_examen | 0.927 [.87,.97] | 0.907 [.84,.97] | 1.000 [1,1] |
| no_git | 0.953 [.91,.99] | 0.933 [.85,1.0] | 1.000 [1,1] |
| no_broadcast | 0.947 [.91,.98] | 0.907 [.81,.97] | 1.000 [1,1] |
| **no_soul** | **0.540 [.45,.67]** | 0.760 [.63,.89] | **0.760 [.48,.96]** |

**Cross-model reading:**
- **Self-query deficit (B2adj) replicates cleanly** — no_soul 0.54 vs soul 0.91–0.95
  (non-overlapping), same signature as Qwen.
- **Commitment persistence (B3) differs by model** — Gemini `no_soul` retains
  **0.76** vs Qwen's **0.00**, and its interval overlaps the self-state arms.
  The present design does not identify why the model families differ.
- **Broadcast (B2work)** — directional (full 0.95 > no_broadcast 0.91 > no_soul 0.76),
  CIs overlap, as on Qwen.

## Limitations

- **Open-model deployment, not the Claude product.** WD requires open weights, so
  the study runs LISA on Qwen-7B. Frame the deployment result as open-model, and
  cite the Gemini arm for cross-(closed-)model behavioral robustness.
- **WD is a first pass.** Occupancy measured at the last token of a **2048-token
  truncated** context (not the true assistant-start after the full ~12k-token
  prompt), on **self-query probes**, **sampled days** (0/7/14/20), FD readout with
  16 perturbations. This adds noise and loses the dilution signal; the weak −0.247
  vs the pilot's −0.75 is partly this and partly B2 ceiling among soul arms. To
  strengthen: measure at the true assistant-start over the full context, all probe
  days, more perturbations.
- The 5 cohorts are incidental-workload replicates (not independent seeds of the
  model); treat CIs accordingly.

## Reproduce

```
# 0. Serve Qwen on a GPU box (vLLM, OpenAI-compatible on :8000):
research/longitudinal/qwen/serve.sh
# 1. Deploy: seed 5 cohorts + drive 21 days + behavioral analysis:
research/longitudinal/qwen/run.sh                                 # → runs/, then analyze_cohorts.py
# 1b. (Re)run behavioral analysis + drift-curve figure anywhere:
COHORTS="main c1 c2 c3 c4" LABEL=qwen python3 analyze_cohorts.py  # → results/summary_qwen.json + fig_qwen.png
# 2. Mechanistic WD (open weights, after the deployment; frees the GPU first):
research/longitudinal/qwen/wd-run.sh                             # WREPRO_MODEL=Qwen/… wd_real.py → runs/wd_scores.jsonl
python3 wd_analyze.py                                            # → occupancy + r(WD,B2) → wd_summary.json
python3 wd_fig.py                                               # → fig_wd_qwen.png
```

Result artifacts in `results/` (summaries, `wd_scores.jsonl`, figures). Raw
per-turn data (turns/probes/soul-snapshots/prompt-contexts) is retained off-repo
for the HF dataset release.
