"""Resting-limit test: is there an edge if you place a limit order AT his level when the letter comes out?

    python limit_test.py   -> limit_test.csv (every cell x all/H1/H2), limit_test_trades.csv (best cell), limit_test_summary.md

Order: placed at the letter's publish time (or 18:00 if earlier), good until 15:55 ET the plan day. Fade setups only
(hold / LBAF / LAAF / failed reclaim) — a breakout has no natural resting-limit entry.
  long  = buy limit inside/at the zone, price must be ABOVE the limit when the order goes in (else skipped: already through)
  short = sell limit, price must be BELOW it
Entry price: zone near edge ("near": long = zone top), middle ("mid"), or far edge ("far": long = zone bottom).
Fill: "touch" = bar low <= limit (long); "through" = bar low <= limit - 1 tick (realistic queue position).
  A bar that opens beyond the limit fills at its open (price improvement).
Stop (planned when the order is placed, so size is known in advance):
  zone far edge minus 0.25 / 0.5 / 1.0 x ATR5;  entry minus 1.5 x ATR5;  entry minus 0.75 x ATR15.   Min risk 0.2 x ATR15.
Fill bar: its low/high counts against the stop; no target credit (we don't know whether the high came before the fill).
Then the same management engine as backtest_grid (BE at 1R or none; target t1 / first >= 1.0 / 1.5 / 2.0R; flat 15:55
close), 2 ticks slippage on stops (none on the limit entry or limit target), $2.60/micro, $500 risk sizing on the planned
risk.  Windows: all fills, or no fills between 00:00 and 09:30 ET.  Graded trades only for headline; days/contract map,
ATR and ref resolution exactly as backtest_grid.py (per-contract bars, publish-time start, both ES & NQ days).
"""
import glob, json, itertools
import numpy as np, pandas as pd
import backtest, plan_refs, contracts, contract_map
import backtest_grid as bg

tz = "America/New_York"; TICK = bg.TICK
ENTRIES = ["near", "mid", "far"]
STOPS = [("far-atr5", 0.25), ("far-atr5", 0.5), ("far-atr5", 1.0), ("entry-atr5", 1.5), ("entry-atr15", 0.75)]
BES = [None, 1.0]
TGTS = ["t1", "ge1.0", "ge1.5", "ge2.0"]
FILLS = ["touch", "through"]
WINDOWS = ["all", "no-overnight"]


def collect():
    """One record per resolved fade trade: session bars from publish time, zone, targets, ATR."""
    cmap = contract_map.build(); recs = []
    for f in sorted(glob.glob("plans/plan-*.json")):
        date = json.load(open(f))["date"]
        if date > bg.LAST_DATE or date not in cmap or not cmap[date]["both"]: continue
        C = {s: cmap[date][s]["contract"] for s in ("ES", "NQ")}
        p, trades = plan_refs.load_plan(f, bars_for=lambda s: contracts.load(s, C[s]), skip=set())
        post = pd.Timestamp(bg.POST_TIMES[date]["posted_et"], tz=tz) if date in bg.POST_TIMES else None
        cache = {}
        for pt in trades:
            s = pt["instrument"]
            if s not in cache:
                d5 = contracts.load(s, C[s]); a = bg.atr_for(s, C[s], date)
                if a is None: cache[s] = None; continue
                sess = backtest.session(d5, date)
                sess = sess[sess.time < pd.Timestamp(date, tz=tz).replace(hour=16)]
                if post is not None: sess = sess[sess.time >= post]
                cache[s] = (sess.reset_index(drop=True), a[0], a[1])
            if cache[s] is None: continue
            bars, a5, a15 = cache[s]
            kind = pt.get("kind") or ("break" if backtest.BREAK.search(pt["name"] + " " + str(pt.get("gate", ""))) else "fade")
            if kind != "fade" or len(bars) == 0: continue
            tag = pt.get("tag", "") or ""
            recs.append(dict(date=date, id=pt["id"], sym=s, dir=pt["dir"], tag=tag, grade=bg.grade(tag), graded=bool(bg.grade(tag)),
                             gate=sorted(pt["levels"]["gate"]), tg=bg._tg(pt), atr5=a5, atr15=a15, contract=C[s],
                             ts=bars.time.astype(str).values, hm=(bars.time.dt.hour * 60 + bars.time.dt.minute).values,
                             O=bars.Open.values.astype(float), H=bars.High.values.astype(float),
                             L=bars.Low.values.astype(float), Cl=bars.Close.values.astype(float)))
    return recs


def run(recs, entry, stop, be, tgt, fill, window):
    rows = []
    for r in recs:
        up = r["dir"] == "long"; sg = 1 if up else -1; g0, g1 = r["gate"][0], r["gate"][-1]
        near, far = (g1, g0) if up else (g0, g1)
        P = {"near": near, "mid": (g0 + g1) / 2, "far": far}[entry]
        P = round(P / TICK) * TICK
        if (r["O"][0] <= P) if up else (r["O"][0] >= P): continue            # already at/through the level when the order goes in
        k, v = stop
        if k == "far-atr5": S = far - sg * v * r["atr5"]
        elif k == "entry-atr5": S = P - sg * v * r["atr5"]
        else: S = P - sg * v * r["atr15"]
        rk = abs(P - S)
        if rk < 0.2 * r["atr15"]: rk = 0.2 * r["atr15"]; S = P - sg * rk
        thr = P - sg * (TICK if fill == "through" else 0)
        hit = np.flatnonzero(r["L"] <= thr) if up else np.flatnonzero(r["H"] >= thr)
        if not len(hit): continue
        j = hit[0]
        if window == "no-overnight" and r["hm"][j] < 570: continue          # skip fills between 00:00 and 09:30 ET
        e = min(P, r["O"][j]) if up else max(P, r["O"][j])                   # gap through the limit fills at the open
        n = int(bg.RISK // ((rk + bg.SLIP) * bg.MICRO[r["sym"]]))
        if n < 1: continue
        H, L, O = r["H"][j:].copy(), r["L"][j:].copy(), r["O"][j:].copy()
        if up: H[0] = e
        else: L[0] = e
        O[0] = e
        t = dict(dir=r["dir"], sym=r["sym"], e=e, H=H, L=L, O=O, C=r["Cl"][j:])
        tp = bg.pick_target(r["tg"], P, rk, up, tgt)
        rk_act = abs(e - S)
        pnl, how, pts = bg.simulate_one(t, S, rk_act, n, tp, be, None)
        pnl += bg.SLIP * bg.MICRO[r["sym"]] * n                               # simulate_one charges entry slippage; a limit fill has none
        rows.append(dict(date=r["date"], entry_time=r["ts"][j], id=r["id"], sym=r["sym"], dir=r["dir"], grade=r["grade"], tag=r["tag"],
                         contract=r["contract"], limit=P, fill=e, stop=S, risk_pts=rk, micros=n, target=tp, exit=how,
                         pnl=pnl, R=pnl / bg.RISK, at_floor=False))
    return pd.DataFrame(rows)


def main():
    out = []; P_ = lambda *a: (print(*a), out.append(" ".join(str(x) for x in a)))
    recs = collect()
    G = [r for r in recs if r["graded"]]; U = [r for r in recs if not r["graded"]]
    split = "2026-06-09"   # same halves as backtest_grid.py
    P_("# Resting limit order at his level\n")
    P_(f"{len(recs)} fade setups on {len({r['date'] for r in recs})} plan days ({len(G)} graded). Orders go in when the letter "
       f"is published; halves split at {split} like the grid.\n")
    rows = []; per = {}
    for entry, stop, be, tgt, fill, win in itertools.product(ENTRIES, STOPS, BES, TGTS, FILLS, WINDOWS):
        d = run(G, entry, stop, be, tgt, fill, win)
        name = f"{entry} | stop {stop[0]} {stop[1]} | BE {be or 'none'} | {tgt} | {fill} | {win}"
        per[name] = d
        for lab, sub in (("all", d), ("H1", d[d.date <= split] if len(d) else d), ("H2", d[d.date > split] if len(d) else d)):
            m = bg.metrics(sub) if len(sub) else dict(n=0)
            m.update(cell=name, period=lab, entry=entry, stop=f"{stop[0]} {stop[1]}", be=be, tgt=tgt, fill=fill, window=win)
            rows.append(m)
    grid = pd.DataFrame(rows); grid.to_csv("limit_test.csv", index=False)
    al = grid[grid.period == "all"].set_index("cell"); h2 = grid[grid.period == "H2"].set_index("cell")
    h1 = grid[(grid.period == "H1") & (grid.n >= 30)].sort_values("avgR_cap3", ascending=False)
    pos = al[(al.n >= 60)]
    P_(f"**{int((pos.avgR_cap3 > 0).sum())} of {len(pos)} cells (with >= 60 trades) are profitable over the whole sample** "
       f"({int(((pos.avgR_cap3 > 0) & (pos.index.str.contains('through'))).sum())} of {int(pos.index.str.contains('through').sum())} with the realistic 'through' fill).\n")
    P_("## Top 10 cells chosen on H1 (capped avg R), with out-of-sample H2\n")
    tr = []
    for c in h1.cell.head(10):
        tr.append(bg.mrow(c + " — H1", h1.set_index("cell").loc[c].to_dict())); tr.append(bg.mrow("   ↳ H2", h2.loc[c].to_dict()))
    P_(bg.md_table(tr, bg.COLS))
    P_("## One reference cell per entry level (stop far edge − 0.5×ATR5, BE 1R, first target ≥ 1.5R, 'through' fill)\n")
    ref = []
    for entry in ENTRIES:
        for win in WINDOWS:
            c = f"{entry} | stop far-atr5 0.5 | BE 1.0 | ge1.5 | through | {win}"
            ref.append(bg.mrow(c + " — all", al.loc[c].to_dict()))
            ref.append(bg.mrow("   ↳ H1", grid[(grid.cell == c) & (grid.period == "H1")].iloc[0].to_dict()))
            ref.append(bg.mrow("   ↳ H2", h2.loc[c].to_dict()))
    P_(bg.md_table(ref, bg.COLS))
    best = h1.cell.iloc[0]
    bd = per[best]; bd.to_csv("limit_test_trades.csv", index=False)
    P_(f"## Best H1 cell by session and grade (all data): {best}\n")
    bd["hour"] = bd.entry_time.str.slice(11, 13).astype(int)
    seg = pd.cut(bd.hour, [-1, 8, 15, 23], labels=["00-09", "09-16", "18-24"])
    P_(bg.md_table([bg.mrow(f"session {k}", bg.metrics(bd[seg == k])) for k in ["18-24", "00-09", "09-16"]] +
                   [bg.mrow(f"grade {g}", bg.metrics(bd[bd.grade == g])) for g in "ABC"] +
                   [bg.mrow(s, bg.metrics(bd[bd.sym == s])) for s in ("ES", "NQ")], bg.COLS))
    spec = dict(zip(["entry", "stop", "be", "tgt", "fill", "win"], best.split(" | ")))
    st = spec["stop"].replace("stop ", "").split(" "); stop = (st[0], float(st[1]))
    be = None if spec["be"] == "BE none" else 1.0
    ung = run(U, spec["entry"], stop, be, spec["tgt"], spec["fill"], spec["win"])
    P_(f"Same cell on ungraded ideas: {bg.fmt(bg.metrics(ung))}\n")
    by_m = bd.assign(month=pd.to_datetime(bd.date).dt.to_period("M")).groupby("month").pnl.agg(["size", "sum"]).round(0)
    P_("Monthly P&L of that cell:\n\n" + by_m.to_string() + "\n")
    open("limit_test_summary.md", "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
