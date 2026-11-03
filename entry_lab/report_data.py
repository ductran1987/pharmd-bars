"""Collect everything the report needs into entry_lab/out/report.json."""
import os, sys, json, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import lab
from analyze import boot_ci, geo_null, OUT

SPLIT = "2026-05-20"
COSTS = {"conservative": "", "light": "light", "gross": "gross"}


def fam(t):
    for f in ("rsi_div_ext", "rsi_div", "macdh_div", "macd_div", "rsi_hook30", "rsi_hook35", "mss", "reject", "engulf", "reclaim", "touch"):
        if t.startswith(f): return f
    return t


def tf_of(t):
    for tf in ("60m", "30m", "15m", "10m", "5m"):
        if f"_{tf}" in t: return tf
    return "5m" if t == "touch_limit" else ""


def board(U, ex="base"):
    rows = []
    Ts = {c: pd.read_pickle(os.path.join(OUT, d, f"trades_{U}.pkl") if d else os.path.join(OUT, f"trades_{U}.pkl")) for c, d in COSTS.items()}
    for trig, d in Ts["conservative"][Ts["conservative"].exit_rule == ex].groupby("trig"):
        d = d.sort_values("entry_t")
        lo, hi = boot_ci(d, "R", 1000)
        w = d.pnl[d.pnl > 0].sum(); l = -d.pnl[d.pnl < 0].sum()
        cum = d.R.cumsum(); dd = float((cum - np.maximum(cum.cummax(), 0)).min())
        r = dict(trig=trig, fam=fam(trig), tf=tf_of(trig), n=len(d), win=float((d.R > 0).mean()), avgR=float(d.R.mean()),
                 lo=float(lo), hi=float(hi), pf=float(w / l) if l > 0 else None, totR=float(d.R.sum()), ddR=dd,
                 fp1=float(d.fp1.mean()), H1=float(d[d.date < SPLIT].R.mean()), H2=float(d[d.date >= SPLIT].R.mean()),
                 ES=float(d[d.sym == "ES"].R.mean()), NQ=float(d[d.sym == "NQ"].R.mean()),
                 RTH=float(d[d.rth].R.mean()) if d.rth.any() else None, ETH=float(d[~d.rth].R.mean()) if (~d.rth).any() else None,
                 n_rth=int(d.rth.sum()), long=float(d[d.dir == "long"].R.mean()), short=float(d[d.dir == "short"].R.mean()),
                 risk_atr5=float(d.risk_atr5.median()), tgtR=float(d.tgtR.median()))
        for c in ("light", "gross"):
            x = Ts[c][(Ts[c].exit_rule == ex) & (Ts[c].trig == trig)]
            r[f"avgR_{c}"] = float(x.R.mean()) if len(x) else None
        rows.append(r)
    nulls = {}
    for c, dd_ in COSTS.items():
        N = pd.read_pickle(os.path.join(OUT, dd_, f"null_{U}.pkl") if dd_ else os.path.join(OUT, f"null_{U}.pkl"))
        nulls[c] = {str(p): geo_null(N, ex, p)[0] for p in (1.0, 0.25, 0.05)}
        if c == "conservative":
            nulls["fp1"] = {str(p): geo_null(N, ex, p)[1] for p in (1.0, 0.25, 0.05)}
            nulls["H1"] = {str(p): geo_null(N, ex, p, SPLIT, 1)[0] for p in (1.0, 0.25, 0.05)}
            nulls["H2"] = {str(p): geo_null(N, ex, p, SPLIT, 2)[0] for p in (1.0, 0.25, 0.05)}
    return rows, nulls


def exits_table(U, trigs):
    T = pd.read_pickle(os.path.join(OUT, f"trades_{U}.pkl"))
    x = T[T.trig.isin(trigs)].pivot_table(index="trig", columns="exit_rule", values="R", aggfunc="mean")
    return {t: {k: float(v) for k, v in x.loc[t].items()} for t in x.index}


def equity(U, trigs):
    T = pd.read_pickle(os.path.join(OUT, f"trades_{U}.pkl"))
    out = {}
    for t in trigs:
        d = T[(T.trig == t) & (T.exit_rule == "base")].sort_values("entry_t")
        dates = pd.to_datetime(d.entry_t, utc=True).dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
        out[t] = dict(d=list(dates), cum=[round(float(v), 3) for v in d.R.cumsum()])
    return out


def reaction():
    R = pd.read_pickle(os.path.join(OUT, "reaction.pkl"))
    out = {}
    for u, g in R.groupby("uni"):
        out[u] = dict(n=len(g))
        for k in (0.5, 1.0, 1.5, 2.0, 3.0):
            v = g[f"p{k}"].dropna(); p = float(v.mean()); se = float(np.sqrt(p * (1 - p) / len(v)))
            out[u][str(k)] = dict(p=p, se=se, n=int(len(v)))
        for c in ("rth", "dir", "sym"):
            for kk, v in g.groupby(c):
                out[u][f"{c}={kk}"] = dict(n=len(v), p1=float(v["p1.0"].mean()))
    return out


def control_C():
    C = pd.read_pickle(os.path.join(OUT, "trades_C.pkl"))
    C["fam"] = C.trig.map(fam)
    g = C.groupby(["fam", "at_level"]).agg(n=("R", "size"), avgR=("R", "mean"), fp1=("fp1", "mean")).reset_index()
    return dict(by_fam=g.to_dict("records"), share_at=float(C.at_level.mean()), n=len(C))


def mtf():
    out = {}
    for U in ("A", "B"):
        D = pd.read_pickle(os.path.join(OUT, f"mtf_{U}.pkl")); d = D[D.exit_rule == "base"]
        rows = []
        for t, g in d.groupby("trig"):
            lo, hi = boot_ci(g, "R", 600)
            rows.append(dict(trig=t, n=len(g), win=float((g.R > 0).mean()), avgR=float(g.R.mean()), lo=float(lo), hi=float(hi),
                             fp1=float(g.fp1.mean()), H1=float(g[g.date < SPLIT].R.mean()), H2=float(g[g.date >= SPLIT].R.mean())))
        out[U] = rows
    return out


def counts():
    A, B, days = pickle.load(open(os.path.join(OUT, "setups.pkl"), "rb"))
    IA = pd.read_pickle(os.path.join(OUT, "setups_A.pkl")); IB = pd.read_pickle(os.path.join(OUT, "setups_B.pkl"))
    d = sorted({s["date"] for s in A})
    return dict(A=len(A), A_touched=int(IA.touched.sum()), A_touch_rth=float(IA[IA.touched].arm_rth.mean()),
                B=len(B), B_touched=int(IB.touched.sum()), days=len({(x["date"]) for x in days}), sessions=len(days),
                first=d[0], last=d[-1], split=SPLIT,
                graded=int(sum(1 for s in A if s["grade"])), es_days=sum(1 for x in days if x["sym"] == "ES"),
                nq_days=sum(1 for x in days if x["sym"] == "NQ"))


if __name__ == "__main__":
    out = dict(counts=counts(), reaction=reaction(), control=control_C(), mtf=mtf())
    for U in ("A", "B"):
        rows, nulls = board(U); out[f"board_{U}"] = rows; out[f"null_{U}"] = nulls
    key = ["reclaim_5m", "touch_limit", "macd_div_5m_R2", "macd_div_10m_R2", "rsi_div_5m_R1", "macdh_div_5m_R2", "rsi_div_15m_R1", "engulf_5m"]
    out["exits_A"] = exits_table("A", key); out["exits_B"] = exits_table("B", key)
    out["equity_A"] = equity("A", ["reclaim_5m", "macd_div_5m_R2", "rsi_div_5m_R1", "macdh_div_5m_R2", "touch_limit"])
    def clean(o):
        if isinstance(o, dict): return {str(k): clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)): return [clean(v) for v in o]
        if isinstance(o, (float, np.floating)): return None if not np.isfinite(o) else round(float(o), 4)
        if isinstance(o, (np.integer,)): return int(o)
        if isinstance(o, (np.bool_,)): return bool(o)
        return o
    json.dump(clean(out), open(os.path.join(OUT, "report.json"), "w"))
    print("wrote report.json", {k: (len(v) if hasattr(v, "__len__") else v) for k, v in out.items()})
