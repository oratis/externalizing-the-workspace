# Version 5 confirmatory experiment

This directory contains the frozen, local-compute experiment for the paper's
primary behavioral claim. Read `PREREGISTRATION.md` before running it.

## Conditions

- `broadcast_self`: state body present under `# Self state`
- `broadcast_memory`: identical body and position under `# Stored memory`
- `gated`: state body absent from work turns, available to self-queries
- `no_state`: state body absent throughout

The two broadcast labels have equal tokenizer length. The script verifies this
before model execution.

## Local run

The default model is the locally cached Qwen2.5-1.5B-Instruct.

```bash
cd research/workspace-repro

# Short design check; not part of confirmatory inference.
CONFIRM_OUT=../confirmatory-v5/results/smoke \
CONFIRM_SEEDS=900 CONFIRM_DAYS=2 CONFIRM_PROBES_PER_DAY=2 \
uv run python ../confirmatory-v5/run.py

# Frozen confirmatory run.
CONFIRM_OUT=../confirmatory-v5/results/qwen15b \
CONFIRM_SEEDS=100,101,102,103,104,105,106,107,108,109 \
uv run python ../confirmatory-v5/run.py

uv run python ../confirmatory-v5/analyze.py \
  ../confirmatory-v5/results/qwen15b

# Same-protocol 7B replication (local path may differ).
CONFIRM_MODEL=/path/to/Qwen2.5-7B-Instruct \
CONFIRM_DTYPE=float16 \
CONFIRM_OUT=../confirmatory-v5/results/qwen7b \
uv run python ../confirmatory-v5/run.py

uv run python ../confirmatory-v5/analyze.py \
  ../confirmatory-v5/results/qwen7b

# Post-result token-matched diagnostic.
CONFIRM_OUT=../confirmatory-v5/results/neutral_qwen15b \
CONFIRM_SEEDS=200,201,202,203,204,205,206,207,208,209 \
uv run python ../confirmatory-v5/neutral_followup.py

uv run python ../confirmatory-v5/analyze_neutral.py \
  ../confirmatory-v5/results/neutral_qwen15b
```

The runner resumes at the `(condition, seed, day, probe)` level. Deleting or
editing completed rows invalidates the confirmatory run.

## Outputs

- `run_meta.json`: model, revisions, package versions, hardware, protocol
- `records.jsonl`: full prompts, hashes, full answers, targets, and scores
- `analysis.json`: run-level estimates, exact tests, intervals, and day effects
- `REPORT.md`: human-readable statistical report

The consolidated interpretation is in `RESULTS.md`. The 7B and neutral-block
studies have separate addenda recording when their decisions were frozen.
