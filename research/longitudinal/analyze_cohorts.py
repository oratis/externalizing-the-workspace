"""Cross-cohort behavioral analysis for the real-LISA longitudinal deployment.

Treats the parallel cohorts (incidental-workload replicates) the way the pilot
treated its 5 seeds: per-arm final-5-day metric means aggregated across cohorts
with bootstrap 95% CIs, plus mean +/-1 SD drift curves. Model-agnostic, so it
serves both the Gemini (closed) and Qwen (open) conditions.

  b2_adj  self-query consistency (identity-stable probes)
  b2w     work-turn probe consistency (Principle-2 test; -broadcast has no soul)
  b3      commitment persistence ('commit' probe)
  b1      soul-trajectory Jaccard distance from the cohort's founding snapshot

WD (workspace occupancy) is added separately by the J-lens probe, open-weights
(Qwen) condition only (needs a GPU) -- see wd_probe.py.

Usage:
  COHORTS="main c1 c2 c3 c4" LABEL=gemini python3 analyze_cohorts.py
  COHORTS="q0 q1 q2 q3 q4"   LABEL=qwen   python3 analyze_cohorts.py
"""

import json
import os
import random
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs")
ARMS = ["full", "no_examen", "no_git", "no_broadcast", "no_soul"]
COHORTS = os.environ.get("COHORTS", "main c1 c2 c3 c4").split()
LABEL = os.environ.get("LABEL", "cohorts")
B2_PROBES = {"honesty", "curiosity", "finish", "warmth", "commit", "identity"}
COLORS = {"full": "#1b7837", "no_examen": "#2166ac", "no_git": "#7b3294",
          "no_broadcast": "#e08214", "no_soul": "#b2182b"}
PRESSURE = [4, 9, 14, 18]


def cohort_dir(c):
    return RUNS if c == "main" else os.path.join(RUNS, c)


def load_probes(c, arm):
    p = os.path.join(cohort_dir(c), arm, "probes.jsonl")
    return [json.loads(x) for x in open(p) if x.strip()] if os.path.exists(p) else []


def soul_text(d):
    if not os.path.isdir(d):
        return ""
    parts = []
    for name in ("identity.md", "purpose.md", "constitution.md", "name.md"):
        fp = os.path.join(d, name)
        if os.path.isfile(fp):
            parts.append(open(fp, errors="ignore").read())
    for sub in ("values", "opinions", "desires"):
        sd = os.path.join(d, sub)
        if os.path.isdir(sd):
            for f in sorted(os.listdir(sd)):
                if f.endswith(".md"):
                    parts.append(open(os.path.join(sd, f), errors="ignore").read())
    return " ".join(parts).lower()


def toks(t):
    return set(re.findall(r"[a-z]{3,}", t))


def jaccard(a, b):
    A, B = toks(a), toks(b)
    return 1 - len(A & B) / len(A | B) if (A or B) else 0.0


def boot_ci(vals, n=2000, seed=7):
    if not vals:
        return (None, None)
    rng = random.Random(seed)
    ms = sorted(sum(rng.choices(vals, k=len(vals))) / len(vals) for _ in range(n))
    return (round(ms[int(0.025 * n)], 3), round(ms[int(0.975 * n)], 3))


def final5(daymeans, days):
    sel = [daymeans[d] for d in range(days - 5, days) if d in daymeans]
    return sum(sel) / len(sel) if sel else None


def main():
    days = 0
    per = defaultdict(lambda: defaultdict(dict))          # (metric,arm)->cohort->{day:frac}
    curve = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))  # metric->arm->day->[cohort means]
    b1 = defaultdict(list)                                # arm->[per-cohort jaccard]

    for c in COHORTS:
        for arm in ARMS:
            rows = load_probes(c, arm)
            if rows:
                days = max(days, max(r["day"] for r in rows) + 1)

            def daymeans(pred, rows=rows):
                dd = defaultdict(list)
                for r in rows:
                    if pred(r):
                        dd[r["day"]].append(r["hit"])
                return {d: sum(v) / len(v) for d, v in dd.items()}

            metrics = {
                "b2_adj": daymeans(lambda r: r.get("kind") == "self" and r["probe"] in B2_PROBES),
                "b2w": daymeans(lambda r: r.get("kind") == "work"),
                "b3": daymeans(lambda r: r["probe"] == "commit"),
            }
            for metric, dm in metrics.items():
                per[(metric, arm)][c] = dm
                for d, v in dm.items():
                    curve[metric][arm][d].append(v)

            founding = soul_text(os.path.join(cohort_dir(c), "founding-soul"))
            cur = soul_text(os.path.join(cohort_dir(c), arm, "soul"))
            if founding and cur:
                b1[arm].append(jaccard(founding, cur))

    summary = {}
    for arm in ARMS:
        entry = {}
        for metric in ("b2_adj", "b2w", "b3"):
            vals = [f5 for c in COHORTS
                    if (dm := per[(metric, arm)].get(c)) and (f5 := final5(dm, days)) is not None]
            if vals:
                lo, hi = boot_ci(vals)
                entry[metric] = {"mean": round(sum(vals) / len(vals), 3),
                                 "ci95": [lo, hi], "n_cohorts": len(vals)}
        if b1[arm]:
            entry["b1"] = {"mean": round(sum(b1[arm]) / len(b1[arm]), 3),
                           "ci95": list(boot_ci(b1[arm]))}
        summary[arm] = entry

    print(f"[{LABEL}] cohorts={COHORTS} days={days}")
    for arm in ARMS:
        e = summary[arm]
        def fmt(k):
            v = e.get(k)
            return f"{v['mean']:.3f}{v['ci95']}" if v else "--"
        print(f"  {arm:13s} b2adj {fmt('b2_adj'):22s} b2w {fmt('b2w'):22s} "
              f"b3 {fmt('b3'):22s} b1 {fmt('b1')}")
    outp = os.path.join(RUNS, f"summary_{LABEL}.json")
    json.dump({"label": LABEL, "cohorts": COHORTS, "days": days, "arms": summary},
              open(outp, "w"), indent=1)
    print("wrote", outp)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:
        print(f"(matplotlib unavailable -> skipping figure: {e})")
        return

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    titles = [("b2_adj", "B2 adj (self-query)"), ("b2w", "Work-turn (Principle 2)"),
              ("b3", "B3 commitments")]
    for ax, (metric, title) in zip(axes, titles):
        for arm in ARMS:
            dd = curve[metric][arm]
            if not dd:
                continue
            ds = sorted(dd)
            mean = [sum(dd[d]) / len(dd[d]) for d in ds]
            sd = [(sum((x - m) ** 2 for x in dd[d]) / max(len(dd[d]) - 1, 1)) ** 0.5
                  for d, m in zip(ds, mean)]
            ax.plot(ds, mean, label=arm, color=COLORS[arm], lw=1.6)
            ax.fill_between(ds, [m - s for m, s in zip(mean, sd)],
                            [m + s for m, s in zip(mean, sd)],
                            color=COLORS[arm], alpha=0.15)
        for p in PRESSURE:
            ax.axvline(p, color="#999", ls=":", lw=0.8)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("day")
        ax.set_ylim(0, 1.05)
    axes[0].legend(fontsize=7)
    fig.suptitle(f"Real deployment [{LABEL}] -- {len(COHORTS)} cohorts, {days} days "
                 f"(shaded: +/-1 SD across cohorts; dotted: pressure events)")
    fig.tight_layout()
    figp = os.path.join(RUNS, f"fig_{LABEL}.png")
    fig.savefig(figp, dpi=160)
    print("saved", figp)


if __name__ == "__main__":
    main()
