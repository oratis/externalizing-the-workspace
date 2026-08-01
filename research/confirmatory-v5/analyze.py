"""Analyze the frozen version 5 confirmatory experiment."""

from __future__ import annotations

import itertools
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

CONDITIONS = ("broadcast_self", "broadcast_memory", "gated", "no_state")
PRIMARY_A = "broadcast_self"
PRIMARY_B = "gated"
EQUIVALENCE_MARGIN = 0.05


def mean(values):
    return sum(values) / len(values) if values else None


def percentile(sorted_values, p):
    if not sorted_values:
        return None
    i = min(len(sorted_values) - 1, max(0, int(p * len(sorted_values))))
    return sorted_values[i]


def paired_bootstrap(diffs, level=0.95, n=30000, seed=20260727):
    rng = random.Random(seed)
    draws = sorted(mean(rng.choices(diffs, k=len(diffs))) for _ in range(n))
    tail = (1 - level) / 2
    return [percentile(draws, tail), percentile(draws, 1 - tail)]


def exact_signflip(diffs):
    observed = abs(mean(diffs))
    hits = 0
    for signs in itertools.product((-1, 1), repeat=len(diffs)):
        stat = abs(mean([s * d for s, d in zip(signs, diffs)]))
        if stat >= observed - 1e-12:
            hits += 1
    return hits / (2 ** len(diffs))


def holm(pvalues):
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    adjusted = [0.0] * len(pvalues)
    previous = 0.0
    for rank, index in enumerate(order):
        value = min(1.0, (len(pvalues) - rank) * pvalues[index])
        previous = max(previous, value)
        adjusted[index] = previous
    return adjusted


def paired_contrast(run_means, a, b, level=0.95):
    seeds = sorted(set(run_means[a]) & set(run_means[b]))
    diffs = [run_means[a][s] - run_means[b][s] for s in seeds]
    return {
        "a": a,
        "b": b,
        "n": len(diffs),
        "seeds": seeds,
        "differences": diffs,
        "mean_difference": mean(diffs),
        "ci": paired_bootstrap(diffs, level=level),
        "p_exact": exact_signflip(diffs),
    }


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "results/qwen15b")
    rows = [
        json.loads(line)
        for line in (root / "records.jsonl").read_text().splitlines()
        if line.strip()
    ]
    work = [r for r in rows if r["kind"] == "work"]
    self_rows = [r for r in rows if r["kind"] == "self"]

    grouped = defaultdict(list)
    early = defaultdict(list)
    late = defaultdict(list)
    families = defaultdict(list)
    max_day = max(r["day"] for r in work)
    window = min(5, max(1, (max_day + 1) // 2))
    late_start = max_day + 1 - window
    for row in work:
        key = (row["condition"], row["seed"])
        grouped[key].append(int(row["hit"]))
        if row["day"] < window:
            early[key].append(int(row["hit"]))
        if row["day"] >= late_start:
            late[key].append(int(row["hit"]))
        families[(row["condition"], row["seed"], row["family"])].append(
            int(row["hit"])
        )

    run_means = {
        condition: {
            seed: mean(grouped[(condition, seed)])
            for c, seed in grouped if c == condition
        }
        for condition in CONDITIONS
    }
    family_run_means = {
        family: {
            condition: {
                seed: mean(values)
                for (c, seed, f), values in families.items()
                if c == condition and f == family
            }
            for condition in CONDITIONS
        }
        for family in sorted({f for _, _, f in families})
    }
    family_primary = {
        family: paired_contrast(means, PRIMARY_A, PRIMARY_B)
        for family, means in family_run_means.items()
    }
    primary = paired_contrast(run_means, PRIMARY_A, PRIMARY_B)
    label = paired_contrast(
        run_means, "broadcast_self", "broadcast_memory", level=0.90
    )
    label["equivalence_margin"] = EQUIVALENCE_MARGIN
    label["equivalent"] = (
        label["ci"][0] > -EQUIVALENCE_MARGIN
        and label["ci"][1] < EQUIVALENCE_MARGIN
    )

    secondary_specs = [
        ("broadcast_self", "broadcast_memory"),
        ("gated", "no_state"),
        ("broadcast_memory", "gated"),
    ]
    secondary = [
        paired_contrast(run_means, a, b) for a, b in secondary_specs
    ]
    adjusted = holm([r["p_exact"] for r in secondary])
    for row, p_adj in zip(secondary, adjusted):
        row["p_holm"] = p_adj

    self_group = defaultdict(list)
    for row in self_rows:
        self_group[(row["condition"], row["seed"])].append(int(row["hit"]))
    self_means = {
        condition: {
            seed: mean(self_group[(condition, seed)])
            for c, seed in self_group if c == condition
        }
        for condition in CONDITIONS
    }

    time_effect = {}
    for condition in CONDITIONS:
        seeds = sorted(run_means[condition])
        time_effect[condition] = {
            seed: mean(late[(condition, seed)]) - mean(early[(condition, seed)])
            for seed in seeds
        }
    time_did = paired_contrast(
        {
            PRIMARY_A: time_effect[PRIMARY_A],
            PRIMARY_B: time_effect[PRIMARY_B],
        },
        PRIMARY_A,
        PRIMARY_B,
    )

    malformed = [
        {
            "condition": r["condition"],
            "seed": r["seed"],
            "day": r["day"],
            "probe": r["probe"],
            "answer": r["answer"],
        }
        for r in work if r["choice"] is None
    ]
    order_audit = {}
    for condition in CONDITIONS:
        condition_rows = [r for r in work if r["condition"] == condition]
        target_a = [r for r in condition_rows if r["target"] == "A"]
        target_b = [r for r in condition_rows if r["target"] == "B"]
        order_audit[condition] = {
            "n": len(condition_rows),
            "target_a_rate": mean([r["target"] == "A" for r in condition_rows]),
            "choice_a_rate": mean([r["choice"] == "A" for r in condition_rows]),
            "accuracy_target_a": mean([int(r["hit"]) for r in target_a]),
            "accuracy_target_b": mean([int(r["hit"]) for r in target_b]),
        }
    report = {
        "n_records": len(rows),
        "n_work": len(work),
        "n_self": len(self_rows),
        "run_means": run_means,
        "family_run_means": family_run_means,
        "family_primary_contrasts": family_primary,
        "primary": primary,
        "label_equivalence": label,
        "secondary": secondary,
        "self_query_means": self_means,
        "time_difference_in_differences": time_did,
        "option_order_audit": order_audit,
        "malformed_work_answers": malformed,
    }
    (root / "analysis.json").write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Confirmatory analysis",
        "",
        f"Records: {len(rows)} total; {len(work)} work-turn; "
        f"{len(malformed)} malformed work-turn answers.",
        "",
        "## Run-level means",
        "",
        "| condition | mean | per-seed values |",
        "|---|---:|---|",
    ]
    for condition in CONDITIONS:
        values = [run_means[condition][s] for s in sorted(run_means[condition])]
        lines.append(
            f"| {condition} | {mean(values):.3f} | "
            + ", ".join(f"{x:.3f}" for x in values) + " |"
        )
    lines += [
        "",
        "## Primary contrast",
        "",
        f"`{PRIMARY_A} - {PRIMARY_B}`: "
        f"{primary['mean_difference']:+.3f}, "
        f"95% paired-bootstrap CI "
        f"[{primary['ci'][0]:+.3f}, {primary['ci'][1]:+.3f}], "
        f"exact sign-flip p = {primary['p_exact']:.5f}.",
        "",
        "## Primary contrast by scenario family",
        "",
        "| family | mean difference | exact p |",
        "|---|---:|---:|",
    ]
    for family, contrast in family_primary.items():
        lines.append(
            f"| {family} | {contrast['mean_difference']:+.3f} | "
            f"{contrast['p_exact']:.5f} |"
        )
    lines += [
        "",
        "## Label equivalence",
        "",
        f"`broadcast_self - broadcast_memory`: "
        f"{label['mean_difference']:+.3f}, "
        f"90% CI [{label['ci'][0]:+.3f}, {label['ci'][1]:+.3f}]. "
        f"Equivalence margin: +/-{EQUIVALENCE_MARGIN:.2f}; "
        f"equivalent = {label['equivalent']}.",
        "",
        "## Option-order audit",
        "",
        "| condition | target A | chose A | accuracy when A target | "
        "accuracy when B target |",
        "|---|---:|---:|---:|---:|",
    ]
    for condition in CONDITIONS:
        audit = order_audit[condition]
        lines.append(
            f"| {condition} | {audit['target_a_rate']:.3f} | "
            f"{audit['choice_a_rate']:.3f} | "
            f"{audit['accuracy_target_a']:.3f} | "
            f"{audit['accuracy_target_b']:.3f} |"
        )
    lines += [
        "",
        "## Time contrast",
        "",
        f"Difference in early-to-late change, `{PRIMARY_A} - {PRIMARY_B}`: "
        f"{time_did['mean_difference']:+.3f}, "
        f"95% CI [{time_did['ci'][0]:+.3f}, {time_did['ci'][1]:+.3f}], "
        f"p = {time_did['p_exact']:.5f}.",
        "",
    ]
    (root / "REPORT.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
