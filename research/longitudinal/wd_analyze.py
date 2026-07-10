import json, glob
from collections import defaultdict
wd=defaultdict(list)
for l in open("runs/wd_scores.jsonl"):
    r=json.loads(l); wd[(r["cohort"],r["arm"],r["day"])].append(r["j_mlr"])
wd={k:sum(v)/len(v) for k,v in wd.items()}
B2={"honesty","curiosity","finish","warmth","commit","identity"}
b2=defaultdict(list)
for f in glob.glob("runs/**/probes.jsonl",recursive=True):
    p=f.split("/"); cohort=p[1] if len(p)==4 else "main"
    for l in open(f):
        r=json.loads(l)
        if r.get("kind")=="self" and r.get("probe") in B2:
            b2[(cohort,r["arm"],r["day"])].append(r["hit"])
b2={k:sum(v)/len(v) for k,v in b2.items()}
armwd=defaultdict(list)
for (c,a,d),v in wd.items(): armwd[a].append(v)
print("=== WD occupancy per arm (J-lens mean log10 rank; LOWER = soul more loaded) ===")
for a in ["full","no_examen","no_git","no_broadcast","no_soul"]:
    if armwd[a]: print("  %-13s j_mlr=%.3f  (n=%d)"%(a,sum(armwd[a])/len(armwd[a]),len(armwd[a])))
xs=[];ys=[]
for k in wd:
    if k in b2: xs.append(wd[k]); ys.append(b2[k])
n=len(xs); r=0
if n>3:
    mx=sum(xs)/n; my=sum(ys)/n
    num=sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    den=(sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys))**0.5
    r=num/den if den else 0
print("=== r(WD, B2adj) = %.3f   (n=%d arm-cohort-days) ===  [pilot: -0.75]"%(r,n))
json.dump({"arm_wd":{a:round(sum(v)/len(v),3) for a,v in armwd.items() if v},"r_wd_b2":round(r,3),"n":n}, open("runs/wd_summary.json","w"),indent=1)
