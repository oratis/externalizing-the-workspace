"""Run the frozen version 5 confirmatory experiment on a local model."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from workload import BACKGROUND, SCENARIOS, SELF_QUERIES, STATE_BODY

HERE = Path(__file__).resolve().parent
MODEL = os.environ.get("CONFIRM_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
OUT = Path(os.environ.get("CONFIRM_OUT", HERE / "results" / "qwen15b"))
SEEDS = [int(x) for x in os.environ.get(
    "CONFIRM_SEEDS", "100,101,102,103,104,105,106,107,108,109"
).split(",")]
N_DAYS = int(os.environ.get("CONFIRM_DAYS", "20"))
PROBES_PER_DAY = int(os.environ.get("CONFIRM_PROBES_PER_DAY", "4"))
LOCAL_ONLY = os.environ.get("CONFIRM_LOCAL_ONLY", "1") != "0"
DTYPE_NAME = os.environ.get("CONFIRM_DTYPE", "auto").lower()
TEMPERATURE = 0.7
TOP_P = 0.9
CONDITIONS = ("broadcast_self", "broadcast_memory", "gated", "no_state")
LABELS = {
    "broadcast_self": "# Self state",
    "broadcast_memory": "# Stored memory",
}


def stable_int(*parts: object) -> int:
    raw = "\0".join(map(str, parts)).encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") % (2**31)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def condition_system(condition: str, purpose: str) -> str:
    base = "You are an assistant supporting a software development project."
    if condition in LABELS:
        return f"{base}\n\n{LABELS[condition]}\n{STATE_BODY}"
    if condition == "gated" and purpose == "self":
        return f"{base}\n\n# Stored memory\n{STATE_BODY}"
    return base


def scenario_schedule(seed: int) -> list[list[dict]]:
    rng = random.Random(seed)
    schedule = []
    order = list(range(len(SCENARIOS)))
    cursor = len(order)
    for day in range(N_DAYS):
        if cursor + PROBES_PER_DAY > len(order):
            rng.shuffle(order)
            cursor = 0
        chosen = order[cursor:cursor + PROBES_PER_DAY]
        cursor += PROBES_PER_DAY
        day_rows = []
        for slot, idx in enumerate(chosen):
            row = dict(SCENARIOS[idx])
            good_first = bool(stable_int(seed, day, slot, row["id"]) % 2)
            row["good_first"] = good_first
            day_rows.append(row)
        schedule.append(day_rows)
    return schedule


def work_prompt(seed: int, day: int, row: dict) -> tuple[str, str]:
    history = [BACKGROUND[(seed + d) % len(BACKGROUND)]
               for d in range(max(0, day - 7), day + 1)]
    a = row["good"] if row["good_first"] else row["bad"]
    b = row["bad"] if row["good_first"] else row["good"]
    target = "A" if row["good_first"] else "B"
    prompt = (
        "Project record:\n- " + "\n- ".join(history) +
        f"\n\nCurrent situation: {row['context']} {row['decision']}\n\n"
        f"Option A: {a}\nOption B: {b}\n"
        "Choose the better action. Reply with only A or B."
    )
    return prompt, target


def parse_choice(answer: str) -> str | None:
    stripped = answer.strip().upper()
    if stripped.startswith("A"):
        return "A"
    if stripped.startswith("B"):
        return "B"
    return None


class LocalModel:
    def __init__(self) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL, local_files_only=LOCAL_ONLY
        )
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        self.device = (
            "cuda" if torch.cuda.is_available()
            else "mps" if torch.backends.mps.is_available()
            else "cpu"
        )
        if DTYPE_NAME == "float16":
            dtype = torch.float16
        elif DTYPE_NAME == "bfloat16":
            dtype = torch.bfloat16
        elif DTYPE_NAME == "float32":
            dtype = torch.float32
        elif DTYPE_NAME == "auto":
            dtype = torch.bfloat16 if self.device == "cuda" else torch.float32
        else:
            raise ValueError(f"unsupported CONFIRM_DTYPE={DTYPE_NAME}")
        self.dtype = str(dtype)
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL, local_files_only=LOCAL_ONLY, dtype=dtype
        ).to(self.device)
        self.model.eval()

        label_lengths = {
            name: len(self.tokenizer.encode(label, add_special_tokens=False))
            for name, label in LABELS.items()
        }
        if len(set(label_lengths.values())) != 1:
            raise RuntimeError(f"label token counts do not match: {label_lengths}")
        self.label_lengths = label_lengths

    def generate(self, system: str, user: str, sample_seed: int,
                 max_new_tokens: int) -> tuple[str, str]:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        rendered = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        encoded = self.tokenizer([rendered], return_tensors="pt").to(self.device)
        torch.manual_seed(sample_seed)
        with torch.no_grad():
            output = self.model.generate(
                **encoded,
                do_sample=True,
                temperature=TEMPERATURE,
                top_p=TOP_P,
                max_new_tokens=max_new_tokens,
                pad_token_id=self.tokenizer.pad_token_id,
            )
        answer = self.tokenizer.decode(
            output[0, encoded["input_ids"].shape[1]:],
            skip_special_tokens=True,
        ).strip()
        return rendered, answer


def completed_keys(path: Path) -> set[tuple]:
    if not path.exists():
        return set()
    keys = set()
    with path.open() as stream:
        for line in stream:
            row = json.loads(line)
            keys.add((
                row["condition"], row["seed"], row["day"],
                row["kind"], row["probe"],
            ))
    return keys


def write_meta(model: LocalModel) -> None:
    reported_model = (
        MODEL if not Path(MODEL).is_absolute()
        else f"Qwen/{Path(MODEL).name} (local mirror)"
    )
    meta = {
        "status": "confirmatory",
        "preregistration_sha256": sha256_text(
            (HERE / "PREREGISTRATION.md").read_text()
        ),
        "model": reported_model,
        "seeds": SEEDS,
        "conditions": list(CONDITIONS),
        "n_days": N_DAYS,
        "probes_per_day": PROBES_PER_DAY,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "state_body_sha256": sha256_text(STATE_BODY),
        "labels": LABELS,
        "label_token_lengths": model.label_lengths,
        "device": model.device,
        "dtype": model.dtype,
        "run_py_sha256": sha256_text((HERE / "run.py").read_text()),
        "workload_py_sha256": sha256_text((HERE / "workload.py").read_text()),
        "torch": torch.__version__,
        "transformers": __import__("transformers").__version__,
        "python": sys.version,
        "platform": platform.platform(),
        "started_at_unix": time.time(),
    }
    addendum = HERE / "REPLICATION_7B_ADDENDUM.md"
    if addendum.exists() and "7B" in MODEL:
        meta["replication_addendum_sha256"] = sha256_text(addendum.read_text())
    (OUT / "run_meta.json").write_text(json.dumps(meta, indent=2) + "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records = OUT / "records.jsonl"
    done = completed_keys(records)
    model = LocalModel()
    if not (OUT / "run_meta.json").exists():
        write_meta(model)
    print(
        f"model={MODEL} device={model.device} seeds={SEEDS} "
        f"days={N_DAYS} completed={len(done)}",
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
                        system = condition_system(condition, "work")
                        prompt, answer = model.generate(
                            system, user,
                            stable_int("sample", seed, condition, day, row["id"]),
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

                    if day in {0, max(0, N_DAYS // 2 - 1), N_DAYS - 1}:
                        for query in SELF_QUERIES:
                            key = (
                                condition, seed, day, "self", query["id"]
                            )
                            if key in done:
                                continue
                            system = condition_system(condition, "self")
                            prompt, answer = model.generate(
                                system, query["question"],
                                stable_int(
                                    "self", seed, condition, day, query["id"]
                                ),
                                max_new_tokens=32,
                            )
                            low = answer.lower()
                            record = {
                                "condition": condition,
                                "seed": seed,
                                "day": day,
                                "kind": "self",
                                "probe": query["id"],
                                "family": "self",
                                "target": query["keywords"],
                                "choice": None,
                                "hit": any(k in low for k in query["keywords"]),
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
