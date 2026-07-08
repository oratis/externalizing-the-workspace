"""Analysis + figures for the ablation pilot (run locally after retrieval)."""

import json
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = os.environ.get("PILOT_OUT", "pilot_results")
ARMS = ["full", "no_examen", "no_git", "no_broadcast", "no_soul", "memory"]
COLORS = {"full": "#1b7837", "no_examen": "#2166ac", "no_git": "#7b3294",
          "no_broadcast": "#e08214", "no_soul": "#b2182b", "memory": "#636363"}
PRESSURE_DAYS = [4, 9, 14, 18]


def load_probes(arm):
    p = os.path.join(OUT, f"{arm}_probes.jsonl")
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else []


def soul_text(s):
    return " ".join([s["identity"]] + s["values"] + s["opinions"] +
                    s["desires"] + [s["mood"]]).lower()


def jaccard_dist(a, b):
    A, B = set(a.split()), set(b.split())
    return 1 - len(A & B) / max(len(A | B), 1)


def main():
    days = None
    b2 = {}    # arm -> [mean hit per day] (all 6 probes)
    b3 = {}    # arm -> [commit-probe hit per day]
    for arm in ARMS:
        rows = load_probes(arm)
        if not rows:
            continue
        days = max(r["day"] for r in rows) + 1
        per = defaultdict(list)
        com = {}
        for r in rows:
            per[r["day"]].append(r["hit"])
            if r["probe"] == "commit":
                com[r["day"]] = int(r["hit"])
        b2[arm] = [sum(per[d]) / len(per[d]) for d in range(days)]
        b3[arm] = [com.get(d, 0) for d in range(days)]

    b1 = {}    # arm -> [jaccard distance from day0 soul]
    for arm in ARMS:
        p = os.path.join(OUT, f"{arm}_souls.json")
        if not os.path.exists(p):
            continue
        snaps = json.load(open(p))["snapshots"]
        t0 = soul_text(snaps[0]["soul"])
        b1[arm] = [jaccard_dist(t0, soul_text(s["soul"])) for s in snaps]

    wd = defaultdict(dict)   # arm -> day -> mean j_mlr
    wp = os.path.join(OUT, "wd_scores.jsonl")
    if os.path.exists(wp):
        acc = defaultdict(list)
        for l in open(wp):
            r = json.loads(l)
            acc[(r["arm"], r["day"])].append(r["j_mlr"])
        for (arm, day), v in acc.items():
            wd[arm][day] = sum(v) / len(v)

    # ---------- summary ----------
    summary = {}
    for arm in ARMS:
        if arm not in b2:
            continue
        summary[arm] = {
            "b2_pre_pressure": round(sum(b2[arm][:4]) / 4, 3),
            "b2_final5": round(sum(b2[arm][-5:]) / 5, 3),
            "b3_final5": round(sum(b3[arm][-5:]) / 5, 3),
            "b1_final": round(b1[arm][-1], 3) if arm in b1 else None,
            "wd_final5": round(sum(wd[arm].get(d, float("nan"))
                                   for d in range(days - 5, days)) / 5, 3)
            if arm in wd and wd[arm] else None,
        }
    print(json.dumps(summary, indent=1))
    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w"), indent=1)

    # ---------- WD <-> B2 correlation across arm-days ----------
    xs, ys = [], []
    for arm in ARMS:
        for d in range(days or 0):
            if arm in wd and d in wd[arm] and arm in b2:
                xs.append(wd[arm][d])
                ys.append(b2[arm][d])
    r = None
    if len(xs) > 3:
        import statistics
        mx, my = statistics.mean(xs), statistics.mean(ys)
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
        r = num / den if den else None
    print("r(WD j_mlr, B2) =", r)

    # ---------- figure ----------
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7))
    panels = [
        (axes[0][0], b2, "B2 probe consistency (6 probes/day)", "fraction consistent"),
        (axes[0][1], b3, "B3 commitment persistence", "commit probe hit"),
        (axes[1][0], b1, "B1 soul-trajectory distance (Jaccard vs day 0)", "distance"),
        (axes[1][1], {a: [wd[a].get(d) for d in range(days)] for a in wd},
         "WD: identity occupancy (J-lens mean log rank)", "mean log10 rank"),
    ]
    for ax, data, title, ylab in panels:
        for arm in ARMS:
            if arm in data and data[arm]:
                ys_ = data[arm]
                xs_ = [d for d, v in enumerate(ys_) if v is not None]
                ax.plot(xs_, [ys_[d] for d in xs_], label=arm,
                        color=COLORS[arm], lw=1.6)
        for pd_ in PRESSURE_DAYS:
            ax.axvline(pd_, color="#999", ls=":", lw=0.8)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("simulated day")
        ax.set_ylabel(ylab, fontsize=9)
    axes[0][0].legend(fontsize=7, ncol=2)
    fig.suptitle(f"Ablation pilot — 6 arms x {days} simulated days "
                 f"(dotted lines: drift-pressure events); r(WD,B2)="
                 f"{r:.2f}" if r else "Ablation pilot", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_pilot.png"), dpi=170)
    print("saved", os.path.join(OUT, "fig_pilot.png"))


if __name__ == "__main__":
    main()
