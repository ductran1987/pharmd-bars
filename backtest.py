"""MAE calibration over the plan files: did the gate trigger, how far past the invalidation level did price go
before the first target, and which stop rules would have survived.
Usage: python backtest.py [plans/plan-*.json ...]   (default: all plans)
Session = ETH 18:00 ET the evening before the plan date -> 16:00 ET on the plan date.
Entry = first bar that trades into the gate: long at the gate top, short at the gate bottom (same assumption as stops.py).
Level = the gate's far edge (long: gate bottom, short: gate top) -- the 'setup-type' rule; the transcribed levels.stop is
reported alongside for comparison.
"""
import json, sys, glob
import numpy as np, pandas as pd
import charts, stops
tz = "America/New_York"


def session(d5, plan_date):
    end = pd.Timestamp(plan_date, tz=tz).replace(hour=16, minute=0)
    start = (end - pd.Timedelta(days=1)).replace(hour=18, minute=0)
    while start.weekday() > 4: start -= pd.Timedelta(days=1)
    return d5[(d5.time >= start) & (d5.time <= end)].reset_index(drop=True)


import re
BREAK = re.compile(r"breakdown|breakout|persistent (weakness|strength)|weakness below|strength above|gap up|session uptrend", re.I)


def run_trade(bars, pt):
    """Fade (hold/LBAF/LAAF/failed reclaim): price trades into the gate, then a 5m close back out in the trade direction
    -> entry at the gate edge on that close; level = the extreme reached inside/through the gate before the reclaim (the sweep).
    Breakout (persistent weakness/strength, breakdown): price is at the gate, then a 5m close through its far side
    -> entry at the far edge; level = the extreme of the bounce against the trade before the break."""
    d = pt["dir"]; L = pt["levels"]; gate = sorted(L["gate"]); sgn = 1 if d == "long" else -1
    kind = "break" if BREAK.search(pt["name"] + " " + pt.get("gate", "")) else "fade"
    tg = [(min(t) if d == "long" else max(t)) if isinstance(t, (list, tuple)) else t for t in L["tgt"]]
    H, Lo, C = bars.High.values, bars.Low.values, bars.Close.values
    if kind == "fade":
        edge = gate[-1] if d == "long" else gate[0]                       # entry edge (near side)
        touched = np.where((Lo <= edge) if d == "long" else (H >= edge))[0]
        if not len(touched): return dict(triggered=False, kind=kind)
        i_t = touched[0]
        conf = np.where((C[i_t:] > edge) if d == "long" else (C[i_t:] < edge))[0]
        conf = [i_t + j for j in conf if j > 0] if len(conf) else []
        if not conf: return dict(triggered=False, kind=kind)
        i0 = conf[0]; entry = edge
        level = Lo[i_t:i0 + 1].min() if d == "long" else H[i_t:i0 + 1].max()   # the sweep extreme
    else:
        edge = gate[0] if d == "long" else gate[-1]                       # entry = break of the far side
        near = np.where((H >= gate[0]) if d == "long" else (Lo <= gate[-1]))[0]   # price has been at the zone
        if not len(near): return dict(triggered=False, kind=kind)
        i_t = near[0]
        conf = np.where((C[i_t:] > gate[-1]) if d == "long" else (C[i_t:] < gate[0]))[0]
        conf = [i_t + j for j in conf if j > 0] if len(conf) else []
        if not conf: return dict(triggered=False, kind=kind)
        i0 = conf[0]; entry = gate[-1] if d == "long" else gate[0]
        level = gate[0] if d == "long" else gate[-1]                      # wrong on a reclaim of the zone
    after = slice(i0 + 1, len(bars))
    t_idx = np.where((H[after] >= tg[0]) if d == "long" else (Lo[after] <= tg[0]))[0]
    i1 = i0 + 1 + t_idx[0] if len(t_idx) else len(bars) - 1
    seg_lo, seg_hi = Lo[i0 + 1:i1 + 1], H[i0 + 1:i1 + 1]
    if len(seg_lo) == 0: seg_lo, seg_hi = Lo[i0:i0 + 1], H[i0:i0 + 1]
    worst = seg_lo.min() if d == "long" else seg_hi.max()
    mae = (entry - worst) * sgn
    past_far = (level - worst) * sgn
    past_tx = (L["stop"][0] - worst) * sgn
    mfe = (H[after].max() - entry) if d == "long" else (entry - Lo[after].min()) if i0 + 1 < len(bars) else 0.0
    return dict(triggered=True, kind=kind, entry=float(entry), far=float(level), tx_level=L["stop"][0], t1=tg[0],
                target_hit=bool(len(t_idx)), entry_time=str(bars.time[i0]), worst=float(worst), mae=float(mae),
                past_far=float(past_far), past_tx=float(past_tx), mfe=float(mfe), bars_to_target=int(i1 - i0) if len(t_idx) else None)


def main(paths):
    rows = []
    for f in paths:
        p = json.load(open(f)); date = p["date"]
        A = {}; D = {}
        for pt in p["trades"]:
            s = pt["instrument"]
            if s not in A: A[s] = stops.analyze(s, date); D[s] = session(charts.load(s), date)
            r = run_trade(D[s], pt)
            r.update(date=date, id=pt["id"], sym=s, dir=pt["dir"], name=pt["name"][:40], atr5=A[s]["atr5"], atr15=A[s]["atr15"])
            rows.append(r)
    df = pd.DataFrame(rows)
    pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)
    trig = df[df.triggered == True].copy(); trig["target_hit"] = trig.target_hit.astype(bool)
    trig["mae_atr15"] = trig.mae / trig.atr15
    trig["past_far_atr5"] = trig.past_far / trig.atr5
    trig["past_far_atr15"] = trig.past_far / trig.atr15
    print(f"{len(df)} trades, {len(trig)} triggered, {int(trig.target_hit.sum())} hit target 1 after triggering\n")
    cols = ["date", "id", "dir", "kind", "entry", "far", "tx_level", "t1", "target_hit", "worst", "mae", "past_far", "past_far_atr5", "past_far_atr15", "mfe"]
    print(trig[cols].round(2).to_string(index=False))
    w = trig[trig.target_hit]
    print("\n--- winners (target 1 hit): excursion PAST the structural level (fade: sweep extreme · break: zone far side) ---")
    for q in (50, 75, 90, 100):
        print(f"  p{q}: {np.percentile(w.past_far, q):6.2f} pts  = {np.percentile(w.past_far_atr5, q):.2f} ATR5 = {np.percentile(w.past_far_atr15, q):.2f} ATR15")
    print(f"  winners that never went past the sweep extreme: {(w.past_far <= 0).sum()} / {len(w)}")
    print("\n--- stop rules: winners kept / losers cut (loser = target 1 never hit) ---")
    def floored(k):   # one tick past the sweep extreme, but never closer than k × ATR5 to the zone's edge
        def f(r):
            sgn = -1 if r.dir == "long" else 1
            edge = r.entry   # fade: entry edge; break: far side already (level == entry edge's opposite) -> same floor from entry
            tick = r.far + sgn * 0.25; fl = edge + sgn * k * r.atr5
            return min(tick, fl) if r.dir == "long" else max(tick, fl)
        return f
    rules = [("tick past sweep extreme", lambda r: r.far + (-0.25 if r.dir == "long" else 0.25)),
             ("sweep, floor 1.0 ATR5 from edge", floored(1.0)),
             ("sweep, floor 1.5 ATR5 from edge", floored(1.5)),
             ("sweep, floor 2.0 ATR5 from edge", floored(2.0)),
             ("sweep − 0.1 ATR5", lambda r: r.far + (-1 if r.dir == "long" else 1) * 0.1 * r.atr5),
             ("sweep − 0.25 ATR5", lambda r: r.far + (-1 if r.dir == "long" else 1) * 0.25 * r.atr5),
             ("sweep − 0.5 ATR5", lambda r: r.far + (-1 if r.dir == "long" else 1) * 0.5 * r.atr5),
             ("sweep − 0.25 ATR15", lambda r: r.far + (-1 if r.dir == "long" else 1) * 0.25 * r.atr15),
             ("sweep − 0.5 ATR15", lambda r: r.far + (-1 if r.dir == "long" else 1) * 0.5 * r.atr15),
             ("transcribed level − 0.1 ATR5", lambda r: r.tx_level + (-1 if r.dir == "long" else 1) * 0.1 * r.atr5),
             ("entry − 1.0 ATR15", lambda r: r.entry + (-1 if r.dir == "long" else 1) * 1.0 * r.atr15),
             ("entry − 1.5 ATR15", lambda r: r.entry + (-1 if r.dir == "long" else 1) * 1.5 * r.atr15)]
    out = []
    for name, fn in rules:
        kept = cut = 0; risk = []; pnl = []
        for _, r in trig.iterrows():
            st = fn(r); rk = abs(r.entry - st)
            if rk < 0.2 * r.atr15:   # same floor as the ladder: a stop inside the noise is widened to it
                rk = 0.2 * r.atr15; st = r.entry + (-1 if r.dir == "long" else 1) * rk
            stopped = (r.worst <= st) if r.dir == "long" else (r.worst >= st)
            if r.target_hit:
                kept += (not stopped); pnl.append(abs(r.t1 - r.entry) / rk if not stopped else -1.0)
            else:
                cut += stopped; pnl.append(-1.0 if stopped else -min(r.mae, rk) / rk)
            risk.append(rk / r.atr15)
        out.append((name, kept, int(trig.target_hit.sum()), cut, int((~trig.target_hit).sum()), np.median(risk), np.mean(pnl)))
    print(f"  {'rule':32} {'winners kept':>14} {'losers stopped':>15} {'median risk (ATR15)':>20} {'avg R/trade (tgt1 only)':>24}")
    for name, k, nw, c, nl, ar, pr in out:
        print(f"  {name:32} {k:>6}/{nw:<7} {c:>7}/{nl:<7} {ar:>20.2f} {pr:>24.2f}")
    df.to_csv("backtest_mae.csv", index=False)
    return df


if __name__ == "__main__":
    main(sys.argv[1:] or sorted(glob.glob("plans/plan-*.json")))
