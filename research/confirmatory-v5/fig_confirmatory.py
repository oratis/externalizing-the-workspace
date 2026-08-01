"""Figure for the independent-seed and neutral-context experiments."""

from __future__ import annotations

import json
import random
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def load(name: str) -> dict:
    return json.loads((RESULTS / name / "analysis.json").read_text())


def interval(values, seed):
    rng = random.Random(seed)
    draws = sorted(
        sum(rng.choices(values, k=len(values))) / len(values)
        for _ in range(10000)
    )
    return draws[250], draws[9749]


def draw_condition_panel(ax, reports):
    conditions = ("broadcast_self", "broadcast_memory", "gated", "no_state")
    labels = ("self", "memory", "gated", "none")
    colors = {"1.5B": "#2b6cb0", "7B": "#c53030"}
    offsets = {"1.5B": -0.12, "7B": 0.12}
    for model_index, (model, report) in enumerate(reports.items()):
        for index, condition in enumerate(conditions):
            values = [
                report["run_means"][condition][seed]
                for seed in sorted(report["run_means"][condition], key=int)
            ]
            x = index + offsets[model]
            jitter = np.linspace(-0.045, 0.045, len(values))
            ax.scatter(
                x + jitter,
                values,
                s=18,
                alpha=0.55,
                color=colors[model],
                edgecolor="none",
            )
            low, high = interval(values, 100 + model_index * 10 + index)
            average = sum(values) / len(values)
            ax.errorbar(
                x,
                average,
                yerr=[[average - low], [high - average]],
                fmt="o",
                ms=6,
                capsize=4,
                lw=1.5,
                color=colors[model],
                label=model if index == 0 else None,
            )
    ax.set_xticks(range(len(labels)), labels)
    ax.set_ylim(0.65, 1.015)
    ax.set_ylabel("work-turn accuracy")
    ax.set_title("A. Same protocol, different scale")
    ax.legend(frameon=False, loc="center right")
    ax.text(
        0.02,
        0.04,
        "self − gated: 1.5B −.079 (p=.0098); 7B +.004 (p=.25)",
        transform=ax.transAxes,
        fontsize=8,
    )


def draw_neutral_panel(ax, report):
    conditions = ("state_memory", "neutral_memory", "no_state")
    labels = ("state\n81 tokens", "neutral\n81 tokens", "no block")
    colors = ("#2b6cb0", "#718096", "#2f855a")
    for index, (condition, color) in enumerate(zip(conditions, colors)):
        values = [
            report["run_means"][condition][seed]
            for seed in sorted(report["run_means"][condition], key=int)
        ]
        jitter = np.linspace(-0.05, 0.05, len(values))
        ax.scatter(
            index + jitter,
            values,
            s=18,
            alpha=0.55,
            color=color,
            edgecolor="none",
        )
        low, high = interval(values, 200 + index)
        average = sum(values) / len(values)
        ax.errorbar(
            index,
            average,
            yerr=[[average - low], [high - average]],
            fmt="o",
            ms=6,
            capsize=4,
            lw=1.5,
            color=color,
        )
    ax.set_xticks(range(len(labels)), labels)
    ax.set_ylim(0.60, 0.90)
    ax.set_ylabel("work-turn accuracy")
    ax.set_title("B. Token-matched 1.5B follow-up")
    ax.text(
        0.02,
        0.04,
        "state − neutral: +.001; neutral − no block: −.077",
        transform=ax.transAxes,
        fontsize=8,
    )


def main():
    qwen15 = load("qwen15b")
    qwen7 = load("qwen7b")
    neutral = load("neutral_qwen15b")
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.6))
    draw_condition_panel(axes[0], {"1.5B": qwen15, "7B": qwen7})
    draw_neutral_panel(axes[1], neutral)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#e2e8f0", lw=0.7)
        ax.set_axisbelow(True)
    fig.tight_layout()
    output = RESULTS / "fig_confirmatory.png"
    fig.savefig(output, dpi=220)
    print(f"saved {output}")


if __name__ == "__main__":
    main()
