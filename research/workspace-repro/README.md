# workspace-repro

Scaled-down, open-compute reproduction of the core findings of:

> Gurnee, Sofroniew, Pearce, et al. **"Verbalizable Representations Form a
> Global Workspace in Language Models."** Transformer Circuits Thread,
> 2026-07-06. http://transformer-circuits.pub/2026/workspace/index.html

Target model: **Qwen2.5-1.5B-Instruct** (28 layers, d=1536), fp32 on Apple
MPS. Runs end-to-end on a consumer laptop (tested: M5 Pro, 48 GB).

## Method (and deviations from the paper)

The paper's J-lens is `lens(h) = softmax(W_U norm(J_l h))` with
`J_l = E[dh_final/dh_l]` averaged over ~1000 pretraining-like prompts on
Claude-family models. We approximate on open weights:

| Paper | Here |
|---|---|
| Exact averaged Jacobian `J_l` | Two estimators: (a) **concept lens vectors** `v_t(l) = E[d logit_t(last)/dh_l]` by batched backprop (= rows of `W_U J_l`, target restricted to the final position); (b) **full-vocab readouts** `W_U E[J_l] ĥ` by central finite differences around corpus activations (folds the final-RMSNorm Jacobian into the linearization) |
| ~1000-prompt corpus | 48 diverse pretraining-like snippets (`corpus.py`) |
| Claude Sonnet/Haiku/Opus | Qwen2.5-1.5B-Instruct |
| Full-vocab lens vectors | 52 curated single-token concepts (`concepts.py`) |

Known negative result at this scale: mean-centering probe activations
against the corpus mean *destroys* readouts (see `diag.py`); raw activations
are used throughout.

## Layout

- `jlens.py` — core: model wrapper, hooks, concept-gradient lens vectors,
  FD readouts, logit-lens baseline, steering/ablation generation.
- `corpus.py` / `eval_texts.py` — averaging corpus / held-out texts.
- `concepts.py` — concept battery (single-token filtered at runtime).
- `experiments.py` — E1 lens quality, E2 unverbalized intermediates,
  E3 pre-report probing, E4 steering, E5 automatic/flexible ablation
  dissociation (with random-subspace control).
- `run_all.py` — master runner; results land in `results/*.json`.
- `smoke_test.py`, `diag.py` — sanity checks and the layer×position scan
  that fixed the probe band.

## Run

```bash
uv sync
uv run python smoke_test.py   # ~1 min
uv run python run_all.py      # full suite; ~30-60 min on M5 Pro
```

Model weights: place Qwen2.5-1.5B-Instruct under
`models/qwen2.5-1.5b-instruct/` (we pull from ModelScope; HF hub also works
if your network allows).

## Findings

See `results/REPORT.md` (generated after `run_all.py`) and §6 of the paper
draft in `../paper/`.
