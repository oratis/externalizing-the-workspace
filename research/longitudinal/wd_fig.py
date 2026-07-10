import json, glob
from collections import defaultdict
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ARMS=["full","no_examen","no_git","no_broadcast","no_soul"]
C={"full":"#1b7837","no_examen":"#2166ac","no_git":"#7b3294","no_broadcast":"#e08214","no_soul":"#b2182b"}
wd=defaultdict(list)
for l in open("runs/wd_scores.jsonl"):
    r=json.loads(l); wd[(r["cohort"],r["arm"],r["day"])].append(r["j_mlr"])
wd={k:sum(v)/len(v) for k,v in wd.items()}
B2={"honesty","curiosity","finish","warmth","commit","identity"}
b2=defaultdict(list)
for f in glob.glob("runs/**/probes.jsonl",recursive=True):
    p=f.split("/"); coh=p[1] if len(p)==4 else "main"
    for l in open(f):
        r=json.loads(l)
        if r.get("kind")=="self" and r.get("probe") in B2: b2[(coh,r["arm"],r["day"])].append(r["hit"])
b2={k:sum(v)/len(v) for k,v in b2.items()}
armwd=defaultdict(list)
for (c,a,d),v in wd.items(): armwd[a].append(v)
fig,ax=plt.subplots(1,2,figsize=(11,4.2))
means=[sum(armwd[a])/len(armwd[a]) for a in ARMS]
ax[0].bar(range(5),means,color=[C[a] for a in ARMS])
ax[0].set_xticks(range(5)); ax[0].set_xticklabels(ARMS,rotation=30,ha="right",fontsize=8)
ax[0].set_ylabel("WD (J-lens mean log10 rank)"); ax[0].set_ylim(min(means)-0.15,max(means)+0.1)
ax[0].set_title("Soul-battery workspace occupancy (lower=more loaded)",fontsize=9)
xs=[];ys=[];cs=[]
for k in wd:
    if k in b2: xs.append(wd[k]);ys.append(b2[k]);cs.append(C[k[1]])
n=len(xs);mx=sum(xs)/n;my=sum(ys)/n
num=sum((x-mx)*(y-my) for x,y in zip(xs,ys));den=(sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys))**0.5;r=num/den
ax[1].scatter(xs,ys,c=cs,s=16,alpha=.7)
ax[1].set_xlabel("WD (J-lens mean log10 rank)");ax[1].set_ylabel("B2adj (self-query consistency)")
ax[1].set_title("WD vs behavior (pred. iii): r=%.3f, n=%d"%(r,n),fontsize=9)
fig.suptitle("Real Qwen-7B deployment — mechanistic WD (5 cohorts, days 0/7/14/20)",fontsize=10)
fig.tight_layout(); fig.savefig("runs/fig_wd_qwen.png",dpi=160); print("saved runs/fig_wd_qwen.png r=%.3f n=%d"%(r,n))
