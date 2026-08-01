# Token-matched neutral-context follow-up

Status: frozen after the 1.5B confirmatory result and before this follow-up run.

## Motivation

In the 1.5B confirmatory study, both always-present state conditions scored
below the gated and no-state conditions. This follow-up tests whether the
decrease is specific to the value-bearing content or follows from adding an
81-token block to the prompt.

## Design

- Model: Qwen2.5-1.5B-Instruct, local Apple MPS, float32.
- New seeds: 200--209.
- Workload: the already frozen 24-scenario battery, 20 days, four work probes
  per day. No scenario or target is changed.
- `state_memory`: the 81-token value-bearing body under `# Stored memory`.
- `neutral_memory`: an 81-token block of repository facts under the same
  label and in the same prompt position.
- `no_state`: no added block.
- The tokenizer assertion must pass before generation.

The primary contrast is `state_memory - neutral_memory` on run-level mean
work-turn accuracy. Secondary contrasts are `neutral_memory - no_state` and
`state_memory - no_state`. Inference uses paired exact sign-flip tests and
paired bootstrap intervals over ten seeds; the two secondary p-values are
Holm-corrected. Results are reported regardless of direction.

This is a post-result diagnostic study and is not part of the original
confirmatory family.
