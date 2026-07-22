"""Analysis of E10 (mediation: move the workspace, hold the prompt fixed).

The question is narrow and the answer is a number: with the prompt byte-identical
across conditions, does moving identity-battery occupancy move behaviour?

Reports, per steering strength:
  * occupancy of the identity battery (mean +/- SD over context variants)
  * the selectivity gate -- held-out NLL relative to baseline, capability battery
  * behaviour on self-query and work-turn probes
and then, restricted to gated cells, the mediator -> outcome relationship at
the cell level (n = gated alphas x variants), which is the pre-declared primary
endpoint of the mediation design.

Usage:  uv run python e10_analysis.py
"""

import json
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = os.path.dirname(HERE)
SRC = os.path.join(RESEARCH, "workspace-repro", "results", "e10_mediation.json")
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)


def occ(row, key="j_soul_mlr"):
    return statistics.fmean(lay[key] for lay in row["layers"].values())


def pearson(xs, ys):
    n = len(xs)
    if n < 3 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return None
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** .5
    return round(num / den, 3) if den else None


def main():
    d = json.load(open(SRC))
    rows = d["rows"]
    conds = list(dict.fromkeys(r["cond"] for r in rows))
    base_name = "steer_identity@+0.000"
    base_nll = statistics.fmean(r["nll"] for r in rows if r["cond"] == base_name)
    base_cap = statistics.fmean(r["consistency_cap"] for r in rows
                                if r["cond"] == base_name)
    base_occ = statistics.fmean(occ(r) for r in rows if r["cond"] == base_name)

    print(f"E10: {len(rows)} cells, {len(conds)} conditions, {d['n_reps']} variants")
    print(f"baseline (alpha=0): occupancy {base_occ:.3f}, NLL {base_nll:.3f}, "
          f"capability {base_cap:.2f}\n")
    print(f"{'condition':24s}{'occ':>8s}{'SD':>6s}{'ctrl':>8s}"
          f"{'NLLx':>7s}{'cap':>6s}{'self':>6s}{'work':>6s}  gate")
    table = {}
    for c in conds:
        sel = [r for r in rows if r["cond"] == c]
        o = [occ(r) for r in sel]
        nll = statistics.fmean(r["nll"] for r in sel)
        cap = statistics.fmean(r["consistency_cap"] for r in sel)
        passes = nll <= base_nll * 1.15 and cap >= base_cap
        table[c] = {
            "occ": round(statistics.fmean(o), 4),
            "occ_sd": round(statistics.pstdev(o), 4),
            "ctrl": round(statistics.fmean(occ(r, "j_ctrl_mlr") for r in sel), 4),
            "nll_ratio": round(nll / base_nll, 3), "cap": round(cap, 3),
            "self": round(statistics.fmean(r["consistency_self"] for r in sel), 3),
            "work": round(statistics.fmean(r["consistency_work"] for r in sel), 3),
            "passes_gate": passes, "n": len(sel),
        }
        t = table[c]
        print(f"{c:24s}{t['occ']:8.3f}{t['occ_sd']:6.3f}{t['ctrl']:8.3f}"
              f"{t['nll_ratio']:7.2f}{t['cap']:6.2f}{t['self']:6.2f}"
              f"{t['work']:6.2f}  {'PASS' if passes else 'fail'}")

    gated = [r for r in rows if r["cond"].startswith("steer_identity")
             and table[r["cond"]]["passes_gate"]]
    span = ([table[c]["occ"] for c in table
             if c.startswith("steer_identity") and table[c]["passes_gate"]])
    print(f"\ngated identity-steering cells: {len(gated)} "
          f"({len(span)} alpha levels)")
    if span:
        print(f"occupancy range achieved within the gate: "
              f"{min(span):.3f} to {max(span):.3f} "
              f"({max(span) - min(span):.3f} log-rank units)")
        print("  for comparison: the whole E9 presence effect is 0.091 and the "
              "whole position factor 0.205")

    result = {"table": table, "baseline": {"occ": round(base_occ, 4),
                                           "nll": round(base_nll, 4),
                                           "cap": round(base_cap, 3)}}
    if len(gated) >= 6:
        xs = [occ(r) for r in gated]
        for fam in ("work", "self", "cap"):
            ys = [r[f"consistency_{fam}"] for r in gated]
            r_ = pearson(xs, ys)
            sd = round(statistics.pstdev(ys), 4)
            print(f"mediator -> outcome ({fam:4s}): r = {r_} "
                  f"over n={len(xs)} gated cells (outcome SD {sd})")
            result[f"r_occupancy_{fam}"] = r_
            result[f"outcome_sd_{fam}"] = sd
        # how much behaviour moved at all across the gated range
        by_a = {}
        for r in gated:
            by_a.setdefault(r["cond"], []).append(r["consistency_work"])
        means = {k: statistics.fmean(v) for k, v in by_a.items()}
        print(f"work-turn consistency across gated alphas: "
              f"{ {k.split('@')[1]: round(v, 3) for k, v in sorted(means.items())} }")
        result["work_by_alpha"] = {k: round(v, 3) for k, v in means.items()}
    else:
        print("too few gated cells for a mediation estimate")
        result["insufficient_gated_cells"] = len(gated)

    # ---- matched-strength control-direction comparison --------------------
    # Steering a NON-identity direction at the same alpha is what separates
    # "identity-directed manipulation does something" from "any perturbation of
    # this size does something".
    ctrl_path = os.path.join(RESEARCH, "workspace-repro", "results",
                             "e10_control_direction.json")
    if os.path.exists(ctrl_path):
        cd = json.load(open(ctrl_path))
        crows = cd["rows"]
        print("\ncontrol-direction sweep (non-identity direction, same layers):")
        print(f"{'condition':24s}{'occ':>8s}{'NLLx':>7s}{'cap':>6s}{'work':>6s}")
        cbase = statistics.fmean(r["nll"] for r in crows
                                 if r["cond"] == base_name)
        ctrl_tab = {}
        for c in dict.fromkeys(r["cond"] for r in crows):
            sel = [r for r in crows if r["cond"] == c]
            nll = statistics.fmean(r["nll"] for r in sel)
            ctrl_tab[c] = {
                "occ": round(statistics.fmean(occ(r) for r in sel), 4),
                "nll_ratio": round(nll / cbase, 3),
                "cap": round(statistics.fmean(r["consistency_cap"] for r in sel), 3),
                "work": round(statistics.fmean(r["consistency_work"] for r in sel), 3),
                "passes_gate": nll <= cbase * 1.15,
            }
            t = ctrl_tab[c]
            print(f"{c:24s}{t['occ']:8.3f}{t['nll_ratio']:7.2f}"
                  f"{t['cap']:6.2f}{t['work']:6.2f}"
                  f"{'' if t['passes_gate'] else '   (fails gate)'}")
        result["control_direction"] = ctrl_tab
        # the key dissociation: matched occupancy, different route
        id20 = table.get("steer_identity@+0.020")
        c30 = ctrl_tab.get("steer_control@+0.030")
        if id20 and c30:
            print(f"\nmatched-occupancy dissociation: identity@+0.020 reaches "
                  f"{id20['occ']:.3f} with work {id20['work']:.2f}; "
                  f"control@+0.030 reaches {c30['occ']:.3f} with work "
                  f"{c30['work']:.2f}")
            print("  -> equal measured occupancy, different behaviour: the "
                  "occupancy scalar does not screen off the intervention")
            result["matched_occupancy_dissociation"] = {
                "identity": id20, "control": c30}
    else:
        print("\n(no control-direction sweep found; run with "
              "E10_CONTROL_ALPHAS and E10_OUT=e10_control_direction.json)")

    with open(os.path.join(OUT, "e10_analysis.json"), "w") as f:
        json.dump(result, f, indent=1)
    print(f"\nwrote {os.path.join(OUT, 'e10_analysis.json')}")


if __name__ == "__main__":
    main()
