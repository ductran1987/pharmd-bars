"""P&L simulation of the management rules over the plan files (graded trades only).
Baseline: entry on the first 5m close back through the zone edge (backtest.run_trade), stop = 1 tick past the sweep
extreme floored at K_FLOOR x ATR5 from the edge (min 0.2 x ATR15), breakeven at +BE_R, exit at the first of his targets
that is >= MIN_TARGET_R away (last target if none), flat at the 16:00 close, $RISK in micros, SLIP on entry and stop.
Usage: python backtest_pnl.py [--k 1.5] [--be 1.0] [--min-target-r 1.5] [--no-be]
"""
import argparse, glob, json
import numpy as np, pandas as pd
import charts, stops, backtest, plan_refs

RISK = 500.0; MICRO = {"ES": 5.0, "NQ": 2.0}; SLIP = 0.5; COMM = 2.6


def build_setups(k_floor=1.5):
    bars5 = {s: charts.load(s) for s in ("ES", "NQ")}; cA = {}; cB = {}; setups = []
    for f in sorted(glob.glob("plans/plan-*.json")):
        p, trades = plan_refs.load_plan(f)
        for pt in trades:
            if not pt.get("tag"): continue
            s = pt["instrument"]; key = (s, p["date"])
            if key not in cA: cA[key] = stops.analyze(s, p["date"]); cB[key] = backtest.session(bars5[s], p["date"])
            A = cA[key]; bars = cB[key]; r = backtest.run_trade(bars, pt)
            if not r["triggered"]: continue
            d = pt["dir"]; sg = -1 if d == "long" else 1; e = r["entry"]
            stp = (min if d == "long" else max)(r["far"] + sg * 0.25, e + sg * k_floor * A["atr5"]); rk = abs(e - stp)
            if rk < 0.2 * A["atr15"]: rk = 0.2 * A["atr15"]; stp = e + sg * rk
            tg = [(min(x) if d == "long" else max(x)) if isinstance(x, list) else x for x in pt["levels"]["tgt"]]
            i0 = bars.index[bars.time == pd.Timestamp(r["entry_time"])][0]; after = bars.loc[i0 + 1:]
            setups.append(dict(sym=s, date=p["date"], id=pt["id"], tag=pt["tag"], dir=d, e=e, stop=stp, rk=rk, tg=tg,
                               sweep_depth_atr5=abs(e - r["far"]) / A["atr5"], H=after.High.values, L=after.Low.values,
                               C=after.Close.values, n=int(RISK // ((rk + SLIP) * MICRO[s]))))
    return setups


def simulate(setups, be_R=1.0, min_target_r=1.5, choose=None):
    rows = []
    for t in setups:
        up = t["dir"] == "long"; sg = 1 if up else -1; e = t["e"]; stp = t["stop"]; rk = t["rk"]; tg = t["tg"]
        tgt = choose(tg, e, rk) if choose else next((x for x in tg if abs(x - e) / rk >= min_target_r), tg[-1])
        moved = False; res = None; how = None
        for H, L, C in zip(t["H"], t["L"], t["C"]):
            fav = H if up else L; adv = L if up else H
            if (adv <= stp if up else adv >= stp): res = (stp - e) * sg - SLIP; how = "be" if moved else "stop"; break
            if (fav >= tgt if up else fav <= tgt): res = abs(tgt - e) - SLIP; how = "target"; break
            if be_R is not None and not moved and (fav >= e + sg * be_R * rk if up else fav <= e + sg * be_R * rk):
                moved = True
                if (e + sg * 0.25) * sg > stp * sg: stp = e + sg * 0.25
        if res is None: res = (t["C"][-1] - e) * sg - SLIP; how = "close"
        pnl = res * MICRO[t["sym"]] * t["n"] - COMM * t["n"]
        rows.append(dict(date=t["date"], id=t["id"], sym=t["sym"], tag=t["tag"], dir=t["dir"], entry=e, stop=t["stop"], risk_pts=rk,
                         target=tgt, R_to_target=abs(tgt - e) / rk, micros=t["n"], exit=how, pts=res, pnl=pnl, R=pnl / RISK))
    return pd.DataFrame(rows)


def summary(d, label=""):
    d = d.copy(); d["cum"] = d.pnl.cumsum()
    wk = d.groupby(pd.to_datetime(d.date).dt.to_period("W")).pnl.sum()
    return dict(label=label, n=len(d), win=(d.pnl > 0).mean(), targets=(d.exit == "target").sum(), stops=(d.exit == "stop").sum(),
                be=(d.exit == "be").sum(), total=d.pnl.sum(), avg=d.pnl.mean(), std=d.pnl.std(), worst=d.pnl.min(),
                max_dd=(d.cum - d.cum.cummax()).min(), worst_week=wk.min(),
                pf=d[d.pnl > 0].pnl.sum() / max(1e-9, -d[d.pnl < 0].pnl.sum()),
                es=d[d.sym == "ES"].pnl.sum(), nq=d[d.sym == "NQ"].pnl.sum())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=float, default=1.5); ap.add_argument("--be", type=float, default=1.0)
    ap.add_argument("--min-target-r", type=float, default=1.5); ap.add_argument("--no-be", action="store_true")
    a = ap.parse_args()
    S = build_setups(a.k)
    d = simulate(S, None if a.no_be else a.be, a.min_target_r)
    d.to_csv("backtest_pnl.csv", index=False)
    pd.set_option("display.width", 220)
    s_ = summary(d, f"k={a.k} be={'none' if a.no_be else a.be} minTargetR={a.min_target_r}"); print(s_.pop("label")); print(pd.Series(s_).round(2).to_string())
    print("\nby week:"); print(d.groupby(pd.to_datetime(d.date).dt.to_period("W")).agg(trades=("pnl", "size"), pnl=("pnl", "sum"), win=("pnl", lambda x: (x > 0).mean())).round(2).to_string())
    print("\nvariants:")
    rows = [summary(simulate(S, None, 1.0, lambda tg, e, rk: tg[0]), "t1, no BE"),
            summary(simulate(S, 1.0, 1.0, lambda tg, e, rk: tg[0] if (abs(tg[0] - e) / rk >= 1 or len(tg) < 2) else tg[1]), "t1 or t2 if t1<1R, BE 1R"),
            summary(simulate(S, None, 1.5), "first tgt >=1.5R, no BE"),
            summary(simulate(S, 1.0, 1.5), "first tgt >=1.5R, BE 1R"),
            summary(simulate(S, 1.0, 2.0), "first tgt >=2R, BE 1R")]
    print(pd.DataFrame(rows).round(2).to_string(index=False))
