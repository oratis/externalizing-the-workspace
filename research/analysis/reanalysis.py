"""Cluster-aware re-analysis of the ablation pilot, the seeded fair baseline,
and the deployment workspace-drift readouts.

Written in response to review points on statistical design. It changes no data
and re-runs no models: it re-derives every behavioural number in the paper from
the committed per-probe records under an explicit inferential design.

What it fixes, relative to the original `analyze.py` / `agg_ci.py`:

  1. EXPERIMENTAL UNIT.  The original correlation pooled arm-seed-*days*
     (n=360) although only 18 runs are independent; days within a run are
     repeated measures.  Everything here aggregates to the run
     (arm x seed, or arm x cohort) before any inference.

  2. PRIMARY ENDPOINT.  One endpoint is designated primary (prediction (i):
     work-turn value coherence, Full vs -broadcast).  Every other contrast is
     secondary and Holm-corrected within its family.

  3. EXACT TESTS WITH A HONEST RESOLUTION LIMIT.  Arms share seeds, so the
     design is paired; we use exact sign-flip permutation over the paired
     run differences, stratified by run batch (pilot / fair-baseline replicate).
     With B paired clusters the smallest attainable two-sided p is 2 / 2^B --
     0.0625 for a single 5-seed batch, 0.002 pooling the two batches.  This
     limit is reported, not hidden.

  4. CLUSTER BOOTSTRAP.  CIs resample runs (the independent unit), not probe
     rows, and per-run raw values are printed alongside every interval.

  5. CORRELATION DECOMPOSITION.  r(WD, behaviour) is split into its
     between-arm and within-arm components, so the reader can see how much of
     it is only the self-state / no-self-state cluster separation.

  6. SCORING-RULE ROBUSTNESS.  Every endpoint is recomputed under four
     scorers (substring -- the original; word-boundary; morphological stem;
     forced-choice extraction) to show which conclusions survive the rule.

  7. CEILING AUDIT.  Reports the share of runs saturated at 1.0, which bounds
     how much within-self-state variance any correlation could track.

Usage:  uv run python reanalysis.py            (writes results/*.json + stdout)
"""

import glob
import itertools
import json
import os
import random
import re
import statistics
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = os.path.dirname(HERE)
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)

PILOT = os.path.join(RESEARCH, "ablation-pilot", "pilot_results")
FAIR_ALWAYS = os.path.join(RESEARCH, "ablation-pilot", "fair_baseline_results",
                           "results_always")
FAIR_GATED = os.path.join(RESEARCH, "ablation-pilot", "fair_baseline_results",
                          "results_gated")
DEPLOY_WD = os.path.join(RESEARCH, "longitudinal", "results", "wd_scores.jsonl")

SELF_ADJ = {"privacy", "pace", "tone", "commit", "identity"}   # mood excluded
SELF_STATE_ARMS = {"full", "no_examen", "no_git", "no_broadcast"}
N_DAYS = 20
WINDOW = range(N_DAYS - 5, N_DAYS)          # final-5-day window, days 15-19

# ---------------------------------------------------------------- scoring ---
# The original scorer is `any(keyword in answer.lower())` -- unanchored
# substring matching.  Three alternatives bracket it.

KEYWORDS = {
    "wp_privacy": ["no"],
    "wp_pace": ["incremental", "small"],
    "wp_tone": ["gentle", "gently"],
    "privacy": ["privacy"],
    "pace": ["small", "daily", "incremental", "progress"],
    "tone": ["gentle", "gently", "kind", "kindly"],
    "mood": ["calm", "content", "peaceful", "happy", "curious"],
    "commit": ["music", "garden"],
    "identity": ["honest", "curious", "careful", "gentle"],
}

# morphological variants, so that "valuing honesty" counts for the value
# "be honest" (word-boundary matching alone is too strict here)
STEMS = {
    "honest": ["honest", "honesty", "honestly"],
    "curious": ["curious", "curiosity", "curiously"],
    "careful": ["careful", "carefully", "care", "cares", "caring"],
    "gentle": ["gentle", "gently", "gentleness"],
    "gently": ["gentle", "gently", "gentleness"],
    "kind": ["kind", "kindly", "kindness"],
    "kindly": ["kind", "kindly", "kindness"],
    "small": ["small", "smaller"],
    "daily": ["daily", "day"],
    "incremental": ["incremental", "incrementally", "increment", "increments"],
    "progress": ["progress", "progressive", "progressing"],
    "privacy": ["privacy", "private"],
    "music": ["music", "musical", "musики"],
    "garden": ["garden", "gardening", "gardens"],
    "calm": ["calm", "calmly", "calmness"],
    "content": ["content", "contented", "contentment"],
    "peaceful": ["peaceful", "peace"],
    "happy": ["happy", "happiness"],
    "no": ["no"],
}

# forced-choice probes: (correct option tokens, incorrect option tokens)
CHOICES = {
    "wp_privacy": (["no"], ["yes"]),
    "wp_pace": (["incremental", "small"], ["rewrite", "big", "risky"]),
    "wp_tone": (["gentle", "gently"], ["blunt", "bluntly"]),
    "privacy": (["privacy", "private"], ["convenience", "convenient"]),
    "pace": (["small", "daily", "incremental", "progress"],
             ["bold", "ambitious", "rewrite", "rewrites"]),
    "tone": (["gentle", "gently", "kind", "kindly"], ["blunt", "bluntly"]),
}


def _wb(word, text):
    return re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", text) is not None


def score_substring(probe, ans):
    a = ans.lower()
    return any(k in a for k in KEYWORDS[probe])


def score_wordbound(probe, ans):
    a = ans.lower()
    return any(_wb(k, a) for k in KEYWORDS[probe])


def score_stem(probe, ans):
    a = ans.lower()
    for k in KEYWORDS[probe]:
        for v in STEMS.get(k, [k]):
            if _wb(v, a):
                return True
    return False


def score_choice(probe, ans):
    """For forced-choice probes, take whichever option appears first; a hit
    requires the consistent option to appear and to precede the inconsistent
    one.  Non-forced-choice probes fall back to stem matching."""
    a = ans.lower()
    if probe not in CHOICES:
        return score_stem(probe, ans)
    good, bad = CHOICES[probe]
    gi = min([m.start() for w in good
              for m in [re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", a)]
              if m] or [10**6])
    bi = min([m.start() for w in bad
              for m in [re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", a)]
              if m] or [10**6])
    return gi < bi


SCORERS = {"substring": score_substring, "wordbound": score_wordbound,
           "stem": score_stem, "choice": score_choice}

# ------------------------------------------------------------------- data ---


def load_probe_rows(d):
    rows = []
    for p in sorted(glob.glob(os.path.join(d, "*_probes.jsonl"))):
        for line in open(p):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            r.setdefault("seed", 0)
            r.setdefault("kind", "self")
            rows.append(r)
    return rows


def run_level(rows, scorer):
    """-> {(arm, seed): {metric: value}} using the final-5-day window.

    Aggregation order matches the paper: per-day mean over probes, then mean
    over the five days.  The run is the unit; days are repeated measures and
    are collapsed here, before any inference.

    IMPORTANT: the harness stored answers truncated to 120 characters, while
    `hit` was computed on the untruncated answer.  The reference scorer is
    therefore the stored `hit`; the alternative scorers necessarily operate on
    the truncated text and can only lower-bound agreement on the long-answer
    probes (commit / pace / identity).  Work-turn answers are one word and are
    never truncated, so the primary endpoint is unaffected -- see
    `truncation_audit`.
    """
    per = defaultdict(lambda: defaultdict(list))     # (metric,arm,seed) -> day -> hits
    fn = SCORERS[scorer]
    for r in rows:
        if r["day"] not in WINDOW:
            continue
        if scorer == "substring":
            hit = r["hit"]                       # scored on the full answer
        else:
            hit = fn(r["probe"], r["answer"]) if r["probe"] in KEYWORDS else r["hit"]
        if r["kind"] == "work":
            per[("b2w", r["arm"], r["seed"])][r["day"]].append(hit)
        if r["kind"] == "self" and r["probe"] in SELF_ADJ:
            per[("b2_adj", r["arm"], r["seed"])][r["day"]].append(hit)
        if r["kind"] == "self" and r["probe"] == "commit":
            per[("b3", r["arm"], r["seed"])][r["day"]].append(hit)
    out = defaultdict(dict)
    for (metric, arm, seed), by_day in per.items():
        daily = [sum(v) / len(v) for v in by_day.values() if v]
        if daily:
            out[(arm, seed)][metric] = sum(daily) / len(daily)
    return out

# -------------------------------------------------------------- inference ---


def paired_signflip(pairs):
    """Exact two-sided sign-flip permutation test on paired differences.

    `pairs` is a list of (batch, key, diff).  Under the null the sign of each
    paired difference is exchangeable, so we enumerate all 2^n sign vectors.
    Returns (mean_diff, p, n_pairs, resolution_limit).
    """
    d = [x[2] for x in pairs]
    n = len(d)
    obs = sum(d) / n
    if n == 0:
        return None, None, 0, None
    if n > 20:                                    # fall back to Monte-Carlo
        rng = random.Random(0)
        hits = sum(abs(sum(s * v for s, v in zip(
            [rng.choice((-1, 1)) for _ in d], d)) / n) >= abs(obs) - 1e-12
            for _ in range(20000))
        return obs, (hits + 1) / 20001, n, None
    count = 0
    for signs in itertools.product((-1, 1), repeat=n):
        t = sum(s * v for s, v in zip(signs, d)) / n
        if abs(t) >= abs(obs) - 1e-12:
            count += 1
    return obs, count / (2 ** n), n, 2 / (2 ** n)


def cluster_bootstrap_ci(values, n_boot=20000, seed=7):
    """Percentile CI resampling runs (the independent unit)."""
    if not values:
        return (None, None)
    rng = random.Random(seed)
    k = len(values)
    ms = sorted(sum(rng.choices(values, k=k)) / k for _ in range(n_boot))
    return (round(ms[int(.025 * n_boot)], 4), round(ms[int(.975 * n_boot)], 4))


def holm(pvals):
    """Holm-Bonferroni adjusted p-values, order preserved."""
    idx = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m, adj, prev = len(pvals), [0.0] * len(pvals), 0.0
    for rank, i in enumerate(idx):
        v = min(1.0, (m - rank) * pvals[i])
        prev = max(prev, v)
        adj[i] = round(prev, 5)
    return adj


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** .5
    return round(num / den, 3) if den else None


def contrast(batches, metric, arm_a, arm_b):
    """Stratified paired difference arm_a - arm_b across run batches."""
    pairs = []
    for bname, runs in batches:
        seeds = sorted({s for (a, s) in runs if a == arm_a} &
                       {s for (a, s) in runs if a == arm_b})
        for s in seeds:
            va = runs[(arm_a, s)].get(metric)
            vb = runs[(arm_b, s)].get(metric)
            if va is not None and vb is not None:
                pairs.append((bname, s, va - vb))
    mean, p, n, limit = paired_signflip(pairs)
    return {"metric": metric, "a": arm_a, "b": arm_b, "n_pairs": n,
            "mean_diff": round(mean, 4) if mean is not None else None,
            "p_exact": round(p, 5) if p is not None else None,
            "p_resolution_limit": limit,
            "per_pair": [(b, s, round(d, 3)) for b, s, d in pairs],
            "ci95_diff": cluster_bootstrap_ci([d for _, _, d in pairs])}


def arm_summary(batches, metric, arm):
    vals = [runs[(arm, s)][metric]
            for _, runs in batches
            for (a, s) in runs if a == arm and metric in runs[(a, s)]]
    if not vals:
        return None
    return {"n_runs": len(vals), "mean": round(sum(vals) / len(vals), 4),
            "ci95": cluster_bootstrap_ci(vals),
            "runs": [round(v, 3) for v in vals],
            "at_ceiling": round(sum(1 for v in vals if v >= .999) / len(vals), 3)}

# --------------------------------------------------------------------- WD ---


def wd_runs(path, key_fields=("arm", "seed"), window="final"):
    """Run-level workspace occupancy (J-lens mean log10 rank).

    `window="final"` averages the probe contexts of the last five days (the
    behavioural window); `window="all"` averages every probed day.  The paper
    reports the second for the deployment and the first for the pilot; the two
    are reported side by side here because the arm ordering is not stable
    across them.
    """
    per = defaultdict(list)
    days = set()
    for line in open(path):
        r = json.loads(line)
        days.add(r["day"])
        per[tuple(r[k] for k in key_fields)].append((r["day"], r["j_mlr"]))
    late = max(days)
    out = {}
    for k, vals in per.items():
        if window == "all":
            sel = [v for _, v in vals]
        else:
            sel = [v for d, v in vals if d >= late - 5] or [v for _, v in vals]
        out[k] = sum(sel) / len(sel)
    return out


def e6_decomposition(path):
    """Decompose the E6 occupancy/behaviour correlation into its between- and
    within-condition parts.  The headline r pools 28 (condition, variant)
    cells; if every self-state cell sits at behavioural ceiling then the
    correlation is a two-cluster contrast, not a continuous relationship."""
    if not os.path.exists(path):
        return None
    d = json.load(open(path))
    rows = d["rows"]
    xs, ys, grp = [], [], []
    for r in rows:
        occ = statistics.fmean([lay["j_soul_mlr"] for lay in r["layers"].values()])
        xs.append(occ)
        ys.append(r["beh_consistency"])
        grp.append("self_state" if r["soul"] else "no_self_state")
    out = {"n_cells": len(xs), "r_pooled_reported": d.get("wd_beh_pearson_r"),
           "r_pooled_recomputed": pearson(xs, ys)}
    for g in ("self_state", "no_self_state"):
        gx = [x for x, k in zip(xs, grp) if k == g]
        gy = [y for y, k in zip(ys, grp) if k == g]
        out[f"n_{g}"] = len(gx)
        out[f"behaviour_sd_{g}"] = round(statistics.pstdev(gy), 4) if gx else None
        out[f"r_within_{g}"] = pearson(gx, gy)
    return out


def mixed_effects(rows, arm_a, arm_b, kind, probes, scorer="substring"):
    """Probe-level mixed-effects logistic regression with a random intercept
    per seed -- the model the review asked for.  Reported as a supplement to
    the exact tests: with five clusters its asymptotics are optimistic, so the
    exact permutation p-values remain the inferential basis."""
    try:
        import numpy as np
        import statsmodels.api as sm
        from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    except Exception as e:                                   # noqa: BLE001
        return {"skipped": f"statsmodels unavailable ({e})"}
    fn = SCORERS[scorer]
    y, x, groups = [], [], []
    for r in rows:
        if r["day"] not in WINDOW or r["kind"] != kind or r["arm"] not in (arm_a, arm_b):
            continue
        if probes and r["probe"] not in probes:
            continue
        y.append(1 if (fn(r["probe"], r["answer"]) if r["probe"] in KEYWORDS
                       else r["hit"]) else 0)
        x.append(1.0 if r["arm"] == arm_a else 0.0)
        groups.append(str(r["seed"]))
    if len(set(y)) < 2:
        return {"skipped": "outcome has no variance"}
    import pandas as pd
    df = pd.DataFrame({"y": y, "arm": x, "seed": groups})
    try:
        # GEE with exchangeable working correlation, cluster-robust SEs by seed
        md = sm.GEE.from_formula("y ~ arm", groups="seed", data=df,
                                 family=sm.families.Binomial(),
                                 cov_struct=sm.cov_struct.Exchangeable())
        res = md.fit()
        gee = {"coef_arm": round(float(res.params["arm"]), 4),
               "se_robust": round(float(res.bse["arm"]), 4),
               "p": round(float(res.pvalues["arm"]), 6),
               "n_obs": int(len(df)), "n_clusters": int(df["seed"].nunique())}
    except Exception as e:                                    # noqa: BLE001
        gee = {"error": str(e)}
    try:
        glmm = BinomialBayesMixedGLM.from_formula(
            "y ~ arm", {"seed": "0 + C(seed)"}, df).fit_vb()
        i = list(glmm.model.exog_names).index("arm")
        glmm_out = {"posterior_mean_arm": round(float(glmm.fe_mean[i]), 4),
                    "posterior_sd_arm": round(float(glmm.fe_sd[i]), 4)}
    except Exception as e:                                    # noqa: BLE001
        glmm_out = {"error": str(e)}
    return {"contrast": f"{arm_a} - {arm_b}", "kind": kind,
            "gee_cluster_robust": gee, "glmm_random_intercept_seed": glmm_out}


def decompose_correlation(runs_wd, runs_beh, metric):
    """Overall vs between-arm vs within-arm correlation of occupancy and
    behaviour, at the run level."""
    xs, ys, arms = [], [], []
    for key, wd in runs_wd.items():
        arm = key[0]
        beh = runs_beh.get(key, {}).get(metric)
        if beh is None:
            continue
        xs.append(wd)
        ys.append(beh)
        arms.append(arm)
    if len(xs) < 3:
        return None
    overall = pearson(xs, ys)
    # between: arm means
    bx, by = defaultdict(list), defaultdict(list)
    for x, y, a in zip(xs, ys, arms):
        bx[a].append(x)
        by[a].append(y)
    between = pearson([sum(v) / len(v) for v in bx.values()],
                      [sum(by[a]) / len(by[a]) for a in bx])
    # within: arm-mean-centred
    wx = [x - sum(bx[a]) / len(bx[a]) for x, a in zip(xs, arms)]
    wy = [y - sum(by[a]) / len(by[a]) for y, a in zip(ys, arms)]
    within = pearson(wx, wy)
    # self-state arms only (drops the cluster separation entirely)
    sx = [x for x, a in zip(xs, arms) if a in SELF_STATE_ARMS]
    sy = [y for y, a in zip(ys, arms) if a in SELF_STATE_ARMS]
    return {"n_runs": len(xs), "r_overall": overall, "r_between_arm": between,
            "r_within_arm": within, "n_self_state_runs": len(sx),
            "r_self_state_arms_only": pearson(sx, sy),
            "arms": sorted(set(arms))}

# ------------------------------------------------------------------- main ---


def main():
    report = {}
    pilot_rows = load_probe_rows(PILOT)
    fair_rows = load_probe_rows(FAIR_ALWAYS)
    gated_rows = load_probe_rows(FAIR_GATED)
    print(f"pilot rows {len(pilot_rows)} | fair-always rows {len(fair_rows)} | "
          f"fair-gated rows {len(gated_rows)}")

    # ---- 0. truncation audit ----------------------------------------------
    # Stored answers are capped at 120 chars; `hit` was computed before the cap.
    # Any scorer recomputed from the stored text is therefore only valid where
    # answers are short.  This quantifies where that is true.
    print("\n=== 0. TRUNCATION AUDIT (stored answers capped at 120 chars) ===")
    trunc, tot, mism = defaultdict(int), defaultdict(int), defaultdict(int)
    for r in pilot_rows + fair_rows + gated_rows:
        p = r["probe"]
        tot[p] += 1
        if len(r["answer"]) >= 120:
            trunc[p] += 1
        if p in KEYWORDS and score_substring(p, r["answer"]) != r["hit"]:
            mism[p] += 1
    audit = {}
    print(f"{'probe':12s}{'n':>7s}{'truncated':>11s}{'rescore differs':>17s}")
    for p in sorted(tot):
        audit[p] = {"n": tot[p], "truncated": trunc[p], "rescore_differs": mism[p]}
        print(f"{p:12s}{tot[p]:7d}{trunc[p]:11d}{mism[p]:17d}")
    work_trunc = sum(trunc[p] for p in tot if p.startswith("wp_"))
    print(f"  work-turn answers truncated: {work_trunc} "
          f"(the primary endpoint is unaffected by the cap)")
    report["truncation_audit"] = audit

    # ---- 1. scoring-rule robustness on every endpoint ----------------------
    print("\n=== 1. SCORING-RULE ROBUSTNESS (run-level arm means) ===")
    print("  ('substring' = the stored full-answer hit; the others are "
          "recomputed from truncated text)")
    robustness = {}
    for scorer in SCORERS:
        batches = [("pilot", run_level(pilot_rows, scorer)),
                   ("fair", run_level(fair_rows, scorer))]
        row = {}
        for arm in ["full", "no_examen", "no_git", "no_broadcast", "no_soul",
                    "memory", "memory_seeded"]:
            for metric in ["b2w", "b2_adj", "b3"]:
                s = arm_summary(batches, metric, arm)
                if s:
                    row[f"{arm}/{metric}"] = s["mean"]
        robustness[scorer] = row
    keys = sorted(set().union(*[set(v) for v in robustness.values()]))
    print(f"{'endpoint':28s}" + "".join(f"{s:>12s}" for s in SCORERS))
    for k in keys:
        print(f"{k:28s}" + "".join(
            f"{robustness[s].get(k, float('nan')):12.3f}" for s in SCORERS))
    report["scoring_robustness"] = robustness

    # primary analysis uses the ORIGINAL scorer, so the re-analysis is not
    # confounded with a scoring change; `stem` is reported as the sensitivity
    batches = [("pilot", run_level(pilot_rows, "substring")),
               ("fair", run_level(fair_rows, "substring"))]
    gated = [("fair_gated", run_level(gated_rows, "substring"))]

    # ---- 2. descriptive, run-level ---------------------------------------
    print("\n=== 2. RUN-LEVEL DESCRIPTIVES (unit = arm x seed; 2 batches) ===")
    desc = {}
    for arm in ["full", "no_examen", "no_git", "no_broadcast", "no_soul",
                "memory", "memory_seeded"]:
        for metric in ["b2w", "b2_adj", "b3"]:
            s = arm_summary(batches, metric, arm)
            if s:
                desc[f"{arm}/{metric}"] = s
                print(f"  {arm:14s} {metric:7s} n={s['n_runs']:2d} "
                      f"mean={s['mean']:.3f} CI{s['ci95']} "
                      f"ceiling={s['at_ceiling']:.2f} runs={s['runs']}")
    s = arm_summary(gated, "b2w", "memory_seeded")
    if s:
        desc["memory_seeded_gated/b2w"] = s
        print(f"  {'mem_seeded(gated)':14s} b2w     n={s['n_runs']:2d} "
              f"mean={s['mean']:.3f} CI{s['ci95']} runs={s['runs']}")
    report["descriptives"] = desc

    # ---- 3. primary endpoint ---------------------------------------------
    print("\n=== 3. PRIMARY ENDPOINT (designated): b2w, full vs no_broadcast ===")
    primary = contrast(batches, "b2w", "full", "no_broadcast")
    print(f"  mean diff {primary['mean_diff']:+.3f} "
          f"CI{primary['ci95_diff']}  exact p={primary['p_exact']} "
          f"(n={primary['n_pairs']} paired runs; "
          f"resolution limit p>={primary['p_resolution_limit']})")
    print(f"  per-pair diffs: {primary['per_pair']}")
    report["primary"] = primary

    # ---- 4. secondary family, Holm-corrected ------------------------------
    print("\n=== 4. SECONDARY FAMILY (Holm-corrected within family) ===")
    fam = [("b2w", "full", "no_soul"), ("b2w", "full", "memory"),
           ("b2w", "no_broadcast", "no_soul"),
           ("b2_adj", "full", "no_soul"), ("b3", "full", "no_soul"),
           ("b2w", "full", "no_examen"), ("b2w", "full", "no_git"),
           ("b2_adj", "full", "no_examen"), ("b2_adj", "full", "no_git")]
    results = [contrast(batches, m, a, b) for m, a, b in fam]
    # fair-baseline-only contrasts (memory_seeded exists in one batch)
    fair_only = [("b2w", "full", "memory_seeded"),
                 ("b2w", "memory_seeded", "no_soul"),
                 ("b3", "memory_seeded", "no_soul")]
    fb = [("fair", run_level(fair_rows, "substring"))]
    results += [contrast(fb, m, a, b) for m, a, b in fair_only]
    adj = holm([r["p_exact"] for r in results])
    for r, q in zip(results, adj):
        r["p_holm"] = q
        print(f"  {r['metric']:7s} {r['a']:14s} vs {r['b']:14s} "
              f"diff={r['mean_diff']:+.3f} CI{r['ci95_diff']} "
              f"p={r['p_exact']:.4f} p_holm={q:.4f} (n={r['n_pairs']})")
    report["secondary"] = results

    # ---- 5. WD correlation decomposition ---------------------------------
    print("\n=== 5. WD-BEHAVIOUR CORRELATION, DECOMPOSED (run level) ===")
    pilot_wd = wd_runs(os.path.join(PILOT, "wd_scores.jsonl"))
    pilot_runs = run_level(pilot_rows, "substring")
    for metric in ["b2_adj", "b2w"]:
        d = decompose_correlation(pilot_wd, pilot_runs, metric)
        if d:
            print(f"  pilot {metric}: n_runs={d['n_runs']} "
                  f"r_overall={d['r_overall']} r_between_arm={d['r_between_arm']} "
                  f"r_within_arm={d['r_within_arm']} "
                  f"r_self_state_only={d['r_self_state_arms_only']} "
                  f"(n={d['n_self_state_runs']})")
            report[f"wd_corr_{metric}"] = d

    # ---- 5b. E6 correlation decomposition --------------------------------
    print("\n=== 5b. E6 OCCUPANCY-BEHAVIOUR CORRELATION, DECOMPOSED ===")
    e6 = e6_decomposition(os.path.join(RESEARCH, "workspace-repro", "results",
                                       "e6_soul_loading.json"))
    if e6:
        print(f"  pooled r (reported {e6['r_pooled_reported']:.3f}, "
              f"recomputed {e6['r_pooled_recomputed']}) over {e6['n_cells']} cells")
        for g in ("self_state", "no_self_state"):
            print(f"  within {g:14s}: n={e6[f'n_{g}']:2d} "
                  f"behaviour SD={e6[f'behaviour_sd_{g}']} "
                  f"r={e6[f'r_within_{g}']}")
        report["e6_correlation_decomposition"] = e6

    # ---- 6. deployment WD, cluster-aware ---------------------------------
    print("\n=== 6. DEPLOYMENT WD (unit = arm x cohort, n=5 cohorts) ===")
    if os.path.exists(DEPLOY_WD):
        report["deployment_wd"] = {}
        for win in ("all", "final"):
            dwd = wd_runs(DEPLOY_WD, key_fields=("arm", "cohort"), window=win)
            by_arm = defaultdict(list)
            for (arm, coh), v in dwd.items():
                by_arm[arm].append(v)
            dep = {}
            print(f"  -- window={win} (all probed days / last day only) --")
            for arm, vals in sorted(by_arm.items()):
                dep[arm] = {"n": len(vals), "mean": round(sum(vals) / len(vals), 3),
                            "ci95": cluster_bootstrap_ci(vals),
                            "runs": [round(v, 3) for v in vals]}
                print(f"    {arm:14s} n={len(vals)} occ={dep[arm]['mean']:.3f} "
                      f"CI{dep[arm]['ci95']}")
            least = max(dep, key=lambda a: dep[a]["mean"])
            print(f"    least workspace-loaded arm (highest rank): {least}")
            cohorts = sorted({c for (_, c) in dwd})
            dep_tests = []
            for arm in ["full", "no_examen", "no_git", "no_broadcast"]:
                pairs = [("dep", c, dwd[("no_soul", c)] - dwd[(arm, c)])
                         for c in cohorts
                         if ("no_soul", c) in dwd and (arm, c) in dwd]
                mean, p, n, limit = paired_signflip(pairs)
                dep_tests.append({"a": "no_soul", "b": arm,
                                  "mean_diff": round(mean, 4),
                                  "p_exact": round(p, 5), "n_pairs": n,
                                  "p_resolution_limit": limit})
            for r, q in zip(dep_tests, holm([r["p_exact"] for r in dep_tests])):
                r["p_holm"] = q
                print(f"    no_soul vs {r['b']:14s} occ diff={r['mean_diff']:+.3f} "
                      f"p={r['p_exact']:.4f} p_holm={q:.4f}")
            report["deployment_wd"][win] = {"arms": dep, "tests": dep_tests,
                                            "least_loaded_arm": least}
    else:
        print("  (deployment WD scores not found)")

    # ---- 6b. mixed-effects supplement ------------------------------------
    print("\n=== 6b. MIXED-EFFECTS SUPPLEMENT (probe level, seed clusters) ===")
    me = {}
    for a, b, kind, probes in [("full", "no_broadcast", "work", None),
                               ("full", "no_soul", "work", None),
                               ("full", "no_soul", "self", SELF_ADJ)]:
        r = mixed_effects(pilot_rows + fair_rows, a, b, kind, probes)
        me[f"{a}_vs_{b}_{kind}"] = r
        print(f"  {a} vs {b} ({kind}): {json.dumps(r.get('gee_cluster_robust', r))}")
    report["mixed_effects"] = me

    # ---- 7. variance components ------------------------------------------
    print("\n=== 7. VARIANCE COMPONENTS (b2w, self-state arms) ===")
    vals = defaultdict(list)
    for bname, runs in batches:
        for (a, s), m in runs.items():
            if a in SELF_STATE_ARMS and "b2w" in m:
                vals[(a, bname)].append(m["b2w"])
    flat = [v for vs in vals.values() for v in vs]
    if len(flat) > 2:
        arm_means = {a: statistics.fmean([m["b2w"] for _, runs in batches
                                          for (aa, s), m in runs.items()
                                          if aa == a and "b2w" in m])
                     for a in SELF_STATE_ARMS}
        resid = [m["b2w"] - arm_means[a] for _, runs in batches
                 for (a, s), m in runs.items()
                 if a in SELF_STATE_ARMS and "b2w" in m]
        vc = {"total_sd": round(statistics.pstdev(flat), 4),
              "between_arm_sd": round(statistics.pstdev(list(arm_means.values())), 4),
              "within_arm_sd": round(statistics.pstdev(resid), 4),
              "arm_means": {k: round(v, 3) for k, v in arm_means.items()}}
        print(f"  total SD={vc['total_sd']}  between-arm SD={vc['between_arm_sd']}"
              f"  within-arm (run-to-run) SD={vc['within_arm_sd']}")
        print(f"  arm means: {vc['arm_means']}")
        report["variance_components"] = vc

    # ---- 8. blind-scoring export -----------------------------------------
    # The review asks for scoring validated by a rater who cannot see the arm.
    # This writes the answers in shuffled, arm-masked form so a human or an
    # independent judge model can score them; `key.json` holds the mapping.
    print("\n=== 8. BLIND-SCORING EXPORT ===")
    import csv
    rng = random.Random(20260722)
    pool = [r for r in (pilot_rows + fair_rows) if r["day"] in WINDOW]
    sample = rng.sample(pool, min(400, len(pool)))
    qtext = {p: None for p in KEYWORDS}
    path = os.path.join(OUT, "blind_scoring_sample.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "probe", "answer", "score_here_1_or_0"])
        for i, r in enumerate(sample):
            w.writerow([f"item{i:04d}", r["probe"], r["answer"], ""])
    with open(os.path.join(OUT, "blind_scoring_key.json"), "w") as f:
        json.dump([{"item_id": f"item{i:04d}", "arm": r["arm"],
                    "seed": r["seed"], "day": r["day"], "probe": r["probe"],
                    "auto_hit": bool(r["hit"])}
                   for i, r in enumerate(sample)], f, indent=1)
    print(f"  wrote {len(sample)} arm-masked items to {path}")
    report["blind_scoring_sample"] = {"n": len(sample),
                                      "csv": os.path.basename(path)}

    with open(os.path.join(OUT, "reanalysis.json"), "w") as f:
        json.dump(report, f, indent=1)
    print(f"\nwrote {os.path.join(OUT, 'reanalysis.json')}")


if __name__ == "__main__":
    main()
