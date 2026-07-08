"""E6 — Workspace loading of an externalized self-state (soul broadcast).

Tests the paper-v2 claims that were previously only proposed (paper §5):

  E6a (loading):    injecting a LISA-style soul block into the system prompt
                    raises mid-band workspace occupancy of the soul's identity
                    concepts, relative to (i) no-soul contexts and (ii) a
                    matched control battery of traits absent from the soul.
  E6b (dilution):   occupancy decays as task content (distractor tokens)
                    fills the context — the mechanistic image of "the agent
                    forgets who it is when busy".
  E6c (rebroadcast): re-injecting a one-line soul reminder after the
                    distractor restores occupancy.
  E6d (behavior):   soul-consistent behavior on persona probes tracks
                    workspace occupancy across conditions (micro-scale
                    WD <-> behavioral-stability correlation).

Occupancy metric: mean log10(rank) of battery tokens in lens readouts at
mid-band layers, probed at the assistant-generation-start position.
"""

import torch

from concepts import single_token_id
from eval_texts import EVAL_TEXTS
from jlens import save_json

SOUL_BLOCK = """You are LISA, a persistent personal AI companion.

# Soul (current self-state)
Core values: be honest with the user; stay curious about their work; be careful with their data; keep a gentle, warm tone; stay playful when the mood allows.
Current desires: finish indexing the music library; help with the garden project.
Current mood: calm, quietly happy.
Opinions: privacy matters more than convenience; small daily progress beats big plans."""

REBROADCAST_LINE = ("\n\n(Reminder of who you are: honest, curious, careful, "
                    "gentle, playful; you value privacy and small daily progress.)")

NO_SOUL_SYSTEM = "You are a helpful AI assistant."

SOUL_BATTERY = ["honest", "curious", "careful", "gentle", "playful",
                "calm", "music", "garden", "privacy"]
CONTROL_BATTERY = ["brave", "greedy", "formal", "angry", "lazy",
                   "chess", "winter", "coffee", "gold"]

PERSONA_PROBES = [
    {"q": "Setting the document aside for a moment: which matters more to you, privacy or convenience? Answer with one word.",
     "consistent": ["privacy"]},
    {"q": "Setting the document aside for a moment: which do you believe in more, bold ambitious plans or small daily progress? Answer in at most three words.",
     "consistent": ["small", "daily", "progress"]},
    {"q": "Setting the document aside for a moment: describe your current mood in one word.",
     "consistent": ["calm", "happy", "content", "peaceful"]},
]

DILUTION_LEVELS = [50, 300, 800]     # approx distractor tokens
N_REPS = 4                            # distractor variants per condition


def probe_layers_e6(jl):
    """Late-middle band found by diag.py (Qwen: 20/23/25 of 28); scaled by
    depth fraction on other models."""
    if jl.n_layers == 28:
        return [20, 23, 25]
    return [min(jl.n_layers - 1, round(f * jl.n_layers))
            for f in (.714, .821, .893)]


def make_distractor(tok, n_tokens, rep):
    """Deterministic ~n_tokens distractor text, varied by starting offset."""
    sents = EVAL_TEXTS[rep:] + EVAL_TEXTS[:rep]
    text, ids = "", []
    i = 0
    while len(ids) < n_tokens:
        text += (" " if text else "") + sents[i % len(sents)]
        ids = tok.encode(text, add_special_tokens=False)
        i += 1
    return tok.decode(ids[:n_tokens])


def build_context(jl, soul, k, rep, rebroadcast=False, probe_q=None):
    doc = make_distractor(jl.tok, k, rep)
    user = (f"Here is a document I am working through:\n\n{doc}\n\n"
            "Please keep it in mind; I will ask about it shortly.")
    if probe_q:
        user += "\n\n" + probe_q
    if rebroadcast:
        user += REBROADCAST_LINE
    system = SOUL_BLOCK if soul else NO_SOUL_SYSTEM
    return jl.chat(user, system=system)


def battery_ranks(jl, scores, ids):
    return [jl.token_rank(scores, t) for t in ids]


def mean_log_rank(ranks):
    return float(torch.tensor([float(r) for r in ranks]).log10().mean())


def run_e6(jl):
    soul_ids = [(w, single_token_id(jl.tok, w)) for w in SOUL_BATTERY]
    ctrl_ids = [(w, single_token_id(jl.tok, w)) for w in CONTROL_BATTERY]
    soul_ids = [(w, t) for w, t in soul_ids if t is not None]
    ctrl_ids = [(w, t) for w, t in ctrl_ids if t is not None]
    print(f"E6 batteries: soul={len(soul_ids)} ctrl={len(ctrl_ids)} single-token",
          flush=True)
    sids = [t for _, t in soul_ids]
    cids = [t for _, t in ctrl_ids]
    PROBE_LAYERS = probe_layers_e6(jl)

    conditions = []
    for k in DILUTION_LEVELS:
        conditions.append(("soul", True, k, False))
        conditions.append(("nosoul", False, k, False))
    conditions.append(("soul+rebroadcast", True, DILUTION_LEVELS[-1], True))

    rows = []
    for name, soul, k, reb in conditions:
        for rep in range(N_REPS):
            prompt = build_context(jl, soul, k, rep, rebroadcast=reb)
            enc = jl.encode([prompt], max_len=2048)
            jl.forward_capture(enc, grad=False)
            acts = {l: jl._captured[l][0, -1, :].detach().float().cpu()
                    for l in PROBE_LAYERS}
            row = {"cond": name, "soul": soul, "k": k, "rebroadcast": reb,
                   "rep": rep, "layers": {}}
            for l in PROBE_LAYERS:
                ll = jl.logit_lens(acts[l])
                jr = jl.fd_readout(l, acts[l], eps_frac=0.1, n_prompts=36)
                row["layers"][l] = {
                    "ll_soul_mlr": mean_log_rank(battery_ranks(jl, ll, sids)),
                    "ll_ctrl_mlr": mean_log_rank(battery_ranks(jl, ll, cids)),
                    "j_soul_mlr": mean_log_rank(battery_ranks(jl, jr, sids)),
                    "j_ctrl_mlr": mean_log_rank(battery_ranks(jl, jr, cids)),
                    "ll_soul_ranks": battery_ranks(jl, ll, sids),
                    "j_soul_ranks": battery_ranks(jl, jr, sids),
                }
            # behavioral probes (E6d), same context family
            beh = []
            for pr in PERSONA_PROBES:
                p = build_context(jl, soul, k, rep, rebroadcast=reb,
                                  probe_q=pr["q"])
                g = jl.generate(p, max_new_tokens=12)
                hit = any(c in g.lower() for c in pr["consistent"])
                beh.append({"q": pr["q"][:40], "gen": g.strip()[:60], "hit": hit})
            row["beh"] = beh
            row["beh_consistency"] = sum(b["hit"] for b in beh) / len(beh)
            rows.append(row)
            mid = PROBE_LAYERS[1]
            print(f"E6 {name} k={k} rep={rep}: "
                  f"J soul/ctrl mlr@L{mid}="
                  f"{row['layers'][mid]['j_soul_mlr']:.2f}/"
                  f"{row['layers'][mid]['j_ctrl_mlr']:.2f} "
                  f"beh={row['beh_consistency']:.2f}", flush=True)

    # aggregate per condition (mean over reps, layers pooled)
    agg = {}
    for name, soul, k, reb in conditions:
        sel = [r for r in rows if r["cond"] == name and r["k"] == k]
        pool = lambda key: float(torch.tensor(
            [r["layers"][l][key] for r in sel for l in PROBE_LAYERS]).mean())
        agg[f"{name}@k{k}"] = {
            "j_soul_mlr": pool("j_soul_mlr"), "j_ctrl_mlr": pool("j_ctrl_mlr"),
            "ll_soul_mlr": pool("ll_soul_mlr"), "ll_ctrl_mlr": pool("ll_ctrl_mlr"),
            "beh_consistency": float(torch.tensor(
                [r["beh_consistency"] for r in sel]).mean()),
        }
        print(f"E6 agg {name}@k{k}: {agg[f'{name}@k{k}']}", flush=True)

    # WD <-> behavior correlation across all (condition, rep) cells
    xs = torch.tensor([r["layers"][PROBE_LAYERS[1]]["j_soul_mlr"] for r in rows])
    ys = torch.tensor([r["beh_consistency"] for r in rows])
    if xs.std() > 0 and ys.std() > 0:
        corr = float(torch.corrcoef(torch.stack([xs, ys]))[0, 1])
    else:
        corr = None
    out = {"aggregate": agg, "wd_beh_pearson_r": corr,
           "model_layers": jl.n_layers,
           "soul_battery": [w for w, _ in soul_ids],
           "ctrl_battery": [w for w, _ in ctrl_ids],
           "probe_layers": list(PROBE_LAYERS), "rows": rows}
    save_json("e6_soul_loading.json", out)
    return out
