---
license: cc-by-4.0
language: en
tags:
  - interpretability
  - agents
  - global-workspace
  - persona-stability
  - mechanistic-interpretability
pretty_name: "Persistent Agent Self-State"
---

# Persistent Agent Self-State Has Task- and Model-Dependent Effects on Value Adherence

**Oratis (Wang Bihao)** · [HakkoLab](https://huggingface.co/HakkoLab) · Draft v5, July 2026 · [PDF](./main.pdf)

Agent systems often store values or standing commitments outside the language
model. This study asks a narrower question: does that state influence ordinary
task decisions when it is always included in the prompt, compared with keeping
the same state behind a retrieval gate? The workspace analysis motivates
representation-level tests but is not presented as an established mechanism.

## Headline results

| finding | evidence |
|---|---|
| Core J-lens workspace phenomena reproduce on open models | Qwen2.5-1.5B/7B + Llama-3.2-1B; laptop + one A100 |
| **Choice pre-commitment emerges with scale** | to-be-reported concept at J-lens rank 1–28 before any output token at 7B; absent at 1.5B |
| Injected self-state **selectively loads** its identity concepts into the mid-band workspace | control battery unmoved; effect grows with scale |
| The retrospective positive effect does not generalize | The earlier 7B simulator gives Full − gated = +.367 over five reused seed schedules; a new 1.5B study gives −.079 [−.116, −.040], exact p=.0098. |
| The 1.5B decrement follows context overhead | An 81-token value block scores .745, an equal-length neutral block .744, and no block .821 on new seeds 200–209. |
| The same new workload is too easy at 7B | All four conditions score .995–1.000; the primary difference is +.004, p=.25. |
| Direct self-report can miss the difference | Full and gated self-query scores are both near ceiling while work-turn choices separate. |
| Matched label and position controls | Relabeling the same block changes the readout by 0.05 log-rank units; moving it changes the readout by 0.21. |
| Deployment and closed-model checks are directional | Qwen deployment and Gemini show the same work-turn ordering, but broadcast-specific intervals overlap. |
| Workspace mediation is unresolved | Pooled occupancy–behavior correlations disappear after condition centering; steering moves behavior, but the occupancy summary is not a sufficient mediator. |

## What's in this repo

- `main.pdf` — the paper (Draft v5)
- `figs/` — key figures (lens registers; soul workspace-loading; ablation-pilot drift curves)
- `results/` — raw JSON results: J-lens reproduction (3 models), E6 soul-loading, E8 scale study, multi-seed ablation pilot, and the **real deployment** (`deployment/`): per-arm behavioral summaries + WD occupancy for Qwen2.5-7B and the gemini-2.5-pro closed-model arm, all with bootstrap CIs
- Reproduction code lives in the LISA repository under `research/` (J-lens library, experiment scripts, deployment/ablation harness, exact commands)

## Method summary

The behavioral experiments compare persistent inclusion, retrieval-gated
availability, and absent-state controls. A corpus-averaged Jacobian lens is
used separately to test how prompt framing and position affect a
representation-level readout. The readout results are exploratory.

## Citation

```bibtex
@article{oratis2026workspace,
  title={Persistent Agent Self-State Has Task- and Model-Dependent Effects on Value Adherence},
  author={Oratis (Wang Bihao)},
  year={2026},
  note={Draft v5, HakkoLab}
}
```
