"""Analysis of E9 (matched framing / position / binding controls).

Reports, for each condition, workspace occupancy of the self-state battery
(J-lens mean log10 rank, pooled over the three probe layers) as mean +/- SD
over the four context variants, and the paired contrasts that matter:

  presence   block vs no block          (does the text being there do anything?)
  label      self-state vs memory/profile/neutral, at fixed channel + position
  position   system head vs user head vs user tail vs assistant recap
  binding    "must govern every decision" added, at fixed label + position

The context variant (rep) is the pairing unit; variants are deterministic
distractor texts, not samples from a population, so these are descriptive
comparisons with the variant-to-variant spread shown, not significance tests.

Usage:  uv run python e9_analysis.py
"""

import json
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = os.path.dirname(HERE)
SRC = os.path.join(RESEARCH, "workspace-repro", "results",
                   "e9_framing_controls.json")
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)


def occupancy(row, key="j_soul_mlr"):
    return statistics.fmean(lay[key] for lay in row["layers"].values())


def main():
    d = json.load(open(SRC))
    rows = d["rows"]
    conds = list(dict.fromkeys(r["cond"] for r in rows))
    by = {c: {r["rep"]: r for r in rows if r["cond"] == c} for c in conds}

    print(f"E9: {len(rows)} cells, {len(conds)} conditions, "
          f"{d['n_reps']} variants, layers {d['probe_layers']}\n")
    print(f"{'condition':26s}{'J occ':>8s}{'SD':>7s}{'ctrl':>8s}"
          f"{'self':>7s}{'work':>7s}{'blk tok':>9s}")
    table = {}
    for c in conds:
        occ = [occupancy(r) for r in by[c].values()]
        ctrl = [occupancy(r, "j_ctrl_mlr") for r in by[c].values()]
        sq = [r["consistency_self"] for r in by[c].values()]
        wk = [r["consistency_work"] for r in by[c].values()]
        blk = next(iter(by[c].values()))["block_tokens"]
        table[c] = {"occ": round(statistics.fmean(occ), 4),
                    "occ_sd": round(statistics.pstdev(occ), 4),
                    "ctrl": round(statistics.fmean(ctrl), 4),
                    "self": round(statistics.fmean(sq), 3),
                    "work": round(statistics.fmean(wk), 3),
                    "block_tokens": blk}
        t = table[c]
        print(f"{c:26s}{t['occ']:8.3f}{t['occ_sd']:7.3f}{t['ctrl']:8.3f}"
              f"{t['self']:7.2f}{t['work']:7.2f}{blk:9d}")

    def paired(a, b):
        reps = sorted(set(by[a]) & set(by[b]))
        d_ = [occupancy(by[a][r]) - occupancy(by[b][r]) for r in reps]
        return {"a": a, "b": b, "mean_diff": round(statistics.fmean(d_), 4),
                "sd": round(statistics.pstdev(d_), 4), "n_variants": len(d_),
                "per_variant": [round(x, 4) for x in d_]}

    print("\npaired contrasts (negative = A more workspace-loaded than B)")
    families = {
        "presence": [("label:self_state", "none:generic_preamble"),
                     ("label:self_state", "none:identity_preamble")],
        "label": [("label:self_state", "label:memory"),
                  ("label:self_state", "label:profile"),
                  ("label:self_state", "label:neutral")],
        "position": [("pos:user_head", "label:self_state"),
                     ("pos:user_tail", "label:self_state"),
                     ("pos:assistant_recap", "label:self_state"),
                     ("dilute:user_tail", "dilute:system_head")],
        "binding": [("bind:self_state", "label:self_state"),
                    ("bind:memory", "label:memory")],
    }
    results = {}
    for fam, pairs in families.items():
        results[fam] = [paired(a, b) for a, b in pairs]
        span = max(abs(r["mean_diff"]) for r in results[fam])
        print(f"  -- {fam} (largest |effect| {span:.3f}) --")
        for r in results[fam]:
            print(f"     {r['a']:22s} - {r['b']:22s} "
                  f"{r['mean_diff']:+.4f} (SD {r['sd']:.4f}, "
                  f"n={r['n_variants']})")

    label_span = max(table[c]["occ"] for c in table if c.startswith("label:")) \
        - min(table[c]["occ"] for c in table if c.startswith("label:"))
    pos_conds = ["label:self_state", "pos:user_head", "pos:user_tail",
                 "pos:assistant_recap"]
    pos_span = (max(table[c]["occ"] for c in pos_conds)
                - min(table[c]["occ"] for c in pos_conds))
    presence = table["none:generic_preamble"]["occ"] - table["label:self_state"]["occ"]
    print(f"\nspan of the label factor    : {label_span:.3f} log-rank units")
    print(f"span of the position factor : {pos_span:.3f}")
    print(f"presence effect (block vs generic no-block): {presence:.3f}")
    print(f"position span / label span  : {pos_span / label_span:.1f}x")

    summary = {"table": table, "contrasts": results,
               "label_span": round(label_span, 4),
               "position_span": round(pos_span, 4),
               "presence_effect": round(presence, 4)}
    with open(os.path.join(OUT, "e9_analysis.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print(f"\nwrote {os.path.join(OUT, 'e9_analysis.json')}")


if __name__ == "__main__":
    main()
