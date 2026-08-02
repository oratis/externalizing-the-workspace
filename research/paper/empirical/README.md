# Empirical version

**No Benefit from Persistent Value Context: A Pre-Specified Replication with
Token-Matched Controls** — 12 pages, 2 figures.

A self-contained replication report. It asks whether including a compact record
of an agent's values in every model call improves value-relevant decisions made
during ordinary work, relative to storing that record behind a retrieval gate.

The short answer is that our own earlier positive estimate (+.37) does not
replicate, and that the effect it appeared to measure is a length effect:

- Under a protocol frozen before execution, with ten run seeds disjoint from the
  exploratory ones, the persistent condition scores `.746` against `.825` for the
  gated condition on Qwen2.5-1.5B (difference `-.079`, exact `p=.0098`).
- Holding label, position and length fixed at 81 tokens and swapping the
  value-bearing body for neutral repository facts changes nothing (`.745` vs
  `.744`), while both sit below a no-block condition (`.821`).
- Qwen2.5-7B saturates in all four conditions, so no effect is estimable there.
- Self-query accuracy is identical in the two conditions that differ by `.079`
  on embedded decisions.

## Relationship to `../main.tex`

`../main.tex` is a longer version (24 pages) that additionally reports a J-lens
reproduction on open weights and three representation-level experiments. The two
share the behavioral data and report identical numbers for it.

They are maintained as separate documents on purpose. This one is deliberately
narrower: it drops the workspace framing, the design principles, the agent
implementation description, and every representation-level analysis, and leads
with the replication failure instead. Do not merge them, and do not treat this
directory as generated output — `main.tex` here is its own source and is not
produced by `../make_variants.py`.

## Build

```
tectonic main.tex
```

Figures are copied from `../figs/`. `abstract.txt` is the plain-ASCII abstract.

## Data

Everything the paper reports comes from `../../confirmatory-v5/` (the frozen
protocol documents, the workload generator, the analysis scripts, and the
complete per-record data for all three runs) and `../../analysis/` (the
re-analysis of the earlier simulator study).
