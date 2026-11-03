"""Paired test: does a trigger's TIMING beat a random entry on the SAME setup?
For every setup, E_null = expected R of the real-time random entry (enter with prob p=0.25 at each 5m bar at the
level, first success).  diff = trigger R - E_null of that setup.  Mean diff with a day-clustered bootstrap CI."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from analyze import boot_ci, OUT
P = 0.25


def setup_null(N, ex):
    nb = N[N.exit_rule == ex].sort_values(["date", "sym", "id", "entry_t"]).copy()
    k = nb.groupby(["date", "sym", "id"]).cumcount().values
    nb["w"] = P * (1 - P) ** k; nb["wR"] = nb.w * nb.R
    g = nb.groupby(["date", "sym", "id"]).agg(w=("w", "sum"), wR=("wR", "sum"))
    return (g.wR / g.w).rename("Enull")


def family(t):
    for f in ("rsi_div_ext", "rsi_div", "macdh_div", "macd_div", "rsi_hook30", "rsi_hook35", "mss", "reject", "engulf", "reclaim", "touch"):
        if t.startswith(f): return f
    return t


def run(cost="", ex="base"):
    base = os.path.join(OUT, cost) if cost else OUT
    out = []
    for U in ("A", "B"):
        T = pd.read_pickle(os.path.join(base, f"trades_{U}.pkl")); N = pd.read_pickle(os.path.join(base, f"null_{U}.pkl"))
        En = setup_null(N, ex)
        t = T[T.exit_rule == ex].join(En, on=["date", "sym", "id"])
        t = t[t.Enull.notna()].copy(); t["diff"] = t.R - t.Enull
        for trig, d in t.groupby("trig"):
            lo, hi = boot_ci(d, "diff", 600)
            out.append(dict(uni=U, trig=trig, fam=family(trig), n=len(d), R=d.R.mean(), Enull=d.Enull.mean(), diff=d["diff"].mean(), lo=lo, hi=hi))
    return pd.DataFrame(out)


if __name__ == "__main__":
    pd.set_option("display.width", 200); pd.set_option("display.max_rows", 200)
    D = run()
    D.to_csv(os.path.join(OUT, "paired_conservative.csv"), index=False)
    for U in ("A", "B"):
        x = D[D.uni == U].sort_values("diff", ascending=False)
        print(f"== {U}: trigger R minus same-setup random-entry R (p={P}), base exit, conservative costs")
        print(x.round(3).head(12).to_string(index=False))
        print("  significant (CI excludes 0):", x[(x.lo > 0) | (x.hi < 0)][["trig", "diff", "lo", "hi"]].round(3).to_dict("records"))
        fam = x.groupby("fam").apply(lambda g: pd.Series(dict(variants=len(g), trades=g.n.sum(), wdiff=(g["diff"] * g.n).sum() / g.n.sum(),
                                                               pos=(g["diff"] > 0).mean())), include_groups=False)
        print(fam.round(3).sort_values("wdiff", ascending=False).to_string())
