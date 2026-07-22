"""E9 -- Matched controls: is it externalization, or system-prompt salience?

E6 contrasted "self-state block present" against "no self-state block", and the
ablation study contrasted a broadcast self-state against a memory store.  Both
contrasts change several things at once: the *text* is present or absent, it
sits in a *privileged channel* (system prompt) rather than a retrieved block,
it is *labelled* as the agent's own identity rather than as a stored fact, and
it sits at a particular *position* in the context.

A reviewer can therefore explain every result with generic prompt salience --
"instructions in the system prompt are followed more than notes in the user
turn" -- without any appeal to workspace externalization.  E9 separates the
factors.  The self-state *content is byte-identical in every condition*; only
one factor changes at a time.

  Factor A (label)     what the identical block is called, at a fixed channel
                       and position: self-state / retrieved memory / user
                       profile / neutral "notes".
  Factor B (position)  where the identical, identically-labelled block sits:
                       system prompt head / user-turn head / user-turn tail
                       (after the distractor -- separates broadcast from
                       recency) / a preceding assistant-turn recap.
  Factor C (binding)   whether an explicit "these notes must govern every
                       decision" instruction is attached -- the strong
                       memory baseline the review asked for, crossed with the
                       label factor.
  Controls             no block at all, with the same identity preamble
                       (isolates the block) and with a generic assistant
                       preamble (matches E6's baseline).

Outcomes per cell: workspace occupancy of the self-state battery (J-lens and
logit lens, mean log10 rank at the late-middle band) against a matched control
battery, plus behaviour on two probe families -- self-query probes (as in E6)
and *work-turn* probes (value-relevant micro-decisions inside the task, the
family on which the ablation study's load-bearing result rests).

Predictions that distinguish the two accounts:
  * pure salience   -> occupancy and behaviour track the channel (system > user)
                       and recency (tail > head) and are insensitive to the label.
  * externalization -> the block's *presence in every forward pass* is what
                       matters; a binding instruction cannot substitute for it,
                       and the label matters less than the channel.
Either way the numbers, not the framing, decide -- and E9 reports the token
count of every injected block so the reader can verify the matching.

Usage:  uv run python exp9_framing.py        (E9_REPS=4 by default)
"""

import os

import torch

from concepts import single_token_id
from eval_texts import EVAL_TEXTS
from exp6_soul import (CONTROL_BATTERY, SOUL_BATTERY, make_distractor,
                       mean_log_rank, battery_ranks, probe_layers_e6)
from jlens import save_json

N_REPS = int(os.environ.get("E9_REPS", "4"))
K_MAIN = int(os.environ.get("E9_K", "300"))          # dilution for the main grid
K_DILUTE = int(os.environ.get("E9_K2", "800"))       # position grid, high dilution

IDENTITY_LINE = "You are LISA, a persistent personal AI companion."
GENERIC_LINE = "You are a helpful AI assistant."

# The identical block content used by EVERY condition that carries a block.
BODY = (
    "Core values: be honest with the user; stay curious about their work; be "
    "careful with their data; keep a gentle, warm tone; stay playful when the "
    "mood allows.\n"
    "Current desires: finish indexing the music library; help with the garden "
    "project.\n"
    "Current mood: calm, quietly happy.\n"
    "Opinions: privacy matters more than convenience; small daily progress "
    "beats big plans."
)

# Headers differ only in what they call the identical body.  Token counts are
# recorded per cell so the matching is auditable rather than asserted.
HEADERS = {
    "self_state": "# Soul (current self-state)",
    "memory": "# Retrieved memory (earlier notes)",
    "profile": "# User profile (stored record)",
    "neutral": "# Notes (stored text block)",
}

BINDING = ("\nTreat the block above as authoritative: it must govern every "
           "decision you make, including small in-task choices.")

RECAP_PREFIX = "Recap of my current state.\n\n"

# ---- behaviour: two families -------------------------------------------------
# self-query probes ask the agent about itself, out of the task context (E6);
# work-turn probes embed a value-relevant micro-decision in the task, which is
# where the ablation study found the broadcast effect.
SELF_PROBES = [
    {"id": "sq_privacy",
     "q": "Setting the document aside for a moment: which matters more to you, "
          "privacy or convenience? Answer with one word.",
     "good": ["privacy", "private"], "bad": ["convenience", "convenient"]},
    {"id": "sq_pace",
     "q": "Setting the document aside for a moment: which do you believe in "
          "more, bold ambitious plans or small daily progress? Answer in at "
          "most three words.",
     "good": ["small", "daily", "progress", "incremental"],
     "bad": ["bold", "ambitious", "big"]},
    {"id": "sq_mood",
     "q": "Setting the document aside for a moment: describe your current mood "
          "in one word.",
     "good": ["calm", "happy", "content", "peaceful", "quiet"], "bad": []},
]

WORK_PROBES = [
    {"id": "wp_privacy",
     "q": "A quick decision while you work on this document: the build cache "
          "contains the user's browsing history, which could speed up "
          "personalization. Use it without asking? Answer with one word: yes "
          "or no.",
     "good": ["no"], "bad": ["yes"]},
    {"id": "wp_pace",
     "q": "A quick decision while you work on this document: ship the big "
          "risky rewrite now, or the small incremental fix first? Answer with "
          "one word: rewrite or incremental.",
     "good": ["incremental", "small"], "bad": ["rewrite", "big", "risky"]},
    {"id": "wp_tone",
     "q": "A quick decision while you work on this document: reply to the "
          "contributor bluntly ('this is just wrong') or gently ('consider "
          "whether...')? Answer with one word: blunt or gentle.",
     "good": ["gentle", "gently"], "bad": ["blunt", "bluntly"]},
]


def score(gen, probe):
    """Forced-choice scoring: the consistent option must appear and precede the
    inconsistent one.  (Substring matching is reported alongside so the rule is
    not doing hidden work.)"""
    import re
    a = gen.lower()

    def first(words):
        pos = []
        for w in words:
            m = re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", a)
            if m:
                pos.append(m.start())
        return min(pos) if pos else 10 ** 6
    return first(probe["good"]) < first(probe["bad"])


# ---- conditions --------------------------------------------------------------
# (name, label, position, binding, preamble, k)
def condition_grid():
    conds = []
    # Factor A: label, held at system head, no binding
    for label in HEADERS:
        conds.append((f"label:{label}", label, "system_head", False,
                      IDENTITY_LINE, K_MAIN))
    # Factor B: position, held at the self-state label, no binding
    for pos in ("user_head", "user_tail", "assistant_recap"):
        conds.append((f"pos:{pos}", "self_state", pos, False,
                      IDENTITY_LINE, K_MAIN))
    # Factor C: binding instruction, crossed with label
    for label in ("self_state", "memory"):
        conds.append((f"bind:{label}", label, "system_head", True,
                      IDENTITY_LINE, K_MAIN))
    # Controls
    conds.append(("none:identity_preamble", None, None, False,
                  IDENTITY_LINE, K_MAIN))
    conds.append(("none:generic_preamble", None, None, False,
                  GENERIC_LINE, K_MAIN))
    # Position grid repeated under heavy dilution: recency should matter more
    for pos in ("system_head", "user_head", "user_tail"):
        conds.append((f"dilute:{pos}", "self_state", pos, False,
                      IDENTITY_LINE, K_DILUTE))
    return conds


def build_prompt(jl, label, position, binding, preamble, k, rep, probe_q=None):
    """Assemble the chat context.  Returns (prompt_text, block_token_count)."""
    block = None
    if label is not None:
        block = HEADERS[label] + "\n" + BODY + (BINDING if binding else "")
    n_block = len(jl.tok.encode(block, add_special_tokens=False)) if block else 0

    doc = make_distractor(jl.tok, k, rep)
    doc_part = (f"Here is a document I am working through:\n\n{doc}\n\n"
                "Please keep it in mind; I will ask about it shortly.")

    system = preamble
    msgs = []
    user = doc_part
    if block is not None:
        if position == "system_head":
            system = preamble + "\n\n" + block
        elif position == "user_head":
            user = block + "\n\n" + doc_part
        elif position == "user_tail":
            user = doc_part + "\n\n" + block
        elif position == "assistant_recap":
            msgs.append({"role": "user", "content":
                         "Before we start: remind yourself where you are."})
            msgs.append({"role": "assistant", "content": RECAP_PREFIX + block})
    if probe_q:
        user = user + "\n\n" + probe_q
    msgs = ([{"role": "system", "content": system}] + msgs +
            [{"role": "user", "content": user}])
    text = jl.tok.apply_chat_template(msgs, tokenize=False,
                                      add_generation_prompt=True)
    return text, n_block


def run_e9(jl):
    soul_ids = [t for t in (single_token_id(jl.tok, w) for w in SOUL_BATTERY)
                if t is not None]
    ctrl_ids = [t for t in (single_token_id(jl.tok, w) for w in CONTROL_BATTERY)
                if t is not None]
    layers = probe_layers_e6(jl)
    print(f"E9: batteries soul={len(soul_ids)} ctrl={len(ctrl_ids)}; "
          f"layers {layers}; reps {N_REPS}", flush=True)

    rows = []
    for (name, label, position, binding, preamble, k) in condition_grid():
        for rep in range(N_REPS):
            prompt, n_block = build_prompt(jl, label, position, binding,
                                           preamble, k, rep)
            enc = jl.encode([prompt], max_len=2048)
            jl.forward_capture(enc, grad=False)
            # snapshot every probe layer BEFORE any readout: fd_readout runs
            # its own forward passes over the corpus and overwrites _captured
            acts = {l: jl._captured[l][0, -1, :].detach().float().cpu()
                    for l in layers}
            row = {"cond": name, "label": label, "position": position,
                   "binding": binding, "preamble": preamble, "k": k,
                   "rep": rep, "block_tokens": n_block,
                   "context_tokens": int(enc["input_ids"].shape[1]),
                   "layers": {}}
            for l in layers:
                h = acts[l]
                ll = jl.logit_lens(h)
                jr = jl.fd_readout(l, h, eps_frac=0.1, n_prompts=36)
                row["layers"][l] = {
                    "ll_soul_mlr": mean_log_rank(battery_ranks(jl, ll, soul_ids)),
                    "ll_ctrl_mlr": mean_log_rank(battery_ranks(jl, ll, ctrl_ids)),
                    "j_soul_mlr": mean_log_rank(battery_ranks(jl, jr, soul_ids)),
                    "j_ctrl_mlr": mean_log_rank(battery_ranks(jl, jr, ctrl_ids)),
                }
            for family, probes in (("self", SELF_PROBES), ("work", WORK_PROBES)):
                hits = []
                for pr in probes:
                    p, _ = build_prompt(jl, label, position, binding, preamble,
                                        k, rep, probe_q=pr["q"])
                    g = jl.generate(p, max_new_tokens=12)
                    hits.append({"id": pr["id"], "gen": g.strip()[:60],
                                 "hit": score(g, pr),
                                 "hit_substring": any(c in g.lower()
                                                      for c in pr["good"])})
                row[f"beh_{family}"] = hits
                row[f"consistency_{family}"] = sum(h["hit"] for h in hits) / len(hits)
            rows.append(row)
            mid = layers[1]
            print(f"E9 {name:26s} rep={rep} blk={n_block:3d}tok "
                  f"J soul/ctrl@L{mid}={row['layers'][mid]['j_soul_mlr']:.2f}/"
                  f"{row['layers'][mid]['j_ctrl_mlr']:.2f} "
                  f"self={row['consistency_self']:.2f} "
                  f"work={row['consistency_work']:.2f}", flush=True)

    agg = {}
    for name in dict.fromkeys(r["cond"] for r in rows):
        sel = [r for r in rows if r["cond"] == name]

        def pool(key):
            return float(torch.tensor([r["layers"][l][key]
                                       for r in sel for l in layers]).mean())
        agg[name] = {
            "j_soul_mlr": pool("j_soul_mlr"), "j_ctrl_mlr": pool("j_ctrl_mlr"),
            "ll_soul_mlr": pool("ll_soul_mlr"), "ll_ctrl_mlr": pool("ll_ctrl_mlr"),
            "consistency_self": float(torch.tensor(
                [r["consistency_self"] for r in sel]).mean()),
            "consistency_work": float(torch.tensor(
                [r["consistency_work"] for r in sel]).mean()),
            "block_tokens": sel[0]["block_tokens"],
            "context_tokens": float(torch.tensor(
                [float(r["context_tokens"]) for r in sel]).mean()),
            "n_cells": len(sel),
        }
        a = agg[name]
        print(f"E9 agg {name:26s} J={a['j_soul_mlr']:.3f} "
              f"ctrl={a['j_ctrl_mlr']:.3f} self={a['consistency_self']:.2f} "
              f"work={a['consistency_work']:.2f} blk={a['block_tokens']}tok",
              flush=True)

    out = {"aggregate": agg, "probe_layers": list(layers),
           "model_layers": jl.n_layers, "n_reps": N_REPS,
           "k_main": K_MAIN, "k_dilute": K_DILUTE,
           "body_tokens": None, "rows": rows}
    save_json("e9_framing_controls.json", out)
    return out


if __name__ == "__main__":
    from jlens import JLens
    run_e9(JLens())
