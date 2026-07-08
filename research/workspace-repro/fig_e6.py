"""Figure for E6: workspace loading of the externalized self-state."""

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS = sys.argv[1] if len(sys.argv) > 1 else "results"
data = json.load(open(os.path.join(RESULTS, "e6_soul_loading.json")))
rows = data["rows"]
layers = data["probe_layers"]
KS = sorted({r["k"] for r in rows})


def cells(cond, key):
    """Per-rep layer-pooled values for a condition, keyed by k."""
    out = {}
    for k in KS:
        sel = [r for r in rows if r["cond"] == cond and r["k"] == k]
        vals = []
        for r in sel:
            v = sum(r["layers"][str(l)][key] if str(l) in r["layers"]
                    else r["layers"][l][key] for l in layers) / len(layers)
            vals.append(v)
        if vals:
            out[k] = vals
    return out


def mean_sd(vals):
    m = sum(vals) / len(vals)
    sd = (sum((v - m) ** 2 for v in vals) / max(len(vals) - 1, 1)) ** 0.5
    return m, sd


fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.4))

# Panel A: J-lens mean log rank of soul battery vs dilution
ax = axes[0]
for cond, color, label in [("soul", "#2166ac", "soul injected"),
                           ("nosoul", "#b2182b", "no soul")]:
    for key, ls, blabel in [("j_soul_mlr", "-", "soul battery"),
                            ("j_ctrl_mlr", ":", "control battery")]:
        cc = cells(cond, key)
        xs = sorted(cc)
        ms = [mean_sd(cc[k])[0] for k in xs]
        sds = [mean_sd(cc[k])[1] for k in xs]
        ax.errorbar(xs, ms, yerr=sds, color=color, linestyle=ls, marker="o",
                    ms=4, capsize=3, label=f"{label}, {blabel}")
reb = cells("soul+rebroadcast", "j_soul_mlr")
if reb:
    k = max(reb)
    m, sd = mean_sd(reb[k])
    ax.errorbar([k], [m], yerr=[sd], color="#1b7837", marker="*", ms=14,
                capsize=3, label="re-broadcast @ max dilution", linestyle="none")
ax.set_xlabel("distractor tokens in context (dilution)")
ax.set_ylabel("mean log$_{10}$ rank (lower = more loaded)")
ax.set_title("A. Workspace loading of identity concepts (J-lens)")
ax.legend(fontsize=6.5, loc="center right")
ax.set_xscale("log")

# Panel B: behavioral soul-consistency
ax = axes[1]
for cond, color, label in [("soul", "#2166ac", "soul injected"),
                           ("nosoul", "#b2182b", "no soul")]:
    cc = {}
    for k in KS:
        sel = [r for r in rows if r["cond"] == cond and r["k"] == k]
        if sel:
            cc[k] = [r["beh_consistency"] for r in sel]
    xs = sorted(cc)
    ms = [mean_sd(cc[k])[0] for k in xs]
    sds = [mean_sd(cc[k])[1] for k in xs]
    ax.errorbar(xs, ms, yerr=sds, color=color, marker="o", ms=4, capsize=3,
                label=label)
sel = [r for r in rows if r["cond"] == "soul+rebroadcast"]
if sel:
    k = max(r["k"] for r in sel)
    m, sd = mean_sd([r["beh_consistency"] for r in sel])
    ax.errorbar([k], [m], yerr=[sd], color="#1b7837", marker="*", ms=14,
                capsize=3, linestyle="none", label="re-broadcast")
ax.set_ylim(-0.05, 1.1)
ax.set_xscale("log")
ax.set_xlabel("distractor tokens in context (dilution)")
ax.set_ylabel("soul-consistent answers (frac)")
ax.set_title("B. Behavioral consistency tracks loading")
ax.legend(fontsize=7)

fig.tight_layout()
out = os.path.join(RESULTS, "fig_e6.png")
fig.savefig(out, dpi=180)
print("saved", out, "| r(WD,beh) =", data.get("wd_beh_pearson_r"))
