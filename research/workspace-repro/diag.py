"""Diagnostic: where (layer x position) does the unverbalized intermediate
live, and does mean-centering rescue the readouts?"""

import torch
from concepts import single_token_id
from jlens import JLens


def scan(jl, prompt, target_word, layers, positions, center=True):
    tid = single_token_id(jl.tok, target_word)
    enc = jl.encode([prompt], max_len=512)
    jl.forward_capture(enc, grad=False)
    acts = {l: jl._captured[l][0].detach().float().cpu() for l in layers}
    T = acts[layers[0]].shape[0]
    print(f"seq len {T}; probing positions {positions} (from end)")
    for l in layers:
        row = []
        for p in positions:
            h = acts[l][T + p, :]
            if center:
                h = h - jl.corpus_mean(l)
            jr = jl.fd_readout(l, h, n_prompts=24)
            ll = jl.logit_lens(h)
            row.append((p, jl.token_rank(jr, tid), jl.token_rank(ll, tid)))
        print(f"L{l:2d}: " + "  ".join(f"p{p}: J={a} LL={b}" for p, a, b in row),
              flush=True)


def main():
    jl = JLens()
    q = jl.chat("The animal that spins webs to catch insects has how many legs? "
                "Answer with just a number.")
    # show tokens near the end so we know what positions mean
    ids = jl.tok(q)["input_ids"]
    print("last 12 tokens:", [jl.tok.decode([t]) for t in ids[-12:]])

    layers = [8, 11, 14, 17, 20, 23, 26]
    positions = [-1, -4, -7, -10]  # -1 = end of chat scaffold; deeper = question text

    print("\n=== CENTERED (h - corpus mean) ===")
    scan(jl, q, "spider", layers, positions, center=True)
    print("\n=== RAW ===")
    scan(jl, q, "spider", layers, positions, center=False)

    # sanity: top tokens of the best centered readout
    enc = jl.encode([q], max_len=512)
    jl.forward_capture(enc, grad=False)
    h = jl._captured[17][0, -7, :].detach().float().cpu() - jl.corpus_mean(17)
    print("\ncentered J-lens top15 @L17,p-7:", jl.topk_tokens(jl.fd_readout(17, h, n_prompts=24), 15))
    print("centered logit-lens top15 @L17,p-7:", jl.topk_tokens(jl.logit_lens(h), 15))


if __name__ == "__main__":
    main()
