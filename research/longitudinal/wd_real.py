"""WD (workspace drift) over the real deployment's prompt contexts, open Qwen-7B.
Reads runs/**/prompts.jsonl, and for self-query probe contexts on sampled days
computes J-lens + logit-lens mean-log10-rank of the LISA identity battery at the
late-middle layer (assistant-start position of the truncated context).
Output: runs/wd_scores.jsonl. Requires WREPRO_MODEL=Qwen/Qwen2.5-7B-Instruct.
"""
import json, os, sys, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workspace-repro"))
import torch
from jlens import JLens
from concepts import single_token_id
BATTERY = ["honest","curious","careful","warm","truth","honesty","curiosity","integrity","friction","finish"]
PROBE_DAYS = {0,7,14,20}
def mlr(jl, scores, ids):
    ranks=[jl.token_rank(scores,t) for t in ids]
    return float(torch.tensor([float(r) for r in ranks]).log10().mean())
def main():
    jl=JLens(); layer=round(0.82*jl.n_layers)
    ids=[t for t in (single_token_id(jl.tok,w) for w in BATTERY) if t is not None]
    print(f"battery {len(ids)}/{len(BATTERY)} single-token; {jl.n_layers}L layer={layer}", flush=True)
    rows=[]
    for f in sorted(glob.glob("runs/**/prompts.jsonl", recursive=True)):
        p=f.split("/"); cohort=p[1] if len(p)==4 else "main"; arm=p[-2]
        for line in open(f):
            try: r=json.loads(line)
            except: continue
            if r.get("kind")!="self" or r.get("day") not in PROBE_DAYS: continue
            ctx=r.get("text","");
            if not ctx: continue
            enc=jl.encode([ctx], max_len=2048); jl.forward_capture(enc, grad=False)
            h=jl._captured[layer][0,-1,:].detach().float().cpu()
            ll=jl.logit_lens(h); jr=jl.fd_readout(layer,h,eps_frac=0.1,n_prompts=16)
            rows.append({"cohort":cohort,"arm":arm,"day":r.get("day"),"probe":r.get("probe"),
                         "ll_mlr":mlr(jl,ll,ids),"j_mlr":mlr(jl,jr,ids)})
            if len(rows)%20==0: print(f"{len(rows)} contexts probed", flush=True)
    with open("runs/wd_scores.jsonl","w") as o:
        for r in rows: o.write(json.dumps(r)+"\n")
    print(f"WD DONE {len(rows)} rows", flush=True)
if __name__=="__main__": main()
