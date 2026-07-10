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

## Operational notes (2026-07-10 audit)

The live deployment does **not** run from this worktree. A verification pass
found three blockers that forced changes:

1. **macOS TCC blocks launchd under `~/Documents`.** LaunchAgents cannot
   `getcwd`/exec anything inside `~/Documents` (`Operation not permitted`), so
   the runnable copy (self-contained `dist/` + `node_modules` + this harness +
   `runs/`) lives at **`~/lisa-longitudinal/`** (non-protected). The plist
   points there; this worktree copy is the git source of truth. To relocate:
   copy `dist/`, `node_modules/`, `research/longitudinal/` preserving the
   `REPO/dist` + `REPO/research/longitudinal` layout.
2. **launchd has a minimal PATH** (no Homebrew `node`) — `tick.sh` now prepends
   `/opt/homebrew/bin`.
3. **The GCP relay 401s** (deployed revision pins a stale secret). `fix-keys.sh`
   rewrites each arm's `config.env` to reach Anthropic directly with the relay's
   own upstream key + the local clash proxy (`127.0.0.1:7897`). **Run it after
   every `seed-arms.mjs --force`**, which re-copies the broken relay config.

**Dependencies for the daily 03:30 launchd tick:** the clash proxy (7897) must
be running; `node` on `/opt/homebrew/bin`; the relocated tree intact.

**Integrity guards added:** `drive-day.mjs` aborts a day (exit 3) if every work
turn returns empty/errored, snapshots the soul per day to
`runs/<arm>/soul_snapshots.jsonl` (for the B1 trajectory metric), and purges a
day's partial rows before re-running it; `tick.sh` advances `state.json` **only
when every arm succeeds**, so a broken backend can never silently corrupt the
series (this exact failure — empty day-1 turns advancing the counter — is what
the audit caught).

**Reset-and-restart recipe:**
```bash
cd ~/lisa-longitudinal/research/longitudinal
node seed-arms.mjs --force     # common soul, state=0
bash fix-keys.sh               # direct key + proxy (undo relay)
bash tick.sh                   # run day 0; launchd takes over at 03:30 daily
```
