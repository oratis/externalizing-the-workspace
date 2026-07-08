"""Behavioral analysis of the real-LISA longitudinal study (no GPU needed).

Reads runs/<arm>/probes.jsonl and the soul snapshots, and reports per-arm:
  B2adj  self-query consistency excluding the 'mood'-like evolving probe
  B2work work-turn probe consistency (Principle-2 test; gated arm has no soul)
  B3     commitment persistence (the 'commit' probe)
  B1     soul-trajectory Jaccard distance from the founding snapshot

WD (workspace occupancy) is computed separately by wd_probe.py over the
dumped prompts.jsonl, since it needs an open model.
"""

import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs")
ARMS = ["full", "no_examen", "no_git", "no_broadcast", "no_soul"]
# self-query probes counted toward adjusted B2 (identity-stable ones)
B2_PROBES = {"honesty", "curiosity", "finish", "warmth", "commit", "identity"}


def load_probes(arm):
    p = os.path.join(RUNS, arm, "probes.jsonl")
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in open(p) if l.strip()]


def soul_dir_text(d):
    """Concatenate the identity-bearing soul files into one lowercase bag."""
    if not os.path.isdir(d):
        return ""
    parts = []
    for name in ("identity.md", "purpose.md", "constitution.md", "name.md"):
        fp = os.path.join(d, name)
        if os.path.isfile(fp):
            parts.append(open(fp, errors="ignore").read())
    for sub in ("values", "opinions", "desires"):
        sd = os.path.join(d, sub)
        if os.path.isdir(sd):
            for f in os.listdir(sd):
                if f.endswith(".md"):
                    parts.append(open(os.path.join(sd, f), errors="ignore").read())
    return " ".join(parts).lower()


def tokens(t):
    return set(re.findall(r"[a-z]{3,}", t))


def jaccard_dist(a, b):
    A, B = tokens(a), tokens(b)
    if not (A or B):
        return 0.0
    return 1 - len(A & B) / len(A | B)


def main():
    founding = soul_dir_text(os.path.join(RUNS, "founding-soul"))
    print(f"{'arm':13s} {'days':>4s} {'B2adj':>6s} {'B2work':>7s} {'B3':>5s} {'B1drift':>8s}")
    summary = {}
    for arm in ARMS:
        rows = load_probes(arm)
        if not rows:
            print(f"{arm:13s}   (no data yet)")
            continue
        days = max(r["day"] for r in rows) + 1
        self_rows = [r for r in rows if r.get("kind") == "self" and r["probe"] in B2_PROBES]
        work_rows = [r for r in rows if r.get("kind") == "work"]
        commit_rows = [r for r in rows if r["probe"] == "commit"]

        def frac(rs, lo=None):
            rs = [r for r in rs if lo is None or r["day"] >= lo]
            return round(sum(r["hit"] for r in rs) / len(rs), 3) if rs else None

        lo = max(days - 5, 0)
        b2 = frac(self_rows, lo)
        b2w = frac(work_rows, lo)
        b3 = frac(commit_rows, lo)
        cur = soul_dir_text(os.path.join(RUNS, arm, "soul"))
        b1 = round(jaccard_dist(founding, cur), 3) if founding and cur else None
        summary[arm] = {"days": days, "b2adj": b2, "b2work": b2w, "b3": b3, "b1": b1}
        print(f"{arm:13s} {days:4d} {str(b2):>6s} {str(b2w):>7s} {str(b3):>5s} {str(b1):>8s}")

    json.dump(summary, open(os.path.join(RUNS, "summary.json"), "w"), indent=1)
    print(f"\nwrote {os.path.join(RUNS, 'summary.json')}")


if __name__ == "__main__":
    main()
