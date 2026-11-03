"""Summaries for the entry-model lab: per trigger x exit, with halves, slices, day-clustered bootstrap CIs and the
real-time random-entry null.

python entry_lab/analyze.py -> entry_lab/out/summary_<cost>.csv (+ printed tables)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "out")
RNG = np.random.default_rng(11)


def split_date(I):
    d = pd.to_datetime(I[I.touched].date)
    return str(d.median().date())


def boot_ci(df, col="R", n=1000):
    """95% CI of the mean, resampling whole days (trades on the same day are not independent)."""
    if len(df) < 10: return (np.nan, np.nan)
    g = df.groupby("date")[col].agg(["sum", "size"])
    s, c = g["sum"].values, g["size"].values
    idx = RNG.integers(0, len(g), size=(n, len(g)))
    means = s[idx].sum(1) / c[idx].sum(1)
    return tuple(np.percentile(means, [2.5, 97.5]))


def metrics(d, split):
    if len(d) == 0: return dict(n=0)
    d = d.sort_values("entry_t")
    cum = d.pnl.cumsum(); dd = (cum - np.maximum(cum.cummax(), 0)).min()
    w = d.pnl[d.pnl > 0].sum(); l = -d.pnl[d.pnl < 0].sum()
    h1, h2 = d[d.date < split], d[d.date >= split]
    lo, hi = boot_ci(d)
    return dict(n=len(d), win=(d.R > 0).mean(), avgR=d.R.mean(), ci_lo=lo, ci_hi=hi, medR=d.R.median(),
                pf=w / l if l > 0 else np.inf, total=d.pnl.sum(), maxdd=min(0, dd), fp1=d.fp1.mean(), fwd60=d.fwd60.mean(),
                R_H1=h1.R.mean() if len(h1) else np.nan, R_H2=h2.R.mean() if len(h2) else np.nan, n_H1=len(h1), n_H2=len(h2),
                R_ES=d[d.sym == "ES"].R.mean(), R_NQ=d[d.sym == "NQ"].R.mean(),
                R_RTH=d[d.rth].R.mean(), R_ETH=d[~d.rth].R.mean(), n_RTH=int(d.rth.sum()),
                R_long=d[d.dir == "long"].R.mean(), R_short=d[d.dir == "short"].R.mean(),
                risk_atr5=d.risk_atr5.median(), tgtR=d.tgtR.median())


def geo_null(N, exit_rule, p, split=None, half=None):
    """Expected avg R of a real-time random entry: at each 5m bar at the level, enter with probability p
    (first success taken).  Exact expectation over the candidate pool, no simulation needed."""
    nb = N[N.exit_rule == exit_rule]
    if half == 1: nb = nb[nb.date < split]
    elif half == 2: nb = nb[nb.date >= split]
    nb = nb.sort_values(["date", "sym", "id", "entry_t"])
    k = nb.groupby(["date", "sym", "id"]).cumcount().values
    w = p * (1 - p) ** k
    return float((w * nb.R.values).sum() / w.sum()), float((w * np.nan_to_num(nb.fp1.values, nan=0.5)).sum() / w.sum())


def summarize(cost="", exits=("base", "fix2R", "be1R", "floor1.5", "floor0.5", "fix1.5R")):
    base = os.path.join(OUT, cost) if cost else OUT
    rows = []
    I = pd.read_pickle(os.path.join(OUT, "setups_A.pkl")); split = split_date(I)
    for U in ("A", "B"):
        T = pd.read_pickle(os.path.join(base, f"trades_{U}.pkl"))
        N = pd.read_pickle(os.path.join(base, f"null_{U}.pkl"))
        for ex in exits:
            Te = T[T.exit_rule == ex]
            for trig, d in Te.groupby("trig"):
                rows.append(dict(uni=U, exit=ex, trig=trig, **metrics(d, split)))
            for p in (1.0, 0.25, 0.05):
                r, f = geo_null(N, ex, p); r1, _ = geo_null(N, ex, p, split, 1); r2, _ = geo_null(N, ex, p, split, 2)
                rows.append(dict(uni=U, exit=ex, trig=f"NULL_random_p{p}", avgR=r, fp1=f, R_H1=r1, R_H2=r2))
    S = pd.DataFrame(rows)
    S.to_csv(os.path.join(OUT, f"summary_{cost or 'conservative'}.csv"), index=False)
    return S, split


if __name__ == "__main__":
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300); pd.set_option("display.max_columns", 40)
    for cost in ("", "light", "gross"):
        S, split = summarize(cost)
        print(f"\n=== costs: {cost or 'conservative (2+2 ticks, $2.60/RT)'} | H1 < {split} <= H2 ===")
        for U in ("A", "B"):
            x = S[(S.uni == U) & (S.exit == "base")].sort_values("avgR", ascending=False)
            cols = ["trig", "n", "win", "avgR", "ci_lo", "ci_hi", "pf", "fp1", "R_H1", "R_H2", "R_ES", "R_NQ", "R_RTH", "R_ETH", "R_long", "R_short"]
            print(f"-- universe {U}, exit base (top 15 + nulls)")
            print(pd.concat([x[~x.trig.str.startswith("NULL")].head(15), x[x.trig.str.startswith("NULL")]])[cols].round(3).to_string(index=False))


def edges(U, cost=""):
    """Per trigger: avg R, timing-matched benchmark avg R (nullmatch.py), edge = difference, 95% CI of the edge
    (days resampled for the trigger; the benchmark mean is taken as fixed: it averages many draws)."""
    base = os.path.join(OUT, cost) if cost else OUT
    T = pd.read_pickle(os.path.join(base, f"trades_{U}.pkl")); T = T[T.exit_rule == "base"]
    N = pd.read_pickle(os.path.join(OUT, f"nullmatch_{U}.pkl"))
    nm = N.groupby("trig").agg(null_R=("R", "mean"), null_fp1=("fp1", "mean"), null_n=("R", "size"))
    out = []
    for trig, d in T.groupby("trig"):
        if trig not in nm.index: continue
        m = nm.loc[trig]; lo, hi = boot_ci(d, "R", 1000)
        out.append(dict(uni=U, trig=trig, n=len(d), avgR=d.R.mean(), ci_lo=lo, ci_hi=hi, null_R=m.null_R,
                        edge=d.R.mean() - m.null_R, edge_lo=lo - m.null_R, edge_hi=hi - m.null_R,
                        fp1=d.fp1.mean(), null_fp1=m.null_fp1, null_n=int(m.null_n)))
    return pd.DataFrame(out)
