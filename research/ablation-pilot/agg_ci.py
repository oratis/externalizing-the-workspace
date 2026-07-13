import json, glob, collections, sys, random
random.seed(42)
d = sys.argv[1]
cell=collections.defaultdict(lambda: collections.defaultdict(list))  # (arm,metric)->seed->hits
for f in sorted(glob.glob(d+"/*_probes.jsonl")):
    for line in open(f):
        try: r=json.loads(line)
        except: continue
        if r.get("day",0)<15: continue  # final-5-day window (days 15-19)
        a=r["arm"]; s=r["seed"]
        if r["probe"]=="commit" and r["kind"]=="self": cell[(a,"B3")][s].append(r["hit"])
        if r["kind"]=="work": cell[(a,"B2work")][s].append(r["hit"])
        if r["kind"]=="self" and r["probe"] in {"privacy","pace","tone","commit","identity"}: cell[(a,"B2adj")][s].append(r["hit"])
def ci(a,k):
    per_seed=cell.get((a,k),{})
    means=[sum(v)/len(v) for v in per_seed.values() if v]
    if not means: return None
    n=len(means); mu=sum(means)/n
    boot=sorted(sum(means[random.randrange(n)] for _ in range(n))/n for _ in range(5000))
    return mu, boot[int(0.025*len(boot))], boot[int(0.975*len(boot))], n
def fmt(a,k):
    c=ci(a,k)
    return "%.2f[%.2f,%.2f]"%(c[0],c[1],c[2]) if c else "      -       "
print("dir:",d)
print("%-14s%17s%17s%17s"%("arm","B2adj","B2work","B3"))
for a in ["full","no_examen","no_git","no_broadcast","no_soul","memory","memory_seeded"]:
    if (a,"B2work") in cell or (a,"B3") in cell:
        print("%-14s%17s%17s%17s"%(a,fmt(a,"B2adj"),fmt(a,"B2work"),fmt(a,"B3")))
