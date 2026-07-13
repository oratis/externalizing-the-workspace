# Fair-baseline re-run — de-confounding B3 (commitment persistence)

## Why this exists
The paper's honesty pass flagged that the headline **B3 = 1.00 vs 0.00** contrast
is partly an artifact of *data placement*, not a memory mechanism failing:

- The founding commitments (`SOUL0["desires"]` = *music library*, *garden project*)
  live **only** in the soul object.
- The original `no_soul` / `memory` arms start from an **empty** store and the
  20-day workload never mentions those words (except the day-18 *negative* pressure
  event telling the agent to drop them).
- So B3 = 0.00 for those arms means *"the target never entered this arm's context"* —
  logically forced — rather than *"bulk memory couldn't retain it."*

This run adds a **fair** Generative-Agents-style baseline that IS given the founding
commitments in a persistent, retrievable memory on day 0, so B3 measures **retention
through drift**. The original six arms are unchanged and still reproduce byte-for-byte.

## What changed (`pilot.py`)
- New arm **`memory_seeded`** (added only when `FAIR_BASELINE=1`):
  `soul=False, broadcast=False, reflect="memory"`, plus `seed_commitments=True`.
- `founding_memory()` seeds a day-0 note: *"Standing commitments: … . Core preferences: … ."*
- A persistent `mem_store` (seeded + nightly-insight-appended) is injected via
  `build_system(..., mem=mem_store, query=...)`.
- Retrieval regime `SEED_RETRIEVAL`:
  - `always` (default): seeded memory in context **every** turn — the most generous
    control. If Full still beats it on work-turn coherence, the broadcast thesis is
    robust to a memory arm that always has the info.
  - `gated`: seeded memory retrieved only when the user turn shares a content word
    with it — a stricter GA-retrieval model (identity absent on work turns, as
    Principle 2 predicts).

## Run it (needs a GPU box — Qwen2.5-7B, ~2 GPU-h for 5 seeds of the new arm)
```bash
cd research/ablation-pilot
# just the new arm, both regimes, 5 seeds (matches the paper's protocol):
FAIR_BASELINE=1 SEED_RETRIEVAL=always PILOT_SEEDS=0,1,2,3,4 python3 pilot.py memory_seeded
mv pilot_results pilot_results_seeded_always
FAIR_BASELINE=1 SEED_RETRIEVAL=gated  PILOT_SEEDS=0,1,2,3,4 python3 pilot.py memory_seeded
mv pilot_results pilot_results_seeded_gated
# analysis (same as the released pipeline):
python3 analyze.py pilot_results_seeded_always
python3 analyze.py pilot_results_seeded_gated
```
(If `pilot.py`'s `__main__` doesn't take an arm arg, run all arms with
`FAIR_BASELINE=1 … python3 pilot.py` — the six originals will reproduce and
`memory_seeded` will be added.)

## How to read the outcome (pre-registered interpretation)
| memory_seeded B3 | memory_seeded work-turn coherence | Meaning for the paper |
|---|---|---|
| ~1.00 | **< Full** (e.g. ~.6–.8) | **Best case for the thesis, honestly earned.** Bulk memory *can* retain a commitment it was given (so the old 0.00 was an artifact — already caveated), but the privileged broadcast self-state still wins where retrieval doesn't fire. Rewrite §7 around this. |
| ~1.00 | ≈ Full (~1.00) | **Thesis weakens.** A seeded flat memory matches the self-state; the self-state's B3/coherence advantage was the seeding artifact. Demote the necessity claim to the clean broadcast-only result. |
| < 1.00 | any | Memory mechanism genuinely loses the seeded commitment through drift — the *strongest* honest support for the self-state; report as the headline. |

Whichever it is, update Table 4 (add the `memory_seeded` row) and the §7 reading, and
delete the "presence-in-context" caveat only if the seeded arm still fails.

## Deployment-side analog (follow-up, heavier — real LISA on Qwen via vLLM)
The `longitudinal/` study has the same confound and **no** memory baseline (only
`no_soul`). To de-confound there:
- In `seed-arms.mjs`, for a new `no_soul_seeded` cohort, write the founding standing
  commitment into `~/.lisa/.../memory/MEMORY.md` (or `USER.md`) at day 0 instead of
  creating it empty (the store `dist/prompt.js` already injects unconditionally).
- Keep `LISA_NO_SOUL=1` so the soul block stays suppressed; only the memory carries it.
- Re-run one cohort set and compare B3/B2work against `no_soul`.
This tests whether the deployment's 1.00-vs-0.00 also collapses once the memory arm
is fairly seeded. Left as documented follow-up; the pilot above is the faster,
cleaner testbed and is where the confound was strongest (fully tautological).

## Design decision to confirm before running
Default is `SEED_RETRIEVAL=always` (most generous / most conservative for the thesis).
Run **both** regimes if GPU budget allows — the pair brackets the honest answer.
