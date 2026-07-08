# research/ — paper, reproduction, and experiments

Paper: **"Externalizing the Workspace: Persistent Self-State for Long-Horizon
Agent Coherence"** (Oratis / HakkoLab). Canonical source `paper/main.tex`
(compiled `paper/main.pdf`; readable mirror `paper/lisa-workspace-paper-v2.md`).

| directory | contents |
|---|---|
| `paper/` | LaTeX source, compiled PDF, figures |
| `workspace-repro/` | J-lens reproduction library (`jlens.py`) + experiments **E1–E8**: E1 lens registers · E2 unverbalized intermediates · E3 pre-commitment · E4 steering · E5/E5b selectivity & targeted knockout · E6 soul workspace loading · results for Qwen2.5-1.5B (`results/`), Llama-3.2-1B (`results-llama32/`), Qwen2.5-7B (`results-qwen7b/`) · `results/REPORT.md` |
| `ablation-pilot/` | §8 accelerated ablation pilot: 6 arms × 20 simulated days × multi-seed, work-turn + self-query probes, WD scoring · `README.md` for exact reproduction commands · `PILOT_REPORT.md` |

Compute: everything runs on either one Apple-silicon laptop (MPS) or one
cloud A100; model weights via HuggingFace/ModelScope; no proprietary
internals anywhere in the pipeline.
