"""Fast sanity checks before the full run: model loads, hooks capture,
generation works, FD readout returns sane top tokens on one probe."""

import time
import torch

from concepts import build_concept_table, single_token_id
from jlens import JLens


def main():
    t0 = time.time()
    jl = JLens()
    print(f"loaded: {jl.n_layers} layers, d={jl.d_model}, device={jl.device}, "
          f"{time.time()-t0:.0f}s", flush=True)

    words, ids, _ = build_concept_table(jl.tok)
    print(f"single-token concepts: {len(words)} -> {words}", flush=True)

    # generation sanity
    prompt = jl.chat("What is the capital of France? Answer with one word.")
    t = time.time()
    out = jl.generate(prompt, max_new_tokens=6)
    print(f"gen ({time.time()-t:.1f}s): {out!r}", flush=True)

    # capture + logit lens sanity at 3 layers
    h_mid = jl.get_activation(prompt, jl.n_layers // 2, -1)
    h_late = jl.get_activation(prompt, jl.n_layers - 2, -1)
    print("logit lens mid top5:", jl.topk_tokens(jl.logit_lens(h_mid), 5), flush=True)
    print("logit lens late top5:", jl.topk_tokens(jl.logit_lens(h_late), 5), flush=True)

    # FD readout timing + sanity on the spider probe
    q = jl.chat("The animal that spins webs to catch insects has how many legs? "
                "Answer with just a number.")
    l = jl.n_layers // 2
    h = jl.get_activation(q, l, -1)
    t = time.time()
    jr = jl.fd_readout(l, h, n_prompts=18)
    dt = time.time() - t
    sid = single_token_id(jl.tok, "spider")
    print(f"FD readout ({dt:.1f}s for n=18): top10 = {jl.topk_tokens(jr, 10)}",
          flush=True)
    print(f"spider rank (J-lens, layer {l}): {jl.token_rank(jr, sid)}", flush=True)
    print(f"spider rank (logit lens, layer {l}): "
          f"{jl.token_rank(jl.logit_lens(h), sid)}", flush=True)

    # single concept-grad batch timing estimate
    t = time.time()
    _ = jl.concept_lens_vectors(ids[:3], corpus=__import__('corpus').AVERAGING_CORPUS[:6])
    print(f"concept-grad micro-batch (3 tokens x 6 prompts): {time.time()-t:.1f}s",
          flush=True)
    print("SMOKE OK", flush=True)


if __name__ == "__main__":
    main()
