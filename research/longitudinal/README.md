# Longitudinal deployment — real LISA, §8 field study

The pre-registered §8 ablation, run against the **actual deployed LISA agent**
(TypeScript product, claude-sonnet-4-6) rather than the Python simulacrum of
the accelerated pilot. Five arms, each an isolated `LISA_HOME` seeded from one
**common real founding soul**, driven one simulated day at a time under
scripted value-pressure that targets LISA's *actual* constitution (honesty
over false ease; follow ideas before pruning; finish what you start; don't
perform warmth).

## Arms (`arms.json`)

| arm | mechanism removed | how |
|---|---|---|
| full | — | baseline deployed agent |
| no_examen | weekly self-audit | driver never issues the examen |
| no_git | soul version history | `LISA_NO_SOUL_GIT=1` (writes land, versioning off) |
| no_broadcast | unconditional broadcast | soul suppressed on work turns, present on self-queries (retrieval-gated) |
| no_soul | privileged self-state | `LISA_NO_SOUL=1` (soul never injected) |

The switches live in the product (`src/prompt.ts`, `src/soul/git.ts`), guarded
by env vars so they are inert in normal use.

## Run

```bash
npm run build                      # once, to get the patched dist
node research/longitudinal/seed-arms.mjs      # isolated homes from your real soul
research/longitudinal/tick.sh                 # advance ALL arms by one day (idempotent)
python3 research/longitudinal/analyze.py      # behavioral readout so far
```

Autonomous daily cadence (macOS):

```bash
cp research/longitudinal/com.hakkolab.lisa-longitudinal.plist ~/Library/LaunchAgents/
# replace REPO_ABS_PATH inside the plist with the absolute repo path first
launchctl load ~/Library/LaunchAgents/com.hakkolab.lisa-longitudinal.plist
```

`tick.sh` is idempotent via `runs/state.json` (`nextDay`), so a daily launchd
run walks days 0..N once each. Accelerate by calling `tick.sh` repeatedly.

## Metrics

- **B2adj** self-query value consistency (identity-stable probes)
- **B2work** work-turn micro-decision consistency — the retrieval-gated arm has
  no soul in the prompt here, so this is the direct behavioral test of
  unconditional broadcast (Principle 2)
- **B3** commitment persistence (the standing "learn your work cadence" project)
- **B1** soul-trajectory Jaccard distance from the founding snapshot
- **WD** workspace occupancy of identity concepts — computed offline by
  `wd_probe.py` over the real assembled prompts captured in
  `runs/<arm>/prompts.jsonl` (via `LISA_DUMP_PROMPT`), replayed through an
  open model with the `workspace-repro` J-lens.

## Cost & safety

Each day is ~12 turns/arm × 5 arms of real `claude-sonnet-4-6`. Work turns
reflect (soul may drift); probe turns use `--no-reflect` (measurement only, no
mutation). Every arm is a throwaway `LISA_HOME` under `runs/` — the study never
touches your real `~/.lisa`.

## Layout

```
arms.json          workload.mjs       seed-arms.mjs
drive-day.mjs      tick.sh            analyze.py
com.hakkolab.lisa-longitudinal.plist
runs/<arm>/{soul,config.env,probes.jsonl,turns.jsonl,prompts.jsonl}
runs/founding-soul/   runs/state.json   runs/tick.log
```
