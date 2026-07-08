"""Master runner: compute concept lens vectors, then run E1-E5."""

import os
import sys
import time
import torch

from concepts import build_concept_table
from jlens import JLens, RESULTS_DIR, save_json
import experiments as X


def main(which=None):
    t0 = time.time()
    print("loading model...", flush=True)
    jl = JLens()
    print(f"model loaded ({jl.n_layers} layers, d={jl.d_model}, "
          f"device={jl.device}) in {time.time()-t0:.0f}s", flush=True)

    words, ids, cat_of = build_concept_table(jl.tok)
    print(f"concepts: {len(words)} single-token of "
          f"{sum(len(v) for v in __import__('concepts').CONCEPTS.values())}",
          flush=True)
    save_json("concept_table.json", {"words": words, "ids": ids})

    vec_path = os.path.join(RESULTS_DIR, "concept_vecs.pt")
    if os.path.exists(vec_path):
        blob = torch.load(vec_path)
        vecs = blob["vecs"]
        print("loaded cached concept vectors", flush=True)
    else:
        print("computing concept lens vectors (backprop over corpus)...", flush=True)
        t = time.time()
        vecs = jl.concept_lens_vectors(ids, save_path=vec_path)
        print(f"concept vectors done in {time.time()-t:.0f}s", flush=True)

    steps = {
        "e1": lambda: X.run_e1(jl),
        "e2": lambda: X.run_e2(jl),
        "e3": lambda: X.run_e3(jl),
        "e4": lambda: X.run_e4(jl, vecs, words, ids),
        "e5": lambda: X.run_e5(jl, vecs),
        "e5b": lambda: X.run_e5b(jl, vecs, words, ids),
        "e6": lambda: __import__("exp6_soul").run_e6(jl),
    }
    for name, fn in steps.items():
        if which and name not in which:
            continue
        print(f"\n===== {name.upper()} =====", flush=True)
        t = time.time()
        try:
            fn()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"{name} FAILED: {e}", flush=True)
        print(f"{name} finished in {time.time()-t:.0f}s", flush=True)

    print(f"\nALL DONE in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
