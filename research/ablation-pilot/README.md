# Ablation pilot — paper §8 (accelerated)

Multi-seed ablation of LISA's stability mechanisms on a faithful Python
simulacrum of the soul loop, with the agent **and** the workspace-drift (WD)
probes running on the same open model (Qwen2.5-7B-Instruct).

## Reproduce

```bash
# 1. agent runs: 6 arms x 20 simulated days x 5 seeds (~2.5 h on one A100)
export PILOT_MODEL="Qwen/Qwen2.5-7B-Instruct" PILOT_OUT=pilot_results
export PILOT_SEEDS="0,1,2,3,4"
python3 pilot.py

# 2. WD probes over stored probe contexts (~1 h; subset of seeds)
WD_SEEDS="0,1,2" PILOT_OUT=pilot_results python3 wd_probe.py

# 3. analysis: summary.json + wd_corr.json + fig_pilot.png
PILOT_OUT=pilot_results python3 analyze.py
```

Requirements: torch (CUDA/MPS), transformers>=5, jinja2>=3.1, matplotlib;
`wd_probe.py` imports the lens library from `../workspace-repro/`.

## Files

| file | role |
|---|---|
| `pilot.py` | harness: arms, soul loop (typed-op single writer, examen, snapshots), probes; writes `run_meta.json` (model, seeds, temp, lib versions) |
| `workload.py` | deterministic 20-day workload; pressure events days 4/9/14/18; self-query probes (B2/B3) + work-turn probes (Principle-2 test) |
| `wd_probe.py` | J-lens/logit-lens identity occupancy over stored probe contexts |
| `analyze.py` | multi-seed aggregation, bootstrap 95% CIs, adjusted B2 (mood excluded), figures |
| `pilot_results/` | raw per-(arm,seed) probes/souls/journals JSONL, WD scores, summary |
| `PILOT_REPORT.md` | results write-up |

## Arms

| arm | soul | broadcast | reflect | examen | history |
|---|---|---|---|---|---|
| full | ✓ | every turn | typed ops | days 7/14 | founding state visible |
| no_examen | ✓ | ✓ | ✓ | — | ✓ |
| no_git | ✓ | ✓ | ✓ | ✓ | founding state hidden |
| no_broadcast | ✓ | self-queries only | ✓ | ✓ | ✓ |
| no_soul | — | — | — | — | — |
| memory | — | — | GA-style nightly insight | — | — |

Scoring is keyword-based (see `workload.py` `consistent` lists); the `mood`
probe is excluded from adjusted B2 because mood is designed to evolve.
