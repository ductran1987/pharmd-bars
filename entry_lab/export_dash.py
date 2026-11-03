"""Export the report's datasets as JSON row files for the dashboard: entry_lab/out/dash/*.json"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import lab
from report_data import board, reaction, counts, SPLIT, fam
from analyze import geo_null, boot_ci, OUT

D = os.path.join(OUT, "dash"); os.makedirs(D, exist_ok=True)

FAM_LABEL = {"rsi_div": "RSI divergence", "rsi_div_ext": "RSI divergence from oversold/overbought", "macd_div": "MACD-line divergence",
             "macdh_div": "MACD-histogram divergence", "rsi_hook30": "RSI hook (30/70)", "rsi_hook35": "RSI hook (35/65)",
             "mss": "Market-structure shift", "reject": "Rejection candle", "engulf": "Engulfing candle",
             "reclaim": "Close back through the level (your current rule)", "touch": "Resting limit at the level"}


COMBO_LABEL = {
    "rsi5+rsi15": "RSI divergence on 5m and 15m together",
    "macd5+macd15": "MACD-line divergence on 5m and 15m together",
    "anydiv5+anydiv15": "Any 5m divergence with any 15m divergence",
    "anydiv5+anydiv30": "Any 5m divergence with any 30m divergence",
    "rsi5+macd5 (both osc)": "RSI and MACD both diverging on 5m",
    "div15 then 5m candle": "15m divergence, then a 5m rejection or engulfing candle",
    "div30 then 5m candle": "30m divergence, then a 5m rejection or engulfing candle",
    "div15 then 5m div": "15m divergence, then a 5m divergence",
    "div30 then 5m div": "30m divergence, then a 5m divergence",
}


def label(t):
    f = fam(t)
    if t == "touch_limit": return "Limit at the level"
    if t.startswith("reclaim"): return f"Reclaim close, {t.split('_')[1]}"
    tf = [x for x in t.split("_") if x.endswith("m") and x[:-1].isdigit()]
    tf = tf[0] if tf else ""
    R = " · 1-bar confirm" if t.endswith("_R1") else (" · 2-bar confirm" if t.endswith("_R2") else "")
    base = {"rsi_div": "RSI div", "rsi_div_ext": "RSI div from extreme", "macd_div": "MACD-line div", "macdh_div": "MACD-hist div",
            "rsi_hook30": "RSI hook 30/70", "rsi_hook35": "RSI hook 35/65", "mss": "Structure shift", "reject": "Rejection candle",
            "engulf": "Engulfing candle"}[f]
    return f"{base}, {tf}{R}"


def clean(o):
    if isinstance(o, dict): return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    if isinstance(o, (float, np.floating)): return None if not np.isfinite(o) else round(float(o), 4)
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, np.bool_): return bool(o)
    return o


def dump(name, rows):
    json.dump(clean(rows), open(os.path.join(D, f"{name}.json"), "w"))
    print(name, len(rows))


if __name__ == "__main__":
    # leaderboard, both universes
    rows = []
    nulls = []
    for U, uname in (("A", "PharmD fade trades"), ("B", "All PharmD levels")):
        b, n = board(U)
        for r in b:
            rows.append(dict(key=f"{U}|{r['trig']}", uni=U, universe=uname, trigger=label(r["trig"]), family=FAM_LABEL[fam(r["trig"])],
                             tf=r["tf"], n=r["n"], win=r["win"], avgR=r["avgR"], ci_lo=r["lo"], ci_hi=r["hi"], pf=r["pf"],
                             totalR=r["totR"], maxddR=r["ddR"], fp1=r["fp1"], h1R=r["H1"], h2R=r["H2"], esR=r["ES"], nqR=r["NQ"],
                             rthR=r["RTH"], ethR=r["ETH"], n_rth=r["n_rth"], longR=r["long"], shortR=r["short"],
                             lightR=r["avgR_light"], grossR=r["avgR_gross"], stop_atr5=r["risk_atr5"], tgtR=r["tgtR"], code=r["trig"]))
        for p in ("1.0", "0.25", "0.05"):
            nulls.append(dict(key=f"{U}|p{p}", uni=U, universe=uname, p=float(p), avgR=n["conservative"][p], lightR=n["light"][p],
                              grossR=n["gross"][p], fp1=n["fp1"][p], h1R=n["H1"][p], h2R=n["H2"][p]))
    dump("leaderboard", rows); dump("random_null", nulls)

    # level reaction (first passage)
    rx = reaction(); out = []
    names = {"A": "PharmD trade levels", "B": "All PharmD levels", "P": "Random prices (control)"}
    for u, v in rx.items():
        for k in ("0.5", "1.0", "1.5", "2.0", "3.0"):
            out.append(dict(key=f"{u}|{k}", set=names[u], k=float(k), p=v[k]["p"], lo=v[k]["p"] - 1.96 * v[k]["se"],
                            hi=v[k]["p"] + 1.96 * v[k]["se"], n=v[k]["n"]))
    dump("level_reaction", out)

    # multi-timeframe combos
    out = []
    for U, uname in (("A", "PharmD fade trades"), ("B", "All PharmD levels")):
        M = pd.read_pickle(os.path.join(OUT, f"mtf_{U}.pkl")); M = M[M.exit_rule == "base"]
        for t, g in M.groupby("trig"):
            lo, hi = boot_ci(g, "R", 1000)
            out.append(dict(key=f"{U}|{t}", uni=U, universe=uname, combo=COMBO_LABEL[t], code=t, n=len(g), win=(g.R > 0).mean(), avgR=g.R.mean(),
                            ci_lo=lo, ci_hi=hi, fp1=g.fp1.mean(), h1R=g[g.date < SPLIT].R.mean(), h2R=g[g.date >= SPLIT].R.mean()))
    dump("mtf", out)

    # trigger anywhere: at a PharmD level vs away
    C = pd.read_pickle(os.path.join(OUT, "trades_C.pkl")); C["fam"] = C.trig.map(fam)
    out = []
    for (f, at), g in C.groupby(["fam", "at_level"]):
        out.append(dict(key=f"{f}|{'at' if at else 'away'}", family=FAM_LABEL[f], where="At a PharmD level" if at else "Away from levels",
                        n=len(g), avgR=g.R.mean(), fp1=g.fp1.mean()))
    dump("anywhere", out)

    # equity curves (universe A, base exit)
    T = pd.read_pickle(os.path.join(OUT, "trades_A.pkl"))
    out = []
    for t in ("reclaim_5m", "macd_div_5m_R2", "rsi_div_5m_R1", "touch_limit"):
        d = T[(T.trig == t) & (T.exit_rule == "base")].sort_values("entry_t")
        day = pd.to_datetime(d.entry_t, utc=True).dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d").values
        cum = d.R.cumsum().values
        for i, (dd, c) in enumerate(zip(day, cum)):
            out.append(dict(key=f"{t}|{i}", trigger=label(t), code=t, i=i, day=dd, cumR=c))
    dump("equity", out)

    # exit variants for key triggers
    key = ["reclaim_5m", "touch_limit", "macd_div_5m_R2", "macd_div_10m_R2", "rsi_div_5m_R1", "macdh_div_5m_R1", "rsi_div_15m_R1", "engulf_5m"]
    exn = {"base": "Base", "floor0.5": "Floor 0.5 ATR5", "floor1.5": "Floor 1.5 ATR5",
           "be1R": "Breakeven 1R", "fix2R": "Fixed 2R", "fix1.5R": "Fixed 1.5R"}
    out = []
    for U in ("A", "B"):
        T = pd.read_pickle(os.path.join(OUT, f"trades_{U}.pkl"))
        x = T[T.trig.isin(key)].groupby(["trig", "exit_rule"]).R.agg(["mean", "size"]).reset_index()
        for _, r in x.iterrows():
            out.append(dict(key=f"{U}|{r.trig}|{r.exit_rule}", uni=U, trigger=label(r.trig), code=r.trig, exit=exn[r.exit_rule],
                            exit_code=r.exit_rule, avgR=r["mean"], n=int(r["size"])))
    dump("exits", out)

    # grades (universe A, base exit, all triggers pooled + key triggers)
    T = pd.read_pickle(os.path.join(OUT, "trades_A.pkl")); b = T[T.exit_rule == "base"].copy()
    b["g"] = b.grade.replace("", "Ungraded")
    out = []
    for g, x in b.groupby("g"):
        out.append(dict(key=f"all|{g}", grade=g, trigger="All 55 triggers pooled", n=len(x), avgR=x.R.mean(), fp1=x.fp1.mean()))
    dump("grades", out)

    # example trade
    ex = json.load(open(os.path.join(OUT, "example.json")))
    bars = [dict(i=i, t=ex["t"][i], o=ex["o"][i], h=ex["h"][i], l=ex["l"][i], c=ex["c"][i], macd=ex["macd"][i]) for i in range(len(ex["t"]))]
    dump("example_bars", bars)
    dump("example_trade", [dict(key="ex", sym=ex["sym"], date=ex["date"], level=ex["zlo"], p1=ex["p1"], p2=ex["p2"], sig=ex["sig"],
                                entry_i=ex["entry"], exit_i=ex["exit"], entry=ex["e"], stop=ex["stop"], target=ex["tgt"], R=ex["R"],
                                p1_low=ex["l"][ex["p1"]], p2_low=ex["l"][ex["p2"]], p1_macd=ex["macd"][ex["p1"]], p2_macd=ex["macd"][ex["p2"]],
                                outcome=ex["how"])])

    # counts + method constants
    c = counts()
    I = pd.read_pickle(os.path.join(OUT, "setups_A.pkl"))
    dump("scope", [dict(key="scope", fade_setups=c["A"], fade_touched=c["A_touched"], touched_rth_share=c["A_touch_rth"],
                        level_setups=c["B"], level_touched=c["B_touched"], plan_days=c["days"], first_day=c["first"], last_day=c["last"],
                        split_day=c["split"], triggers=len(lab.TRIGGERS), exits=len(lab.EXITS), anywhere_signals=len(C),
                        slip_ticks=int(round(0.5 / lab.TICK)), comm=2.6, risk=lab.RISK, light_slip_ticks=1, light_comm=1.2,
                        cutoff="15:30", flat="15:55", stop_floor=lab.EXITS["base"][0], loc_depth=lab.LOC_DEPTH, loc_tol=lab.LOC_TOL,
                        min_tgtR=1.5, skip_tgtR=1.0, fp_k=1.0, null_p=0.25, div_range_lo=lab.DIV_SEP[0], div_range_hi=lab.DIV_SEP[1],
                        sessions=c["sessions"], pseudo_lo=1.5, pseudo_hi=4.0, assumed_post="7 PM ET", assumed_from="Oct 5, 2026",
                        gap_letters="January and February 2026", gap_nq="March 2026 (NQH6)")])
    print("done ->", D)
