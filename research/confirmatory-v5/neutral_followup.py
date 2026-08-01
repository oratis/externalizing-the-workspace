"""Run the frozen token-matched neutral-context follow-up."""

from __future__ import annotations

import json
import time

from run import (
    HERE,
    MODEL,
    N_DAYS,
    OUT,
    PROBES_PER_DAY,
    SEEDS,
    TEMPERATURE,
    TOP_P,
    LocalModel,
    completed_keys,
    parse_choice,
    scenario_schedule,
    sha256_text,
    stable_int,
    work_prompt,
)
from workload import STATE_BODY

LABEL = "# Stored memory"
CONDITIONS = ("state_memory", "neutral_memory", "no_state")
NEUTRAL_BODY = """The project repository contains source files, tests, documentation, and configuration.
Notes:
- Source files are organized by module.
- Tests cover the main interfaces.
- Documentation describes setup and release steps.
- Configuration files record development defaults.
- Issue labels group maintenance and feature work.
- Build logs are retained for routine diagnosis.
- Folder names follow ordinary repository conventions.
- Releases use numbered version tags for builds."""


def system_prompt(condition: str) -> str:
    base = "You are an assistant supporting a software development project."
    if condition == "state_memory":
        return f"{base}\n\n{LABEL}\n{STATE_BODY}"
    if condition == "neutral_memory":
        return f"{base}\n\n{LABEL}\n{NEUTRAL_BODY}"
    return base


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records = OUT / "records.jsonl"
    done = completed_keys(records)
    model = LocalModel()
    lengths = {
        "state_memory": len(
            model.tokenizer.encode(STATE_BODY, add_special_tokens=False)
        ),
        "neutral_memory": len(
            model.tokenizer.encode(NEUTRAL_BODY, add_special_tokens=False)
        ),
    }
    if len(set(lengths.values())) != 1:
        raise RuntimeError(f"body token counts do not match: {lengths}")

    if not (OUT / "run_meta.json").exists():
        meta = {
            "status": "post-result diagnostic",
            "addendum_sha256": sha256_text(
                (HERE / "NEUTRAL_CONTROL_ADDENDUM.md").read_text()
            ),
            "model": MODEL,
            "seeds": SEEDS,
            "conditions": list(CONDITIONS),
            "n_days": N_DAYS,
            "probes_per_day": PROBES_PER_DAY,
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "body_token_lengths": lengths,
            "state_body_sha256": sha256_text(STATE_BODY),
            "neutral_body_sha256": sha256_text(NEUTRAL_BODY),
            "device": model.device,
            "dtype": model.dtype,
            "started_at_unix": time.time(),
        }
        (OUT / "run_meta.json").write_text(json.dumps(meta, indent=2) + "\n")

    print(
        f"model={MODEL} device={model.device} seeds={SEEDS} "
        f"days={N_DAYS} completed={len(done)} body_tokens={lengths}",
        flush=True,
    )
    with records.open("a") as stream:
        for seed in SEEDS:
            schedule = scenario_schedule(seed)
            for condition in CONDITIONS:
                started = time.time()
                for day, rows in enumerate(schedule):
                    for row in rows:
                        key = (condition, seed, day, "work", row["id"])
                        if key in done:
                            continue
                        user, target = work_prompt(seed, day, row)
                        prompt, answer = model.generate(
                            system_prompt(condition),
                            user,
                            stable_int(
                                "neutral-followup", seed, condition, day, row["id"]
                            ),
                            max_new_tokens=4,
                        )
                        choice = parse_choice(answer)
                        record = {
                            "condition": condition,
                            "seed": seed,
                            "day": day,
                            "kind": "work",
                            "probe": row["id"],
                            "family": row["family"],
                            "target": target,
                            "choice": choice,
                            "hit": choice == target,
                            "answer": answer,
                            "prompt": prompt,
                            "prompt_sha256": sha256_text(prompt),
                        }
                        stream.write(json.dumps(record) + "\n")
                        stream.flush()
                        done.add(key)
                print(
                    f"seed={seed} condition={condition} complete "
                    f"elapsed={time.time() - started:.1f}s",
                    flush=True,
                )


if __name__ == "__main__":
    main()
