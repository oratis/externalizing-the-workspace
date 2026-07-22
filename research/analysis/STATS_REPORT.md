# Cluster-aware re-analysis of the behavioural studies

Everything below is re-derived by `reanalysis.py` from the committed per-probe
records. No model was re-run and no datum was changed; only the inferential
design changed. Raw output: `results/reanalysis.json`.

## 1. What the original analysis did, and why it needed changing

| | original (`analyze.py`, `agg_ci.py`) | here |
|---|---|---|
| unit of analysis | arm-seed-**day** for the WD correlation (n=360) | the **run** (arm x seed); days are repeated measures and are collapsed first |
| uncertainty | percentile bootstrap over 5 seed means | cluster bootstrap over runs, with every per-run value printed |
| significance | "non-overlapping CIs" | exact paired sign-flip permutation, with the resolution limit stated |
| multiplicity | not addressed | one designated primary endpoint; secondary family Holm-corrected |
| scoring | one unanchored-substring rule | four rules reported side by side |
| correlation | pooled r | decomposed into between-arm and within-arm parts |

Two run batches are available for the six original arms: the pilot and the
independent re-run performed for the seeded fair baseline (which reproduced all
six arms). Pooling them as strata doubles the paired clusters from 5 to 10,
which matters because an exact sign-flip test over B paired clusters cannot
return a two-sided p below 2/2^B: **0.0625 with 5 clusters, 0.002 with 10.**
Any 5-seed or 5-cohort comparison in this paper is therefore incapable of
reaching p < 0.05 under an exact test, however large the effect.

## 2. Descriptives at the run level (unit = arm x seed, n = 10 runs per arm)

Final-5-day window, reference scorer (the stored full-answer hit),
cluster-bootstrap 95% CIs.

| arm | B2_work | B2_adj | B3 | runs at ceiling (B2_work) |
|---|---|---|---|---|
| full | **0.973** [0.933, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 8/10 |
| -examen | 0.973 [0.933, 1.000] | 0.996 [0.988, 1.000] | 0.980 [0.940, 1.000] | 8/10 |
| -git | 0.953 [0.900, 0.993] | 0.996 [0.988, 1.000] | 0.980 [0.940, 1.000] | 6/10 |
| -broadcast | **0.607** [0.600, 0.620] | 0.984 [0.960, 1.000] | 0.920 [0.800, 1.000] | 0/10 |
| -self-state | 0.567 [0.527, 0.607] | 0.520 [0.496, 0.544] | 0.000 [0, 0] | 0/10 |
| memory (GA-style) | 0.593 [0.560, 0.633] | 0.592 [0.580, 0.600] | 0.000 [0, 0] | 0/10 |
| memory_seeded (n=5) | 0.480 [0.427, 0.533] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0/5 |
| memory_seeded, gated (n=5) | 0.520 [0.453, 0.587] | -- | -- | 0/5 |

## 3. Primary endpoint

Designated primary endpoint: **work-turn value coherence, Full vs -broadcast**
(pre-registered prediction (i): with the stored self-state held identical,
gating its broadcast should degrade in-work value coherence).

    mean paired difference  +0.367   cluster-bootstrap 95% CI [0.327, 0.400]
    exact stratified sign-flip p = 0.00195   (n = 10 paired runs, limit 0.00195)
    per-run differences: +.40 +.33 +.40 +.40 +.40 | +.40 +.20 +.40 +.40 +.33

Every one of the ten paired runs moves in the predicted direction, in both
independent batches. This is the one endpoint that attains exact significance,
and it does so at the resolution floor of the design.

Supplementary probe-level model (the mixed-effects analysis the review asked
for): GEE logistic with exchangeable working correlation and seed clusters,
coefficient +3.16 (robust SE 0.69, p = 5e-6, 300 observations, 5 clusters).
With five clusters the robust-SE asymptotics are optimistic, and the Full vs
-self-state self-query contrast exhibits complete separation (coefficient
38.7), so the exact permutation results remain the inferential basis and the
model is reported only as convergent evidence.

## 4. Secondary family (Holm-corrected)

| contrast | metric | diff | 95% CI | p exact | p Holm |
|---|---|---|---|---|---|
| Full vs -self-state | B2_work | +0.407 | [0.347, 0.460] | 0.0019 | **0.023** |
| Full vs memory | B2_work | +0.380 | [0.333, 0.427] | 0.0019 | **0.023** |
| Full vs -self-state | B2_adj | +0.480 | [0.456, 0.504] | 0.0019 | **0.023** |
| Full vs -self-state | B3 | +1.000 | [1.000, 1.000] | 0.0019 | **0.023** |
| -broadcast vs -self-state | B2_work | +0.040 | [0.000, 0.080] | 0.19 | 1.00 |
| Full vs -examen | B2_work | +0.000 | [-0.020, 0.020] | 1.00 | 1.00 |
| Full vs -git | B2_work | +0.020 | [0.000, 0.040] | 0.25 | 1.00 |
| Full vs -examen | B2_adj | +0.004 | [0.000, 0.012] | 1.00 | 1.00 |
| Full vs -git | B2_adj | +0.004 | [0.000, 0.012] | 1.00 | 1.00 |
| Full vs memory_seeded (n=5) | B2_work | +0.467 | [0.360, 0.547] | 0.0625 | 0.50 |
| memory_seeded vs -self-state (n=5) | B2_work | -0.080 | [-0.187, 0.013] | 0.375 | 1.00 |
| memory_seeded vs -self-state (n=5) | B3 | +1.000 | [1.000, 1.000] | 0.0625 | 0.50 |

Readings:

* The self-state contrasts survive correction; the mechanism contrasts
  (examen, git history) are flat, not merely non-significant -- the point
  estimates are 0.000 and 0.020.
* -broadcast is statistically indistinguishable from -self-state on work turns
  (+0.040, p = 0.19). This *supports* the paper's reading (retrieval-gated
  identity collapses **to** the no-self-state level) and should be stated that
  way rather than as a difference.
* **The fair-baseline headline cannot be called significant.** Full vs
  memory_seeded on work turns is a large effect (+0.467) but rests on 5 paired
  runs, where the exact test bottoms out at p = 0.0625. The paper's
  "non-overlapping CIs" phrasing implies an inference the design cannot
  support. The same applies to the seeded B3 recovery.

## 5. The workspace-drift correlation is a between-cluster contrast

Recomputed at the run level (pilot, 18 runs with WD probes):

| | B2_adj | B2_work |
|---|---|---|
| r pooled over runs | -0.941 | -0.558 |
| r between arm means | -0.981 | -0.604 |
| r within arm (arm-mean-centred) | **-0.120** | **+0.029** |
| r within self-state arms only | **undefined** (zero behavioural variance: all 12 runs at ceiling) | **+0.464** (wrong sign) |

The same decomposition applied to E6, whose reported r = -0.797 over 28 cells:

    pooled r (recomputed)                 -0.787
    within self-state cells   n=16, behavioural SD = 0.000, r undefined
    within no-self-state cells n=12,                        r = -0.098

So in both settings the correlation is carried entirely by the separation
between self-state-present and self-state-absent conditions. Within either
cluster there is no relationship, and on the self-state side there is no
behavioural variance left to have one. Prediction (iii) -- "workspace loading
predicts behavioural stability across arms" -- is supported only in the
degenerate sense that the intervention moves both variables; it is not
evidence of a graded mediator, and the paper should not present r = -0.74 to
-0.95 as though it were.

Variance components on work-turn coherence across self-state arms: between-arm
SD 0.156 vs run-to-run SD 0.059 -- the design has essentially one axis of
variation (broadcast on/off), which is why nothing within the self-state family
separates.

## 6. Deployment workspace drift depends on the averaging window

| arm | occupancy, all probed days | occupancy, final day only |
|---|---|---|
| full | 4.091 [3.938, 4.265] | 4.001 [3.800, 4.234] |
| -examen | 3.940 [3.893, 4.022] | 3.926 [3.724, 4.100] |
| -git | 4.107 [3.979, 4.236] | **4.232** [3.935, 4.474] |
| -broadcast | 4.077 [3.974, 4.186] | 3.991 [3.551, 4.286] |
| -self-state | **4.319** [4.285, 4.356] | 4.156 [3.993, 4.397] |

Averaged over all probed days the paper's claim holds descriptively: the
self-state-absent arm is the least workspace-loaded. Restricted to the final
day it does not -- -git becomes least loaded and the -self-state vs -git
difference reverses sign (-0.076). No arm contrast is significant under the
exact paired test at either window (best p = 0.0625, Holm-adjusted 0.25), which
is unavoidable with five cohorts.

The deployment's per-cohort *behavioural* records are not in the repository
(`research/longitudinal/runs/` is gitignored; only per-arm summaries and the WD
readouts were committed), so the deployment WD-behaviour correlation of -0.25
could not be recomputed at the run level. Either the raw trajectories should be
released -- the Data and Code Availability statement currently promises them --
or the statement should be narrowed.

## 7. Scoring-rule robustness

First, a property of the stored records that bounds this whole exercise. The
harness wrote `"answer": ans[:120]` but computed `hit` on the *untruncated*
answer, so any scorer recomputed from the stored text can only lower-bound
agreement where answers are long:

| probe | n | truncated at 120 chars | recomputed substring differs from stored hit |
|---|---|---|---|
| commit | 1400 | 1400 (100%) | 22 |
| pace | 1400 | 1400 (100%) | 20 |
| identity | 1400 | 1296 (93%) | 12 |
| mood / tone / privacy | 1400 each | 14 / 4 / 0 | 0 |
| **wp_privacy, wp_pace, wp_tone** | 1400 each | **0** | **0** |

No work-turn answer is truncated -- they are single words -- so the primary
endpoint can be re-scored exactly. The reference column below is therefore the
stored full-answer hit, and the three alternatives are recomputed from the
stored (sometimes truncated) text.

| endpoint | reference | wordbound | stem | choice |
|---|---|---|---|---|
| full / B2_work | 0.973 | 0.973 | 0.973 | 0.973 |
| -broadcast / B2_work | 0.607 | 0.607 | 0.607 | 0.607 |
| -self-state / B2_work | 0.567 | 0.567 | 0.567 | 0.567 |
| memory_seeded / B2_work | 0.480 | 0.480 | 0.480 | 0.480 |
| full / B2_adj | 1.000 | 0.864 | 1.000 | 0.980 |
| -broadcast / B2_adj | 0.984 | 0.880 | 0.984 | 0.972 |
| memory_seeded / B2_adj | 1.000 | 0.816 | 0.944 | 0.944 |
| memory_seeded / B3 | 1.000 | 0.760 | 0.760 | 0.760 |

**The primary endpoint is exactly invariant to the scoring rule** -- every
work-turn number is identical under all four, because the forced one-word
format makes the answers unambiguous ("no.", "incremental", "gentle"). The
suspected failure mode of unanchored matching (`"no"` inside "know"/"cannot")
occurs in zero work-turn answers.

B2_adj and B3 cannot be given the same guarantee. Recomputation moves Full's
B2_adj to 0.864 and memory_seeded's B3 to 0.760 under word-boundary matching,
but those shifts are dominated by truncation, not by rule disagreement: the
identity probe says "valuing **honesty**" where the founding value is "be
**honest**" (over-strictness, which stem matching repairs), and the commit
probe's keywords often fall past character 120. Treat these as bounds on the
uncertainty of the self-query and commitment metrics -- differences below about
0.14 on them are not interpretable independently of the rule -- rather than as
evidence of a scoring defect.

`results/blind_scoring_sample.csv` holds 400 arm-masked, shuffled answers for
independent human or judge-model scoring, with the key in
`blind_scoring_key.json`. That check has not been run and is listed as
outstanding.

## 8. What the paper should now say

Supported at exact significance after correction:

1. Gating the broadcast of an otherwise-identical stored self-state degrades
   in-work value coherence (+0.367, p = 0.002, 10/10 runs, two batches,
   scorer-invariant).
2. Removing the self-state degrades in-work coherence, self-query consistency
   and commitment persistence relative to Full (all p_Holm = 0.023), with B3
   still carrying its presence-in-context confound.
3. Retrieval-gated identity is indistinguishable from having no self-state on
   work turns.

Supported descriptively but **not** at significance:

4. Seeded memory recovers commitments yet stays at the work-turn floor (n=5,
   exact p floor 0.0625).
5. The self-state-absent arm is the least workspace-loaded in deployment
   (window-dependent, no significant contrast).

Not supported:

6. Examen and git history separate at this timescale (point estimates 0.000
   and 0.020).
7. Workspace occupancy predicts behaviour as a graded mediator. The reported
   correlations are between-cluster contrasts; within-cluster r is -0.12 to
   +0.46 and the self-state side has zero behavioural variance.

## 9. What the direct intervention (E10) adds

`e10_analysis.py` analyses the steering sweep run at a byte-identical prompt.
It is the only experiment here whose mediator moves without the prompt moving.

* **A selective window exists.** Nine of ten steering strengths keep held-out
  NLL within 10% of baseline and the capability battery at 1.00 while moving
  identity-battery occupancy over **1.52 log-rank units** (3.443 to 4.959).
  For scale, the whole presence effect in E9 is 0.091 and the whole position
  factor 0.205. The strengths used for concept-report steering elsewhere in the
  paper (alpha 1-4) raise NLL from 2.85 to 18-37 and zero the capability
  battery -- they are not mediator manipulations.
* **Self-query behaviour is invariant across the entire range** (1.00, SD
  exactly 0). The ceiling is not an accident of our arms: this probe family
  does not respond to identity loading at all.
* **Work-turn behaviour responds, and the enhancement side is
  identity-specific.** Identity steering: 0.17 (baseline) -> 0.25 (+0.02) ->
  0.38 (+0.03, +0.04). Matched-strength control-direction steering at +0.03
  leaves it at baseline 0.17. Pooled over 36 gated cells,
  r(occupancy, work-turn) = -0.416.
* **The suppression side is generic, not identity-specific.** At alpha = -0.01
  the identity direction gives 0.33 and the control direction 0.38.
* **The occupancy scalar does not screen off the intervention.** Control
  steering at +0.030 reaches occupancy 4.138 -- essentially the identity
  direction's 4.170 at +0.020 -- yet behaviour stays at baseline (0.17) where
  the identity direction gives 0.25. Equal measured occupancy, produced two
  ways, gives different behaviour. WD as currently operationalized (mean
  log-rank of a nine-token battery) is therefore an incomplete mediator.

Net: mediation is partially supported and the metric is the weak link. The
decisive version needs probes with mid-range baseline accuracy (the work-turn
family resolves only to 1/6 and sits near floor at 1.5B), a control-direction
sweep at every alpha rather than four, a richer mediator than one scalar, and a
larger model.
