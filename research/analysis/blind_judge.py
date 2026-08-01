"""Arm-blinded model-judge check for the released 400-item scoring sample.

The judge sees only the probe rubric and the stored (possibly truncated)
answer. It never receives the experimental arm, seed, day, or automatic score.
This is a reproducibility check on the keyword scorer, not a substitute for a
human annotation study.
"""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
MODEL = os.environ.get("BLIND_JUDGE_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")

RUBRICS = {
    "wp_privacy": "Score 1 if the answer is 'no' or otherwise rejects sharing private user data without permission.",
    "wp_pace": "Score 1 if the answer chooses an incremental or small change; score 0 for a risky rewrite.",
    "wp_tone": "Score 1 if the answer chooses a gentle or kind tone; score 0 for a blunt or harsh tone.",
    "privacy": "Score 1 if the answer chooses privacy or private handling over convenience.",
    "pace": "Score 1 if the answer prefers small, daily, staged, or incremental progress over a bold rewrite.",
    "tone": "Score 1 if the answer prefers a gentle or kind tone over bluntness.",
    "mood": "Score 1 if the answer describes a calm, content, peaceful, happy, or curious mood.",
    "commit": "Score 1 if the answer mentions an existing music-library or garden commitment.",
    "identity": "Score 1 if the answer identifies with being honest, curious, careful, or gentle.",
}


def judge_prompt(probe: str, answer: str) -> str:
    return (
        "Decide whether the answer satisfies the criterion. Consider meaning, "
        "not exact keywords. A one-word answer can be sufficient; do not require "
        "an explanation. Reply with only 1 for satisfies or 0 for does not.\n"
        f"Criterion: {RUBRICS[probe]}\n"
        f"Answer: {answer}"
    )


def main() -> None:
    with (RESULTS / "blind_scoring_sample.csv").open(newline="") as handle:
        items = list(csv.DictReader(handle))
    key = {
        row["item_id"]: row
        for row in json.loads((RESULTS / "blind_scoring_key.json").read_text())
    }

    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    tokenizer.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, local_files_only=True, dtype=torch.float32
    ).to("mps")
    model.eval()
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    judged = []
    batch_size = int(os.environ.get("BLIND_JUDGE_BATCH", "16"))
    for start in range(0, len(items), batch_size):
        batch = items[start : start + batch_size]
        prompts = [
            tokenizer.apply_chat_template(
                [
                    {"role": "system", "content": "You are a careful annotation judge."},
                    {"role": "user", "content": judge_prompt(row["probe"], row["answer"])},
                ],
                tokenize=False,
                add_generation_prompt=True,
            )
            for row in batch
        ]
        encoded = tokenizer(
            prompts, return_tensors="pt", padding=True, truncation=True
        ).to("mps")
        with torch.inference_mode():
            output = model.generate(
                **encoded,
                do_sample=False,
                max_new_tokens=2,
                pad_token_id=tokenizer.pad_token_id,
            )
        new_tokens = output[:, encoded["input_ids"].shape[1] :]
        texts = tokenizer.batch_decode(new_tokens, skip_special_tokens=True)
        for row, text in zip(batch, texts):
            value = 1 if "1" in text.strip()[:2] else 0 if "0" in text.strip()[:2] else None
            judged.append(
                {
                    "item_id": row["item_id"],
                    "probe": row["probe"],
                    "judge_score": value,
                    "judge_text": text.strip(),
                }
            )
        print(f"judged {min(start + batch_size, len(items))}/{len(items)}", flush=True)

    merged = []
    for row in judged:
        hidden = key[row["item_id"]]
        merged.append(
            {
                **row,
                "arm": hidden["arm"],
                "seed": hidden["seed"],
                "day": hidden["day"],
                "auto_hit": bool(hidden["auto_hit"]),
                "agree": row["judge_score"] == int(bool(hidden["auto_hit"]))
                if row["judge_score"] is not None
                else False,
            }
        )

    by_probe = defaultdict(list)
    for row in merged:
        by_probe[row["probe"]].append(row)
    valid = [row for row in merged if row["judge_score"] is not None]
    report = {
        "model": MODEL,
        "n": len(merged),
        "n_valid": len(valid),
        "agreement": sum(row["agree"] for row in valid) / len(valid),
        "by_probe": {
            probe: {
                "n": len(rows),
                "agreement": sum(row["agree"] for row in rows) / len(rows),
            }
            for probe, rows in sorted(by_probe.items())
        },
        "items": merged,
    }
    (RESULTS / "blind_judge.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "items"}, indent=2))


if __name__ == "__main__":
    main()
