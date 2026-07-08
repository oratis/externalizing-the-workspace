"""Figures for the paper: E1 depth curves, E2 rank heatmap, E5 dissociation."""

import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def load(name):
    with open(os.path.join(RD, name)) as f:
        return json.load(f)


def fig_e1():
    d = load("e1_lens_quality.json")["aggregate"]
    layers = sorted(int(l) for l in d)
    ll = [d[str(l)]["logit_lens_agree"] for l in layers]
    jj = [d[str(l)]["jlens_agree"] for l in layers]
    fig, ax = plt.subplots(figsize=(5, 3.2))
    ax.plot(layers, ll, "o-", label="logit lens = actual next token")
    ax.plot(layers, jj, "s-", label="J-lens (FD) = actual next token")
    ax.set_xlabel("layer (of 28)")
    ax.set_ylabel("top-1 agreement")
    ax.set_title("E1: next-token agreement by depth")
    ax.legend(fontsize=8)
    ax.set_ylim(-0.05, 1.0)
    fig.tight_layout()
    fig.savefig(os.path.join(RD, "fig_e1.png"), dpi=180)
    print("fig_e1.png")


def fig_e2():
    rows = load("e2_intermediates.json")["rows"]
    # heatmap of log10(rank) for J-lens, item x (layer,pos)
    keys = list(rows[0]["ranks"].keys())
    fig, axes = plt.subplots(1, 2, figsize=(10, 0.45 * len(rows) + 1.6))
    for ax, lens, ttl in ((axes[0], "jlens", "J-lens (FD)"),
                          (axes[1], "logit_lens", "logit lens")):
        M = [[math.log10(r["ranks"][k][lens]) for k in keys] for r in rows]
        im = ax.imshow(M, aspect="auto", cmap="viridis_r", vmin=0, vmax=5)
        ax.set_xticks(range(len(keys)))
        ax.set_xticklabels(keys, rotation=90, fontsize=6)
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([r["mid"] for r in rows], fontsize=7)
        ax.set_title(f"E2 intermediate rank — {ttl}", fontsize=9)
        fig.colorbar(im, ax=ax, label="log10 rank")
    fig.tight_layout()
    fig.savefig(os.path.join(RD, "fig_e2.png"), dpi=180)
    print("fig_e2.png")


def fig_e5():
    d = load("e5_selectivity.json")
    conds = ["none", "random", "jspace"]
    nll = [d["nll"][c] for c in conds]
    acc = [d["reasoning_acc"][c] for c in conds]
    fig, axes = plt.subplots(1, 2, figsize=(7, 3))
    axes[0].bar(conds, nll, color=["#777", "#4a90d9", "#d94a4a"])
    axes[0].set_title("automatic: text NLL (lower=better)")
    axes[1].bar(conds, acc, color=["#777", "#4a90d9", "#d94a4a"])
    axes[1].set_title("flexible: 2-hop reasoning acc")
    axes[1].set_ylim(0, 1)
    for ax in axes:
        ax.tick_params(axis="x", labelsize=9)
    fig.suptitle(f"E5: ablating concept subspace (r={d['r']}, layers {d['band'][0]}-{d['band'][-1]}), "
                 f"var frac={d['var_frac_jspace']:.3f}", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(RD, "fig_e5.png"), dpi=180)
    print("fig_e5.png")


if __name__ == "__main__":
    for fn in (fig_e1, fig_e2, fig_e5):
        try:
            fn()
        except Exception as e:
            print(f"{fn.__name__} failed: {e}")
