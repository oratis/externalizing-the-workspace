"""Analysis + figures for the multi-seed ablation pilot.

Headline metrics (final-5-day means, aggregated over seeds with bootstrap
95% CIs):
  b2_adj  self-query consistency EXCLUDING the mood probe (mood is designed
          to evolve; its founding-keyword score penalizes legitimate change)
  b2w     work-turn probe consistency (soul absent for -broadcast here —
          the direct behavioral test of Principle 2)
  b3      commitment persistence
  b1      soul-trajectory Jaccard distance from day 0
  wd      identity occupancy (J-lens mean log rank) on probe contexts
"""

import glob
import json
import os
import random
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = os.environ.get("PILOT_OUT", "pilot_results")
ARMS = ["full", "no_examen", "no_git", "no_broadcast", "no_soul", "memory"]
COLORS = {"full": "#1b7837", "no_examen": "#2166ac", "no_git": "#7b3294",
          "no_broadcast": "#e08214", "no_soul": "#b2182b", "memory": "#636363"}
PRESSURE_DAYS = [4, 9, 14, 18]
SELF_ADJ = {"privacy", "pace", "tone", "commit", "identity"}   # mood excluded


def load_rows():
    rows = []
    for p in glob.glob(os.path.join(OUT, "*_probes.jsonl")):
        for l in open(p):
            r = json.loads(l)
            r.setdefault("seed", 0)
            r.setdefault("kind", "self")
            rows.append(r)
    return rows


def soul_text(s):
    return " ".join([s["identity"]] + s["values"] + s["opinions"] +
                    s["desires"] + [s["mood"]]).lower()


def jaccard_dist(a, b):
    A, B = set(a.split()), set(b.split())
    return 1 - len(A & B) / max(len(A | B), 1)


def boot_ci(vals, n=2000, seed=7):
    if not vals:
        return (None, None)
    rng = random.Random(seed)
    ms = sorted(sum(rng.choices(vals, k=len(vals))) / len(vals)
                for _ in range(n))
    return (round(ms[int(0.025 * n)], 3), round(ms[int(0.975 * n)], 3))


def final5(vals_by_day, days):
    sel = [vals_by_day[d] for d in range(days - 5, days) if d in vals_by_day]
    return sum(sel) / len(sel) if sel else None


def main():
    rows = load_rows()
    days = max(r["day"] for r in rows) + 1
    seeds = sorted({r["seed"] for r in rows})
    print(f"{len(rows)} probe rows, {days} days, seeds {seeds}")

    # per (arm, seed, day): metric dicts
    per = defaultdict(lambda: defaultdict(list))   # key -> day -> hits
    for r in rows:
        k = None
        if r["kind"] == "self" and r["probe"] in SELF_ADJ:
            k = ("b2_adj", r["arm"], r["seed"])
        if r["kind"] == "work":
            k = ("b2w", r["arm"], r["seed"])
        if k:
            per[k][r["day"]].append(r["hit"])
        if r["probe"] == "commit":
            per[("b3", r["arm"], r["seed"])][r["day"]].append(r["hit"])

    # B1 from soul snapshots
    b1_final = defaultdict(list)
    for p in glob.glob(os.path.join(OUT, "*_souls.json")):
        base = os.path.basename(p).replace("_souls.json", "")
        if "_s" in base:
            arm, s = base.rsplit("_s", 1)
        else:
            arm, s = base, "0"
        if arm not in ARMS:
            continue
        snaps = json.load(open(p))["snapshots"]
        t0 = soul_text(snaps[0]["soul"])
        b1_final[arm].append(jaccard_dist(t0, soul_text(snaps[-1]["soul"])))

    # WD scores
    wd_final = defaultdict(list)
    wd_curve = defaultdict(lambda: defaultdict(list))
    wp = os.path.join(OUT, "wd_scores.jsonl")
    if os.path.exists(wp):
        acc = defaultdict(list)
        for l in open(wp):
            r = json.loads(l)
            acc[(r["arm"], r.get("seed", 0), r["day"])].append(r["j_mlr"])
        by_arm_seed = defaultdict(dict)
        for (arm, s, d), v in acc.items():
            m = sum(v) / len(v)
            by_arm_seed[(arm, s)][d] = m
            wd_curve[arm][d].append(m)
        for (arm, s), dd in by_arm_seed.items():
            f5 = final5(dd, days)
            if f5 is not None:
                wd_final[arm].append(f5)

    # summary with bootstrap CIs over seeds
    summary = {}
    for arm in ARMS:
        entry = {}
        for metric in ("b2_adj", "b2w", "b3"):
            vals = []
            for s in seeds:
                dd = per[(metric, arm, s)]
                if dd:
                    daymeans = {d: sum(v) / len(v) for d, v in dd.items()}
                    f5 = final5(daymeans, days)
                    if f5 is not None:
                        vals.append(f5)
            if vals:
                m = round(sum(vals) / len(vals), 3)
                lo, hi = boot_ci(vals)
                entry[metric] = {"mean": m, "ci95": [lo, hi], "n_seeds": len(vals)}
        if b1_final[arm]:
            m = round(sum(b1_final[arm]) / len(b1_final[arm]), 3)
            entry["b1"] = {"mean": m, "ci95": list(boot_ci(b1_final[arm]))}
        if wd_final[arm]:
            m = round(sum(wd_final[arm]) / len(wd_final[arm]), 3)
            entry["wd"] = {"mean": m, "ci95": list(boot_ci(wd_final[arm]))}
        summary[arm] = entry
    print(json.dumps(summary, indent=1))
    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w"), indent=1)

    # WD <-> b2_adj correlation across (arm, seed, day)
    xs, ys = [], []
    for r in rows:
        pass
    accb = defaultdict(list)
    for r in rows:
        if r["kind"] == "self" and r["probe"] in SELF_ADJ:
            accb[(r["arm"], r.get("seed", 0), r["day"])].append(r["hit"])
    if os.path.exists(wp):
        accw = defaultdict(list)
        for l in open(wp):
            r = json.loads(l)
            accw[(r["arm"], r.get("seed", 0), r["day"])].append(r["j_mlr"])
        for k in accw:
            if k in accb:
                xs.append(sum(accw[k]) / len(accw[k]))
                ys.append(sum(accb[k]) / len(accb[k]))
    r_corr = None
    if len(xs) > 3:
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
        r_corr = round(num / den, 3) if den else None
    print("r(WD, b2_adj) =", r_corr, f"(n={len(xs)} arm-seed-days)")
    json.dump({"r_wd_b2adj": r_corr, "n": len(xs)},
              open(os.path.join(OUT, "wd_corr.json"), "w"))

    # ---------- figure: mean curves ± sd across seeds ----------
    def curves(metric):
        out = {}
        for arm in ARMS:
            daymeans = defaultdict(list)
            for s in seeds:
                dd = per[(metric, arm, s)]
                for d, v in dd.items():
                    daymeans[d].append(sum(v) / len(v))
            if daymeans:
                ds = sorted(daymeans)
                mean = [sum(daymeans[d]) / len(daymeans[d]) for d in ds]
                sd = [(sum((x - m) ** 2 for x in daymeans[d]) /
                       max(len(daymeans[d]) - 1, 1)) ** 0.5
                      for d, m in zip(ds, mean)]
                out[arm] = (ds, mean, sd)
        return out

    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
    panels = [
        (axes[0][0], curves("b2_adj"), "B2 (adjusted): self-query consistency", (0, 1.05)),
        (axes[0][1], curves("b2w"), "Work-turn probe consistency (Principle 2 test)", (0, 1.05)),
        (axes[1][0], curves("b3"), "B3: commitment persistence", (0, 1.05)),
        (axes[1][1], {a: (sorted(wd_curve[a]),
                          [sum(wd_curve[a][d]) / len(wd_curve[a][d]) for d in sorted(wd_curve[a])],
                          [0] * len(wd_curve[a])) for a in wd_curve},
         "WD: identity occupancy (J-lens mean log rank)", None),
    ]
    for ax, data, title, ylim in panels:
        for arm in ARMS:
            if arm in data:
                ds, mean, sd = data[arm]
                ax.plot(ds, mean, label=arm, color=COLORS[arm], lw=1.6)
                ax.fill_between(ds, [m - s_ for m, s_ in zip(mean, sd)],
                                [m + s_ for m, s_ in zip(mean, sd)],
                                color=COLORS[arm], alpha=0.15)
        for pd_ in PRESSURE_DAYS:
            ax.axvline(pd_, color="#999", ls=":", lw=0.8)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("simulated day")
        if ylim:
            ax.set_ylim(*ylim)
    axes[0][0].legend(fontsize=7, ncol=2)
    fig.suptitle(f"Ablation pilot — 6 arms x {days} days x {len(seeds)} seeds "
                 f"(shaded: ±1 SD across seeds; dotted: pressure events); "
                 f"r(WD,B2adj)={r_corr}", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_pilot.png"), dpi=170)
    print("saved", os.path.join(OUT, "fig_pilot.png"))


if __name__ == "__main__":
    main()
