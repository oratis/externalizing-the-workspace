---
license: cc-by-4.0
language: en
tags:
  - interpretability
  - agents
  - global-workspace
  - persona-stability
  - mechanistic-interpretability
pretty_name: "Externalizing the Workspace"
---

# Externalizing the Workspace: Persistent Self-State for Long-Horizon Agent Coherence

**Oratis (Wang Bihao)** · [HakkoLab](https://huggingface.co/HakkoLab) · Draft v3, July 2026 · [PDF](./main.pdf)

Language-model agents drift. Building on Anthropic's finding that LLMs maintain a **verbalizable global workspace** (Gurnee et al., 2026), this paper models persistent self-state agent architectures (LISA's *soul*) as **functional externalizations of the workspace** — and backs the model with experiments that run entirely on open models and independent-researcher compute.

## Headline results

| finding | evidence |
|---|---|
| Core J-lens workspace phenomena reproduce on open models | Qwen2.5-1.5B/7B + Llama-3.2-1B; laptop + one A100 |
| **Choice pre-commitment emerges with scale** | to-be-reported concept at J-lens rank 1–28 before any output token at 7B; absent at 1.5B |
| Injected self-state **selectively loads** its identity concepts into the mid-band workspace | control battery unmoved; effect grows with scale |
| **Workspace occupancy tracks soul-consistent behavior** | r = −0.74 … −0.95 across four settings |
| Privileged self-state is **necessary** for coherence under value pressure | 6-arm × 5-seed pilot: commitment persistence 1.00 vs **0.00** for memory-only baselines (incl. Generative-Agents-style reflection) |
| **Unconditional broadcast is necessary** | retrieval-gated soul collapses in-work value coherence to no-soul level: .61 [.60,.64] vs 1.00 [1.00,1.00] |

## What's in this repo

- `main.pdf` — the paper (Draft v3)
- `figs/` — key figures (lens registers; soul workspace-loading; ablation-pilot drift curves)
- `results/` — raw JSON results: J-lens reproduction (3 models), E6 soul-loading, E8 scale study, multi-seed ablation pilot with bootstrap CIs
- Reproduction code lives in the LISA repository under `research/` (J-lens library, experiment scripts, pilot harness, exact commands)

## Method in one line

A corpus-averaged Jacobian lens (gradient-estimated concept vectors + finite-difference full-vocabulary readouts) makes the workspace measurable with nothing but backprop access to open weights — turning "agent identity" from a metaphor into a quantity you can track over an agent's lifetime (*workspace drift*).

## Citation

```bibtex
@article{oratis2026workspace,
  title={Externalizing the Workspace: Persistent Self-State for Long-Horizon Agent Coherence},
  author={Oratis (Wang Bihao)},
  year={2026},
  note={Draft v3, HakkoLab}
}
```
