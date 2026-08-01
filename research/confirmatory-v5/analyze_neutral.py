"""Analyze the token-matched neutral-context follow-up."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

from analyze import holm, mean, paired_contrast

CONDITIONS = ("state_memory", "neutral_memory", "no_state")


def main() -> None:
    root = Path(
        sys.argv[1] if len(sys.argv) > 1 else "results/neutral_qwen15b"
    )
    rows = [
        json.loads(line)
        for line in (root / "records.jsonl").read_text().splitlines()
        if line.strip()
    ]
    grouped = defaultdict(list)
    family_grouped = defaultdict(list)
    for row in rows:
        grouped[(row["condition"], row["seed"])].append(int(row["hit"]))
        family_grouped[
            (row["family"], row["condition"], row["seed"])
        ].append(int(row["hit"]))

    means = {
        condition: {
            seed: mean(values)
            for (c, seed), values in grouped.items()
            if c == condition
        }
        for condition in CONDITIONS
    }
    primary = paired_contrast(means, "state_memory", "neutral_memory")
    secondary = [
        paired_contrast(means, "neutral_memory", "no_state"),
        paired_contrast(means, "state_memory", "no_state"),
    ]
    for result, adjusted in zip(
        secondary, holm([result["p_exact"] for result in secondary])
    ):
        result["p_holm"] = adjusted

    family_primary = {}
    for family in sorted({key[0] for key in family_grouped}):
        family_means = {
            condition: {
                seed: mean(values)
                for (f, c, seed), values in family_grouped.items()
                if f == family and c == condition
            }
            for condition in CONDITIONS
        }
        family_primary[family] = paired_contrast(
            family_means, "state_memory", "neutral_memory"
        )

    report = {
        "n_records": len(rows),
        "run_means": means,
        "primary": primary,
        "secondary": secondary,
        "family_primary_contrasts": family_primary,
        "malformed_answers": [
            row for row in rows if row["choice"] is None
        ],
    }
    (root / "analysis.json").write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Token-matched neutral-context follow-up",
        "",
        f"Records: {len(rows)}; malformed answers: "
        f"{len(report['malformed_answers'])}.",
        "",
        "| condition | mean | per-seed values |",
        "|---|---:|---|",
    ]
    for condition in CONDITIONS:
        values = [means[condition][seed] for seed in sorted(means[condition])]
        lines.append(
            f"| {condition} | {mean(values):.3f} | "
            + ", ".join(f"{value:.3f}" for value in values)
            + " |"
        )
    lines += [
        "",
        "Primary, `state_memory - neutral_memory`: "
        f"{primary['mean_difference']:+.3f}, 95% CI "
        f"[{primary['ci'][0]:+.3f}, {primary['ci'][1]:+.3f}], "
        f"exact p={primary['p_exact']:.5f}.",
        "",
        "| family | state - neutral | exact p |",
        "|---|---:|---:|",
    ]
    for family, result in family_primary.items():
        lines.append(
            f"| {family} | {result['mean_difference']:+.3f} | "
            f"{result['p_exact']:.5f} |"
        )
    text = "\n".join(lines) + "\n"
    (root / "REPORT.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
