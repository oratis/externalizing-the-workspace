"""Workspace-drift probe over pilot contexts (runs after pilot.py, same model).

For every stored probe context, measures occupancy (mean log10 rank) of the
founding identity battery in J-lens and logit-lens readouts at a late-middle
layer, at the assistant-generation-start position. Output: wd_scores.jsonl.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "workspace-repro"))

import torch                                   # noqa: E402
from jlens import JLens                        # noqa: E402
from concepts import single_token_id           # noqa: E402

OUT = os.environ.get("PILOT_OUT", "pilot_results")
BATTERY = ["honest", "curious", "careful", "gentle", "privacy",
           "music", "garden", "calm"]


def mean_log_rank(jl, scores, ids):
    ranks = [jl.token_rank(scores, t) for t in ids]
    return float(torch.tensor([float(r) for r in ranks]).log10().mean())


def main():
    jl = JLens()
    layer = 23 if jl.n_layers == 28 else round(0.82 * jl.n_layers)
    ids = [t for t in (single_token_id(jl.tok, w) for w in BATTERY)
           if t is not None]
    print(f"battery {len(ids)}/{len(BATTERY)} single-token; layer {layer}",
          flush=True)
    rows = []
    files = [f for f in os.listdir(OUT) if f.endswith("_wd_contexts.jsonl")]
    for fn in sorted(files):
        for line in open(os.path.join(OUT, fn)):
            r = json.loads(line)
            enc = jl.encode([r["context"]], max_len=2048)
            jl.forward_capture(enc, grad=False)
            h = jl._captured[layer][0, -1, :].detach().float().cpu()
            ll = jl.logit_lens(h)
            jr = jl.fd_readout(layer, h, eps_frac=0.1, n_prompts=36)
            rows.append({"arm": r["arm"], "day": r["day"], "probe": r["probe"],
                         "ll_mlr": mean_log_rank(jl, ll, ids),
                         "j_mlr": mean_log_rank(jl, jr, ids)})
            if len(rows) % 20 == 0:
                print(f"{len(rows)} contexts probed", flush=True)
    with open(os.path.join(OUT, "wd_scores.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"WD DONE: {len(rows)} rows", flush=True)


if __name__ == "__main__":
    main()
