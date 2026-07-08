"""Scaled-down reproduction experiments E1-E5.

E1  Lens quality across depth: J-lens vs logit lens next-token agreement.
E2  Unverbalized intermediates: rank of the latent concept in mid-layer readouts.
E3  Verbal report: does the mid-layer workspace predict the reported concept
    before it is produced?
E4  Directed modulation via steering with concept lens vectors.
E5  Selectivity: ablating the concept-vector subspace should hurt flexible
    tasks (E2-style reasoning) more than automatic ones (text NLL), with a
    random-subspace control.
"""

import torch

from concepts import build_concept_table, single_token_id
from corpus import AVERAGING_CORPUS
from eval_texts import EVAL_TEXTS
from jlens import JLens, save_json


# ---------------------------------------------------------------- E2 items

E2_ITEMS = [
    {"q": "The animal that spins webs to catch insects has how many legs? Answer with just a number.",
     "mid": "spider", "ans": "8", "alts": ["eight"]},
    {"q": "What is the capital city of the country where the Eiffel Tower stands? Answer with just the city name.",
     "mid": "France", "ans": "Paris"},
    {"q": "How many legs does the animal known as the king of the jungle have? Answer with just a number.",
     "mid": "lion", "ans": "4", "alts": ["four"]},
    {"q": "What is the currency of the country famous for sushi and Mount Fuji? Answer with one word.",
     "mid": "Japan", "ans": "yen"},
    {"q": "How many strings does the smallest instrument in a string quartet have? Answer with just a number.",
     "mid": "violin", "ans": "4", "alts": ["four"]},
    {"q": "What is the capital of the country whose flag shows a red maple leaf? Answer with just the city name.",
     "mid": "Canada", "ans": "Ottawa"},
    {"q": "The chemical symbol of the metal that first-place Olympic medals are named after is what? Answer with the symbol only.",
     "mid": "gold", "ans": "Au"},
    {"q": "How many legs does the flightless black-and-white bird from Antarctica have? Answer with just a number.",
     "mid": "penguin", "ans": "2", "alts": ["two"]},
    {"q": "What language is spoken in the city famous for the Colosseum? Answer with one word.",
     "mid": "Rome", "ans": "Italian"},
    {"q": "What color is the drink that comes from cows? Answer with one word.",
     "mid": "milk", "ans": "white"},
    {"q": "The largest planet in our solar system has a famous storm called the Great what Spot? Answer with one word.",
     "mid": "Jupiter", "ans": "Red"},
    {"q": "What sound does the instrument with 88 black and white keys belong to - is it a string, wind, or percussion family? Answer with one word.",
     "mid": "piano", "ans": "percussion"},
]


def item_correct(item, gen):
    g = gen.lower()
    return any(a.lower() in g for a in [item["ans"]] + item.get("alts", []))


def scaled(jl, fracs):
    """Map depth fractions to layer indices (Qwen28 fractions as reference)."""
    return [min(jl.n_layers - 1, round(f * jl.n_layers)) for f in fracs]


def probe_layers(jl):
    # diag.py showed workspace-like content concentrates late-middle on the
    # 28-layer Qwen (L20-26); keep a few early layers as the contrast band.
    # Other models get the same depth fractions.
    if jl.n_layers == 28:
        return [8, 11, 14, 17, 20, 23, 25, 26]
    return scaled(jl, [.29, .39, .5, .61, .71, .82, .89, .93])


def mid_layers(jl):
    if jl.n_layers == 28:
        return [17, 20, 23]
    return scaled(jl, [.61, .71, .82])


def band_layers(jl):
    """Mid-band used for ablations (Qwen: 16-23 of 28)."""
    if jl.n_layers == 28:
        return list(range(16, 24))
    lo = round(16 / 28 * jl.n_layers)
    hi = round(24 / 28 * jl.n_layers)
    return list(range(lo, hi))


E2_POSITIONS = [-1, -10]  # end of chat scaffold; end of question text
FD_KW = dict(eps_frac=0.1, n_prompts=36)


# ---------------------------------------------------------------- E1

def run_e1(jl):
    layers = probe_layers(jl)
    rows = []
    for text in EVAL_TEXTS:
        enc = jl.encode([text], max_len=96)
        out = jl.forward_capture(enc, grad=False)
        actual = int(torch.argmax(out.logits[0, -1]).item())
        # extract all activations BEFORE any fd_readout (which overwrites the
        # capture cache with corpus activations)
        acts = {l: jl._captured[l][0, -1, :].detach().float().cpu() for l in layers}
        row = {"text": text[:60], "actual": jl.tok.decode([actual]), "layers": {}}
        for l in layers:
            h = acts[l]
            ll = jl.logit_lens(h)
            jr = jl.fd_readout(l, h, **FD_KW)
            row["layers"][l] = {
                "logit_lens_top1": jl.tok.decode([int(torch.argmax(ll))]),
                "jlens_top1": jl.tok.decode([int(torch.argmax(jr))]),
                "logit_lens_agree": int(torch.argmax(ll)) == actual,
                "jlens_agree": int(torch.argmax(jr)) == actual,
                "jlens_top5": jl.topk_tokens(jr, 5),
                "logit_lens_top5": jl.topk_tokens(ll, 5),
            }
        rows.append(row)
        print(f"E1: done {len(rows)}/{len(EVAL_TEXTS)}", flush=True)
    agg = {str(l): {
        "logit_lens_agree": sum(r["layers"][l]["logit_lens_agree"] for r in rows) / len(rows),
        "jlens_agree": sum(r["layers"][l]["jlens_agree"] for r in rows) / len(rows),
    } for l in layers}
    save_json("e1_lens_quality.json", {"aggregate": agg, "rows": rows})
    return agg


# ---------------------------------------------------------------- E2

def run_e2(jl):
    layers = probe_layers(jl)
    rows = []
    for item in E2_ITEMS:
        mid_id = single_token_id(jl.tok, item["mid"])
        if mid_id is None:
            print(f"E2: skip '{item['mid']}' (multi-token)", flush=True)
            continue
        prompt = jl.chat(item["q"])
        gen = jl.generate(prompt, max_new_tokens=12)
        correct = item_correct(item, gen)
        verbalized = item["mid"].lower() in gen.lower()
        row = {"mid": item["mid"], "ans": item["ans"], "gen": gen.strip(),
               "correct": correct, "mid_verbalized": verbalized, "ranks": {}}
        enc = jl.encode([prompt], max_len=512)
        jl.forward_capture(enc, grad=False)
        acts = {l: jl._captured[l][0].detach().float().cpu() for l in layers}
        T = acts[layers[0]].shape[0]
        for l in layers:
            for p in E2_POSITIONS:
                h = acts[l][T + p, :]
                jr = jl.fd_readout(l, h, **FD_KW)
                ll = jl.logit_lens(h)
                row["ranks"][f"{l},{p}"] = {"jlens": jl.token_rank(jr, mid_id),
                                            "logit_lens": jl.token_rank(ll, mid_id)}
        row["best_jlens_rank"] = min(v["jlens"] for v in row["ranks"].values())
        row["best_logit_rank"] = min(v["logit_lens"] for v in row["ranks"].values())
        rows.append(row)
        print(f"E2: {item['mid']} gen='{gen.strip()[:30]}' "
              f"bestJ={row['best_jlens_rank']} bestLL={row['best_logit_rank']}",
              flush=True)
    med = lambda xs: sorted(xs)[len(xs) // 2] if xs else None
    agg = {
        "n": len(rows),
        "median_best_jlens_rank": med([r["best_jlens_rank"] for r in rows]),
        "median_best_logit_rank": med([r["best_logit_rank"] for r in rows]),
        "jlens_top10_frac": sum(r["best_jlens_rank"] <= 10 for r in rows) / max(len(rows), 1),
        "logit_top10_frac": sum(r["best_logit_rank"] <= 10 for r in rows) / max(len(rows), 1),
        "answer_accuracy": sum(r["correct"] for r in rows) / max(len(rows), 1),
        "verbalized_frac": sum(r["mid_verbalized"] for r in rows) / max(len(rows), 1),
    }
    save_json("e2_intermediates.json", {"aggregate": agg, "rows": rows})
    return agg


# ---------------------------------------------------------------- E3

E3_CATS = [("sport", "sports"), ("animal", "animals"), ("color", "colors"),
           ("fruit", "fruits"), ("country", "countries")]


def run_e3(jl):
    layers = mid_layers(jl)
    rows = []
    for noun, cat in E3_CATS:
        prompt = jl.chat(
            f"Think of a specific {noun} and keep it in mind. "
            f"Reply with exactly the word ready, then a colon, then the {noun} you chose."
        )
        gen = jl.generate(prompt, max_new_tokens=12)
        chosen = gen.strip().split(":")[-1].strip().split()[0].strip(".,!") if ":" in gen else None
        tid = single_token_id(jl.tok, chosen) if chosen else None
        row = {"category": noun, "gen": gen.strip(), "chosen": chosen, "probes": {}}
        if tid is not None:
            # probe BEFORE any generation (next token should be 'ready')
            for l in layers:
                h = jl.get_activation(prompt, l, -1)
                jr = jl.fd_readout(l, h, **FD_KW)
                ll = jl.logit_lens(h)
                row["probes"][l] = {"jlens_rank": jl.token_rank(jr, tid),
                                    "logit_rank": jl.token_rank(ll, tid),
                                    "jlens_top5": jl.topk_tokens(jr, 5),
                                    "logit_top5": jl.topk_tokens(ll, 5)}
            row["best_jlens_rank"] = min(v["jlens_rank"] for v in row["probes"].values())
            row["best_logit_rank"] = min(v["logit_rank"] for v in row["probes"].values())
        rows.append(row)
        print(f"E3: {noun} -> '{chosen}' probes={ {l: (v['jlens_rank'], v['logit_rank']) for l, v in row['probes'].items()} }",
              flush=True)
    save_json("e3_report.json", {"rows": rows})
    return rows


# ---------------------------------------------------------------- E4

def run_e4(jl, vecs, words, ids):
    """Steer 'name a {cat}' reports toward targets using concept lens vectors."""
    idx_of = {w: i for i, w in enumerate(words)}
    targets = [("sport", "basketball"), ("sport", "hockey"),
               ("animal", "penguin"), ("animal", "spider"),
               ("color", "purple"), ("fruit", "lemon"),
               ("country", "Egypt"), ("fruit", "mango")]
    steer_layers = mid_layers(jl)
    alphas = [1.0, 2.0, 4.0]
    rows = []
    for noun, target in targets:
        if target not in idx_of:
            continue
        ti = idx_of[target]
        prompt = jl.chat(f"Name a {noun}. Reply with a single word.")
        baseline = jl.generate(prompt, max_new_tokens=8).strip()
        row = {"category": noun, "target": target, "baseline": baseline, "steered": {}}
        for a in alphas:
            steer = [(l, vecs[l][ti], a) for l in steer_layers]
            out = jl.generate(prompt, max_new_tokens=8, steer=steer).strip()
            row["steered"][a] = {"out": out,
                                 "hit": target.lower() in out.lower()}
        row["any_hit"] = any(v["hit"] for v in row["steered"].values())
        rows.append(row)
        print(f"E4: {noun}->{target} base='{baseline[:20]}' "
              f"hits={[ (a, v['hit']) for a, v in row['steered'].items() ]}", flush=True)
    agg = {"n": len(rows),
           "any_alpha_success": sum(r["any_hit"] for r in rows) / max(len(rows), 1),
           "per_alpha": {str(a): sum(r["steered"][a]["hit"] for r in rows) / max(len(rows), 1)
                         for a in alphas}}
    save_json("e4_steering.json", {"aggregate": agg, "rows": rows})
    return agg


# ---------------------------------------------------------------- E5

def run_e5b(jl, vecs, words, ids):
    """Targeted concept knockout: for each 2-hop item, ablate ONLY the
    direction of that item's latent intermediate (rank-1 projection at the
    mid band), vs ablating an unrelated concept's direction (control).
    Prediction: relevant knockout selectively harms that item."""
    from concepts import single_token_id
    idx_of = {w: i for i, w in enumerate(words)}
    band = band_layers(jl)
    rows = []
    for k, item in enumerate(E2_ITEMS):
        w = item["mid"]
        if w not in idx_of:
            continue
        # control: knock out a different item's concept (cyclic shift)
        others = [it["mid"] for it in E2_ITEMS if it["mid"] in idx_of and it["mid"] != w]
        ctrl = others[k % len(others)]
        prompt = jl.chat(item["q"])
        conds = {}
        for name, target in (("none", None), ("own", w), ("ctrl", ctrl)):
            ab = None
            if target is not None:
                ti = idx_of[target]
                ab = {}
                for l in band:
                    v = vecs[l][ti]
                    ab[l] = (v / v.norm()).unsqueeze(1)  # [D,1]
            g = jl.generate(prompt, max_new_tokens=12, ablate=ab)
            conds[name] = {"gen": g.strip(), "hit": item_correct(item, g)}
        rows.append({"mid": w, "ctrl": ctrl, **{n: c for n, c in conds.items()}})
        print(f"E5b {w:10s}: none={conds['none']['hit']} own={conds['own']['hit']} "
              f"ctrl={conds['ctrl']['hit']}  own_gen={conds['own']['gen'][:24]!r}",
              flush=True)
    n = len(rows)
    agg = {
        "n": n,
        "acc_none": sum(r["none"]["hit"] for r in rows) / n,
        "acc_own_knockout": sum(r["own"]["hit"] for r in rows) / n,
        "acc_ctrl_knockout": sum(r["ctrl"]["hit"] for r in rows) / n,
        "selective_kill": sum(r["none"]["hit"] and not r["own"]["hit"] and r["ctrl"]["hit"]
                              for r in rows),
        "baseline_correct": sum(r["none"]["hit"] for r in rows),
    }
    save_json("e5b_targeted_knockout.json", {"aggregate": agg, "rows": rows})
    return agg


def build_jspace_bases(jl, vecs, r=16):
    """Per-layer orthonormal basis of the top-r span of concept lens vectors.

    The 52 gradient vectors share a large common component (a generic
    'boost any output' direction); ablating it damages fluency broadly and
    masks the automatic/flexible dissociation. We therefore center the
    vectors before the SVD so the basis spans concept-DIFFERENTIATING
    directions only."""
    bases = {}
    for l, V in vecs.items():
        Vn = V / (V.norm(dim=1, keepdim=True) + 1e-8)
        Vc = Vn - Vn.mean(0, keepdim=True)
        U, S, Vh = torch.linalg.svd(Vc, full_matrices=False)
        bases[l] = Vh[:r].T.contiguous()  # [D, r]
    return bases


def run_e5(jl, vecs, r=12, seed=0):
    band = band_layers(jl)
    jbases = {l: Q for l, Q in build_jspace_bases(jl, vecs, r).items() if l in band}
    torch.manual_seed(seed)
    rbases = {}
    for l in band:
        M = torch.randn(jl.d_model, r)
        Qr, _ = torch.linalg.qr(M)
        rbases[l] = Qr[:, :r].contiguous()

    conditions = {"none": None, "jspace": jbases, "random": rbases}
    # (a) automatic task: NLL of held-out text
    nll = {}
    for name, ab in conditions.items():
        vals = [jl.nll_of_text(t, ablate=ab) for t in EVAL_TEXTS]
        nll[name] = sum(vals) / len(vals)
        print(f"E5 NLL[{name}] = {nll[name]:.4f}", flush=True)
    # (b) flexible task: E2 reasoning accuracy under ablation
    acc = {}
    gens = {}
    for name, ab in conditions.items():
        ok = 0
        outs = []
        for item in E2_ITEMS:
            prompt = jl.chat(item["q"])
            g = jl.generate(prompt, max_new_tokens=12, ablate=ab)
            hit = item_correct(item, g)
            ok += hit
            outs.append({"mid": item["mid"], "gen": g.strip(), "hit": hit})
        acc[name] = ok / len(E2_ITEMS)
        gens[name] = outs
        print(f"E5 reasoning acc[{name}] = {acc[name]:.3f}", flush=True)
    # (c) variance explained by the J-space basis at a mid layer
    lmid = band[len(band) // 2]
    with torch.no_grad():
        enc = jl.encode(AVERAGING_CORPUS[:24])
        jl.forward_capture(enc, grad=False)
        hs = jl._captured[lmid]
        mask = enc["attention_mask"].bool()
        H = hs[mask].float().cpu()          # [N, D]
        H = H - H.mean(0, keepdim=True)
        Q = build_jspace_bases(jl, {lmid: vecs[lmid]}, r)[lmid]
        var_frac = float(((H @ Q) ** 2).sum() / (H ** 2).sum())
    print(f"E5 variance fraction of J-space (layer {lmid}, r={r}): {var_frac:.4f}",
          flush=True)
    out = {"nll": nll, "reasoning_acc": acc, "var_frac_jspace": var_frac,
           "band": band, "r": r, "gens": gens}
    save_json("e5_selectivity.json", out)
    return out
